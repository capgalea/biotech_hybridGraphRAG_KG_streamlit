
import pandas as pd
import sys

def load_df_cached(filename: str) -> pd.DataFrame:
    print(f"Loading {filename}...")
    try:
        # Replicating retrieval.py logic
        df = pd.read_csv(filename).fillna("")
        
        # Strip whitespace from all string columns
        df_obj = df.select_dtypes(['object'])
        df[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())
        
        print(f"Loaded {len(df)} rows.")
        print(df.dtypes)
        # Check for NaN again just in case
        if df.isna().any().any():
            print("WARNING: NaNs found!")
            print(df.isna().sum())
        else:
            print("No NaNs.")
            
        return df
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

# Test both
load_df_cached("backend/nhmrc_processed.csv")
load_df_cached("backend/arc_processed.csv")
