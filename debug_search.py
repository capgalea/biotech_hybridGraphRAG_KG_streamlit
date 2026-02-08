import requests
import json

def test_endpoint(url, method="GET", payload=None):
    print(f"\n--- Testing {url} [{method}] ---")
    headers = {"Content-Type": "application/json"}
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        else:
            response = requests.post(url, json=payload, headers=headers)
        
        print(f"Status: {response.status_code}")
        # print first 100 chars of response
        snippet = response.text[:100].replace("\n", " ")
        print(f"Response: {snippet}...")
        return response.status_code
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return -1

def run_tests():
    payload = {
        "query": "test",
        "enable_search": True
    }
    
    with open("debug_output.txt", "w") as f:
        # Redirect stdout to file
        import sys
        sys.stdout = f
        
        test_endpoint("http://127.0.0.1:8000/")
        test_endpoint("http://127.0.0.1:8000/api/test")
        test_endpoint("http://127.0.0.1:8000/api/query", method="POST", payload=payload)
        test_endpoint("http://127.0.0.1:8000/api/query/", method="POST", payload=payload)

if __name__ == "__main__":
    run_tests()
