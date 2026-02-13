import paperscraper
import json

print("Testing paperscraper...")

# Check available modules
print(dir(paperscraper))

# Try a simple search if possible.
# Most 'paperscraper' libs require a 'search_papers' or similar.
# If it's the specific Peterson one, it focuses on 'get_dumps' etc.
# But let's see.

try:
    from paperscraper.scraper import Scraper
    print("Scraper class found")
except ImportError:
    print("Scraper class NOT found using 'from paperscraper.scraper import Scraper'")

try:
    from paperscraper import search_papers
    print("search_papers found")
except ImportError:
    print("search_papers NOT found")
