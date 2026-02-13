import requests
import urllib.parse

def test_openalex():
    title = "Venoms to drugs: translating venom peptides into human therapeutics"
    safe_title = urllib.parse.quote(title)
    url = f"https://api.openalex.org/works?search={safe_title}&per-page=3"
    
    print(f"Requesting: {url}")
    try:
        r = requests.get(url)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            results = data.get('results', [])
            print(f"Found {len(results)} papers")
            for work in results:
                print(f"- {work['title']} ({work['doi']})")
        else:
            print(r.text)
    except Exception as e:
        print(e)
        
if __name__ == "__main__":
    test_openalex()
