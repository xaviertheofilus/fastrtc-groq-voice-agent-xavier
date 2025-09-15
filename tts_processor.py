import os
from pydub import AudioSegment
import io
import tempfile
import logging
import torch
import numpy as np

logger = logging.getLogger(__name__)

class TTSProcessor:
    def __init__(self):
        self.use_kokoro = False
        self.initialized = False
        
        # Coba gunakan Kokoro jika tersedia
        try:
            from kokoro import KPipeline
            self.model = KPipeline(lang_code='i')
            self.use_kokoro = True
            self.initialized = True
            logger.info("Kokoro TTS initialized successfully")
        except ImportError:
            logger.warning("Kokoro TTS not available. Falling back to gTTS")
        except Exception as e:
            logger.error(f"Error initializing Kokoro TTS: {str(e)}. Falling back to gTTS")
    
    def synthesize_speech(self, text: str, language="id") -> bytes:
        if not text or text.strip() == "":
            logger.warning("Empty text provided for TTS")
            return bytes()
            
        try:
            if self.use_kokoro and self.initialized:
                # Gunakan Kokoro untuk TTS
                # Generate audio array and sample rate
                audio_array, sample_rate = self.model(text)
                
                # Convert to audio bytes
                audio_int16 = (audio_array * 32767).astype(np.int16)
                audio_segment = AudioSegment(
                    audio_int16.tobytes(),
                    frame_rate=sample_rate,
                    sample_width=2,  # 16-bit
                    channels=1
                )
                
                # Export to bytes
                buffer = io.BytesIO()
                audio_segment.export(buffer, format="wav")
                
                logger.info(f"Speech synthesized with Kokoro for text: {text[:50]}...")
                return buffer.getvalue()
            else:
                # Fallback to gTTS
                return self._synthesize_with_gtts(text, language)
                
        except Exception as e:
            logger.error(f"Error in speech synthesis: {str(e)}")
            # Fallback to gTTS
            return self._synthesize_with_gtts(text, language)
    
    def _synthesize_with_gtts(self, text: str, language="id") -> bytes:
        """Fallback method using gTTS"""
        try:
            from gtts import gTTS
            lang_code = "id" if language.lower() == "id" else "en"
            
            tts = gTTS(text=text, lang=lang_code, slow=False)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tts.save(tmp.name)
                
                # Convert to WAV
                audio = AudioSegment.from_mp3(tmp.name)
                buffer = io.BytesIO()
                audio.export(buffer, format="wav")
                
            logger.info(f"Speech synthesized with gTTS for text: {text[:50]}...")
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"Error in gTTS fallback: {str(e)}")
            return bytes()