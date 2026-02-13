
import pandas as pd
import numpy as np

def test_strip_behavior():
    df = pd.DataFrame({
        'A': [1, 2, 3],
        'B': [' x ', 'y', 'z '],
        'C': [1.1, 2.2, np.nan]
    })
    
    print("Original types:")
    print(df.dtypes)
    
    # Simulate the logic
    df = df.fillna("")
    if df.isna().any().any(): # Won't be true after fillna("") usually, unless logic is weird
        pass # But let's force the astype(object) like the code does if it finds NaNs BEFORE fillna? 
        # Wait, code is: df = df.fillna(""); if df.isna().any().any(): ...
        # fillna("") should remove all NaNs. So df.isna().any().any() should be False!
    
    # Let's force it to see what happens if we execute the block
    df = df.astype(object)
    print("\nAfter astype(object):")
    print(df)
    print(df.dtypes)
    
    try:
        df_obj = df.select_dtypes(['object'])
        print(f"\nObject columns selected: {list(df_obj.columns)}")
        # Apply .str.strip()
        df[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())
        print("\nAfter strip:")
        print(df)
    except Exception as e:
        print(f"\nError: {e}")

test_strip_behavior()
