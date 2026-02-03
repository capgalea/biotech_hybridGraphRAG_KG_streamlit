import pandas as pd
from app.utils.neo4j_handler import Neo4jHandler
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)

def migrate():
    print("Reading CSV for full migration...")
    cols = ['Application_ID', 'Grant_Title', 'Grant_Status', 'Total_Amount', 
            'Grant_Start_Year', 'Grant_Type', 'Funding_Body', 
            'Broad_Research_Area', 'Field_of_Research']
    df = pd.read_csv('../data/grants.csv', low_memory=False, usecols=cols)
    
    h = Neo4jHandler(
        uri=settings["neo4j"]["uri"],
        user=settings["neo4j"]["user"],
        password=settings["neo4j"]["password"],
        database=settings["neo4j"]["database"]
    )
    
    print("Migrating nodes with correct properties...")
    batch_size = 2000
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size].fillna("").to_dict('records')
        for item in batch:
            item['Application_ID'] = str(item['Application_ID'])
            try:
                item['Amount'] = float(item['Total_Amount'])
            except:
                item['Amount'] = 0.0
            try:
                item['Start_Year'] = int(item['Grant_Start_Year'])
            except:
                item['Start_Year'] = None
                
        query = """
        UNWIND $batch as row
        MERGE (g:Grant {application_id: row.Application_ID})
        SET g.title = row.Grant_Title,
            g.grant_status = row.Grant_Status,
            g.amount = row.Amount,
            g.start_year = row.Start_Year,
            g.grant_type = row.Grant_Type,
            g.funding_body = row.Funding_Body,
            g.broad_research_area = row.Broad_Research_Area,
            g.field_of_research = row.Field_of_Research
        """
        h.execute_cypher(query, {"batch": batch})
        if i % 10000 == 0:
            print(f"Processed {i} grants...")

    print("Ensuring ResearchArea nodes exist...")
    h.execute_cypher("""
    MATCH (g:Grant) 
    WHERE g.broad_research_area IS NOT NULL AND g.broad_research_area <> ''
    MERGE (a:ResearchArea {name: g.broad_research_area})
    MERGE (g)-[:IN_AREA]->(a)
    """)
    
    print("DONE! Database is now in sync.")

if __name__ == "__main__":
    migrate()
