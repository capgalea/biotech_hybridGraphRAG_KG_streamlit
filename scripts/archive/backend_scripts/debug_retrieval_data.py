
import requests
import json
import sys

API_URL = "http://127.0.0.1:8001/api/retrieval/data"

def test_data(source="nhmrc"):
    params = {
        "source": source,
        "page": 1,
        "limit": 10
    }
    print(f"Requesting data for source={source}...")
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
            print(res.text)
    except Exception as e:
        print(f"Error: {e}")

test_data("nhmrc")
test_data("arc")
