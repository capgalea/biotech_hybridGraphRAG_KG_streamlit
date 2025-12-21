#!/usr/bin/env python3

from utils.neo4j_handler import Neo4jHandler
from utils.llm_handler import LLMHandler
from utils.query_processor import QueryProcessor
from pathlib import Path
import toml

# Load secrets
secrets_path = Path('.streamlit/secrets.toml')
secrets = toml.load(secrets_path)

# Initialize handlers
neo4j = Neo4jHandler(
    uri=secrets['neo4j']['uri'],
    user=secrets['neo4j']['user'], 
    password=secrets['neo4j']['password'],
    database=secrets['neo4j']['database']
)

llm_handler = LLMHandler("GPT-4o", dict(secrets))
query_processor = QueryProcessor(neo4j, llm_handler)

# Test the enhanced query that's causing issues
print("Testing summary generation...")
query = "grant details for glenn king"
results = query_processor.process_query(query)

print("\n=== SUMMARY DEBUG ===")
print(f"Summary type: {type(results.get('summary'))}")
print(f"Summary length: {len(results.get('summary', ''))}")
print(f"First 100 chars: {repr(results.get('summary', '')[:100])}")
print(f"Summary: {results.get('summary', '')}")

# Test summary generation separately
print("\n=== DIRECT LLM TEST ===")
test_results = [{"researcher": "Glenn King", "grant": "Test Grant"}]
direct_summary = llm_handler.generate_summary(query, test_results)
print(f"Direct summary type: {type(direct_summary)}")
print(f"Direct summary length: {len(direct_summary)}")
print(f"Direct summary: {repr(direct_summary)}")

# Close connection
neo4j.close()