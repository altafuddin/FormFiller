// frontend/src/app/page.tsx
import VoiceClient from "../components/VoiceClient";

export default function Home() {
    return (
        <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-50">
            <VoiceClient />
        </main>
    );
}