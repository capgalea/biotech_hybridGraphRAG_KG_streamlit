
import pandas as pd
import os

files = ["outcomes.csv", "nhmrc_processed.csv", "arc_processed.csv"]
for f in files:
    if os.path.exists(f):
        df = pd.read_csv(f, nrows=5)
        print(f"File: {f}")
        print(f"Columns: {df.columns.tolist()}")
        print("-" * 20)
    else:
        print(f"File {f} not found")
