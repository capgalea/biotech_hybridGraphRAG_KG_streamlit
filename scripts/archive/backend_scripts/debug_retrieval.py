import requests
import pandas as pd
import os

API_URL = "http://127.0.0.1:8001/api/retrieval"

def check_file(filename):
    if os.path.exists(filename):
        try:
            df = pd.read_csv(filename)
            print(f"[FILE] {filename}: {len(df)} rows. Columns: {list(df.columns)}")
            if 'Funding_Body' in df.columns:
                print(f"       Funding_Body counts: {df['Funding_Body'].value_counts().to_dict()}")
        except Exception as e:
            print(f"[FILE] {filename}: Error reading ({e})")
    else:
        print(f"[FILE] {filename}: DOES NOT EXIST")

def check_api(source):
    print(f"\n[API] Testing source='{source}'...")
    try:
        resp = requests.get(f"{API_URL}/data", params={"source": source, "limit": 5})
        if resp.status_code == 200:
            data = resp.json()
            total = data['pagination']['total']
            print(f"      Response: {total} total records.")
            if total > 0:
                rows = data['data']
                print(f"      First row Funding_Body: {rows[0].get('Funding_Body', 'N/A')}")
        else:
            print(f"      Error: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"      Request failed: {e}")

if __name__ == "__main__":
    print("--- CHECKING FILES ---")
    check_file("outcomes.csv")
    check_file("nhmrc_processed.csv")
    check_file("arc_processed.csv")
    
    print("\n--- CHECKING API ---")
    check_api("combined")
    check_api("nhmrc")
    check_api("arc")
