import requests

def test_filters_direct():
    print("Testing /filters endpoint specifically...\n")
    
    try:
        print("Making request with 60s timeout...")
        resp = requests.get("http://localhost:8000/api/analytics/filters", timeout=60)
        print(f"✓ Status: {resp.status_code}")
        data = resp.json()
        
        print(f"\nFilter options received:")
        for key, values in data.items():
            if isinstance(values, list):
                print(f"  {key}: {len(values)} options")
                if len(values) > 0 and len(values) <= 5:
                    print(f"    Values: {values}")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    test_filters_direct()
