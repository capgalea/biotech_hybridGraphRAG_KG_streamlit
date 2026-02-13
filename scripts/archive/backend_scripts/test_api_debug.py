import requests
import json
import time

def test_query():
    url = "http://localhost:8000/query/"
    payload = {
        "query": "Grant Analysis: Glenn King Research Funding",
        "llm_model": "claude-4-5-sonnet",
        "enable_search": True
    }
    
    print(f"Sending request to {url}...")
    try:
        start = time.time()
        response = requests.post(url, json=payload, timeout=60)
        print(f"Response received in {time.time() - start:.2f}s")
        
        if response.status_code == 200:
            data = response.json()
            # Save full response to file
            with open("debug_response.txt", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            summary = data.get('summary', '')
            print("\nSummary Validation:")
            if "No directly derived confirmed papers found" in summary:
                print("FAILURE: Papers NOT found message present.")
            elif "Related Research Papers" in summary:
                print("SUCCESS: Related Papers section found.")
            else:
                print("UNCERTAIN: Neither success nor failure marker found.")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_query()
