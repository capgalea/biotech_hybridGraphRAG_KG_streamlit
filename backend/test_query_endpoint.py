import requests
import json

url = "http://localhost:8000/api/query/"
payload = {
    "query": "test query",
    "llm_model": "claude-4-5-sonnet",
    "enable_search": False
}

print("Testing query endpoint...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("\nSending request...")

try:
    response = requests.post(url, json=payload, timeout=30)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except requests.exceptions.Timeout:
    print("\n❌ Request timed out after 30 seconds")
    print("This suggests the LLM is taking too long to respond or there's a hanging issue")
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
