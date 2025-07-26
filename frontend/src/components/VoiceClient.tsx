// FIXED VERSION - frontend/src/components/VoiceClient.tsx
'use client';

import { useEffect, useRef, useState } from "react";
import { PipecatClient } from "@pipecat-ai/client-js";
import {
    WebSocketTransport,
    ProtobufFrameSerializer,
} from "@pipecat-ai/websocket-transport";

type ConnectionState = "idle" | "connecting" | "connected" | "error";

interface FormField {
    name: string;
    label: string;
    type: string;
}

function FormDisplay({ fields, values }: { fields: FormField[], values: Record<string, string> }) {
    return (
        <div style={{
            width: '100%',
            maxWidth: '672px',
            margin: '0 auto' // Changed from '32px auto 0' to '0 auto'
        }}>
            <div style={{
                background: 'white',
                borderRadius: '8px',
                padding: '32px',
                boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                border: '1px solid #dbeafe'
            }}>
                <h2 style={{
                    fontSize: '24px',
                    fontWeight: '600',
                    color: '#1f2937',
                    marginBottom: '24px',
                    textAlign: 'center'
                }}>Registration Form</h2>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    {fields.map((field) => (
                        <div key={field.name}>
                            <label style={{
                                display: 'block',
                                fontSize: '14px',
                                fontWeight: '500',
                                color: '#374151',
                                marginBottom: '8px'
                            }}>
                                {field.label}
                            </label>
                            <input
                                type={field.type}
                                readOnly
                                value={values[field.name] || ''}
                                style={{
                                    width: '100%',
                                    padding: '12px 16px',
                                    border: values[field.name] ? '1px solid #86efac' : '1px solid #d1d5db',
                                    borderRadius: '8px',
                                    color: '#1f2937',
                                    background: values[field.name] ? '#f0fdf4' : '#f9fafb',
                                    fontSize: '16px'
                                }}
                                placeholder="Speak to fill this field..."
                            />
                        </div>
                    ))}
                </div>

                <div style={{
                    marginTop: '24px',
                    paddingTop: '16px',
                    borderTop: '1px solid #e5e7eb'
                }}>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        fontSize: '14px',
                        color: '#4b5563'
                    }}>
                        <span>Completed: {Object.keys(values).length} of {fields.length} fields</span>
                        <div style={{ display: 'flex', gap: '4px' }}>
                            {fields.map((_, i) => (
                                <div
                                    key={i}
                                    style={{
                                        width: '12px',
                                        height: '12px',
                                        borderRadius: '50%',
                                        background: Object.keys(values).length > i ? '#4ade80' : '#d1d5db'
                                    }}
                                />
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function VoiceClient() {
    const client = useRef<PipecatClient | null>(null);
    const [connectionState, setConnectionState] = useState<ConnectionState>("idle");
    const [formFields, setFormFields] = useState<FormField[] | null>(null);
    const [formValues, setFormValues] = useState<Record<string, string>>({});

    const pipecatUrl = process.env.NEXT_PUBLIC_PIPECAT_URL || "ws://localhost:8000/voice";

    // Check if form is active
    const isFormActive = formFields !== null;

    useEffect(() => {
        const transport = new WebSocketTransport({
            serializer: new ProtobufFrameSerializer(),
        });

        client.current = new PipecatClient({
            transport: transport,
            callbacks: {
                onConnected: () => setConnectionState("connected"),
                onDisconnected: () => {
                    setConnectionState("idle");
                    setFormFields(null);
                    setFormValues({});
                },
                onError: () => setConnectionState("error"),
                onServerMessage: (message: any) => {
                    console.log("Received server message:", message);
                    const { type, payload } = message;
                    switch (type) {
                        case "open_form":
                            console.log("Opening form with fields:", payload.fields);
                            setFormFields(payload.fields);
                            setFormValues({});
                            break;
                        case "update_field":
                            console.log("Updating field:", payload.field_name, "with value:", payload.field_value);
                            setFormValues(prevValues => ({
                                ...prevValues,
                                [payload.field_name]: payload.field_value,
                            }));
                            break;
                        case "submit_form":
                            console.log("Form submitted successfully!", formValues);
                            setFormFields(null);
                            setFormValues({});
                            break;
                        default:
                            console.log("Unknown message type:", type, payload);
                    }
                },
            },
        });

        return () => {
            client.current?.disconnect();
        };
    }, []);

    const handleConnect = async () => {
        if (!client.current) return;

        setConnectionState("connecting");

        try {
            await client.current.connect({
                ws_url: pipecatUrl,
            });
        } catch (error) {
            console.error("Connection failed:", error);
            setConnectionState("error");
        }
    };

    const handleDisconnect = () => {
        client.current?.disconnect();
    };

    const isConnected = connectionState === "connected";
    const isConnecting = connectionState === "connecting";

    console.log("Current state:", {
        connectionState,
        formFields,
        formValues,
        fieldsCount: formFields?.length || 0,
        valuesCount: Object.keys(formValues).length
    });

    return (
        <div style={{ width: '100%' }}>
            {/* How to Use Section - Only show when form is NOT active */}
            {!isFormActive && (
                <div style={{
                    background: 'white',
                    borderRadius: '8px',
                    padding: '24px',
                    boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                    border: '1px solid #dbeafe',
                    marginBottom: '32px'
                }}>
                    <h2 style={{
                        fontSize: '20px',
                        fontWeight: '600',
                        color: '#374151',
                        marginBottom: '16px',
                        margin: '0 0 16px 0'
                    }}>How to Use</h2>

                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                        gap: '16px',
                        fontSize: '14px'
                    }}>
                        <div style={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            padding: '12px'
                        }}>
                            <div style={{
                                width: '40px',
                                height: '40px',
                                background: '#dbeafe',
                                borderRadius: '50%',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                marginBottom: '12px'
                            }}>
                                <span style={{ color: '#2563eb', fontWeight: 'bold' }}>1</span>
                            </div>
                            <p style={{
                                textAlign: 'center',
                                color: '#4b5563',
                                margin: '0'
                            }}>
                                Click "Connect" to start the voice session
                            </p>
                        </div>

                        <div style={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            padding: '12px'
                        }}>
                            <div style={{
                                width: '40px',
                                height: '40px',
                                background: '#dbeafe',
                                borderRadius: '50%',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                marginBottom: '12px'
                            }}>
                                <span style={{ color: '#2563eb', fontWeight: 'bold' }}>2</span>
                            </div>
                            <p style={{ textAlign: 'center', color: '#4b5563' }}>
                                Speak naturally when the form appears
                            </p>
                        </div>

                        <div style={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            padding: '12px'
                        }}>
                            <div style={{
                                width: '40px',
                                height: '40px',
                                background: '#dbeafe',
                                borderRadius: '50%',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                marginBottom: '12px'
                            }}>
                                <span style={{ color: '#2563eb', fontWeight: 'bold' }}>3</span>
                            </div>
                            <p style={{ textAlign: 'center', color: '#4b5563' }}>
                                Watch your form fill automatically
                            </p>
                        </div>
                    </div>
                </div>
            )}

            {/* Connection Section */}
            <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                marginBottom: '24px'
            }}>
                {/* Status Display */}
                <div style={{ marginBottom: '24px' }}>
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '12px',
                        padding: '12px 24px',
                        background: 'white',
                        borderRadius: '50px',
                        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                        border: '1px solid #dbeafe'
                    }}>
                        <div style={{
                            width: '12px',
                            height: '12px',
                            borderRadius: '50%',
                            background:
                                isConnected ? '#4ade80' :
                                    isConnecting ? '#fbbf24' :
                                        connectionState === "error" ? '#ef4444' : '#9ca3af'
                        }}></div>
                        <span style={{
                            fontSize: '14px',
                            fontWeight: '500',
                            color: '#374151'
                        }}>
                            {connectionState === "idle" ? "Ready to Connect" :
                                connectionState === "connecting" ? "Connecting..." :
                                    connectionState === "connected" ? "Connected - Listening" :
                                        "Connection Error"}
                        </span>
                    </div>
                </div>

                {/* Connect Button */}
                <button
                    onClick={isConnected ? handleDisconnect : handleConnect}
                    disabled={isConnecting}
                    style={{
                        padding: '16px 32px',
                        borderRadius: '8px',
                        fontWeight: '600',
                        fontSize: '18px',
                        minWidth: '192px',
                        border: 'none',
                        cursor: isConnecting ? 'not-allowed' : 'pointer',
                        background:
                            isConnecting ? '#eab308' :
                                isConnected ? '#ef4444' :
                                    '#3b82f6',
                        color: 'white',
                        transition: 'all 0.2s'
                    }}
                    onMouseOver={(e) => {
                        if (!isConnecting) {
                            e.currentTarget.style.background =
                                isConnected ? '#dc2626' : '#2563eb';
                        }
                    }}
                    onMouseOut={(e) => {
                        e.currentTarget.style.background =
                            isConnecting ? '#eab308' :
                                isConnected ? '#ef4444' :
                                    '#3b82f6';
                    }}
                >
                    {isConnecting ? "Connecting..." : isConnected ? "Disconnect" : "Connect"}
                </button>

                {/* Error Message */}
                {connectionState === "error" && (
                    <div style={{
                        marginTop: '16px',
                        padding: '16px',
                        background: '#fef2f2',
                        border: '1px solid #fecaca',
                        borderRadius: '8px',
                        maxWidth: '384px'
                    }}>
                        <p style={{
                            color: '#dc2626',
                            fontSize: '14px',
                            textAlign: 'center',
                            margin: 0
                        }}>
                            Connection failed. Please ensure the backend server is running and try again.
                        </p>
                    </div>
                )}

                {/* Waiting State - Only show when connected but no form */}
                {isConnected && !formFields && (
                    <div style={{
                        marginTop: '24px',
                        padding: '24px',
                        background: '#eff6ff',
                        border: '1px solid #bfdbfe',
                        borderRadius: '8px',
                        maxWidth: '384px'
                    }}>
                        <div style={{ textAlign: 'center' }}>
                            <p style={{
                                color: '#1d4ed8',
                                fontWeight: '500',
                                marginBottom: '4px'
                            }}>Ready for Voice Input</p>
                            <p style={{
                                color: '#2563eb',
                                fontSize: '14px',
                                margin: 0
                            }}>Start speaking to begin filling the form</p>
                        </div>
                    </div>
                )}
            </div>

            {/* Form Display - Now appears right after connection section */}
            {formFields && (
                <FormDisplay fields={formFields} values={formValues} />
            )}
        </div>
    );
}