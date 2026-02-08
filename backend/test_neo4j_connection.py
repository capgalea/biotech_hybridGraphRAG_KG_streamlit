import sys
import threading
from app.config import settings
from neo4j import GraphDatabase

def test_connection():
    try:
        print(f"Testing connection to Neo4j...")
        print(f"URI: {settings['neo4j']['uri']}")
        print(f"User: {settings['neo4j']['user']}")
        
        driver = GraphDatabase.driver(
            settings['neo4j']['uri'], 
            auth=(settings['neo4j']['user'], settings['neo4j']['password']),
            connection_timeout=5.0  # 5 second timeout
        )
        
        driver.verify_connectivity()
        print("✅ Neo4j Connected Successfully!")
        
        # Test a simple query
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            print("✅ Query executed successfully!")
        
        driver.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\nPossible issues:")
        print("1. Database is not started in Neo4j Desktop")
        print("   → Open Neo4j Desktop and click the START button on your database")
        print("2. Wrong password in .env file")
        print("   → Check that NEO4J_PASSWORD matches your database password")
        print("3. Database is running on a different port")
        print("   → Verify the bolt port in Neo4j Desktop settings")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
