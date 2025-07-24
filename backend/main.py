# backend/main.py

"""
Main application file for the Pipecat real-time voice agent.
This script sets up a FastAPI server with a WebSocket endpoint that runs a
Pipecat pipeline, connecting a client to the Google Gemini Live API for a
real-time, voice-to-voice conversation.
"""

# Standard library and dependency imports
import os
import uvicorn
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
from pipecat.serializers.protobuf import ProtobufFrameSerializer
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from form_tools import (
    tools,
    handle_open_form,
    handle_update_field,
    handle_submit_form,
)

# Load environment variables from .env file
load_dotenv()

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
    
    # Initialize the Gemini service with the API key and input parameters.
    # The GOOGLE_API_KEY environment variable is required.
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key is None:
        raise RuntimeError("GOOGLE_API_KEY environment variable is not set.")
    gemini_service = GeminiMultimodalLiveLLMService(
        api_key=api_key,
        params=InputParams(
            modalities=GeminiMultimodalModalities.AUDIO
        ),
        tools=tools,  # Register custom tools with the Gemini service
    )
    
    # Each tool is registered with its corresponding handler function.
    gemini_service.register_function("open_form", handle_open_form)
    gemini_service.register_function("update_field", handle_update_field)
    gemini_service.register_function("submit_form", handle_submit_form)

    # The context object is created, passing both the initial messages and the tools.
    # This prompt is explicit about maintaining a state and handling the conversation flow.
    context = OpenAILLMContext(
        messages=[
        {
            "role": "system",
            "content": (
                "You are a voice assistant that helps users fill out a form. "
                "Your primary goal is to collect information and use your tools to update the form fields. "
                "Wait for the user to speak first."
                "The user will provide information piece by piece. After each piece of information, you MUST call the appropriate tool. "
                "Follow these steps:\n"
                "1. When the user wants to start or open a form, call `open_form`.\n"
                "2. For each piece of data the user provides (like name, email, etc.), you MUST call the `update_field` tool.\n"
                "3. Acknowledge every successful tool call with a brief confirmation (e.g., 'Got it, what's next?').\n"
                "4. Continue asking for the next piece of information until the user says to submit.\n"
                "5. When the user says 'submit' or 'I'm done', you MUST call the `submit_form` tool.\n"
                "Do not stop calling tools until the `submit_form` tool has been called."
            ),
        }
    ],
    tools=tools)

    # A context aggregator is created from the LLM service and the context object.
    context_aggregator = gemini_service.create_context_aggregator(context)


    # The pipeline is updated to include the context_aggregator's user and assistant processors.
    # This ensures the conversation history is maintained correctly.
    pipeline = Pipeline([
        transport.input(),
        context_aggregator.user(),
        gemini_service,
        transport.output(),
        context_aggregator.assistant(),
    ])

    # Create a task to run the pipeline.
    task = PipelineTask(pipeline)

    # Create a runner and execute the task.
    # This starts the agent and keeps it running until disconnection.
    runner = PipelineRunner()
    await runner.run(task)



if __name__ == "__main__":
    # This block allows running the server directly from the script.
    print("Starting FastAPI server for voice agent on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)