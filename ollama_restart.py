import os
import subprocess
import psutil
import time

def restart_ollama():
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
    
    print("Ollama restarted successfully")
    
    # Wait for Ollama to be ready
    time.sleep(5)
    
    # Check status
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    if result.returncode == 0:
        print("Ollama is running correctly")
        if "phi" not in result.stdout:
            print("Pulling phi model...")
            subprocess.run(["ollama", "pull", "phi"], check=True)
    else:
        print("Ollama is not running correctly")

if __name__ == "__main__":
    restart_ollama()