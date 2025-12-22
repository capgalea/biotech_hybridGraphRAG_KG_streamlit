import pandas as pd
df = pd.read_csv('data/grants.csv')
print(f"Row 15000: {df.iloc[14999][['Application_ID', 'Funding_Body']].to_dict()}")
