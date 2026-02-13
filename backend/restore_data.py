import os
import pandas as pd
import logging
from dotenv import load_dotenv
from app.retrieval_agent import normalizer
try:
    from google import genai
except ImportError:
    genai = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def restore_data():
    load_dotenv()
    
    # Setup GenAI Model
    api_key = os.getenv("GOOGLE_API_KEY")
    client = None
    model_name = None
    
    if genai and api_key:
        try:
            client = genai.Client(api_key=api_key)
            model_name = 'gemini-2.0-flash'
        except Exception as e:
            logger.error(f"Failed to initialize GenAI client: {e}")
    
    download_dir = "downloads"
    if not os.path.exists(download_dir):
        logger.error(f"Download directory '{download_dir}' does not exist.")
        return

    nhmrc_dfs = []
    
    files = [f for f in os.listdir(download_dir) if f.endswith('.xlsx')]
    logger.info(f"Found {len(files)} XLSX files in {download_dir}")
    
    for filename in files:
        filepath = os.path.join(download_dir, filename)
        try:
            logger.info(f"Processing {filename}...")
            # Read file intelligently
            df = normalizer.smart_load_excel(filepath)
            
            # Get headers
            headers = df.columns.tolist()
            
            # Get mapping
            mapping = normalizer.get_mapping_fast(client, model_name, headers)
            
            # Normalize
            df_norm = normalizer.normalize_dataframe(df, mapping, filename)
            
            if df_norm is not None and not df_norm.empty:
                nhmrc_dfs.append(df_norm)
                logger.info(f"Processed {filename}: {len(df_norm)} rows")
        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}")

    if nhmrc_dfs:
        nhmrc_df = pd.concat(nhmrc_dfs, ignore_index=True)
        nhmrc_df.to_csv("nhmrc_processed.csv", index=False)
        logger.info(f"Saved nhmrc_processed.csv with {len(nhmrc_df)} rows")
        
        # Also save outcomes.csv (initially just NHMRC)
        # Check if ARC exists
        arc_df = pd.DataFrame()
        if os.path.exists("arc_processed.csv"):
            arc_df = pd.read_csv("arc_processed.csv")
            logger.info(f"Found existing arc_processed.csv with {len(arc_df)} rows")
            
        combined_df = pd.concat([nhmrc_df, arc_df], ignore_index=True)
        
        # Quality Filter
        # missing_mask = combined_df.isnull() | (combined_df == '')
        # missing_pct = missing_mask.sum(axis=1) / len(combined_df.columns)
        # rows_to_keep = missing_pct <= 0.80
        # combined_df = combined_df[rows_to_keep].reset_index(drop=True)
        
        combined_df.to_csv("outcomes.csv", index=False)
        logger.info(f"Saved outcomes.csv with {len(combined_df)} rows")
    else:
        logger.warning("No NHMRC data processed.")

if __name__ == "__main__":
    restore_data()
