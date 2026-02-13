import os
import pandas as pd
import logging
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
# Adjusted imports for the new structure
from app.retrieval_agent import scraper
from app.retrieval_agent import normalizer
# Import sibling module
try:
    from app.retrieval_agent import arc_retriever
except ImportError:
    arc_retriever = None

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_data(nhmrc=True, arc=True, save_files=True, progress_callback=None):
    load_dotenv()
    
    def report_progress(msg):
        if progress_callback:
            try:
                progress_callback(msg)
            except Exception:
                pass

    # Setup GenAI Model
    api_key = os.getenv("GOOGLE_API_KEY")
    client = None
    model_name = None
    
    if not api_key:
        logger.warning("GOOGLE_API_KEY not found in environment. Agent mapping features might fail.")
    
    if genai and api_key:
        try:
            client = genai.Client(api_key=api_key)
            model_name = 'gemini-2.0-flash' # Using standard accessible model name
        except Exception as e:
            logger.error(f"Failed to initialize GenAI client: {e}")
    else:
        logger.error("google.genai library not found or API key missing.")

    download_dir = "downloads"
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        
    nhmrc_dfs = []
    arc_dfs = []

    # 1. NHMRC Scrape & Process
    if nhmrc:
        report_progress("Scraping NHMRC website for data files...")
        logger.info("Starting NHMRC Data Retrieval...")
        url = "https://www.nhmrc.gov.au/funding/data-research/outcomes"
        links = scraper.get_excel_links(url)
        
        if not links:
            logger.warning("No NHMRC Excel links found.")
            report_progress("No NHMRC links found.")
        else:
            total_links = len(links)
            report_progress(f"Found {total_links} NHMRC files. Downloading and processing...")
            
            # Process links concurrently to improve speed
            max_workers = 5
            report_progress(f"Found {total_links} NHMRC files. Downloading and processing with {max_workers} threads...")
            
            def process_link(link):
                try:
                    filepath = scraper.download_file(link, download_dir)
                    if filepath:
                        # Read file intelligently
                        df = normalizer.smart_load_excel(filepath)
                        
                        # Clean headers
                        df.columns = df.columns.astype(str).str.strip()
                        
                        # Get headers
                        headers = df.columns.tolist()
                        
                        # Get mapping
                        mapping = normalizer.get_mapping_fast(client, model_name, headers)
                        
                        # Normalize
                        df_norm = normalizer.normalize_dataframe(df, mapping, os.path.basename(filepath))
                        
                        if df_norm is not None and not df_norm.empty:
                            return df_norm
                except Exception as e:
                    logger.error(f"Failed to process {link}: {e}")
                return None

            completed_count = 0
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_link = {executor.submit(process_link, link): link for link in links}
                
                for future in as_completed(future_to_link):
                    completed_count += 1
                    report_progress(f"Processing NHMRC file {completed_count}/{total_links}...")
                    
                    try:
                        result = future.result()
                        if result is not None:
                            nhmrc_dfs.append(result)
                            logger.info(f"Processed NHMRC file successfully ({len(result)} rows)")
                    except Exception as e:
                        logger.error(f"Error processing future result: {e}")

    # 2. ARC Data Retrieval
    if arc and arc_retriever:
        report_progress("Fetching ARC grants from API...")
        logger.info("Starting ARC Data Retrieval...")
        try:
            # Pass limit_pages=5 for testing if needed, but we'll fetch all by default or let user configure
            # For now, let's limit to 10 pages (~10k records) to avoid huge delays during initial testing
            # UNLESS this is a full run. Let's do full run but be aware it takes time.
            # Actually, let's limit to 20 pages for responsiveness in this demo context.
            # You can remove limit_pages=20 for production.
            arc_df = arc_retriever.fetch_all_grants_concurrent(limit_pages=20, save_csv=False) 
            if not arc_df.empty:
                arc_headers = arc_df.columns.tolist()
                arc_mapping = normalizer.get_mapping_fast(client, model_name, arc_headers)
                arc_df_norm = normalizer.normalize_dataframe(arc_df, arc_mapping, "ARC_API_Data")
                arc_dfs.append(arc_df_norm)
                logger.info(f"Added {len(arc_df_norm)} ARC grants.")
            else:
                logger.warning("No ARC grants fetched.")
        except Exception as e:
            logger.error(f"Failed to fetch ARC grants: {e}")
            report_progress(f"Error fetching ARC data: {e}")
    elif arc:
         logger.warning("arc_retriever module not found, skipping ARC data.")

    # 3. Aggregate
    report_progress("Aggregating and saving data...")
    all_dfs = nhmrc_dfs + arc_dfs
    
    final_df = pd.DataFrame()

    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        
        # Quality Filter
        missing_mask = final_df.isnull() | (final_df == '')
        missing_pct = missing_mask.sum(axis=1) / len(final_df.columns)
        rows_to_keep = missing_pct <= 0.80
        rows_removed = (~rows_to_keep).sum()
        final_df = final_df[rows_to_keep].reset_index(drop=True)
        
        logger.info(f"Total rows: {len(final_df)} (Removed {rows_removed} low quality rows)")

        if save_files:
            try:
                # Helper for atomic saving
                def atomic_save_df(df, filename):
                    import tempfile
                    temp_fd, temp_path = tempfile.mkstemp(suffix=".csv", dir=".")
                    os.close(temp_fd)
                    df.to_csv(temp_path, index=False)
                    if os.path.exists(filename):
                        bak = filename + ".bak"
                        if os.path.exists(bak): os.remove(bak)
                        os.rename(filename, bak)
                    os.rename(temp_path, filename)

                atomic_save_df(final_df, "outcomes.csv")
                logger.info("Saved outcomes.csv")
                
                # Save individual files for separate display
                if nhmrc_dfs:
                     atomic_save_df(pd.concat(nhmrc_dfs, ignore_index=True), "nhmrc_processed.csv")
                     logger.info("Saved nhmrc_processed.csv")
                
                if arc_dfs:
                     atomic_save_df(pd.concat(arc_dfs, ignore_index=True), "arc_processed.csv")
                     logger.info("Saved arc_processed.csv")

            except Exception as e:
                logger.error(f"Failed to save CSV files: {e}")
                
    report_progress("Retrieval complete.")

    return {
        "combined": final_df,
        "nhmrc": pd.concat(nhmrc_dfs, ignore_index=True) if nhmrc_dfs else pd.DataFrame(),
        "arc": pd.concat(arc_dfs, ignore_index=True) if arc_dfs else pd.DataFrame()
    }
