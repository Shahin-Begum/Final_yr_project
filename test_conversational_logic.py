from fastapi.testclient import TestClient
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.main import app

client = TestClient(app)

def test_conversational_logic():
    print("Testing Conversational Logic...")
    
    # 1. Test Valid Breed
    print("\n1. Testing Valid Breed (Cow, Persian)...") 
    # Note: Persian is a Cat breed in the CSV shown earlier, let's use that
    response = client.post(
        "/predict/",
        data={
            "animal": "Cat", 
            "breed": "Persian", 
            "symptoms_tamil": "fever"
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Disease Found: {data.get('disease')}")
        if data.get('disease') != "தெரியவில்லை":
            print("SUCCESS: Found disease using Breed filter")
        else:
            print("FAILURE: Disease not found")
    else:
        print(f"FAILURE: Status {response.status_code}")

    # 2. Test Invalid Age
    print("\n2. Testing Invalid Age (Cat, Persian, Age=999)...")
    response = client.post(
        "/predict/",
        data={
            "animal": "Cat", 
            "breed": "Persian", 
            "age": "999",
            "symptoms_tamil": "fever"
        }
    )
    data = response.json()
    print(f"Response Error: {data.get('error')}")
    if "not found" in str(data.get('error')).lower():
        print("SUCCESS: Correctly returned error for invalid age")
    else:
        print(f"FAILURE: Expected error for invalid age, got {data}")

    # 3. Test Full Flow (Cat, Persian, 7, Female, fever) -> Viral Fever (from CSV line 2)
    print("\n3. Testing Full Flow (Cat, Persian, 7, Female, fever)...")
    response = client.post(
        "/predict/",
        data={
            "animal": "Cat", 
            "breed": "Persian", 
            "age": "7",
            "gender": "Female",
            "symptoms_tamil": "fever"
        }
    )
    data = response.json()
    print(f"Disease: {data.get('disease')}")
    # Viral Fever -> Tamil translation check
    # Check if 'fever' or related term is in there. 
    # CSV Line 2: Cat,Persian,7,Female,Viral Fever...
    # backend translation likely "???" or English if not mapped.
    # Viral Fever is likely mapped or just passed through if not in map.
    
    if data.get('disease') != "தெரியவில்லை":
         print("SUCCESS: Full flow prediction worked")
    else:
         print("FAILURE: Full flow prediction failed")

if __name__ == "__main__":
    test_conversational_logic()
