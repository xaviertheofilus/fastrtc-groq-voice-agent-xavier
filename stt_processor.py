import whisper
import numpy as np
import io
from pydub import AudioSegment
import logging
import torch
import tempfile

logger = logging.getLogger(__name__)

class STTProcessor:
    def __init__(self, model_size="base"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            logger.info(f"Loading Whisper model: {model_size} on {self.device}")
            self.model = whisper.load_model(
                model_size, 
                device=self.device,
                download_root="./models"
            )
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {str(e)}")
            raise e
    
    def transcribe_audio(self, audio_data: bytes) -> str:
        try:
            # Convert bytes to audio segment
            audio = AudioSegment.from_file(io.BytesIO(audio_data))
            
            # Convert to mono and 16kHz sample rate (Whisper requirements)
            audio = audio.set_channels(1).set_frame_rate(16000)
            
            # Export as wav to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                audio.export(tmp.name, format="wav")
                
                # Transcribe with language detection but prioritize Indonesian
                result = self.model.transcribe(
                    tmp.name,
                    fp16=(self.device == "cuda"),
                    language="id",  # Prioritize Indonesian
                    task="transcribe",
                    temperature=0.0,
                    best_of=3,  # Increase for better accuracy
                    beam_size=5  # Increase for better accuracy
                )
            
            logger.info(f"Transcription completed with confidence: {result.get('confidence', 'N/A')}")
            return result["text"]
        except Exception as e:
            logger.error(f"Error transcribing audio: {str(e)}")
            return "Maaf, saya tidak dapat memahami audio yang dikirim. Silakan coba lagi."