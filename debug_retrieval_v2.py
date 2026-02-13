
import requests
import json
import sys
import os

API_URL = "http://127.0.0.1:8001/api/retrieval/data"

def check_file_paths():
    print("Checking file existence...")
    files = [
        "backend/outcomes.csv",
        "backend/nhmrc_processed.csv",
        "backend/arc_processed.csv"
    ]
    for f in files:
        exists = os.path.exists(f)
        print(f"File {f}: {'EXISTS' if exists else 'NOT FOUND'}")
        if exists:
            print(f"  Size: {os.path.getsize(f)} bytes")


def test_data(source="combined"):
    params = {
        "source": source,
        "page": 1,
        "limit": 5
    }
    print(f"\nRequesting data for source={source}...")
    try:
        res = requests.get(API_URL, params=params)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            print(f"Total: {data['pagination']['total']}")
            print(f"Rows returned: {len(data['data'])}")
            if data['data']:
                print(f"First row: {data['data'][0]}")
            else:
                print("No data in response.")
        else:
            print(res.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_file_paths()
    test_data("combined")
    test_data("nhmrc")
