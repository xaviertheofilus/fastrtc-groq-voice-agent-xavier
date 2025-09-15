#### Voice Agent Multibahasa🚀

link demo : https://youtu.be/u9s-UUN91Bc

## Overview

Voice Agent Multibahasa is an AI-powered voice assistant that enables real-time multilingual communication in Indonesian and English using open-source models running entirely locally. This solution provides a comprehensive voice interface with speech-to-text, text-to-speech, and document-based question answering capabilities without requiring external API services.

<img width="1919" height="995" alt="image" src="https://github.com/user-attachments/assets/cad81f01-1629-4950-bfdf-3ae50427165d" />


## Key Features

- **Speech-to-Text (STT)**: Utilizes Whisper for accurate audio-to-text transcription
- **Text-to-Speech (TTS)**: Implements Kokoro with gTTS fallback for speech synthesis
- **Retrieval-Augmented Generation (RAG)**: Employs Ollama and FAISS for document processing and contextual responses
- **Multilingual Support**: Native support for Indonesian and English languages
- **Real-time Communication**: WebSocket-based bidirectional communication
- **Document Processing**: PDF upload and processing for knowledge-based responses
- **Local Processing**: Complete offline operation without external dependencies

## Technical Architecture

- **Backend Framework**: FastAPI with Uvicorn server
- **AI Models**: 
  - Whisper (OpenAI) for speech recognition
  - Ollama (Phi model) for language processing
  - Sentence Transformers for document embeddings
  - Kokoro/gTTS for speech synthesis
- **Vector Database**: FAISS for efficient similarity search
- **Frontend**: Vanilla JavaScript with WebAudio API
- **Audio Processing**: PyDub for audio format conversion

## System Requirements

- **Python**: Version 3.8 or higher
- **Ollama**: Must be installed and running
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: Minimum 2GB available space
- **Operating System**: Windows 10+, macOS 10.15+, or Linux Ubuntu 18.04+

## Installation Guide

### 1. Install Ollama

Download and install Ollama from the official website: https://ollama.ai/

After installation, start the service:
```bash
ollama serve
```

Download the required language model:
```bash
ollama pull phi
```

### 2. Clone the Repository

```bash
git clone https://github.com/your-username/voice-agent-multibahasa.git
cd voice-agent-multibahasa
```

### 3. Set Up Python Environment

Create a virtual environment and install dependencies:

```bash
# For Windows
python -m venv venv
venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 4. Download Whisper Models

The application will automatically download Whisper models on first run, but you can pre-download them:

```bash
python -c "import whisper; whisper.load_model('base', download_root='./models')"
```

### 5. Run the Application

```bash
python run.py
```

The application will be available at http://localhost:8000

## Usage Instructions

### 1. Document Upload (Optional)

- Click the "Upload PDF" button to add knowledge documents
- Supported formats: PDF and text files
- Uploaded documents are processed and used to enhance response accuracy

### 2. Voice Interaction

- Click the "Start Recording" button and begin speaking
- Release the button to send the audio for processing
- The AI will respond with both text and audio responses

### 3. Language Support

- **Indonesian**: Default language, automatically detected
- **English**: Activated when English keywords are detected

## Project Structure

```
voice-agent-multibahasa/
├── data/                   # Directory for document storage
├── models/                 # Whisper model files
├── static/                 # Frontend assets
│   ├── index.html         # Main application page
│   ├── style.css          # Application styles
│   └── script.js          # Client-side functionality
├── app.py                 # Main FastAPI application
├── rag_processor.py       # RAG processing implementation
├── stt_processor.py       # Speech-to-text processing
├── tts_processor.py       # Text-to-speech processing
├── setup_environment.py   # Environment configuration
├── run.py                 # Application entry point
├── requirements.txt       # Python dependencies
└── README.md             # Project documentation
```

## API Documentation

### Endpoints

- `GET /`: Main application interface
- `GET /health`: System health status
- `GET /api/status`: Application status information
- `GET /restart-ollama`: Manual Ollama restart endpoint
- `POST /upload`: Document upload endpoint
- `WS /ws`: WebSocket connection for real-time communication

### WebSocket Protocol

The application uses a JSON-based protocol over WebSocket:

```json
// Client to Server
{
  "type": "audio",
  "data": "base64_encoded_audio_data"
}

// Server to Client
{
  "type": "transcript",
  "data": "transcribed_text"
}

{
  "type": "response_text",
  "text": "generated_response"
}

{
  "type": "response_audio",
  "data": "base64_encoded_audio_response"
}
```

## Troubleshooting

### Common Issues

1. **Ollama Service Not Running**
   ```bash
   # Check if Ollama is running
   ollama list
   
   # Start the service if not running
   ollama serve
   ```

2. **Port 11434 Already in Use**
   ```bash
   # Terminate existing Ollama processes
   pkill ollama  # Linux/macOS
   taskkill /im ollama.exe /f  # Windows
   
   # Restart the service
   ollama serve
   ```

3. **Missing Dependencies**
   ```bash
   # Reinstall requirements
   pip install -r requirements.txt
   ```

4. **Audio Permission Issues**
   - Ensure microphone access is granted in your browser
   - Check system audio settings

5. **Performance Optimization**
   - Close other memory-intensive applications
   - Consider using a smaller Whisper model (tiny) for lower-resource environments

## Contributing

We welcome contributions to enhance this project. Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please ensure your code follows PEP 8 guidelines and includes appropriate tests.

## License

This project is distributed under the MIT License. See the LICENSE file for complete details.

## Acknowledgments

- OpenAI for the Whisper speech recognition model
- Ollama for the efficient language model framework
- FastAPI team for the excellent web framework
- Hugging Face for transformer models and tools

## Support

For technical support, please open an issue in the GitHub repository with detailed information about your problem, including:

- Operating system and version
- Python version
- Steps to reproduce the issue
- Error messages or logs

## Version History

- 1.0.0
  - Initial release with basic functionality
  - Support for Indonesian and English languages
  - PDF document processing capabilities
  - Real-time voice communication

---

**Note**: This project is a prototype and may require additional testing and optimization for production use. Ensure thorough testing before deployment to production environments.
