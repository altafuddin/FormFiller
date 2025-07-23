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


# Load environment variables from .env file
load_dotenv()

# Initialize the FastAPI application
app = FastAPI()

@app.websocket("/voice")
async def websocket_endpoint(websocket: WebSocket):
    """
    This endpoint accepts a WebSocket connection, sets up a Pipecat pipeline,
    and runs the real-time voice-to-voice Gemini agent.
    """
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

    # Design Choice: Instantiate the Gemini Live service. This is the core
    # of our agent. We use environment variables for the API key for security.
    # EVIDENCE: Instantiation verified from the Gemini Multimodal Live docs.
    # The GOOGLE_API_KEY environment variable is required.
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key is None:
        raise RuntimeError("GOOGLE_API_KEY environment variable is not set.")
    gemini_service = GeminiMultimodalLiveLLMService(
        api_key=api_key,
        params=InputParams(
            modalities=GeminiMultimodalModalities.AUDIO
        )
    )
    
    
    # Assemble the pipeline.
    # The flow is: User Audio -> Transport -> Gemini -> Transport -> User
    pipeline = Pipeline([
        transport.input(),
        gemini_service,
        transport.output(),
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
