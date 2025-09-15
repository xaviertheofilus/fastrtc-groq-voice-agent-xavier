import os
import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_environment():
    # Create necessary directories
    directories = ["data", "static", "models"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")
    
    # Check if Ollama is installed
    try:
        result = subprocess.run(["ollama", "--version"], check=True, capture_output=True, text=True)
        logger.info(f"Ollama is installed: {result.stdout.strip()}")
        
        # Check if phi model is available
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if "phi" not in result.stdout:
            logger.info("Downloading phi model...")
            subprocess.run(["ollama", "pull", "phi"], check=True, timeout=300)
            logger.info("Phi model downloaded successfully")
        else:
            logger.info("Phi model is already available")
            
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Ollama is not installed. Please install it from https://ollama.ai/")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        logger.warning("Ollama model download timed out, but continuing...")
    
    # Pre-download Whisper model to avoid first-time delay
    try:
        import whisper
        logger.info("Pre-downloading Whisper tiny model...")
        whisper.load_model("tiny", download_root="./models")
        logger.info("Whisper model pre-downloaded successfully")
    except Exception as e:
        logger.error(f"Error pre-downloading Whisper model: {e}")
    
    logger.info("Environment setup complete!")

if __name__ == "__main__":
    setup_environment()