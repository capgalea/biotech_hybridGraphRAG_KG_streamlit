"""
Quick fix for Query & Chat timeout issue:
The timeout is caused by web scraping in the generate_summary method.

Solution: Add a timeout parameter to the requests in _scrape_webpage method
and handle timeouts gracefully.
"""

# Test if disabling web search fixes the issue
import requests
import json

url = "http://localhost:8000/api/query/"
payload = {
    "query": "cancer research",
    "llm_model": "claude-4-5-sonnet",
    "enable_search": False  # Disable web search to test
}

print("Testing query endpoint WITHOUT web search...")
print(f"Payload: {json.dumps(payload, indent=2)}")
print("\nSending request...")

try:
    response = requests.post(url, json=payload, timeout=60)
    print(f"\n✅ Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Query successful!")
        print(f"   Found {data.get('count', 0)} results")
        print(f"   Summary length: {len(data.get('summary', ''))} characters")
    else:
        print(f"❌ Error: {response.text[:500]}")
except requests.exceptions.Timeout:
    print("\n❌ Request still timed out even without web search")
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
