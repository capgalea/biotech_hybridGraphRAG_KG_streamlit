"""
Data ingestion script for loading grant data into Neo4j
This creates the graph schema and populates the database
"""

import pandas as pd
from neo4j import GraphDatabase, Query
import logging
from typing import Dict, Any, Optional
import sys
import os
import toml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataIngestion:
    """Handle data ingestion into Neo4j"""
    
    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
    
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        """Clear all nodes and relationships (use with caution!)"""
        with self.driver.session(database=self.database) as session:
            logger.info("Clearing database...")
            session.run("MATCH (n) DETACH DELETE n")  # type: ignore
            logger.info("Database cleared")
    
    def create_constraints(self):
        """Create uniqueness constraints"""
        constraints = [
            "CREATE CONSTRAINT grant_id IF NOT EXISTS FOR (g:Grant) REQUIRE g.application_id IS UNIQUE",
            "CREATE CONSTRAINT researcher_name IF NOT EXISTS FOR (r:Researcher) REQUIRE r.name IS UNIQUE",
            "CREATE CONSTRAINT institution_name IF NOT EXISTS FOR (i:Institution) REQUIRE i.name IS UNIQUE",
            "CREATE CONSTRAINT area_name IF NOT EXISTS FOR (a:ResearchArea) REQUIRE a.name IS UNIQUE",
        ]
        
        with self.driver.session(database=self.database) as session:
            for constraint in constraints:
                try:
                    session.run(constraint)  # type: ignore
                    logger.info(f"Created constraint: {constraint[:50]}...")
                except Exception as e:
                    logger.warning(f"Constraint may already exist: {str(e)}")
    
    def create_indexes(self):
        """Create indexes for better query performance"""
        indexes = [
            "CREATE INDEX grant_title IF NOT EXISTS FOR (g:Grant) ON (g.title)",
            "CREATE INDEX grant_amount IF NOT EXISTS FOR (g:Grant) ON (g.amount)",
            "CREATE INDEX grant_year IF NOT EXISTS FOR (g:Grant) ON (g.start_year)",
            "CREATE INDEX researcher_orcid IF NOT EXISTS FOR (r:Researcher) ON (r.orcid_id)",
        ]
        
        with self.driver.session(database=self.database) as session:
            for index in indexes:
                try:
                    session.run(index)  # type: ignore
                    logger.info(f"Created index: {index[:50]}...")
                except Exception as e:
                    logger.warning(f"Index may already exist: {str(e)}")
    
    def ingest_grant(self, session, grant_data: Dict[str, Any]):
        """Ingest a single grant and create relationships"""
        
        # Create Grant node
        grant_cypher = """
        MERGE (g:Grant {application_id: $application_id})
        SET g.title = $title,
            g.description = $description,
            g.grant_type = $grant_type,
            g.amount = $amount,
            g.start_year = $start_year,
            g.end_date = $end_date,
            g.date_announced = $date_announced,
            g.funding_body = $funding_body,
            g.broad_research_area = $broad_research_area,
            g.field_of_research = $field_of_research
        """
        
        session.run(grant_cypher, {  # type: ignore
            'application_id': int(grant_data['Application_ID']),
            'title': grant_data['Grant_Title'],
            'description': grant_data.get('Plain_Description', ''),
            'grant_type': grant_data.get('Grant_Type', ''),
            'amount': float(grant_data.get('Total_Amount', 0)),
            'start_year': int(grant_data.get('Grant_Start_Year', 0)) if pd.notna(grant_data.get('Grant_Start_Year')) else None,
            'end_date': grant_data.get('Grant_End_Date', ''),
            'date_announced': grant_data.get('Date_Announced', ''),
            'funding_body': grant_data.get('Funding_Body', ''),
            'broad_research_area': grant_data.get('Broad_Research_Area', ''),
            'field_of_research': grant_data.get('Field_of_Research', '')
        })
        
        # Create Researcher node and relationship
        if pd.notna(grant_data.get('CIA_Name')):
            researcher_cypher = """
            MERGE (r:Researcher {name: $name})
            SET r.orcid_id = $orcid_id
            WITH r
            MATCH (g:Grant {application_id: $application_id})
            MERGE (r)-[:PRINCIPAL_INVESTIGATOR]->(g)
            """
            
            session.run(researcher_cypher, {  # type: ignore
                'name': grant_data['CIA_Name'],
                'orcid_id': grant_data.get('CIA_ORCID_ID', ''),
                'application_id': int(grant_data['Application_ID'])
            })
        
        # Create Institution node and relationship
        if pd.notna(grant_data.get('Admin_Institution')):
            institution_cypher = """
            MERGE (i:Institution {name: $name})
            WITH i
            MATCH (g:Grant {application_id: $application_id})
            MERGE (g)-[:HOSTED_BY]->(i)
            """
            
            session.run(institution_cypher, {  # type: ignore
                'name': grant_data['Admin_Institution'],
                'application_id': int(grant_data['Application_ID'])
            })
        
        # Create ResearchArea node and relationship
        if pd.notna(grant_data.get('Broad_Research_Area')):
            area_cypher = """
            MERGE (a:ResearchArea {name: $name})
            WITH a
            MATCH (g:Grant {application_id: $application_id})
            MERGE (g)-[:IN_AREA]->(a)
            """
            
            session.run(area_cypher, {  # type: ignore
                'name': grant_data['Broad_Research_Area'],
                'application_id': int(grant_data['Application_ID'])
            })
        
        # Parse and create detailed research field nodes
        if pd.notna(grant_data.get('Field_of_Research')):
            fields = grant_data['Field_of_Research'].split('|')
            for i, field in enumerate(fields):
                field = field.strip()
                if field:
                    field_cypher = """
                    MERGE (f:ResearchField {name: $name})
                    WITH f
                    MATCH (g:Grant {application_id: $application_id})
                    MERGE (g)-[:HAS_FIELD {level: $level}]->(f)
                    """
                    
                    session.run(field_cypher, {  # type: ignore
                        'name': field,
                        'application_id': int(grant_data['Application_ID']),
                        'level': i
                    })
    
    def ingest_csv(self, csv_path: str):
        """Ingest data from CSV file"""
        logger.info(f"Reading CSV file: {csv_path}")
        df = pd.read_csv(csv_path)
        
        logger.info(f"Found {len(df)} records")
        
        with self.driver.session(database=self.database) as session:
            for count, (idx, row) in enumerate(df.iterrows(), 1):
                try:
                    self.ingest_grant(session, row.to_dict())
                    if count % 10 == 0:
                        logger.info(f"Processed {count}/{len(df)} grants")
                except Exception as e:
                    logger.error(f"Error processing grant {row.get('Application_ID')}: {str(e)}")
        
        logger.info("Data ingestion complete!")
    
    def create_vector_index(self):
        """
        Create vector index for semantic search
        Note: Requires Neo4j 5.11+ and embedding generation
        """
        vector_index_cypher = """
        CREATE VECTOR INDEX grant_embeddings IF NOT EXISTS
        FOR (g:Grant) ON (g.embedding)
        OPTIONS {
            indexConfig: {
                `vector.dimensions`: 384,
                `vector.similarity_function`: 'cosine'
            }
        }
        """
        
        try:
            with self.driver.session(database=self.database) as session:
                session.run(vector_index_cypher)  # type: ignore
                logger.info("Vector index created (embeddings need to be added separately)")
        except Exception as e:
            logger.warning(f"Could not create vector index: {str(e)}")
            logger.warning("Vector search will not be available")
    
    def verify_ingestion(self):
        """Verify data was ingested correctly"""
        queries = [
            ("Grants", "MATCH (g:Grant) RETURN count(g) as count"),
            ("Researchers", "MATCH (r:Researcher) RETURN count(r) as count"),
            ("Institutions", "MATCH (i:Institution) RETURN count(i) as count"),
            ("Research Areas", "MATCH (a:ResearchArea) RETURN count(a) as count"),
            ("Relationships", "MATCH ()-[r]->() RETURN count(r) as count"),
        ]
        
        with self.driver.session(database=self.database) as session:
            logger.info("\n=== Database Statistics ===")
            for name, query in queries:
                result = session.run(query)  # type: ignore
                record = result.single()
                if record is not None:
                    count = record['count']
                    logger.info(f"{name}: {count}")
                else:
                    logger.warning(f"{name}: No results returned")


def load_config_from_secrets():
    """Load configuration from Streamlit secrets.toml"""
    secrets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".streamlit", "secrets.toml")
    
    try:
        with open(secrets_path, 'r') as f:
            secrets = toml.load(f)
        
        neo4j_config = secrets.get('neo4j', {})
        return {
            'neo4j': {
                'uri': neo4j_config.get('uri', 'bolt://localhost:7687'),
                'user': neo4j_config.get('user', 'neo4j'),  # Using 'user' key for consistency
                'password': neo4j_config.get('password', 'password'),
                'database': neo4j_config.get('database', 'neo4j')
            },
            'csv_path': secrets.get('csv_path', 'combined_grants_small.csv')
        }
    except FileNotFoundError:
        logger.warning(f"Secrets file not found at {secrets_path}. Using environment variables or defaults.")
        return {
            'neo4j': {
                'uri': os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                'user': os.getenv("NEO4J_USER", "neo4j"),
                'password': os.getenv("NEO4J_PASSWORD", "password"),
                'database': os.getenv("NEO4J_DATABASE", "neo4j")
            },
            'csv_path': os.getenv("CSV_PATH", "combined_grants_small.csv")
        }
    except Exception as e:
        logger.error(f"Error reading secrets file: {e}. Using environment variables or defaults.")
        return {
            'neo4j': {
                'uri': os.getenv("NEO4J_URI", "bolt://localhost:7687"),
                'user': os.getenv("NEO4J_USER", "neo4j"),
                'password': os.getenv("NEO4J_PASSWORD", "password"),
                'database': os.getenv("NEO4J_DATABASE", "neo4j")
            },
            'csv_path': os.getenv("CSV_PATH", "combined_grants_small.csv")
        }


def main():
    """Main execution function"""
    # Load configuration from secrets.toml
    config = load_config_from_secrets()
    neo4j_config = config['neo4j']
    NEO4J_URI = neo4j_config['uri']
    NEO4J_USER = neo4j_config['user']
    NEO4J_PASSWORD = neo4j_config['password']
    CSV_PATH = config['csv_path']
    
    logger.info("Starting data ingestion process...")
    logger.info(f"Neo4j URI: {NEO4J_URI}")
    logger.info(f"Database: {neo4j_config['database']}")
    logger.info(f"CSV Path: {CSV_PATH}")
    
    ingestion = DataIngestion(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, neo4j_config['database'])
    
    try:
        # Step 1: Clear existing data (optional - comment out to preserve data)
        # ingestion.clear_database()
        
        # Step 2: Create constraints and indexes
        ingestion.create_constraints()
        ingestion.create_indexes()
        
        # Step 3: Ingest data
        ingestion.ingest_csv(CSV_PATH)
        
        # Step 4: Create vector index (optional)
        ingestion.create_vector_index()
        
        # Step 5: Verify
        ingestion.verify_ingestion()
        
        logger.info("\n✅ Data ingestion completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during ingestion: {str(e)}")
        raise
    finally:
        ingestion.close()


if __name__ == "__main__":
    main()
