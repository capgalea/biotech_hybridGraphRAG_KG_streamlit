import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
import logging

logger = logging.getLogger(__name__)

def get_excel_links(page_url: str) -> list[str]:
    """
    Scrapes the given URL for links ending in .xlsx.
    """
    logger.info(f"Scraping {page_url} for Excel links...")
    try:
        response = requests.get(page_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.lower().endswith('.xlsx'):
                full_url = urljoin(page_url, href)
                links.append(full_url)
        
        # Deduplicate while preserving order
        unique_links = list(dict.fromkeys(links))
        logger.info(f"Found {len(unique_links)} Excel links.")
        return unique_links
        
    except Exception as e:
        logger.error(f"Error scraping {page_url}: {e}")
        return []

def download_file(url: str, download_folder: str) -> str | None:
    """
    Downloads a file from the URL to the specified folder.
    Returns the path to the downloaded file, or None if failed.
    """
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
        
    filename = unquote(os.path.basename(url))
    filepath = os.path.join(download_folder, filename)
    
    logger.info(f"Downloading {url} to {filepath}...")
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        import tempfile
        # Create temp file in the same directory
        temp_fd, temp_path = tempfile.mkstemp(suffix=".xlsx", dir=download_folder)
        try:
            with os.fdopen(temp_fd, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Atomic rename
            if os.path.exists(filepath):
                os.remove(filepath)
            os.rename(temp_path, filepath)
            logger.info(f"Downloaded {filename}")
            return filepath
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
            
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        return None

