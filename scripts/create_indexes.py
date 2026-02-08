from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

def create_indexes():
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    
    indexes = [
        # Grant indexes
        "CREATE INDEX grant_application_id IF NOT EXISTS FOR (g:Grant) ON (g.application_id)",
        "CREATE INDEX grant_start_year IF NOT EXISTS FOR (g:Grant) ON (g.start_year)",
        "CREATE INDEX grant_amount IF NOT EXISTS FOR (g:Grant) ON (g.amount)",
        "CREATE INDEX grant_grant_type IF NOT EXISTS FOR (g:Grant) ON (g.grant_type)",
        "CREATE INDEX grant_funding_body IF NOT EXISTS FOR (g:Grant) ON (g.funding_body)",
        "CREATE INDEX grant_broad_research_area IF NOT EXISTS FOR (g:Grant) ON (g.broad_research_area)",
        "CREATE INDEX grant_field_of_research IF NOT EXISTS FOR (g:Grant) ON (g.field_of_research)",
        "CREATE INDEX grant_status IF NOT EXISTS FOR (g:Grant) ON (g.grant_status)",
        "CREATE INDEX grant_title IF NOT EXISTS FOR (g:Grant) ON (g.title)",
        
        # Institution indexes
        "CREATE INDEX institution_name IF NOT EXISTS FOR (i:Institution) ON (i.name)",
        
        # Researcher indexes
        "CREATE INDEX researcher_name IF NOT EXISTS FOR (r:Researcher) ON (r.name)",
        
        # ResearchArea indexes
        "CREATE INDEX research_area_name IF NOT EXISTS FOR (a:ResearchArea) ON (a.name)",
        
        # Fulltext search indexes (optional, for text search performance)
        # "CREATE FULLTEXT INDEX grant_fulltext IF NOT EXISTS FOR (g:Grant) ON EACH [g.title, g.description]"
    ]

    print(f"Connecting to {URI}...")
    try:
        with driver.session(database=DATABASE) as session:
            for query in indexes:
                print(f"Running: {query}")
                session.run(query)
        print("Indexes created successfully.")
    except Exception as e:
        print(f"Error creating indexes: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    create_indexes()
