
import sys
import os
import pandas as pd
from app.retrieval_agent import normalizer

print("Testing single file normalization...")
filepath = "downloads/Summary-of-result-2024-app-round-100725.xlsx"

if not os.path.exists(filepath):
    print("File not found")
    sys.exit(1)

df = normalizer.smart_load_excel(filepath)
headers = df.columns.tolist()

# Simulate client=None which caused the bug
mapping = normalizer.get_mapping_fast(None, "gemini-2.0-flash", headers)
print(f"Mapping returned: {len(mapping)} keys")

if not mapping:
    print("FAILURE: Mapping is empty!")
else:
    print("SUCCESS: Mapping is not empty.")
    print(mapping)
    
    # Check if critical headers are mapped
    if 'Application_ID' in mapping.values():
         print("SUCCESS: Application_ID mapped.")
    else:
         print("FAILURE: Application_ID NOT mapped.")

    normalized_df = normalizer.normalize_dataframe(df, mapping, "test_file.xlsx")
    print(normalized_df.head())
    
    # Check first row
    first_row = normalized_df.iloc[0]
    if first_row['Application_ID']:
        print("SUCCESS: Data populated correctly.")
    else:
        print("FAILURE: Data is empty.")
