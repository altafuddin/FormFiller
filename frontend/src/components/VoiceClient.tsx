// frontend/src/components/VoiceClient.tsx
'use client';

// Standard React/Next.js hook and type imports.
import { useEffect, useRef, useState } from "react";

// This is the client-side version of the Pipecat library.
import { PipecatClient } from "@pipecat-ai/client-js";

// This is the required transport package and its necessary components.
import {
    WebSocketTransport,
    ProtobufFrameSerializer,
} from "@pipecat-ai/websocket-transport";

// Standard TypeScript practice for defining state types.
type ConnectionState = "idle" | "connecting" | "connected" | "error";

// Defines the structure for a single form field object received from the backend.
interface FormField {
    name: string;
    label: string;
    type: string;
}

// A dedicated display component for rendering the form. It is "dumb" and only
// renders the data it is given via props.
function FormDisplay({ fields, values }: { fields: FormField[], values: Record<string, string> }) {
    return (
        <div className="w-full mt-8 p-6 bg-gray-50 border rounded-lg">
            <h2 className="text-xl font-semibold mb-4 text-left">Registration Form</h2>
            <div className="space-y-4">
                {fields.map((field) => (
                    <div key={field.name}>
                        <label className="block text-sm font-medium text-gray-700 text-left">{field.label}</label>
                        <input
                            type={field.type}
                            readOnly
                            value={values[field.name] || ''}
                            className="mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                            placeholder="..."
                        />
                    </div>
                ))}
            </div>
        </div>
    );
}


// Main component that manages the Pipecat client, connection state, and form state.
export default function VoiceClient() {
    // Standard React hook for managing object instances.
    const client = useRef<PipecatClient | null>(null);

    // Standard React hook for managing component state.
    const [connectionState, setConnectionState] = useState<ConnectionState>("idle");

    // State for managing the form's structure and its current values.
    const [formFields, setFormFields] = useState<FormField[] | null>(null);
    const [formValues, setFormValues] = useState<Record<string, string>>({});

    // Accessing client-side environment variables.
    const pipecatUrl = process.env.NEXT_PUBLIC_PIPECAT_URL || "ws://localhost:8000/voice";

    // Standard React hook for managing component lifecycle.
    useEffect(() => {
        const transport = new WebSocketTransport({
            serializer: new ProtobufFrameSerializer(),
        });

        // The PipecatClient is instantiated with the transport and a `callbacks` object.
        client.current = new PipecatClient({
            transport: transport,
            callbacks: {
                onConnected: () => setConnectionState("connected"),
                onDisconnected: () => {
                    setConnectionState("idle");
                    // When disconnected, clear the form from the UI.
                    setFormFields(null);
                    setFormValues({});
                },
                onError: () => setConnectionState("error"),
                // This handler listens for custom messages from the backend RTVIProcessor.
                onServerMessage: (message: any) => {
                    console.log("Received server message:", message);
                    const { type, payload } = message;
                    // A switch statement routes the message to the correct state update logic.
                    switch (type) {
                        case "open_form":
                            // When the backend says to open a form, we set the fields
                            // and clear any previous values.
                            setFormFields(payload.fields);
                            setFormValues({});
                            break;
                        case "update_field":
                            // When a field is updated, we add its new value to our state.
                            // Using the functional form of setState ensures we don't have stale state.
                            setFormValues(prevValues => ({
                                ...prevValues,
                                [payload.field_name]: payload.field_value,
                            }));
                            break;
                        case "submit_form":
                            // After submission, we clear the form from the UI.
                            console.log("Form submitted successfully!", formValues);
                            setFormFields(null);
                            setFormValues({});
                            break;
                    }
                },
            },
        });

        // Standard React `useEffect` cleanup function.
        return () => {
            client.current?.disconnect();
        };
    }, []); // Empty dependency array ensures this effect runs only once on mount.

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
            <div className="w-full">
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

            {/* Conditionally render the form only when its definition has been received. */}
            {formFields && (
                <FormDisplay fields={formFields} values={formValues} />
            )}
        </div>
    );
}