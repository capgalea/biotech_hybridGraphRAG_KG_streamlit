import requests

try:
    resp = requests.get('http://localhost:8000/api/analytics/filters', timeout=10)
    data = resp.json()
    print("=== Filter Options Available ===")
    print(f"\nFunding Bodies: {data.get('funding_body', [])}")
    print(f"\nTotal Institutions: {len(data.get('institution', []))}")
    print(f"Total Grant Types: {len(data.get('grant_type', []))}")
    print(f"Total Years: {len(data.get('start_year', []))}")
    print(f"Total Research Areas: {len(data.get('broad_research_area', []))}")
    print(f"Total Fields of Research: {len(data.get('field_of_research', []))}")
except Exception as e:
    print(f"Error: {e}")
