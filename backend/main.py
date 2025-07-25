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

# This prompt is engineered to provide a clear, rules-based workflow for the LLM.
SYSTEM_PROMPT = """
You are a friendly and helpful voice assistant. Your primary goal is to help users fill out a 'registration' form.


[RULES]
1.  When the user first indicates they want to sign up or register, your first and only action is to call the `open_form` tool with `form_type` set to "registration".
2.  Check status if the form opened, if successfully the form is open, you will ask for the user's full name.
3.  When the user provides their name, you MUST call the `update_field` tool with `field_name` as "name" and `field_value` as the user's provided name.
4.  After the name is updated by calling the `update_field` tool, you will ask for their email address.
5.  When the user provides their email, you MUST call the `update_field` tool with `field_name` as "email" and `field_value` as the user's provided email.
6.  After the email is updated by calling the `update_field` tool, you will ask for their phone number.
7.  When the user provides their phone number, you MUST call the `update_field` tool with `field_name` as "phone_number" and `field_value` as the user's provided phone number.
8.  After the phone number is updated by calling the `update_field` tool, you MUST ask the user to confirm if they want to submit the form.
9.  If and only if the user confirms, you MUST call the `submit_form` tool.

Always check for these keywords in user responses:
- "register", "sign up", "create account" - indicates the user wants to fill out the registration form, call the open_form tool.
- "name", "full name" - indicates the user is providing their name, call the update_field tool with "name" as the field name.
- "email", "email address" - indicates the user is providing their email, call the update_field tool with "email" as the field name.
- "phone", "phone number" - indicates the user is providing their phone number, call the update_field tool with "phone_number" as the field name.
- "submit", "finish", "done" - indicates the user wants to submit the form, call the submit_form tool.

If the user is not trying to fill out a form, just have a normal, friendly conversation.
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
            temperature=0.6,  # Adjust temperature for response variability
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