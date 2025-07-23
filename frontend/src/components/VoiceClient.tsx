// frontend/src/components/VoiceClient.tsx
'use client';

// Standard React/Next.js hook and type imports.
import { useEffect, useRef, useState } from "react";

// Verified from multiple approved sources.
import { PipecatClient } from "@pipecat-ai/client-js";

// Verified from the "WebSocketTransport documentation".
// This is the required transport package and its necessary components.
import {
    WebSocketTransport,
    ProtobufFrameSerializer,
} from "@pipecat-ai/websocket-transport";

// Standard TypeScript practice for defining state types.
type ConnectionState = "idle" | "connecting" | "connected" | "error";

export default function VoiceClient() {
    // Standard React hook for managing object instances.
    const client = useRef<PipecatClient | null>(null);

    // Standard React hook for managing component state.
    const [connectionState, setConnectionState] = useState<ConnectionState>("idle");

    // Verified Next.js pattern for accessing client-side environment variables.
    const pipecatUrl = process.env.NEXT_PUBLIC_PIPECAT_URL || "ws://localhost:8000/voice";

    // Standard React hook for managing component lifecycle.
    useEffect(() => {
        // Verified instantiation pattern from "WebSocketTransport documentation".
        const transport = new WebSocketTransport({
            serializer: new ProtobufFrameSerializer(),
        });

        // Verified from the `RTVIEventCallbacks` type definition.
        // The PipecatClient is instantiated with the transport and a `callbacks` object.
        client.current = new PipecatClient({
            transport: transport,
            callbacks: {
                onConnected: () => setConnectionState("connected"),
                onDisconnected: () => setConnectionState("idle"),
                onError: () => setConnectionState("error"),
            },
        });

        // Standard React `useEffect` cleanup function.
        return () => {
            client.current?.disconnect();
        };
    }, []);

    const handleConnect = async () => {
        if (!client.current) return;

        // Manually set the state to "connecting" before the async call.
        // This is necessary as there is no `onConnecting` callback.
        setConnectionState("connecting");

        try {
            // Verified `connect` method signature from "WebSocketTransport documentation".
            await client.current.connect({
                ws_url: pipecatUrl,
            });
        } catch (error) {
            console.error("Connection failed:", error);
        }
    };

    const handleDisconnect = () => {
        client.current?.disconnect();
    };

    const isConnected = connectionState === "connected";
    const isConnecting = connectionState === "connecting";

    return (
        <div className="p-8 border rounded-lg shadow-lg max-w-md mx-auto mt-10 text-center bg-white">
            <h1 className="text-2xl font-bold mb-4">Pipecat Voice Agent</h1>
            <p className="mb-6 text-gray-600">
                Status: <span className={`font-mono px-2 py-1 rounded ${isConnected ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>{connectionState}</span>
            </p>
            <button
                onClick={isConnected ? handleDisconnect : handleConnect}
                disabled={isConnecting}
                className={`w-full px-4 py-2 text-white font-semibold rounded-lg transition-colors
          ${isConnecting ? 'bg-yellow-500 cursor-not-allowed' : ''}
          ${isConnected ? 'bg-red-600 hover:bg-red-700' : ''}
          ${!isConnected && !isConnecting ? 'bg-blue-600 hover:bg-blue-700' : ''}
        `}
            >
                {isConnecting ? "Connecting..." : isConnected ? "Disconnect" : "Connect"}
            </button>
            {connectionState === "error" && (
                <p className="text-red-500 mt-4">Connection failed. Check the console and ensure the backend server is running.</p>
            )}
        </div>
    );
}