# backend/main.py

"""
Main application file for the Pipecat real-time voice agent.
This script sets up a FastAPI server with a WebSocket endpoint that runs a
Pipecat pipeline, connecting a client to the Google Gemini Live API for a
real-time, voice-to-voice conversation with tool-using capabilities.
"""

# Standard library and dependency imports
import os
import uvicorn
import functools
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime


# Pipecat core and service imports
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketTransport,
    FastAPIWebsocketParams,
)
from pipecat.services.gemini_multimodal_live.gemini import (
    GeminiMultimodalLiveLLMService,
    InputParams,
    GeminiMultimodalModalities,
)
from pipecat.transcriptions.language import Language
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frameworks.rtvi import RTVIProcessor, RTVIConfig, RTVIObserver
from form_tools import (
    tools,
    handle_open_form,
    handle_update_field,
    handle_submit_form,
    enhanced_perf_tracker
)

# Load environment variables from .env file
load_dotenv()

# Ultra-fast, direct action prompt optimized for speed
SYSTEM_PROMPT = """
You are a friendly assistant. Chat normally until the user asks to register.

ONLY use tools when:
1. User says "register" or "sign up" → Call open_form tool
2. User gives name → Call update_field tool with field_name="name"  
3. User gives email → Call update_field tool with field_name="email"
4. User says "submit" → Call submit_form tool

DO NOT open forms automatically. Wait for the user to ask.
ALWAYS call the tool when needed. Never just talk about doing it.
"""

# Initialize the FastAPI application
app = FastAPI()


# Add CORS middleware - IMPORTANT for Vercel frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://*.vercel.app",  # Allow all Vercel domains temporarily
        "https://*.onrender.com",  # Allow Render domains 
        "http://localhost:3000",  # For local development
        "https://localhost:3000",  # For local HTTPS development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add health check endpoint for deployment verification
@app.get("/health")
async def health_check():
    """Health check endpoint for deployment verification"""
    return {"status": "healthy", "service": "voice-agent-backend"}

@app.get("/performance-report")
async def get_performance_report():
    """Get current performance metrics"""
    summary = enhanced_perf_tracker.get_performance_summary()
    return {"performance_summary": summary, "timestamp": datetime.now().isoformat()}

@app.post("/export-performance")
async def export_performance_data():
    """Export detailed performance data"""
    enhanced_perf_tracker.export_data("performance_results.json")
    return {"message": "Performance data exported to performance_results.json"}


@app.websocket("/voice")
async def websocket_endpoint(websocket: WebSocket):
    """
    This endpoint runs the real-time voice agent with function calling capabilities
    and proper conversation context management.
    """
    # Accept the WebSocket connection
    await websocket.accept()

    # Create an instance of the serializer to ensure frontend and backend
    # are using the same data format.
    serializer = ProtobufFrameSerializer()

    # Configure the transport layer for audio I/O and specify the serializer.
    # This is the bridge between the web client and the Pipecat pipeline.
    transport = FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            serializer=serializer,
        )
    )
    
    # The RTVIProcessor handles custom messaging between the backend and frontend.
    rtvi = RTVIProcessor(
        config=RTVIConfig(config=[]),
        transport=transport
    )

    # The GOOGLE_API_KEY environment variable is required.
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key is None:
        await websocket.close(code=1008, reason="Server configuration error")
        raise RuntimeError("GOOGLE_API_KEY environment variable is not set.")
        return

    # Initialize the Gemini service, passing the system prompt and tool definitions.
    gemini_service = GeminiMultimodalLiveLLMService(
        api_key=api_key,
        params=InputParams(
            language=Language.EN_US,
            modalities=GeminiMultimodalModalities.AUDIO,
            temperature=0.0,  # Adjust temperature for response variability
            top_p=0.7,  # Top-p sampling for more controlled responses
            top_k=10,  # Top-k sampling to limit response options
        ),
        tools=tools,  # Register custom tools with the Gemini service
        system_instruction=SYSTEM_PROMPT,
        inference_on_context_initialization=True # ensure the service continues processing
    )

    # Register event handlers for function calls to log their start and completion.
    @gemini_service.event_handler("on_function_calls_started")
    async def on_function_calls_started(service, function_calls):
        print(f"Function calls started: {[fc.function_name for fc in function_calls]}")

    @gemini_service.event_handler("on_function_calls_finished") 
    async def on_function_calls_finished(service, function_calls):
        print(f"Function calls finished: {[fc.function_name for fc in function_calls]}")
    

    # `functools.partial` creates new handler functions with the `rtvi` instance
    # pre-filled as the first argument, giving them access to the UI message channel.
    open_form_handler = functools.partial(handle_open_form, rtvi)
    update_field_handler = functools.partial(handle_update_field, rtvi)
    submit_form_handler = functools.partial(handle_submit_form, rtvi)

    # Each tool is registered with its corresponding handler function.
    gemini_service.register_function("open_form", open_form_handler)
    gemini_service.register_function("update_field", update_field_handler)
    gemini_service.register_function("submit_form", submit_form_handler)

    # The context object is created, passing both the initial messages and the tools.
    context = OpenAILLMContext(
    messages=[],
    tools=tools
)

    # A context aggregator is created from the LLM service and the context object.
    context_aggregator = gemini_service.create_context_aggregator(context)


    # The pipeline defines the flow of data and processing
    pipeline = Pipeline([
        transport.input(),          # Receives audio from the client
        rtvi,                       # Handles UI events
        context_aggregator.user(),  # Adds user speech to context
        gemini_service,             # Processes context and calls tools
        transport.output(),         # Sends generated audio to the client
        context_aggregator.assistant(), # Adds bot speech to context
    ])

    # The task wraps the pipeline and includes the RTVIObserver, which is
    # essential for the RTVIProcessor to function correctly.
    task = PipelineTask(
        pipeline,
        observers=[RTVIObserver(rtvi)]  # RTVIObserver to handle UI messages
    )

    # Event handlers manage the session lifecycle.
    @rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi):
        # This kicks off the conversation once the client is fully connected.
        await rtvi.set_bot_ready()
        # Kick off the conversation by sending the initial context (which is just the system prompt)
        await task.queue_frames([context_aggregator.user().get_context_frame()])
    
    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        await task.cancel()

    # Create a runner and execute the task.
    # This starts the agent and keeps it running until disconnection.
    runner = PipelineRunner()
    await runner.run(task)



if __name__ == "__main__":
    # This block allows running the server directly from the script.
    port = int(os.getenv("PORT", 8000))  # Use Render's PORT or fallback to 8000
    print(f"Starting FastAPI server for voice agent on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)