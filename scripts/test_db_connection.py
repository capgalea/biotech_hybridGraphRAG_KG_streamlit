
import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Try to load from .env file
load_dotenv()

def test_connection():
    print("--- Neo4j Connection Tester ---")
    
    # Get credentials
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "password")

    print(f"Testing connection details:")
    print(f"URI: {uri}")
    print(f"User: {user}")
    print(f"Password: {'*' * len(password) if password else '(empty)'}")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        print("\n✅ SUCCESS: Connected to Neo4j successfully!")
        driver.close()
        return True
    except Exception as e:
        print("\n❌ FAILURE: Could not connect to Neo4j.")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_connection()
