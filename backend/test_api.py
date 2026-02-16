import requests
import sys

def test_api():
    base_url = "http://127.0.0.1:8000"
    
    # Test Prediction (Text)
    print("Testing Prediction Endpoint via 127.0.0.1 (Text)...")
    print("Testing Prediction Endpoint via 127.0.0.1...")
    try:
        response = requests.post(
            f"{base_url}/predict/",
            data={"animal": "Cow", "symptoms_tamil": "காய்ச்சல்"}
        )
        response.raise_for_status()
        data = response.json()
        
        
        print("\nPrediction Response:")
        if 'disease' in data:
            disease_val = data.get('disease')
            # Safe print for Windows console
            try:
                print(f"Disease: {disease_val}")
            except UnicodeEncodeError:
                 # fallback to bytes representation
                 print(f"Disease (safe): {disease_val.encode('utf-8', 'ignore')}")
        else:
            print("Disease: Not found in response")
            print(f"Response keys: {list(data.keys())}")
            if 'error' in data:
                 print(f"Error from server: {data['error']}")
        
        print(f"Audio URL: {data.get('audio_url')}")
        
        if not data.get('disease'):
            print("FAILED: No disease returned")
            sys.exit(1)
            
        audio_url = data.get('audio_url')
        if not audio_url or not audio_url.startswith("/audio/"):
            print("FAILED: Invalid audio URL")
            sys.exit(1)
            
    except Exception as e:
        print(f"FAILED: Connection error or invalid response. Ensure server is running on port 8001. Error: {e}")
        sys.exit(1)

    # Test Audio Retrieval
    print("\nTesting Audio Endpoint...")
    try:
        audio_full_url = f"{base_url}{audio_url}"
        audio_response = requests.get(audio_full_url)
        
        if audio_response.status_code == 200:
            print(f"Audio file retrieved successfully ({len(audio_response.content)} bytes)")
        else:
            print(f"FAILED: Audio retrieval failed with status {audio_response.status_code}")
            sys.exit(1)
            
    except Exception as e:
        print(f"FAILED: Error retrieving audio: {e}")
        sys.exit(1)
        
    print("\n[PASS] Verification Successful!")

if __name__ == "__main__":
    test_api()
