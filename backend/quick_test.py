import requests

def quick_test():
    print("Testing individual endpoints...\n")
    
    # Test stats only
    print("1. Stats endpoint:")
    try:
        resp = requests.get("http://localhost:8000/api/analytics/stats", timeout=3)
        print(f"   ✓ Status {resp.status_code}: {resp.json()}")
    except Exception as e:
        print(f"   ✗ Error: {str(e)[:50]}")
    
    # Test institutions only
    print("\n2. Institutions endpoint:")
    try:
        resp = requests.get("http://localhost:8000/api/analytics/institutions?limit=3", timeout=3)
        print(f"   ✓ Status {resp.status_code}: {len(resp.json())} institutions")
    except Exception as e:
        print(f"   ✗ Error: {str(e)[:50]}")

if __name__ == "__main__":
    quick_test()
