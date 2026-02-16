import pandas as pd
import re
import os

# Load dataset
current_dir = os.path.dirname(os.path.abspath(__file__))
dataset_path = os.path.join(current_dir, 'dataset.csv')
df = pd.read_csv(dataset_path)

# Extract all unique symptoms from the dataset columns Symptom1, Symptom2, Symptom3
symptoms = set()
for col in ['Symptom1', 'Symptom2', 'Symptom3']:
    for item in df[col].dropna():
        symptoms.add(str(item).strip().lower())

print(f"Total unique symptoms in CSV: {len(symptoms)}")
print(f"Symptoms: {symptoms}")

# Define the current mapping from main.py (Manually copied for verification)
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
    "அரிப்பு": "itching", 
    "சீழ்": "pus",
    "தீவனம் எடுக்கவில்லை": "loss of appetite",
    "சாப்பிடவில்லை": "loss of appetite",
    "கழிச்சல்": "loose motion",
    "பேதி": "loose motion"
}

mapped_english_symptoms = set(s.lower() for s in tamil_to_english_symptoms.values())

# Check for missing
missing = symptoms - mapped_english_symptoms
if missing:
    print(f"\n[FAIL] Missing mappings for: {missing}")
else:
    print("\n[PASS] All dataset symptoms are mapped.")
