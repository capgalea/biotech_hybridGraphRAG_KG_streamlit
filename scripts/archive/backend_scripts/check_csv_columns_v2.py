
import pandas as pd
import sys

def check_csv(filename):
    print(f"Checking {filename}...")
    try:
        df = pd.read_csv(filename)
        print(f"Columns: {list(df.columns)}")
        print(f"Shape: {df.shape}")
        
        expected = [
            'CIA_Name', 'Grant_Title', 'Grant_Type', 'Total_Amount', 
            'Broad_Research_Area', 'Field_of_Research', 'Plain_Description', 
            'Admin_Institution', 'Grant_Start_Year', 'Grant_End_Date', 
            'CIA_ORCID_ID', 'Funding_Body', 'Source_File', 'Grant_Status', 
            'Investigators'
        ]
        
        missing = [col for col in expected if col not in df.columns]
        if missing:
            print(f"MISSING COLUMNS: {missing}")
        else:
            print("All expected columns present.")
            
        # Print first row
        if not df.empty:
            print("First row:")
            print(df.iloc[0])
            
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    print("-" * 30)

check_csv('backend/nhmrc_processed.csv')
check_csv('backend/arc_processed.csv')
