import requests
import json

def test_map_endpoint():
    url = "http://localhost:8000/api/analytics/map"
    try:
        print(f"Testing URL: {url}")
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Retrieved {len(data)} records.")
            if len(data) > 0:
                print("First record sample:")
                print(json.dumps(data[0], indent=2))
                
                # Check for lat/lon
                has_coords = all('latitude' in item and 'longitude' in item for item in data)
                print(f"\nAll items have coordinates: {has_coords}")
                
                # Check for null coordinates
                null_coords = [item for item in data if item.get('latitude') is None or item.get('longitude') is None]
                if null_coords:
                    print(f"\nWARNING: {len(null_coords)} items have null coordinates!")
                    print("Sample with null coords:", json.dumps(null_coords[0], indent=2))
            else:
                print("Warning: API returned empty list.")
        else:
            print(f"Error: Status code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    test_map_endpoint()
