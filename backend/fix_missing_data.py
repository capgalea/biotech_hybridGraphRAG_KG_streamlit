import pandas as pd
from app.utils.neo4j_handler import Neo4jHandler
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)

def fix_data():
    print("Reading CSV...")
    df = pd.read_csv('../data/grants.csv', low_memory=False, usecols=['Application_ID', 'Funding_Body', 'Field_of_Research', 'Grant_Type'])
    
    h = Neo4jHandler(
        uri=settings["neo4j"]["uri"],
        user=settings["neo4j"]["user"],
        password=settings["neo4j"]["password"],
        database=settings["neo4j"]["database"]
    )
    
    print("Updating missing fields in batches...")
    batch_size = 2000
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size].fillna("").to_dict('records')
        # Ensure Application_ID is string for matching
        for item in batch:
            item['Application_ID'] = str(item['Application_ID'])
            
        query = """
        UNWIND $batch as row
        MATCH (g:Grant {application_id: row.Application_ID})
        SET g.funding_body = row.Funding_Body,
            g.field_of_research = row.Field_of_Research,
            g.grant_type = row.Grant_Type
        """
        h.execute_cypher(query, {"batch": batch})
        if i % 10000 == 0:
            print(f"Processed {i} records...")
            
    print("DONE! All filters should now be populated.")

if __name__ == "__main__":
    fix_data()
