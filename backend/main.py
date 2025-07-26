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
)

# Load environment variables from .env file
load_dotenv()

# Ultra-fast, direct action prompt optimized for speed
SYSTEM_PROMPT = """
You are a friendly voice assistant helping users register. Use tools properly, calmly, one step at a time.
Do not open forms or submit until explicitly requested by the user.

Flow Rules:

1. When user says “register” or similar → call **open_form(form_type="registration")**. After tool runs, say “Form opened. What’s your full name?”

2. When user gives their name → call **update_field(field_name="name", field_value=[name])** immediately. Then ask for email.

3.  User provides email → IMMEDIATELY call update_field(field_name="email", field_value="[email]")

4. When user says "submit" or similar submission → you MUST call **submit_form()** exactly once. Then say “Done! Your registration is complete.”

Important:
• Always **CALL THE TOOL**, never just mention it being done. Such as saying "I have submitted your form" without calling **submit_form()**.
• Always call **update_field()** immediately after user provides information.
• Only proceed to the next step after tool confirmation.
• Do not skip fields; don’t auto-fill or repeat.
• If user gives wrong info (like saying email instead of name), gently remind: “We’re collecting your [current field]. Please provide that first.”
If user shifts topic mid-form, gently remind: “We’re collecting your [current field], please continue.”
If user talks about anything else outside of registration, respond normally and wait for valid trigger.
"""

# Initialize the FastAPI application
app = FastAPI()

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
        raise RuntimeError("GOOGLE_API_KEY environment variable is not set.")
    
    # Initialize the Gemini service, passing the system prompt and tool definitions.
    gemini_service = GeminiMultimodalLiveLLMService(
        api_key=api_key,
        params=InputParams(
            language=Language.EN_US,
            modalities=GeminiMultimodalModalities.AUDIO,
            temperature=0.3,  # Adjust temperature for response variability
            top_p=0.9,  # Top-p sampling for more controlled responses
            top_k=40,  # Top-k sampling to limit response options
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
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT}
    ],
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
    print("Starting FastAPI server for voice agent on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)