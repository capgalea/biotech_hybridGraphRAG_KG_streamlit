from semanticscholar import SemanticScholar
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_search():
    sch = SemanticScholar()
    title = "Venoms to drugs: translating venom peptides into human therapeutics"
    
    print(f"Searching for: {title}")
    try:
        results = sch.search_paper(title, limit=3)
        print(f"Results object type: {type(results)}")
        
        # Check if empty
        # SemanticScholar search_paper returns a PaginatedList usually
        # We need to iterate or check
        data = list(results)
        print(f"Count: {len(data)}")
        
        for i, paper in enumerate(data):
            print(f"{i+1}. {paper.title} ({paper.url})")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_search()
