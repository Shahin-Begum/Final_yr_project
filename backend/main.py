from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
from gtts import gTTS
import os
import uuid
import whisper
import shutil
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='whisper')
import difflib

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load dataset
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(current_dir, "dataset.csv")
    df = pd.read_csv(dataset_path)
    # Normalize dataset columns for easier matching
    df.columns = [c.strip() for c in df.columns]
except Exception as e:
    print(f"Error loading dataset: {e}")
    # Initialize with expected columns to prevent KeyError later if file fails
    df = pd.DataFrame(columns=["animal", "symptoms", "disease", "recovery_days", "remedy", "vet_required", "Remedy1", "Remedy2", "Remedy3", "Symptom1", "Symptom2", "Symptom3"])

# Tamil to English Symptom Mapping
tamil_to_english_symptoms = {
    "காய்ச்சல்": "fever",
    "வயிற்றுப்போக்கு": "loose motion",
    "இருமல்": "cough",
    "சோர்வு": "drowsiness",
    "வாந்தி": "vomiting",
    "அரிப்பு": "itching",
    "வீக்கம்": "swelling",
    "மூச்சுத்திணறல்": "difficulty breathing",
    "நடுக்கம்": "shivering",
    "பால் குறைவு": "milk drop",
    "வயிறு உப்பசம்": "bloating",
    "கொப்புளங்கள்": "blisters",
    "நொண்டி நடத்தல்": "lameness",
    "பலவீனம்": "weakness",
    "நீரிழப்பு": "dehydration",
    "வலி": "pain",
    "மூக்கு ஒழுகுதல்": "nasal discharge",
    "பக்கவாதம்": "paralysis",
    "கழுத்து வளைவு": "twisted neck",
    "இரத்தப்போக்குடன் கூடிய வயிற்றுப்போக்கு": "bloody diarrhea",
    "மந்தமான நிலை": "lethargy",
    "தலை ஆட்டுதல்": "head shaking",
    "காது மெழுகு": "dark wax",
    "சிவத்தல்": "redness",
    "முடி உதிர்தல்": "hair loss",
    "சொறி": "scratching", # Additional term for scratching
    "சீழ்": "pus", 
    "தீவனம் எடுக்கவில்லை": "loss of appetite",
    "சாப்பிடவில்லை": "loss of appetite",
    "கழிச்சல்": "loose motion", 
    "பேதி": "loose motion",
    # Tanglish / Phonetic Mappings
    "kaaichal": "fever",
    "kaaitsel": "fever",
    "fever": "fever",
    "irumal": "cough",
    "vanthi": "vomiting",
    "bedhi": "loose motion",
    "sorvu": "drowsiness",
    "veekkam": "swelling",
    "vali": "pain"
}

# English to Tamil Translations
english_to_tamil_output = {
    "Foot and Mouth Disease": "கிளம்பு நோய் (Foot and Mouth Disease)",
    "Diarrhea": "கழிச்சல் (Diarrhea)",
    "Mastitis": "மடி நோய் (Mastitis)",
    "PPR": "ஆட்டு வாலை நோய் (PPR)",
    "Newcastle Disease": "வெள்ளை கழிச்சல் (Newcastle Disease)",
    "Parvovirus": "பார்வோ வைரஸ் (Parvovirus)",
    "Ear Mites": "காது பூச்சி (Ear Mites)",
    "Bloat": "வயிறு உப்புசம் (Bloat)",
    "Skin Infection": "தோல் நோய் (Skin Infection)",
    "Yes": "ஆம்",
    "No": "இல்லை",
    "Separate the infected animal": "பாதிக்கப்பட்ட விலங்கை தனிமைப்படுத்தவும்",
    "Wash mouth with KmnO4": "வாயை பொட்டாசியம் பர்மாங்கனேட் கொண்டு கழுவவும்",
    "Give soft food": "மென்மையான உணவு கொடுக்கவும்",
    "Give electrolyte solution": "எலக்ட்ரோலைட் கரைசல் கொடுக்கவும்",
    "Avoid milk": "பால் கொடுப்பதை தவிர்க்கவும்",
    "Clean water": "சுத்தமான நீர் கொடுக்கவும்",
    "Consult vet immediately": "உடனடியாக மருத்துவரை அணுகவும்",
    "Clean udder with warm water": "மடியை வெதுவெதுப்பான நீரில் கழுவவும்",
    "Milk frequently": "அடிக்கடி பால் கறக்கவும்",
    "Isolate goat": "ஆட்டை தனிமைப்படுத்தவும்",
    "Provide warm shelter": "வெதுவெதுப்பான தங்குமிடம் வழங்கவும்",
    "Give nutritious food": "சத்தான உணவு கொடுக்கவும்",
    "Isolate bird": "பறவையை தனிமைப்படுத்தவும்",
    "Clean coop": "கூண்டை சுத்தம் செய்யவும்",
    "Provide vitamins": "வைட்டமின்கள் வழங்கவும்",
    "Intravenous fluids": "நரம்பு வழியாக திரவம் ஏற்றவும்",
    "Clean ears": "காதுகளை சுத்தம் செய்யவும்",
    "Apply anti-mite drops": "பூச்சி மருந்து இடவும்",
    "Check other pets": "மற்ற விலங்குகளை பரிசோதிக்கவும்",
    "Give vegetable oil": "தாவர எண்ணெய் கொடுக்கவும்",
    "Massage stomach": "வயிற்றை மசாஜ் செய்யவும்",
    "Walk the animal": "விலங்கை நடக்க வைக்கவும்",
    "Bath with medicated shampoo": "மருந்து ஷாம்பு போட்டு குளிப்பாட்டவும்",
    "Apply ointment": "களிம்பு பூசவும்",
    "Keep dry": "உலர்ந்த நிலையில் வைக்கவும்",
    "Antibiotics": "நுண்ணுயிர் எதிர்ப்பிகள் (Antibiotics)",
    "Vaccination": "தடுப்பூசி (Vaccination)",
    "Supportive care": "ஆதரவு சிகிச்சை (Supportive care)",
    "Ear drops": "காது சொட்டு மருந்து (Ear drops)",
    "Oil drench": "எண்ணெய் மருந்து (Oil drench)",
    "Medicated bath": "மருந்து குளியல் (Medicated bath)",
    "Isolation and vaccination": "தனிமைப்படுத்துதல் மற்றும் தடுப்பூசி",
    "Oral rehydration": "வாய்வழி நீரேற்றம்",
    "Anti-emetics": "வாந்தி தடுப்பு மருந்து",
    "Clean udder": "மடியை சுத்தம் செய்யவும்",
    "Milk completely": "முழுமையாக பால் கறக்கவும்",
    "Consult vet": "மருத்துவரை அணுகவும்"
}

def translate_to_tamil(text):
    return english_to_tamil_output.get(text, text)

# Load Whisper Model (Upgraded to 'small' for better accuracy)
model = whisper.load_model("small")

class PredictionRequest(BaseModel):
    animal: str
    symptoms_tamil: str

@app.post("/predict/")
async def predict(animal: str = Form(None), symptoms_tamil: str = Form(None), file: UploadFile = File(None)):
    
    # print(f"DEBUG: Received animal={animal}, symptoms_tamil={symptoms_tamil}, file={file.filename if file else 'None'}")
    
    detected_lang = None
    transcribed_text = None

    # Handle Audio File Upload
    if file:
        try:
            temp_filename = f"temp_{uuid.uuid4()}.webm"
            temp_path = os.path.join(current_dir, "audio", temp_filename)
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Transcribe with Whisper (Auto-detect language)
            # Added initial_prompt to guide the model towards medical/animal context and Tamil language
            result = model.transcribe(
                temp_path, 
                initial_prompt="This is a medical report about animal diseases. Symptoms: Fever, Cough, Limping, Milk reduction. Tamil and English mixed."
            ) 
            transcribed_text = result["text"]
            detected_lang = result["language"]
            
            # Safe print for debugging
            try:
                print(f"DEBUG: Detected Language: {detected_lang}, Text: {transcribed_text.encode('utf-8', 'ignore').decode('utf-8')}")
            except Exception:
                print("DEBUG: Detected Language and Text (encoding error suppressed)")
            
            # Cleanup temp file
            os.remove(temp_path)
            
        except Exception as e:
            print(f"Whisper Error: {e}")
            return {"error": f"Audio processing failed: {str(e)}"}

    if not animal:
         print(f"DEBUG: Missing data. Animal: {animal}")
         return {"error": f"Missing animal data. Received: Animal='{animal}'"}

    # 1. Identify Symptoms based on Language using Fuzzy Matching
    detected_symptoms_english = []
    
    input_text = transcribed_text if file else symptoms_tamil
    
    if not input_text:
        return {"error": "No audio or text input provided"}

    # Detect language for text input if not already detected
    if not detected_lang:
        if any(ord(c) > 127 for c in input_text): 
            detected_lang = 'ta'
        else:
            detected_lang = 'en'
            
    # try:
    #     print(f"Processing Text: {input_text} (Lang: {detected_lang})")
    # except:
    #     pass

    # Combined Logic for Mixed Language Support
    # We check for BOTH Tamil/Tanglish keys AND English values in the input text regardless of detected language.
    # This handles:
    # 1. Pure Tamil (Tamil script keys)
    # 2. Tanglish (Latin script keys like 'kaaitsel')
    # 3. English (English values)
    # 4. Mixed input
    
    input_text_lower = str(input_text).lower()
    
    # 1. Check ALL keys in tamil_to_english_symptoms (includes Tamil script and Tanglish)
    for key in tamil_to_english_symptoms:
        # Check lowercased key against lowercased input for Latin/Tanglish
        # Tamil script doesn't change with .lower() much but it's safe
        if str(key).lower() in input_text_lower:
             eng_symptom = tamil_to_english_symptoms[key]
             if eng_symptom not in detected_symptoms_english:
                 detected_symptoms_english.append(eng_symptom)

    # 2. Check English values (reverse lookup not needed as we have the values)
    english_symptoms = list(set(tamil_to_english_symptoms.values()))
    for symptom in english_symptoms:
        if str(symptom).lower() in input_text_lower:
            if symptom not in detected_symptoms_english:
                detected_symptoms_english.append(symptom)
    
    # 3. Fuzzy match individual words
    # Split input into words
    words = input_text_lower.split()
    all_keys = list(tamil_to_english_symptoms.keys())
    
    print(f"DEBUG: Detected Symptoms (English): {detected_symptoms_english}")
    
    for word in words:
        # Check against keys (Tamil + Tanglish)
        matches_keys = difflib.get_close_matches(word, [k.lower() for k in all_keys], n=1, cutoff=0.8)
        if matches_keys:
             # Find original key (restore case if needed, but dictionary keys are mostly lower or Tamil)
             # We need to map back to English value
             # match is the lowercased key. Find the key in dictionary that matches.
             matched_key_lower = matches_keys[0]
             # Inefficient lookup but dataset is small
             for original_key in all_keys:
                 if original_key.lower() == matched_key_lower:
                     symptom_en = tamil_to_english_symptoms[original_key]
                     if symptom_en not in detected_symptoms_english:
                         detected_symptoms_english.append(symptom_en)
                     break
        
        # Check against English values
        matches_vals = difflib.get_close_matches(word, [s.lower() for s in english_symptoms], n=1, cutoff=0.8)
        if matches_vals:
             matched_val_lower = matches_vals[0]
             for s in english_symptoms:
                 if s.lower() == matched_val_lower:
                     if s not in detected_symptoms_english:
                         detected_symptoms_english.append(s)
                     break

    # Helper function to generate audio
    def generate_audio_response(text):
        try:
            audio_dir = os.path.join(current_dir, "audio")
            os.makedirs(audio_dir, exist_ok=True)
            filename = f"response_{uuid.uuid4()}.mp3"
            path = os.path.join(audio_dir, filename)
            tts = gTTS(text=text, lang='ta')
            tts.save(path)
            return f"/audio/{filename}"
        except Exception as e:
            print(f"TTS Error: {e}")
            return None

    if not detected_symptoms_english:
        error_msg_ta = "அறிகுறிகள் எதுவும் கண்டறியப்படவில்லை"
        error_msg_en = "No symptoms detected"
        if input_text:
             error_msg_en += f" (Input: {input_text})"
             
        audio_url = generate_audio_response(error_msg_ta)
        
        return {
            "error": f"{error_msg_ta} ({error_msg_en})",
            "disease": "தெரியவில்லை",
            "remedies": [],
            "recovery_days": "-",
            "vet_required": "-",
            "transcribed_text": input_text,
            "audio_url": audio_url
        }

    # 2. Filter dataset by animal
    animal_df = df[df['animal'].str.lower() == animal.lower()]

    if animal_df.empty:
        error_msg_ta = "இந்த விலங்கு தரவுத்தளத்தில் இல்லை"
        audio_url = generate_audio_response(error_msg_ta)
        
        return {
             "error": f"{error_msg_ta} (Animal not found)",
             "disease": "தெரியவில்லை",
             "remedies": [],
             "recovery_days": "-",
             "vet_required": "-"
        }

    # 3. Match symptoms
    best_match = None
    max_score = -1

    for index, row in animal_df.iterrows():
        score = 0
        row_symptoms = [str(row.get(f'Symptom{i}')).lower() for i in range(1, 4)]
        
        for mapped_symptom in detected_symptoms_english:
            for row_symptom in row_symptoms:
                if mapped_symptom.lower() in row_symptom: #'in' handles partial matches within symptom string
                    score += 1


        
        if int(score) > int(max_score):
            max_score = score
            best_match = row

    if best_match is None or max_score == 0:
         error_msg_ta = "பொருத்தமான நோய் கண்டறியப்படவில்லை"
         audio_url = generate_audio_response(error_msg_ta)
         
         return {
            "error": f"{error_msg_ta} (No matching disease found)",
            "disease": "தெரியவில்லை",
            "remedies": [],
            "recovery_days": "-",
            "vet_required": "-",
            "transcribed_text": input_text,
            "audio_url": audio_url
        }

    # 4. Format Output in Tamil
    disease_tamil = translate_to_tamil(best_match['disease'])
    remedies = [
        translate_to_tamil(best_match.get('Remedy1', '')),
        translate_to_tamil(best_match.get('Remedy2', '')),
        translate_to_tamil(best_match.get('Remedy3', ''))
    ]
    remedies = [r for r in remedies if str(r) != 'nan' and r] 
    
    recovery_days = str(best_match['recovery_days'])
    vet_required = translate_to_tamil(best_match['vet_required'])

    result_text = f"""
    உங்கள் விலங்கிற்கு இருக்கும் நோய்: {disease_tamil}
    பரிகாரங்கள்:
    {', '.join(remedies)}
    முழுமையாக குணமாகும் நாட்கள்: {recovery_days}
    மருத்துவர் தேவை: {vet_required}
    """

    # 5. Generate Audio
    audio_url = generate_audio_response(result_text)

    return {
        "disease": disease_tamil,
        "remedies": remedies,
        "recovery_days": recovery_days,
        "vet_required": vet_required,
        "full_text": result_text,
        "audio_url": audio_url,

        "transcribed_text": input_text
    }

@app.get("/instruction-audio")
async def get_instruction_audio():
    text = "உங்கள் விலங்கின் இனம், வயது மற்றும் காணப்படும் அறிகுறிகளை தெளிவாக சொல்லுங்கள். முடிந்ததும் நிறுத்து பொத்தானை அழுத்துங்கள்."
    audio_dir = os.path.join(current_dir, "audio")
    os.makedirs(audio_dir, exist_ok=True)
    filename = "instruction.mp3"
    file_path = os.path.join(audio_dir, filename)
    
    if not os.path.exists(file_path):
        try:
            tts = gTTS(text=text, lang='ta')
            tts.save(file_path)
        except Exception as e:
            return {"error": str(e)}
            
    return FileResponse(file_path)

from fastapi.responses import FileResponse

@app.get("/audio/{filename}")
async def get_audio(filename: str):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    audio_dir = os.path.join(current_dir, "audio")
    file_path = os.path.join(audio_dir, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

# Serve frontend files for convenience
# Mount the frontend directory to serve static files (HTML, CSS, JS)
frontend_dir = os.path.join(os.path.dirname(current_dir), "frontend")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
