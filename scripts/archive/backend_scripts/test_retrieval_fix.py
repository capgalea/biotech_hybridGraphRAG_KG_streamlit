
import sys
import os
import pandas as pd

# Add current dir to path
sys.path.append(os.getcwd())

from app.retrieval_agent.agent import fetch_data

print("Testing fetch_data (NHMRC only)...")
# We don't save files to avoid overwriting production data unless needed, 
# but fetch_data saves anyway if save_files=True. Let's set it to False.
# However, fetch_data logic for nhmrc might rely on downloads existing.
# scraper.download_file uses cache if exists.

try:
    result = fetch_data(nhmrc=True, arc=False, save_files=False)
    df_nhmrc = result.get('nhmrc', pd.DataFrame())
    
    print(f"Result len: {len(df_nhmrc)}")
    if not df_nhmrc.empty:
        print("Columns:", df_nhmrc.columns.tolist())
        # Check first row for actual data
        print("First row sample:")
        print(df_nhmrc.iloc[0].to_dict())
        
        # Check specific columns that were empty before
        sample_app_id = df_nhmrc.iloc[0].get('Application_ID', '')
        if sample_app_id:
            print(f"SUCCESS: Application_ID populated: {sample_app_id}")
        else:
            print("FAILURE: Application_ID still empty")
    else:
        print("FAILURE: DataFrame returned empty")

except Exception as e:
    print(f"Error during test: {e}")
