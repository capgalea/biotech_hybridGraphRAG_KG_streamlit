import sys
import os
import logging
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))

from app.config import settings, secrets
from app.utils.neo4j_handler import Neo4jHandler
from app.utils.llm_handler import LLMHandler
from app.utils.query_processor import QueryProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_query():
    print("--- Starting Debug Script ---")
    
    if not secrets:
        print("ERROR: Secrets not loaded")
        return

    print("Initializing Neo4j Handler...")
    try:
        neo4j_handler = Neo4jHandler(
            uri=settings["neo4j"]["uri"],
            user=settings["neo4j"]["user"],
            password=settings["neo4j"]["password"],
            database=settings["neo4j"]["database"]
        )
    except Exception as e:
        print(f"ERROR: Neo4j Handler Init Failed: {e}")
        return

    print("Initializing LLM Handler...")
    try:
        # Test with DeepSeek R1 as requested
        backend_model = "DeepSeek R1" 
        llm_handler = LLMHandler(backend_model, secrets)
        print(f"LLM Handler initialized with model: {backend_model}")
        print(f"Provider: {llm_handler.provider}")
        print(f"Model ID: {llm_handler.model_id}")
    except Exception as e:
        print(f"ERROR: LLM Handler Init Failed: {e}")
        return

    print("Initializing Query Processor...")
    processor = QueryProcessor(neo4j_handler, llm_handler)

    query = "grants by 'tony velkov'"
    print(f"Running query: '{query}'")
    try:
        # Note: process_query is synchronous in the class, but let's check
        result = processor.process_query(query, include_search=False)
        print("Query processed successfully!")
        print("Result keys:", result.keys())
    except Exception as e:
        print(f"ERROR: Query Processing Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_query()
