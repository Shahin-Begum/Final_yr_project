import requests
import os
from gtts import gTTS

BASE_URL = "http://127.0.0.1:8000"

def test_instruction_audio():
    print("Testing /instruction-audio endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/instruction-audio")
        if response.status_code == 200 and response.headers['content-type'] == 'audio/mpeg':
            print("[OK] Instruction audio retrieved successfully.")
        else:
            print(f"[FAIL] Failed to retrieve instruction audio. Status: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")

def test_audio_upload():
    print("\nTesting /predict/ with English audio upload...")
    
    # Generate a dummy audio file saying "Blister" (Singular, to test fuzzy match with "Blisters")
    audio_text = "Blister"
    audio_file = "test_input_en.mp3"
    tts = gTTS(text=audio_text, lang='en')
    tts.save(audio_file)
    
    try:
        with open(audio_file, "rb") as f:
            files = {"file": (audio_file, f, "audio/mpeg")}
            data = {"animal": "Cow", "symptoms_tamil": "audio_upload"} 
            
            response = requests.post(f"{BASE_URL}/predict/", data=data, files=files)
            
            if response.status_code == 200:
                result = response.json()
                print("[OK] Prediction successful.")
                print("[OK] Prediction successful.")
                transcribed_text = result.get('transcribed_text', '')
                try:
                    print(f"Transcribed Text: {transcribed_text}")
                except UnicodeEncodeError:
                    print(f"Transcribed Text (safe): {transcribed_text.encode('utf-8', 'ignore')}")
                
                disease = result.get('disease', '')
                try:
                     print(f"Disease: {disease}")
                except UnicodeEncodeError:
                     print(f"Disease (safe): {disease.encode('utf-8', 'ignore')}")
                     
                print(f"Audio URL: {result.get('audio_url')}")
                
                # Check directly in bytes or encoded string to avoid print error
                transcribed = result.get('transcribed_text', '')
                if "blister" in transcribed.lower():
                     print("[OK] Transcription matches expectation (English/Blister).")
                else:
                     print(f"[WARN] Transcription mismatch: Expected 'Blister', got '{transcribed}'")

                if result.get('audio_url'):
                    print("[OK] Audio URL received.")
                else:
                    print("[FAIL] Audio URL missing.")
            else:
                print(f"[FAIL] Prediction failed. Status: {response.status_code}")
                # print(response.text)
                
    except Exception as e:
        print(f"[ERROR] Error: {e}")
    finally:
        if os.path.exists(audio_file):
            os.remove(audio_file)

def test_tamil_audio_upload():
    print("\nTesting /predict/ with Tamil audio upload...")
    
    # Generate a dummy audio file saying "காய்ச்சல்" (Fever)
    # text = "எனக்கு காய்ச்சல் உள்ளது" # I have fever
    text = "காய்ச்சல்"
    audio_file = "test_input_ta.mp3"
    tts = gTTS(text=text, lang='ta')
    tts.save(audio_file)
    
    try:
        with open(audio_file, "rb") as f:
            files = {"file": (audio_file, f, "audio/mpeg")}
            data = {"animal": "Cow", "symptoms_tamil": "audio_upload"} 
            
            response = requests.post(f"{BASE_URL}/predict/", data=data, files=files)
            
            if response.status_code == 200:
                result = response.json()
                print("[OK] Tamil Prediction successful.")
                
                transcribed_text = result.get('transcribed_text', '')
                try:
                    print(f"Transcribed Text (Ta): {transcribed_text}")
                except UnicodeEncodeError:
                    print(f"Transcribed Text (safe): {transcribed_text.encode('utf-8', 'ignore')}")

                disease = result.get('disease', '')
                try:
                     print(f"Disease: {disease}")
                except UnicodeEncodeError:
                     print(f"Disease (safe): {disease.encode('utf-8', 'ignore')}")
                     
                # Check if it detected fever (Foot and Mouth has fever?)
                # We interpret "fever" -> "Foot and Mouth Disease" in our mapping logic if fever is a symptom?
                # Actually "fever" maps to "Foot and Mouth Disease" if matched.
                
                if "fever" in str(result.get('remedies', '')).lower() or "foot and mouth" in str(disease).lower() or "fever" in transcribed_text.lower():
                     print("[OK] Tamil logic verified (Fever/Disease detected).")
                else:
                     print("[WARN] Tamil logic check unclear.")

            else:
                print(f"[FAIL] Prediction failed. Status: {response.status_code}")
                
    except Exception as e:
        print(f"[ERROR] Error: {e}")
    finally:
        if os.path.exists(audio_file):
            os.remove(audio_file)

if __name__ == "__main__":
    test_instruction_audio()
    test_audio_upload()
    test_tamil_audio_upload()
