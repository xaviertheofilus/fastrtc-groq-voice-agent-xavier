from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import asyncio
import base64
import os
import logging
import subprocess
import psutil
import time
from rag_processor import RAGProcessor
from stt_processor import STTProcessor
from tts_processor import TTSProcessor

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Multilingual Voice Agent", version="1.0.0")

# Initialize processors
rag_processor = None
stt_processor = None
tts_processor = None

def is_ollama_running():
    """Check if Ollama is already running"""
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                return True
        return False
    except Exception as e:
        logger.error(f"Error checking Ollama processes: {str(e)}")
        return False

def start_ollama():
    """Start Ollama service if not running"""
    if not is_ollama_running():
        try:
            # Start Ollama in background
            subprocess.Popen(["ollama", "serve"], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            logger.info("Starting Ollama service...")
            
            # Wait for Ollama to be ready
            time.sleep(5)
            
            # Check if model exists, pull if not
            try:
                result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=30)
                if "phi" not in result.stdout:
                    logger.info("Downloading phi model...")
                    subprocess.run(["ollama", "pull", "phi"], check=True, timeout=300)
            except subprocess.TimeoutExpired:
                logger.warning("Ollama list command timed out, but continuing...")
            except Exception as e:
                logger.warning(f"Could not check models: {str(e)}")
                
            return True
        except Exception as e:
            logger.error(f"Failed to start Ollama: {str(e)}")
            return False
    return True

def initialize_processors():
    """Initialize all processors with error handling"""
    global rag_processor, stt_processor, tts_processor
    
    try:
        # Start Ollama if not running
        if not start_ollama():
            logger.error("Failed to start Ollama")
            return False
        
        # Check if Ollama is responsive
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                logger.error("Ollama is not responding")
                return False
        except subprocess.TimeoutExpired:
            logger.warning("Ollama list command timed out, but continuing initialization...")
        except Exception as e:
            logger.warning(f"Ollama check had issues: {str(e)}")
        
        # Initialize processors
        rag_processor = RAGProcessor()
        stt_processor = STTProcessor(model_size="base")
        tts_processor = TTSProcessor()
        
        logger.info("All processors initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing processors: {str(e)}")
        return False

# Initialize processors on startup
if not initialize_processors():
    logger.warning("Failed to initialize processors on startup. They will be initialized on first request.")

# Mount static files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    except FileNotFoundError:
        logger.error("index.html not found")
        return HTMLResponse("<h1>Error: Frontend files not found</h1>")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Ensure processors are initialized
    global rag_processor, stt_processor, tts_processor
    
    if rag_processor is None or stt_processor is None or tts_processor is None:
        if not initialize_processors():
            await websocket.close(code=1011, reason="Processors failed to initialize")
            return
    
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            # Receive data from client
            data = await websocket.receive_json()
            
            if data["type"] == "audio":
                try:
                    # Decode base64 audio data
                    audio_data = base64.b64decode(data["data"])
                    
                    # Transcribe audio to text
                    transcript = stt_processor.transcribe_audio(audio_data)
                    logger.info(f"Transcribed: {transcript}")
                    
                    # Send transcript back to client
                    await websocket.send_json({"type": "transcript", "data": transcript})
                    
                    # Process question with RAG
                    response = rag_processor.query(transcript)
                    logger.info(f"Generated response: {response}")
                    
                    # Send text response immediately
                    await websocket.send_json({
                        "type": "response_text", 
                        "text": response
                    })
                    
                    # Detect language - prioritize Indonesian
                    language = "id"
                    if any(word in transcript.lower() for word in ['english', 'inggris', 'hello', 'hi', 'how are you']):
                        language = "en"
                    
                    # Synthesize response to speech
                    audio_response = tts_processor.synthesize_speech(response, language)
                    if audio_response:
                        audio_b64 = base64.b64encode(audio_response).decode("utf-8")
                        await websocket.send_json({
                            "type": "response_audio", 
                            "data": audio_b64
                        })
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "data": "Failed to generate audio response"
                        })
                    
                except Exception as e:
                    logger.error(f"Error processing audio: {str(e)}")
                    await websocket.send_json({
                        "type": "error",
                        "data": f"Error processing request: {str(e)}"
                    })
                    
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        # Save uploaded file to data directory
        file_location = f"data/{file.filename}"
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())
        
        # Reinitialize RAG processor to include new document
        global rag_processor
        rag_processor.setup_qa_chain()
        
        return JSONResponse(
            status_code=200,
            content={"message": "File uploaded successfully", "filename": file.filename}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Endpoint untuk memeriksa status Ollama dan komponen lainnya"""
    try:
        # Cek status Ollama
        try:
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                return JSONResponse(
                    status_code=500,
                    content={"status": "error", "message": "Ollama tidak berjalan", "details": result.stderr}
                )
            
            # Cek model phi tersedia
            if "phi" not in result.stdout:
                return JSONResponse(
                    status_code=500,
                    content={"status": "error", "message": "Model phi tidak ditemukan di Ollama"}
                )
        except subprocess.TimeoutExpired:
            # Timeout doesn't necessarily mean Ollama isn't working
            logger.warning("Ollama health check timed out")
        except Exception as e:
            logger.warning(f"Ollama health check had issues: {str(e)}")
        
        # Cek status processors
        processors_status = {
            "rag_processor": rag_processor is not None,
            "stt_processor": stt_processor is not None,
            "tts_processor": tts_processor is not None,
            "documents_loaded": rag_processor.has_documents if rag_processor else False
        }
        
        return {
            "status": "healthy", 
            "ollama": "running", 
            "model": "available",
            "processors": processors_status
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Error checking health: {str(e)}"}
        )

@app.get("/api/status")
async def get_status():
    """Endpoint untuk mendapatkan status aplikasi"""
    return {
        "status": "running",
        "ollama_available": rag_processor is not None,
        "documents_loaded": rag_processor.has_documents if rag_processor else False
    }

@app.get("/restart-ollama")
async def restart_ollama():
    """Endpoint untuk merestart Ollama secara manual"""
    try:
        # Kill existing Ollama processes
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                proc.kill()
        
        # Wait a moment
        time.sleep(2)
        
        # Start Ollama
        subprocess.Popen(["ollama", "serve"], 
                       stdout=subprocess.DEVNULL, 
                       stderr=subprocess.DEVNULL)
        
        # Wait for Ollama to be ready
        time.sleep(5)
        
        # Reinitialize processors
        global rag_processor, stt_processor, tts_processor
        rag_processor = None
        stt_processor = None
        tts_processor = None
        
        if initialize_processors():
            return {"status": "success", "message": "Ollama restarted successfully"}
        else:
            return {"status": "error", "message": "Failed to restart Ollama"}
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Error restarting Ollama: {str(e)}"}
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)