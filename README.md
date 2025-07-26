# FormFiller
Ultra-low latency AI voice agent for form filling using Pipecat and Gemini Live

A real-time voice-controlled form filling application built with **sub-500ms voice-to-voice communication** using the Pipecat framework and Google Gemini Live API.

![Voice Agent Demo](https://img.shields.io/badge/Status-Live%20Demo-brightgreen)
![Latency](https://img.shields.io/badge/Latency-Sub%20500ms-blue)
![Tech Stack](https://img.shields.io/badge/Stack-Next.js%20%7C%20FastAPI%20%7C%20Pipecat-orange)

## 🚀 Features

- **Ultra-Low Latency**: Sub-500ms voice-to-voice communication
- **Natural Voice Interaction**: Speak naturally to fill forms
- **Real-time Form Updates**: Watch fields populate as you speak
- **Intelligent Field Recognition**: AI automatically maps speech to form fields
- **Visual Feedback**: Real-time connection status and progress indicators
- **Responsive Design**: Works seamlessly across devices

## 🛠 Tech Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Pipecat Client JS** - Real-time audio streaming
- **WebSocket Transport** - Low-latency communication

### Backend
- **FastAPI** - High-performance Python web framework
- **Pipecat Framework** - AI voice agent orchestration
- **Google Gemini Live API** - Advanced speech processing
- **WebSocket** - Real-time bidirectional communication

## 📋 Prerequisites

- Node.js 18+ and npm/yarn
- Python 3.8+
- Google Cloud account with Gemini API access
- Modern browser with microphone support

## 🔧 Installation & Setup

### Frontend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd FormFiller/frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Environment Configuration**
   ```bash
   cp .env.example .env.local
   ```
   
   Update `.env.local`:
   ```env
   NEXT_PUBLIC_PIPECAT_URL=ws://localhost:8000/voice
   ```

4. **Run development server**
   ```bash
   npm run dev
   # or
   yarn dev
   ```

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd ../backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   ```
   
   Update `.env`:
   ```env
   GOOGLE_GEMINI_API_KEY=your_gemini_api_key_here
   PIPECAT_LOG_LEVEL=INFO
   ```

5. **Run FastAPI server**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## 🎯 Usage

1. **Start the Application**
   - Ensure both frontend (port 3000) and backend (port 8000) are running
   - Open your browser to `http://localhost:3000`

2. **Voice Interaction Flow**
   - Click the "Connect" button to establish voice connection
   - Say "I want to sign up" or similar to trigger form appearance
   - Speak naturally to fill form fields:
     - "My name is John Doe"
     - "My email is john@example.com"
     - "My phone number is 555-0123"
   - Say "submit" when all fields are complete

3. **Visual Feedback**
   - 🟢 Green dot: Connected and listening
   - 🟡 Yellow dot: Connecting
   - 🔴 Red dot: Connection error
   - Form fields highlight in green when filled

## 🚢 Deployment

### Frontend (Vercel)

1. **Deploy to Vercel**
   ```bash
   vercel --prod
   ```

2. **Environment Variables**
   Set in Vercel dashboard:
   ```
   NEXT_PUBLIC_PIPECAT_URL=wss://your-backend-domain.com/voice
   ```

### Backend (Railway/Render/AWS)

1. **Build and deploy your FastAPI backend**
2. **Set environment variables in your hosting platform**
3. **Update frontend environment to point to production backend**

## 📊 Performance Metrics

- **Voice-to-Voice Latency**: < 500ms target
- **Form Field Recognition**: Real-time as you speak
- **Connection Establishment**: < 2 seconds
- **Audio Quality**: 16kHz sampling rate
- **Supported Browsers**: Chrome, Firefox, Safari, Edge

## 🏗 Architecture

```
┌─────────────────┐    WebSocket     ┌─────────────────┐
│   Next.js App   │ ◄─────────────► │   FastAPI       │
│                 │                 │                 │
│ - Voice UI      │                 │ - Pipecat       │
│ - Form Display  │                 │ - Gemini Live   │
│ - WebSocket     │                 │ - Voice Process │
└─────────────────┘                 └─────────────────┘
```

## 🔍 Key Components

### Frontend Components
- `VoiceClient.tsx` - Main voice interaction component
- `FormDisplay.tsx` - Dynamic form rendering
- Connection state management and real-time updates

### Backend Components
- Voice stream processing with Pipecat
- Google Gemini Live API integration
- Form field extraction and validation
- WebSocket message routing

## 🐛 Troubleshooting

### Common Issues

1. **Connection Failed**
   - Ensure backend server is running on port 8000
   - Check firewall settings
   - Verify WebSocket URL in environment variables

2. **Microphone Not Working**
   - Grant microphone permissions in browser
   - Use HTTPS in production (required for mic access)
   - Test with different browsers

3. **High Latency**
   - Check network connection
   - Ensure backend is geographically close
   - Monitor CPU usage on backend server

4. **Form Not Appearing**
   - Check browser console for errors
   - Verify backend is sending correct message format
   - Test WebSocket connection manually

## 📝 API Reference

### WebSocket Messages

#### From Backend to Frontend
```typescript
// Open form
{
  type: "open_form",
  payload: {
    fields: [
      { name: "name", label: "Full Name", type: "text" },
      { name: "email", label: "Email", type: "email" }
    ]
  }
}

// Update field
{
  type: "update_field",
  payload: {
    field_name: "name",
    field_value: "John Doe"
  }
}

// Submit form
{
  type: "submit_form",
  payload: {}
}
```


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

##  Acknowledgments

- [Pipecat AI](https://pipecat.ai/) for the excellent voice agent framework
- [Google Gemini](https://ai.google.dev/) for advanced language processing
- [Vercel](https://vercel.com/) for seamless frontend deployment

## 📞 Support

For questions or support:
- Create an issue in this repository
- Check the [troubleshooting section](#🐛-troubleshooting)
- Review Pipecat documentation

---

**Built with ❤️ for ultra-low latency voice interactions**