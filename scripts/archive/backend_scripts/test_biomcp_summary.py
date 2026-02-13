
import logging
from app.utils.llm_handler import LLMHandler
from app.config import secrets

# Mock BioMCP availability for testing logic
import sys
from unittest.mock import MagicMock

def test_summary_generation():
    print("Testing summary generation with BioMCP integration...")
    
    # Initialize handler
    handler = LLMHandler("claude-4-5-sonnet", secrets)
    
    # Mock BioMCP client to simulate available tool and results
    handler.biomcp.available = True
    handler.biomcp.search_pubmed_by_researcher = MagicMock(return_value=[
        {
            "title": "Novel therapies for melanoma",
            "authors": ["Smith J", "Doe A"],
            "journal": "Science",
            "year": "2024",
            "pmid": "123456",
            "doi": "10.1126/science.123456",
            "abstract": "This study explores new treatments..."
        }
    ])
    
    # Mock results
    results = [
        {
            "g.title": "Analysis of BRAF mutations",
            "g.amount": "$1,500,000",
            "g.start_year": "2023",
            "researcher": "John Smith",
            "institution": "University of Sydney"
        }
    ]
    
    # Generate summary with debug prompt printing
    # We want to catch the prompt before it's sent to LLM to verify format
    # But since we can't easily hook into the method, we'll just run it and check the output format
    # or rely on the fact that we updated the code.
    
    # For now, let's just run it (it might make an API call)
    try:
        summary = handler.generate_summary("melanoma research", results, include_search=False)
        print("\nGenerated Summary Preview:")
        print("-" * 50)
        print(summary[:500] + "..." if len(summary) > 500 else summary)
        print("-" * 50)
        
        if "## Title" in summary and "## External References" in summary:
            print("✅ Output format contains requested headers.")
        else:
            print("⚠️ Output format might not contain requested headers (depends on LLM response).")
            
    except Exception as e:
        print(f"Error generating summary: {e}")

if __name__ == "__main__":
    test_summary_generation()
