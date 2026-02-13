import os
import json
import hashlib
import time
import logging
from typing import Any, Callable, Dict, Optional
from app.config import settings

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(settings['data_dir'], ".cache")

def get_cache_key(name: str, **kwargs) -> str:
    """Generate a unique hash for a query/function and its arguments"""
    # Sort keys to ensure consistent hashing
    filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    arg_str = json.dumps(filtered_kwargs, sort_keys=True)
    return hashlib.md5(f"{name}:{arg_str}".encode()).hexdigest()

def get_cached_data(cache_key: str, data_version: str) -> Optional[Any]:
    """Retrieve data from disk cache if version matches"""
    if not os.path.exists(CACHE_DIR):
        return None
        
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    if not os.path.exists(cache_file):
        return None
        
    try:
        with open(cache_file, 'r') as f:
            cached = json.load(f)
            if cached.get("version") == data_version:
                logger.debug(f"Cache hit for {cache_key}")
                return cached.get("data")
    except Exception as e:
        logger.error(f"Error reading cache {cache_file}: {e}")
        
    return None

def set_cached_data(cache_key: str, data_version: str, data: Any):
    """Save data to disk cache with version"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR, exist_ok=True)
        
    cache_file = os.path.join(CACHE_DIR, f"{cache_key}.json")
    try:
        with open(cache_file, 'w') as f:
            json.dump({
                "version": data_version,
                "timestamp": time.time(),
                "data": data
            }, f)
        logger.debug(f"Cache saved for {cache_key}")
    except Exception as e:
        logger.error(f"Error writing cache {cache_file}: {e}")

def clear_cache():
    """Clear all cached files"""
    if os.path.exists(CACHE_DIR):
        import shutil
        shutil.rmtree(CACHE_DIR)
        os.makedirs(CACHE_DIR)
        logger.info("Cache cleared")
