
import pandas as pd
import os

filename = "downloads/Summary-of-result-2024-app-round-100725.xlsx"
if not os.path.exists(filename):
    print(f"File {filename} not found")
else:
    xls = pd.ExcelFile(filename)
    print("Sheet names:", xls.sheet_names)
    
    # Try logic from smart_load_excel_single_sheet
    sheet_name = xls.sheet_names[0]
    priority_sheets = ['GRANTS DATA', 'Grants Data', 'Data']
    for name in priority_sheets:
        if name in xls.sheet_names:
            sheet_name = name
            break
            
    print(f"Reading sheet: {sheet_name}")
    df = pd.read_excel(xls, sheet_name=sheet_name)
    print("Headers:", df.columns.tolist())
    
    # Check detect_format logic
    headers_set = set(df.columns.tolist())
    print("Columns in headers_set:", headers_set)
    
    if 'Application ID' in headers_set and 'Chief Investigator A (Project Lead)' in headers_set:
        print("Detected format: multi_sheet_2020_plus")
    elif 'CIA_NAME' in headers_set and 'GRANT_TYPE' in headers_set:
        print("Detected format: legacy_2014")
    elif ('APP ID' in headers_set or 'App ID' in headers_set) and ('CIA Name' in headers_set or 'CIA_Name' in headers_set):
        print("Detected format: legacy_standard")
    else:
        print("Detected format: unknown")

