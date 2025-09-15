import subprocess
import sys
import os
import time
import psutil
from setup_environment import setup_environment

def is_ollama_running():
    """Check if Ollama is already running"""
    try:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] and 'ollama' in proc.info['name'].lower():
                return True
        return False
    except Exception as e:
        print(f"Error checking Ollama processes: {str(e)}")
        return False

def start_ollama():
    """Start Ollama service if not running"""
    if not is_ollama_running():
        try:
            # Start Ollama in background
            subprocess.Popen(["ollama", "serve"], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            print("Starting Ollama service...")
            
            # Wait for Ollama to be ready
            time.sleep(5)
            return True
        except Exception as e:
            print(f"Failed to start Ollama: {str(e)}")
            return False
    return True

def main():
    try:
        # Setup environment
        setup_environment()
        
        # Ensure Ollama is running
        if not start_ollama():
            print("Failed to start Ollama. Please start it manually with 'ollama serve'")
            sys.exit(1)
        
        # Install requirements
        print("Installing requirements...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        
        # Start the application
        print("Starting server...")
        print("Access the application at: http://localhost:8000")
        print("Press Ctrl+C to stop the server")
        
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\nShutting down server...")
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()