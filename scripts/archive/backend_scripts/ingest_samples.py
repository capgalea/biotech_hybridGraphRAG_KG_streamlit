import pandas as pd
from app.utils.neo4j_handler import Neo4jHandler
from app.config import settings

def ingest_samples():
    h = Neo4jHandler(
        uri=settings["neo4j"]["uri"],
        user=settings["neo4j"]["user"],
        password=settings["neo4j"]["password"],
        database=settings["neo4j"]["database"]
    )
    
    df = pd.read_csv('data/grants.csv')
    
    # Get first few ARC and CTCS records
    arc_samples = df[df['Funding_Body'] == 'ARC'].head(50)
    ctcs_samples = df[df['Funding_Body'] == 'CTCS'].head(50)
    
    samples = pd.concat([arc_samples, ctcs_samples])
    print(f"Ingesting {len(samples)} samples...")
    
    for _, row in samples.iterrows():
        cypher = """
        MERGE (g:Grant {application_id: $application_id})
        SET g.funding_body = $funding_body,
            g.title = $title
        """
        h.execute_cypher(cypher, {
            'application_id': str(row['Application_ID']),
            'funding_body': str(row['Funding_Body']),
            'title': str(row['Grant_Title'])
        })
    
    print("Samples ingested.")

if __name__ == "__main__":
    ingest_samples()
