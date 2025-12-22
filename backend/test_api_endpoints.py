import requests
import json

def test_endpoints():
    base_url = "http://localhost:8000/api/analytics"
    
    print("=== Testing Analytics API Endpoints ===\n")
    
    # Test 1: Stats endpoint (no filters)
    print("1. Testing /stats endpoint (no filters)...")
    try:
        resp = requests.get(f"{base_url}/stats", timeout=5)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Error: {resp.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\n2. Testing /institutions endpoint...")
    try:
        resp = requests.get(f"{base_url}/institutions?limit=5", timeout=5)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"   Found {len(data)} institutions")
            if data:
                print(f"   First institution: {data[0]}")
        else:
            print(f"   Error: {resp.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\n3. Testing /trends endpoint...")
    try:
        resp = requests.get(f"{base_url}/trends?start_year_min=2005&start_year_max=2024", timeout=5)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"   Found {len(data)} data points")
            if data:
                print(f"   First data point: {data[0]}")
        else:
            print(f"   Error: {resp.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\n4. Testing /filters endpoint...")
    try:
        resp = requests.get(f"{base_url}/filters", timeout=30)
        print(f"   Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"   Funding bodies: {data.get('funding_body', [])}")
            print(f"   Institutions count: {len(data.get('institution', []))}")
        else:
            print(f"   Error: {resp.text}")
    except Exception as e:
        print(f"   Exception: {e}")

if __name__ == "__main__":
    test_endpoints()
