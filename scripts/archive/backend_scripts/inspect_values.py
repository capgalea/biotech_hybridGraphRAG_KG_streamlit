
import pandas as pd
import os

if os.path.exists("outcomes.csv"):
    df = pd.read_csv("outcomes.csv")
    print("Unique Grant Types in outcomes.csv:")
    print(df['Grant_Type'].unique())
    
    print("\nUnique Funding Bodies:")
    print(df['Funding_Body'].unique())
else:
    print("outcomes.csv not found")
