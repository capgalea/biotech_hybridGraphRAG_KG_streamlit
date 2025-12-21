#!/usr/bin/env python3
"""
Debug script to check what researchers are in the database
that might match 'jian li' or similar names
"""

import streamlit as st
from utils.neo4j_handler import Neo4jHandler

def debug_researchers():
    """Check what researchers exist in the database"""
    
    # Initialize Neo4j handler
    neo4j_config = {
        "uri": st.secrets["neo4j"]["uri"],
        "user": st.secrets["neo4j"]["user"], 
        "password": st.secrets["neo4j"]["password"]
    }
    
    neo4j_handler = Neo4jHandler(
        neo4j_config["uri"],
        neo4j_config["user"], 
        neo4j_config["password"]
    )
    
    # Query 1: Find all researchers with "li" in their name
    print("\n=== Researchers with 'li' in name ===")
    query1 = """
    MATCH (r:Researcher)
    WHERE toLower(r.name) CONTAINS 'li'
    RETURN r.name as name
    ORDER BY r.name
    """
    
    results1 = neo4j_handler.execute_cypher(query1)
    for record in results1:
        print(f"- {record['name']}")
    
    # Query 2: Find all researchers with "jian" in their name  
    print("\n=== Researchers with 'jian' in name ===")
    query2 = """
    MATCH (r:Researcher)
    WHERE toLower(r.name) CONTAINS 'jian'
    RETURN r.name as name
    ORDER BY r.name
    """
    
    results2 = neo4j_handler.execute_cypher(query2)
    for record in results2:
        print(f"- {record['name']}")
    
    # Query 3: Exact match for "jian li"
    print("\n=== Exact match for 'jian li' ===")
    query3 = """
    MATCH (r:Researcher)
    WHERE toLower(r.name) = 'jian li'
    RETURN r.name as name
    """
    
    results3 = neo4j_handler.execute_cypher(query3)
    if results3:
        for record in results3:
            print(f"✅ FOUND: {record['name']}")
    else:
        print("❌ No exact match for 'jian li'")
    
    # Query 4: Flexible matching for "jian li"
    print("\n=== Flexible matching for 'jian li' patterns ===")
    query4 = """
    MATCH (r:Researcher)
    WHERE (toLower(r.name) = 'jian li' 
           OR toLower(r.name) = 'li, jian'
           OR toLower(r.name) = 'dr jian li'
           OR toLower(r.name) = 'prof jian li'
           OR toLower(r.name) = 'professor jian li'
           OR (toLower(r.name) CONTAINS 'jian li' AND LENGTH(r.name) <= 20))
    RETURN r.name as name
    ORDER BY r.name
    """
    
    results4 = neo4j_handler.execute_cypher(query4)
    if results4:
        print("✅ FLEXIBLE MATCHES FOUND:")
        for record in results4:
            print(f"  - {record['name']}")
    else:
        print("❌ No flexible matches for 'jian li'")
    
    # Query 5: Show total researcher count
    print("\n=== Total Researchers ===")
    query5 = """
    MATCH (r:Researcher)
    RETURN count(r) as total
    """
    
    results5 = neo4j_handler.execute_cypher(query5)
    total = results5[0]['total'] if results5 else 0
    print(f"Total researchers in database: {total}")
    
    neo4j_handler.close()

if __name__ == "__main__":
    debug_researchers()