import requests
import json
import logging
import pandas as pd
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://dataportal.arc.gov.au/NCGP/API/grants"
PAGE_SIZE = 1000 # Max allowed by API
OUTPUT_FILE = "arc_grants.csv"
MAX_WORKERS = 10

def fetch_page(page_number):
    """Fetches a single page of results."""
    params = {
        "page[number]": page_number,
        "page[size]": PAGE_SIZE
    }
    # Increase timeout for large pages
    response = requests.get(BASE_URL, params=params, timeout=60)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch page {page_number}: Status {response.status_code}")
        
    data = response.json()
    grant_list = data.get('data', [])
    return grant_list

def fetch_all_grants_concurrent(limit_pages=None, save_csv=True):
    """Fetches all grants from the ARC Data Portal API concurrently and optionally saves to CSV."""
    
    logger.info("Starting Concurrent ARC Grant Retrieval...")
    
    # 1. Get Metadata for total pages
    try:
        params = {"page[number]": 1, "page[size]": PAGE_SIZE}
        resp = requests.get(BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        meta = data.get('meta', {})
        total_records = meta.get('total-size', 0)
        total_pages = meta.get('total-pages', 0)
        
        logger.info(f"Total records: {total_records}")
        logger.info(f"Total pages (size {PAGE_SIZE}): {total_pages}")
        
    except Exception as e:
        logger.error(f"Failed to connect to API: {e}")
        raise # Raise to let caller know it failed

    if total_pages == 0:
        logger.warning("No pages to fetch.")
        return pd.DataFrame()

    # 2. Generate Page Numbers
    if limit_pages:
        total_pages = min(total_pages, limit_pages)
        logger.info(f"Limiting to first {total_pages} pages.")
        
    page_numbers = range(1, total_pages + 1)
    all_grants = []
    
    # 3. Fetch in Parallel
    logger.info(f"Fetching {total_pages} pages with {MAX_WORKERS} threads...")
    
    failed_pages = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_page = {executor.submit(fetch_page, page): page for page in page_numbers}
        
        completed_count = 0
        for future in as_completed(future_to_page):
            page_num = future_to_page[future]
            try:
                grant_list = future.result()
                
                for item in grant_list:
                    # Flatten structure: 'id', 'type' + 'attributes' content
                    grant_obj = {
                        'id': item.get('id'),
                        'type': item.get('type'),
                        'Funding_Body': 'ARC'  # Requested fixed column
                    }
                    
                    # Add attributes
                    attributes = item.get('attributes', {})
                    for key, value in attributes.items():
                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                grant_obj[f"{key}_{sub_key}"] = sub_value
                        elif isinstance(value, list):
                             grant_obj[key] = str(value)
                        else:
                            grant_obj[key] = value
                    
                    all_grants.append(grant_obj)
            except Exception as e:
                logger.error(f"Error on page {page_num}: {e}")
                failed_pages.append(page_num)
            
            completed_count += 1
            if completed_count % 5 == 0:
                logger.info(f"Progress: {completed_count}/{total_pages} pages processed.")

    if failed_pages:
        logger.error(f"Failed to fetch {len(failed_pages)} pages: {failed_pages}")
        # If more than 10% of pages failed, or any page failed and we want strictness
        if len(failed_pages) > total_pages * 0.1:
            raise Exception(f"Too many failed pages ({len(failed_pages)}/{total_pages}). Retrieval aborted to protect data integrity.")

    # 4. Save to CSV
    if all_grants:
        logger.info(f"Fetched {len(all_grants)} grants.")
        df = pd.DataFrame(all_grants)
        
        # Sort by ID to keep order somewhat consistent
        if 'code' in df.columns:
             df.sort_values('code', inplace=True)
             
        if save_csv:
            try:
                # Atomic save: write to temp then rename
                import tempfile
                temp_fd, temp_path = tempfile.mkstemp(suffix=".csv", dir=".")
                os.close(temp_fd)
                
                logger.info(f"Saving to temporary file {temp_path}...")
                df.to_csv(temp_path, index=False)
                
                if os.path.exists(OUTPUT_FILE):
                    bak_file = OUTPUT_FILE + ".bak"
                    if os.path.exists(bak_file):
                        os.remove(bak_file)
                    os.rename(OUTPUT_FILE, bak_file)
                
                os.rename(temp_path, OUTPUT_FILE)
                logger.info(f"Success! Saved to {os.path.abspath(OUTPUT_FILE)}")
            except Exception as e:
                logger.error(f"Failed to save CSV: {e}")
                raise
        
        return df
    else:
        logger.warning("No grants were fetched.")
        return pd.DataFrame()


if __name__ == "__main__":
    fetch_all_grants_concurrent()
