// Global variables
let mediaRecorder;
let audioChunks = [];
let isRecording = false;

function selectAnimal(animal) {
    localStorage.setItem('selectedAnimal', animal);
    window.location.href = 'predict.html';
}

function speakInstruction() {
    const audio = new Audio('/instruction-audio');
    audio.play().catch(e => console.error("Error playing instruction:", e));
}

// MediaRecorder Logic
async function startRecording() {
    audioChunks = [];
    document.getElementById('recognized-text').innerText = '';
    document.getElementById('status').innerText = "பதிவாகிறது (Recording)...";
    document.getElementById('start-btn').disabled = true;
    document.getElementById('stop-btn').disabled = false;
    document.getElementById('result-box').style.display = 'none';

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

        mediaRecorder.ondataavailable = event => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = sendToBackend;

        mediaRecorder.start();
        isRecording = true;

    } catch (err) {
        console.error("Error accessing microphone:", err);
        document.getElementById('status').innerText = "மைக்ரோஃபோன் அணுகல் பிழை (Microphone Error): " + err.message;
        document.getElementById('start-btn').disabled = false;
        document.getElementById('stop-btn').disabled = true;
    }
}

function stopRecording() {
    if (isRecording && mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
        isRecording = false;
        document.getElementById('status').innerText = "செயலாக்குகிறது (Processing)...";
        document.getElementById('start-btn').disabled = false;
        document.getElementById('stop-btn').disabled = true;

        // Stop all tracks
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
}

async function sendToBackend() {
    const animal = localStorage.getItem('selectedAnimal');
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });

    if (audioBlob.size === 0) {
        document.getElementById('status').innerText = "எதுவும் கேட்கவில்லை. மீண்டும் முயற்சிக்கவும்.";
        return;
    }

    const formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");

    if (!animal) {
        alert("Animal not selected! Redirecting to home page.");
        window.location.href = 'index.html';
        return;
    }

    formData.append("animal", animal);
    formData.append("symptoms_tamil", "audio_upload"); // Placeholder

    try {
        const response = await fetch('http://127.0.0.1:8000/predict/', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.transcribed_text) {
            document.getElementById('recognized-text').innerText = "You said: " + data.transcribed_text;
        }

        displayResult(data);

    } catch (error) {
        console.error("Error Detail:", error);
        document.getElementById('status').innerText = "சர்வர் பிழை (Server Error): " + error.message;
    }
}

function displayResult(data) {
    const resultBox = document.getElementById('result-box');
    const resultContent = document.getElementById('result-content');
    const status = document.getElementById('status');
    const audioPlayer = document.getElementById('result-audio');

    status.innerText = "முடிவு (Done)";
    resultBox.style.display = 'block';

    if (data.error && !data.disease) {
        resultContent.innerHTML = `<p style="color:red; font-weight:bold;">${data.error}</p>`;
        return;
    }

    // Format output
    let html = `
        <p><strong>நோய் (Disease):</strong> ${data.disease}</p>
        <p><strong>குணமாகும் நாட்கள் (Recovery):</strong> ${data.recovery_days}</p>
        <p><strong>மருத்துவர் தேவை (Vet Required):</strong> ${data.vet_required}</p>
        <p><strong>பரிகாரங்கள் (Remedies):</strong></p>
        <ul>
            ${data.remedies.map(r => `<li>${r}</li>`).join('')}
        </ul>
    `;

    resultContent.innerHTML = html;

    // Play Audio
    if (data.audio_url) {
        audioPlayer.src = data.audio_url;
        audioPlayer.style.display = 'block';
        audioPlayer.play().catch(e => console.log("Audio play blocked", e));
    }
}
