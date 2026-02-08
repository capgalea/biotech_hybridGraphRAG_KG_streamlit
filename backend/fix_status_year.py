import pandas as pd
from app.utils.neo4j_handler import Neo4jHandler
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)

def migrate():
    print("Reading CSV...")
    cols = ['Application_ID', 'Grant_Title', 'Grant_Status', 'Total_Amount', 
            'Grant_Start_Year']
    df = pd.read_csv('../data/grants.csv', low_memory=False, usecols=cols)
    
    h = Neo4jHandler(
        uri=settings["neo4j"]["uri"],
        user=settings["neo4j"]["user"],
        password=settings["neo4j"]["password"],
        database=settings["neo4j"]["database"]
    )
    
    print("Updating specific fields...")
    batch_size = 5000
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size].to_dict('records')
        # Clean data for Neo4j
        for item in batch:
            item['app_id'] = str(item['Application_ID'])
            item['status'] = str(item['Grant_Status']) if pd.notna(item['Grant_Status']) else "Unknown"
            try:
                item['year'] = int(item['Grant_Start_Year']) if pd.notna(item['Grant_Start_Year']) else None
            except:
                item['year'] = None
                
        query = """
        UNWIND $batch as row
        MATCH (g:Grant {application_id: row.app_id})
        SET g.grant_status = row.status,
            g.start_year = row.year
        """
        h.execute_cypher(query, {"batch": batch})
        if i % 10000 == 0:
            print(f"Processed {i}...")

    print("DONE!")

if __name__ == "__main__":
    migrate()
