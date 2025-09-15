let mediaRecorder;
let audioChunks = [];
let isRecording = false;
let socket;

// Initialize WebSocket connection
function initWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    socket = new WebSocket(wsUrl);
    
    socket.onopen = function() {
        console.log('Connected to server');
        updateUIStatus('connected');
        addMessage("System", "Connected to server. You can start speaking now.", "system");
    };
    
    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.type === 'transcript') {
            addMessage("You", data.data, "user");
        } else if (data.type === 'response_text') {
            // Remove any existing typing indicator
            removeTypingIndicator();
            addMessage("Assistant", data.text, "bot");
        } else if (data.type === 'response_audio') {
            const audio = new Audio('data:audio/wav;base64,' + data.data);
            audio.play();
        } else if (data.type === 'error') {
            addMessage("System", "Error: " + data.data, "system");
        }
    };
    
    socket.onerror = function(error) {
        console.error('WebSocket error:', error);
        updateUIStatus('error');
        addMessage("System", "Connection error. Please refresh the page.", "system");
    };
    
    socket.onclose = function() {
        console.log('WebSocket connection closed');
        updateUIStatus('disconnected');
        addMessage("System", "Connection closed. Please refresh the page.", "system");
    };
}

// Add message to chat
function addMessage(sender, text, type) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    messageText.textContent = text;
    
    const messageTime = document.createElement('div');
    messageTime.className = 'message-time';
    messageTime.textContent = new Date().toLocaleTimeString();
    
    messageDiv.appendChild(messageText);
    messageDiv.appendChild(messageTime);
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Add typing indicator
function addTypingIndicator() {
    const chatMessages = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typing-indicator';
    typingDiv.className = 'message bot-message typing-indicator';
    
    typingDiv.innerHTML = `
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
    `;
    
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Remove typing indicator
function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Update UI status
function updateUIStatus(status) {
    const statusElement = document.getElementById('recordingStatus');
    switch(status) {
        case 'connected':
            statusElement.textContent = 'Terhubung ke server';
            statusElement.style.color = '#27ae60';
            break;
        case 'error':
            statusElement.textContent = 'Koneksi error';
            statusElement.style.color = '#e74c3c';
            break;
        case 'disconnected':
            statusElement.textContent = 'Terputus dari server';
            statusElement.style.color = '#7f8c8d';
            break;
    }
}

// Toggle recording
async function toggleRecording() {
    if (!isRecording) {
        // Start recording
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.ondataavailable = (event) => {
                audioChunks.push(event.data);
            };
            
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                const arrayBuffer = await audioBlob.arrayBuffer();
                const base64Audio = btoa(
                    new Uint8Array(arrayBuffer).reduce(
                        (data, byte) => data + String.fromCharCode(byte), ''
                    )
                );
                
                // Show typing indicator while processing
                addTypingIndicator();
                
                // Send audio to server
                if (socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({
                        type: 'audio',
                        data: base64Audio
                    }));
                }
            };
            
            mediaRecorder.start();
            isRecording = true;
            document.getElementById('recordButton').classList.add('recording');
            document.getElementById('recordText').textContent = 'Stop Rekam';
            document.getElementById('recordingStatus').textContent = 'Sedang merekam...';
            document.getElementById('recordingStatus').classList.add('recording');
        } catch (error) {
            console.error('Error accessing microphone:', error);
            addMessage("System", "Tidak dapat mengakses mikrofon. Pastikan Anda memberikan izin.", "system");
        }
    } else {
        // Stop recording
        mediaRecorder.stop();
        isRecording = false;
        document.getElementById('recordButton').classList.remove('recording');
        document.getElementById('recordText').textContent = 'Mulai Rekam';
        document.getElementById('recordingStatus').classList.remove('recording');
        
        // Stop all audio tracks
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
}

// Upload PDF
async function uploadPDF() {
    const fileInput = document.getElementById('pdfUpload');
    const file = fileInput.files[0];
    const statusElement = document.getElementById('uploadStatus');
    
    if (!file) {
        statusElement.textContent = 'Pilih file PDF terlebih dahulu';
        statusElement.className = 'error';
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        statusElement.textContent = 'Mengupload file...';
        statusElement.className = '';
        
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const result = await response.json();
            statusElement.textContent = `File ${result.filename} berhasil diupload`;
            statusElement.className = 'success';
            addMessage("System", `File ${result.filename} berhasil diupload. Anda sekarang dapat bertanya tentang isi PDF.`, "system");
            
            // Clear file input
            fileInput.value = '';
        } else {
            const error = await response.json();
            statusElement.textContent = `Error: ${error.detail || 'Upload gagal'}`;
            statusElement.className = 'error';
        }
    } catch (error) {
        console.error('Error uploading file:', error);
        statusElement.textContent = 'Error uploading file';
        statusElement.className = 'error';
    }
}

// Initialize when page loads
window.onload = function() {
    initWebSocket();
    
    // Add event listener for file input change
    document.getElementById('pdfUpload').addEventListener('change', function() {
        uploadPDF();
    });
    
    // Add welcome message
    setTimeout(() => {
        addMessage("System", "Selamat datang di Voice Agent Multibahasa. Upload PDF dan mulai berbicara!", "system");
    }, 1000);
};