import pandas as pd
df = pd.read_csv('data/grants.csv')
print("Unique funding bodies in CSV:")
print(df['Funding_Body'].unique())
print("\nCounts:")
print(df['Funding_Body'].value_counts())
