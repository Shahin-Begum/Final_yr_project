// Global variables
let mediaRecorder;
let audioChunks = [];
let isRecording = false;

// Conversation State
const steps = ['breed', 'age', 'gender', 'symptom1', 'symptom2', 'symptom3'];
let currentStepIndex = 0;
let conversationData = {
    animal: localStorage.getItem('selectedAnimal') || 'Cow',
    breed: null,
    age: null,
    gender: null,
    symptom1: null,
    symptom2: null,
    symptom3: null
};

// DOM Elements
const chatBox = document.getElementById('chat-box');
const micBtn = document.getElementById('mic-btn');
const statusText = document.getElementById('status');
const startSection = document.getElementById('start-section');
const controls = document.getElementById('controls');
const welcomeText = document.getElementById('welcome-text');

// Init
document.addEventListener('DOMContentLoaded', () => {
    if (!conversationData.animal) {
        // Fallback or redirect
        conversationData.animal = "Cow";
    }

    // Update Welcome Text
    // Tamil mapping for display
    // Tamil mapping for display and audio
    const animalMap = {
        'Cattle': 'பசு (Cattle)',
        'Buffalo': 'எருமை (Buffalo)',
        'Goat': 'ஆடு (Goat)',
        'Poultry': 'கோழி (Poultry)',
        'Dog': 'நாய் (Dog)',
        'Cat': 'பூனை (Cat)'
    };

    // Tamil names for TTS (Voice)
    const animalVoiceMap = {
        'Cattle': 'பசு',
        'Buffalo': 'எருமை',
        'Goat': 'ஆடு',
        'Poultry': 'கோழி',
        'Dog': 'நாய்',
        'Cat': 'பூனை'
    };

    const displayName = animalMap[conversationData.animal] || conversationData.animal;
    const voiceName = animalVoiceMap[conversationData.animal] || conversationData.animal;

    welcomeText.innerText = `வணக்கம், நீங்கள் தேர்ந்தெடுத்தது: ${displayName}`;

    // Generate and Play Welcome Audio
    // "Hello. You selected [Animal]. To provide details, press the 'Start' button."
    const welcomeMsg = `வணக்கம். நீங்கள் ${voiceName} தேர்ந்தெடுத்தீர்கள். விவரங்களைச் சொல்ல, 'தொடங்கு' என்ற பொத்தானை அழுத்தவும்.`;
    fetchTTS(welcomeMsg, 'audio-welcome', true);
});

function fetchTTS(text, elementId, autoPlay = false, onEnded = null) {
    const formData = new FormData();
    formData.append("text", text);

    fetch('/text-to-speech/', { method: 'POST', body: formData })
        .then(res => res.json())
        .then(data => {
            if (data.audio_url) {
                const audio = document.getElementById(elementId);
                audio.src = data.audio_url;

                // Clear previous handlers
                audio.onended = null;

                if (onEnded) {
                    audio.onended = onEnded;
                }

                if (autoPlay) {
                    audio.play().catch(e => {
                        console.log("Auto-play blocked:", e);
                        // If blocked/fails, we might want to trigger callback anyway? 
                        // But for now let's rely on user click if blocked.
                    });
                }
            }
        })
        .catch(err => {
            console.error("TTS Error:", err);
            // Fallback: if TTS fails, start recording anyway
            if (onEnded) onEnded();
        });
}

function startConversation() {
    startSection.style.display = 'none';
    chatBox.style.display = 'block';
    controls.style.display = 'flex';

    // Start first step
    currentStepIndex = 0;
    processStep();
}

function processStep() {
    const step = steps[currentStepIndex];
    let msg = "";
    let ttsMsg = ""; // Text for Audio

    switch (step) {
        case 'breed':
            msg = "1. உங்கள் விலங்கின் இனம் என்ன? (What is the breed?)";
            ttsMsg = "உங்கள் விலங்கின் இனம் என்ன?";
            break;
        case 'age':
            msg = "2. உங்கள் விலங்கின் வயது என்ன? (What is the age?)";
            ttsMsg = "உங்கள் விலங்கின் வயது என்ன?";
            break;
        case 'gender':
            msg = "3. அது ஆணா அல்லது பெண்ணா? (Male or Female?)";
            ttsMsg = "அது ஆணா அல்லது பெண்ணா?";
            break;
        case 'symptom1':
            msg = "4. முதல் அறிகுறி என்ன? (What is the 1st symptom?)";
            ttsMsg = "முதல் அறிகுறி என்ன?";
            break;
        case 'symptom2':
            msg = "5. வேறு அறிகுறி உள்ளதா? (2nd Symptom?)";
            ttsMsg = "வேறு அறிகுறி உள்ளதா?";
            break;
        case 'symptom3':
            msg = "6. வேறு ஏதேனும் அறிகுறி? (3rd Symptom?)";
            ttsMsg = "வேறு ஏதேனும் அறிகுறி?";
            break;
    }

    addMessage(msg, 'bot');

    // Play the Tamil TTS and start recording when done
    statusText.innerText = "பேசுகிறது (Speaking)...";
    fetchTTS(ttsMsg, 'audio-prompt', true, startRecording);
}

function addMessage(text, sender) {
    const div = document.createElement('div');
    div.classList.add('message', sender === 'user' ? 'user-message' : 'bot-message');
    // Simple styling for now
    div.style.padding = "10px";
    div.style.margin = "5px";
    div.style.borderRadius = "10px";
    div.style.width = "fit-content";
    div.style.maxWidth = "80%";

    if (sender === 'user') {
        div.style.backgroundColor = "#e3f2fd";
        div.style.alignSelf = "flex-end";
        div.style.marginLeft = "auto";
    } else {
        div.style.backgroundColor = "#f1f8e9";
        div.style.alignSelf = "flex-start";
    }

    div.innerText = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function playAudio(id) {
    const audio = document.getElementById(id);
    if (audio) {
        audio.currentTime = 0;
        audio.play().catch(e => console.error("Audio play error:", e));
    } else {
        console.warn("Audio element not found:", id);
    }
}

function toggleRecording() {
    if (!isRecording) {
        startRecording();
    } else {
        stopRecording();
    }
}

async function startRecording() {
    audioChunks = [];
    statusText.innerText = "கேட்கிறது... (Listening - Speak now)";
    micBtn.style.display = 'none'; // Hide mic btn in auto mode or change style
    micBtn.classList.add('recording');

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);

        mediaRecorder.ondataavailable = event => {
            if (event.data.size > 0) audioChunks.push(event.data);
        };

        mediaRecorder.onstop = processRecording;
        mediaRecorder.start();
        isRecording = true;

        // Start Silence Detection
        detectSilence(stream, () => {
            if (isRecording) {
                console.log("Silence detected, stopping...");
                stopRecording();
            }
        });

    } catch (err) {
        console.error("Mic Error:", err);
        statusText.innerText = "Mic Error: " + err.message;
    }
}

function detectSilence(stream, onSilence) {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    let silenceStart = Date.now();
    const silenceThreshold = 15; // Slightly increased threshold
    const silenceDuration = 2500; // Increased to 2.5 seconds to allow pauses

    const check = () => {
        if (!isRecording) {
            audioContext.close();
            return;
        }

        analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) sum += dataArray[i];
        let average = sum / bufferLength;

        // Console log for debug (optional)
        // console.log("Vol:", average);

        if (average < silenceThreshold) {
            if (Date.now() - silenceStart > silenceDuration) {
                onSilence();
                return;
            }
        } else {
            silenceStart = Date.now();
        }

        requestAnimationFrame(check);
    };

    // Also set a max timeout of 8 seconds to prevent hanging
    setTimeout(() => {
        if (isRecording) {
            console.log("Max timeout reached");
            onSilence();
        }
    }, 8000);

    check();
}

function stopRecording() {
    if (isRecording && mediaRecorder) {
        mediaRecorder.stop();
        isRecording = false;
        micBtn.classList.remove('recording');
        statusText.innerText = "செயலாக்குகிறது (Processing)...";

        // Stop all tracks
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
}

async function processRecording() {
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append("file", audioBlob, "recording.webm");
    formData.append("animal", conversationData.animal);

    try {
        const response = await fetch('/predict/', { method: 'POST', body: formData });
        const data = await response.json();

        const text = data.transcribed_text || "(No text detected)";
        addMessage(text, 'user');

        // Save data
        const currentStep = steps[currentStepIndex];
        conversationData[currentStep] = text;

        // Auto-advance
        if (currentStepIndex < steps.length - 1) {
            currentStepIndex++;
            setTimeout(processStep, 1000);
        } else {
            statusText.innerText = "முடிந்தது (Done).";
            stopConversation();
        }

    } catch (error) {
        console.error("Error:", error);
        addMessage("Error: " + error.message, 'bot');
        // Retry? or advance? Let's advance for flow
        if (currentStepIndex < steps.length - 1) {
            currentStepIndex++;
            setTimeout(processStep, 1000);
        } else {
            stopConversation();
        }
    }
}

function stopConversation() {
    // Hide controls
    controls.style.display = 'none';
    // chatBox.style.display = 'none'; // Keep chat visible

    // Finalize
    statusText.innerText = "முடிவுகளைப் பெறுகிறது (Analyzing)...";
    finalizePrediction();
}

async function finalizePrediction() {
    const formData = new FormData();
    formData.append("animal", conversationData.animal);
    if (conversationData.breed) formData.append("breed", conversationData.breed);
    if (conversationData.age) formData.append("age", conversationData.age);
    if (conversationData.gender) formData.append("gender", conversationData.gender);
    if (conversationData.symptom1) formData.append("symptom1", conversationData.symptom1);
    if (conversationData.symptom2) formData.append("symptom2", conversationData.symptom2);
    if (conversationData.symptom3) formData.append("symptom3", conversationData.symptom3);

    try {
        const response = await fetch('/predict/', { method: 'POST', body: formData });

        if (!response.ok) {
            const errText = await response.text();
            throw new Error(`Server Error (${response.status}): ${errText}`);
        }

        const data = await response.json();
        showResult(data);
    } catch (err) {
        console.error("Finalize Error:", err);
        const resultBox = document.getElementById('result-box');
        const resultContent = document.getElementById('result-content');
        resultBox.style.display = 'block';
        resultContent.innerHTML = `<p style="color:red; font-weight:bold;">Error: ${err.message}</p>`;
        resultBox.scrollIntoView({ behavior: 'smooth' });
    }
}

function showResult(data) {
    const resultBox = document.getElementById('result-box');
    const resultContent = document.getElementById('result-content');

    resultBox.style.display = 'block';
    setTimeout(() => {
        resultBox.scrollIntoView({ behavior: 'smooth' });
    }, 100);

    if (data.error && !data.disease) {
        resultContent.innerHTML = `<p style="color:red; font-weight:bold;">${data.error}</p>`;
    } else {
        // Handle Care items (array)
        const careList = Array.isArray(data.care) ? data.care.map(c => `<li>${c}</li>`).join('') : `<li>${data.care || '-'}</li>`;

        let html = `
            <p><strong>நோய் (Disease):</strong> ${data.disease}</p>
            <p><strong>குணமாகும் நாட்கள் (Recovery):</strong> ${data.recovery_days}</p>
            <p><strong>மருத்துவர் தேவை (Vet Required):</strong> ${data.vet_required}</p>
            <hr style="margin: 10px 0; border: 0; border-top: 1px solid #eee;">
            <p><strong>மருந்து (Medicine):</strong> ${data.medicine}</p>
            <p><strong>பராமரிப்பு (Care):</strong></p>
            <ul>${careList}</ul>
        `;
        resultContent.innerHTML = html;

        // Add OK Button dynamically
        const okBtn = document.createElement('button');
        okBtn.innerText = "OK (முடிந்தது)";
        okBtn.className = "ok-btn";
        okBtn.style.backgroundColor = "#2e7d32";
        okBtn.style.color = "white";
        okBtn.style.marginTop = "10px";
        okBtn.style.marginRight = "10px";
        // Simple distinct style
        okBtn.style.padding = "10px 20px";
        okBtn.style.border = "none";
        okBtn.style.borderRadius = "5px";
        okBtn.style.cursor = "pointer";

        okBtn.onclick = function () {
            // "Project over" -> Redirect to First Page
            window.location.href = 'index.html';
        };

        resultContent.appendChild(okBtn);
    }

    if (data.audio_url) {
        const audio = document.getElementById('response-audio');
        audio.src = data.audio_url;
        audio.style.display = 'block';
        audio.play().catch(e => console.log(e));
    }
}

function selectAnimal(animal) {
    localStorage.setItem('selectedAnimal', animal);
    window.location.href = 'predict.html';
}
