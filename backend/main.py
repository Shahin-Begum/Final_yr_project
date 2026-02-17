from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
from gtts import gTTS
import os
import uuid
import shutil
import speech_recognition as sr
import sys
import io

# Force UTF-8 for Windows Console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

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
    # Normalize dataset columns to match code expectations
    # CSV has: animal_type, breed, age, gender, disease, core_symptom, symptom_1, symptom_2, symptom_3, medicine, recovery_days, vet_required
    
    df.rename(columns={
        'animal_type': 'animal',
        'symptom_1': 'Symptom1',
        'symptom_2': 'Symptom2',
        'symptom_3': 'Symptom3',
        'medicine': 'Remedy1',
        'care_1': 'Remedy2',
        'care_2': 'Remedy3'
    }, inplace=True)

    # Add missing vet_required column if it doesn't exist
    if 'vet_required' not in df.columns:
        df['vet_required'] = "Yes"
        
    # Ensure recovery_days is string
    df['recovery_days'] = df['recovery_days'].astype(str)

    # Normalize dataset columns
    df.columns = [c.strip() for c in df.columns]
except Exception as e:
    print(f"Error loading dataset: {e}")
    # Initialize with expected columns
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
    "சொறி": "scratching",
    "சீழ்": "pus", 
    "தீவனம் எடுக்கவில்லை": "loss of appetite",
    "சாப்பிடவில்லை": "loss of appetite",
    "கழிச்சல்": "loose motion", 
    "பேதி": "loose motion",
    # Tanglish / Phonetic
    "kaaichal": "fever",
    "kaaitsel": "fever",
    "fever": "fever",
    "irumal": "cough",
    "vanthi": "vomiting",
    "bedhi": "loose motion",
    "sorvu": "drowsiness",
    "veekkam": "swelling",
    "vali": "pain",
    "mooku": "nasal discharge",
    "mooku oluguthal": "nasal discharge",
    "mudi": "hair loss",
    "mudi udhirthal": "hair loss",
    "sali": "nasal discharge",
    "cough": "cough",
    "irumal": "cough",
    "thalai aattuthal": "head shaking",
    "kan": "redness",
    "kavalai": "lethargy",
    "sappidala": "loss of appetite",
    "theevanam": "loss of appetite",
    "weight": "weakness",
    "eda": "weakness"
}

# English to Tamil Translations
english_to_tamil_output = {
    # Diseases
    "Viral Fever": "வைரஸ் காய்ச்சல் (Viral Fever)",
    "Digestive Disorder": "செரிமானக் கோளாறு (Digestive Disorder)",
    "Eye Infection": "கண் நோய் (Eye Infection)",
    "Nutritional Deficiency": "சத்து குறைபாடு (Nutritional Deficiency)",
    "Fever Infection": "காய்ச்சல் தொற்று (Fever Infection)",
    "Bacterial Infection": "பாக்டீரியா தொற்று (Bacterial Infection)",
    "Foot Rot": "கால் அழுகல் நோய் (Foot Rot)",
    "Parasitic Worms": "குடல் புழுக்கள் (Parasitic Worms)",
    "Respiratory Infection": "சுவாசத் தொற்று (Respiratory Infection)",
    "Skin Allergy": "தோல் ஒவ்வாமை (Skin Allergy)",
    "Foot and Mouth Disease": "கிளம்பு நோய் (Foot and Mouth Disease)",
    "Mastitis": "மடி நோய் (Mastitis)",
    "PPR": "ஆட்டு வாலை நோய் (PPR)",
    "Newcastle Disease": "வெள்ளை கழிச்சல் (Newcastle Disease)",
    "Parvovirus": "பார்வோ வைரஸ் (Parvovirus)",
    "Ear Mites": "காது பூச்சி (Ear Mites)",
    "Bloat": "வயிறு உப்புசம் (Bloat)",
    "Skin Infection": "தோல் நோய் (Skin Infection)",

    # Medicines
    "Supportive IV fluids": "சலைன் (IV திரவம்)",
    "Digestive tonic": "செரிமான டானிக்",
    "Eye drops": "கண் சொட்டு மருந்து",
    "Vitamin supplement": "வைட்டமின் சத்து மருந்து",
    "Antipyretic injection": "காய்ச்சல் ஊசி",
    "Broad spectrum antibiotic": "நுண்ணுயிர் எதிர்ப்பு மருந்து (Antibiotic)",
    "Hoof antibiotic spray": "கால் குளம்பு ஸ்ப்ரே",
    "Deworming medicine": "குடற்புழு நீக்க மருந்து",
    "Antibiotic syrup": "நுண்ணுயிர் எதிர்ப்பு சிரப் (Antibiotic Syrup)",
    "Antihistamine cream": "ஒவ்வாமை களிம்பு (Cream)",
    "Ear drops": "காது சொட்டு மருந்து",
    "Oil drench": "எண்ணெய் மருந்து",
    "Medicated bath": "மருந்து குளியல்",
    "Oral rehydration": "வாய்வழி நீரேற்றம்",
    "Anti-emetics": "வாந்தி தடுப்பு மருந்து",

    # Care / Instructions
    "Regular vaccination": "முறையான தடுப்பூசி போடவும்",
    "Keep shelter clean": "இருப்பிடத்தை சுத்தமாக வைத்திருக்கவும்",
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
    "Isolation and vaccination": "தனிமைப்படுத்துதல் மற்றும் தடுப்பூசி",
    "Clean udder": "மடியை சுத்தம் செய்யவும்",
    "Milk completely": "முழுமையாக பால் கறக்கவும்",
    "Consult vet": "மருத்துவரை அணுகவும்",
    
    # General
    "Yes": "ஆம்",
    "No": "இல்லை"
}

# Helper function
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

def translate_to_tamil(text):
    return english_to_tamil_output.get(text, text)

@app.post("/text-to-speech/")
async def text_to_speech(text: str = Form(...)):
    url = generate_audio_response(text)
    if url:
        return {"audio_url": url}
    return {"error": "TTS failed"}

@app.post("/predict/")
async def predict(
    animal: str = Form(...), 
    breed: str = Form(None),
    age: str = Form(None),
    gender: str = Form(None),
    symptom1: str = Form(None),
    symptom2: str = Form(None),
    symptom3: str = Form(None),
    file: UploadFile = File(None)
):
    transcribed_text = ""
    
    try:
        # 0. Process Audio if present
        if file:
            try:
                temp_filename = f"temp_{uuid.uuid4()}.webm"
                temp_path = os.path.join(current_dir, "audio", temp_filename)
                os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                
                with open(temp_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                    
                # Transcribe
                r = sr.Recognizer()
                
                # Convert WebM to WAV using pydub
                wav_path = temp_path.replace(".webm", ".wav")
                
                try:
                    from pydub import AudioSegment
                    audio = AudioSegment.from_file(temp_path)
                    audio.export(wav_path, format="wav")
                    
                    with sr.AudioFile(wav_path) as source:
                        audio_data = r.record(source)
                        try:
                            # Recognize Tamil
                            transcribed_text = r.recognize_google(audio_data, language="ta-IN")
                            print(f"DEBUG: Transcribed Text: {transcribed_text}")
                        except sr.UnknownValueError:
                            print("DEBUG: Speech Recognition could not understand audio")
                            transcribed_text = "(Not understood / புரியவில்லை)"
                        except sr.RequestError as e:
                            print(f"DEBUG: Could not request results from Google Speech Recognition service; {e}")
                            transcribed_text = "(API Error / பிழை)"
                except Exception as e:
                     print(f"Conversion/Transcription Error: {e}")
                     transcribed_text = f"(Audio Error: {str(e)})"
                finally:
                    # Cleanup
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    if os.path.exists(wav_path):
                        os.remove(wav_path)
                
            except Exception as e:
                print(f"Audio processing error: {e}")
                transcribed_text = f"(Audio Error: {str(e)})"
        
        # 1. Map Tamil inputs to English
        s1_en = tamil_to_english_symptoms.get(symptom1, symptom1) if symptom1 else None
        s2_en = tamil_to_english_symptoms.get(symptom2, symptom2) if symptom2 else None
        s3_en = tamil_to_english_symptoms.get(symptom3, symptom3) if symptom3 else None
        
        detected_symptoms = [s for s in [s1_en, s2_en, s3_en] if s]

        # 2. Filter dataset
        animal_df = df[df['animal'].str.lower() == animal.lower()]

        if breed:
            filtered_by_breed = animal_df[animal_df['breed'].astype(str).str.lower() == breed.lower()]
            if not filtered_by_breed.empty:
                animal_df = filtered_by_breed
                
        if age:
             filtered_by_age = animal_df[animal_df['age'].astype(str) == str(age)]
             if not filtered_by_age.empty:
                 animal_df = filtered_by_age
                 
        if gender:
            filtered_by_gender = animal_df[animal_df['gender'].str.lower() == gender.lower()]
            if not filtered_by_gender.empty:
                animal_df = filtered_by_gender

        if animal_df.empty:
            error_msg_ta = "இந்த விலங்கு தரவுத்தளத்தில் இல்லை"
            audio_url = generate_audio_response(error_msg_ta)
            return {
                 "transcribed_text": transcribed_text,
                 "error": f"{error_msg_ta} (Animal/Details not found)",
                 "disease": "தெரியவில்லை",
                 "remedies": [],
                 "recovery_days": "-",
                 "vet_required": "-",
                 "audio_url": audio_url
            }

        # 3. Match symptoms
        best_match = None
        max_score = -1

        for index, row in animal_df.iterrows():
            score = 0
            row_symptoms = [
                str(row.get('Symptom1', '')).lower(), 
                str(row.get('Symptom2', '')).lower(), 
                str(row.get('Symptom3', '')).lower()
            ]
            
            for input_symptom in detected_symptoms:
                for db_symptom in row_symptoms:
                    if input_symptom.lower() in db_symptom:
                        score += 1
            
            if score > max_score:
                max_score = score
                best_match = row

        if best_match is None or max_score == 0:
             error_msg_ta = "அறிகுறிகள் பொருந்தவில்லை"
             audio_url = generate_audio_response(error_msg_ta)
             
             return {
                "transcribed_text": transcribed_text,
                "error": f"{error_msg_ta} (No matching disease found)",
                "disease": "தெரியவில்லை",
                "remedies": [],
                "recovery_days": "-",
                "vet_required": "-",
                "audio_url": audio_url
            }

        # 4. Format Output in Tamil
        disease_en = best_match['disease']
        disease_tamil = translate_to_tamil(disease_en)
        
        # Extract Medicine
        medicine = str(best_match.get('Remedy1', ''))
        medicine_ta = translate_to_tamil(medicine) if medicine != 'nan' else "-"
        
        # Extract Care
        care1 = str(best_match.get('Remedy2', ''))
        care2 = str(best_match.get('Remedy3', ''))
        
        care_items = []
        if care1 != 'nan' and care1: care_items.append(translate_to_tamil(care1))
        if care2 != 'nan' and care2: care_items.append(translate_to_tamil(care2))
        
        care_ta = ", ".join(care_items) if care_items else "-"
        
        recovery_days = str(best_match['recovery_days'])
        vet_required = translate_to_tamil(best_match.get('vet_required', '-'))

        # Construct explicit Text
        result_text = f"உங்கள் விலங்கிற்கு இருக்கும் நோய்: {disease_tamil}. "
        result_text += f"மருந்து (Medicine): {medicine_ta}. "
        result_text += f"பராமரிப்பு (Care): {care_ta}. "
        result_text += f"முழுமையாக குணமாகும் நாட்கள்: {recovery_days}. "
        result_text += f"மருத்துவர் தேவை: {vet_required}."

        # 5. Generate Audio
        audio_url = generate_audio_response(result_text)

        return {
            "transcribed_text": transcribed_text,
            "disease": disease_tamil,
            "medicine": medicine_ta,
            "care": care_items,
            "recovery_days": recovery_days,
            "vet_required": vet_required,
            "full_text": result_text,
            "audio_url": audio_url
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"CRITICAL SERVER ERROR: {e}")
        return {
             "transcribed_text": transcribed_text,
             "error": f"Server Error: {str(e)}",
             "disease": "Error",
             "medicine": "-",
             "care": [],
             "recovery_days": "-",
             "vet_required": "-",
             "audio_url": None
        }

from fastapi.responses import FileResponse

# Serve audio files
audio_dir = os.path.join(current_dir, "audio")
os.makedirs(audio_dir, exist_ok=True)
app.mount("/audio", StaticFiles(directory=audio_dir), name="audio")

# Serve frontend files
frontend_dir = os.path.join(os.path.dirname(current_dir), "frontend")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
