// FIXED VERSION - frontend/src/app/page.tsx
import VoiceClient from "../components/VoiceClient";

export default function Home() {
    return (
        <div style={{
            minHeight: '100vh',
            background: 'linear-gradient(to bottom right, #dbeafe, #f1f5f9)',
            padding: '48px 24px',
            fontFamily: 'system-ui, -apple-system, sans-serif'
        }}>
            <main style={{
                display: 'flex',
                minHeight: 'auto',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'flex-start'
            }}>
                {/* Header Section */}
                <div style={{
                    width: '100%',
                    maxWidth: '672px',
                    textAlign: 'center',
                    marginBottom: '48px'
                }}>
                    <h1 style={{
                        fontSize: '36px',
                        fontWeight: 'bold',
                        color: '#1f2937',
                        marginBottom: '16px',
                        margin: '0 0 16px 0'
                    }}>
                        Voice Form Filler
                    </h1>

                    <p style={{
                        fontSize: '18px',
                        color: '#4b5563',
                        marginBottom: '32px',
                        lineHeight: '1.75',
                        margin: '0 0 32px 0'
                    }}>
                        Fill out forms using your voice. Simply connect, speak naturally,
                        and watch as your words are converted into form data instantly.
                    </p>
                </div>

                {/* Voice Client Component - Now handles its own layout logic */}
                <div style={{ width: '100%', maxWidth: '896px' }}>
                    <VoiceClient />
                </div>
            </main>
        </div>
    );
}