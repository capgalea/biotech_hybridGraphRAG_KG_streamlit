import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Resolve project root and load .env from there (works when running from backend/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DOTENV_PATH = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(dotenv_path=DOTENV_PATH)

class Settings(BaseSettings):
    # Neo4j
    NEO4J_URI: str = ""
    NEO4J_USER: str = ""
    NEO4J_PASSWORD: str = ""
    NEO4J_DATABASE: str = "neo4j"
    
    # LLMs
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    GOOGLE_SEARCH_API_KEY: str = ""
    GOOGLE_CSE_ID: str = ""
    DEEPSEEK_API_KEY: str = ""
    
    # Data
    CSV_PATH: str = ""
    
    # Embeddings
    EMBEDDINGS_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDINGS_DIMENSION: int = 384

    class Config:
        # Point directly to the root .env so uvicorn started from backend/ still loads it
        env_file = DOTENV_PATH
        extra = "ignore"

# Instantiate settings
_settings = Settings()

# Export as dictionary to maintain compatibility with existing code structure
settings = {
    "neo4j": {
        "uri": _settings.NEO4J_URI,
        "user": _settings.NEO4J_USER,
        "password": _settings.NEO4J_PASSWORD,
        "database": _settings.NEO4J_DATABASE,
    },
    "openai": {
        "api_key": _settings.OPENAI_API_KEY
    },
    "anthropic": {
        "api_key": _settings.ANTHROPIC_API_KEY
    },
    "google": {
        "api_key": _settings.GOOGLE_API_KEY,
        "search_api_key": _settings.GOOGLE_SEARCH_API_KEY,
        "cse_id": _settings.GOOGLE_CSE_ID
    },
    "deepseek": {
        "api_key": _settings.DEEPSEEK_API_KEY
    },
    "embeddings": {
        "model": _settings.EMBEDDINGS_MODEL,
        "dimension": _settings.EMBEDDINGS_DIMENSION
    },
    "csv_path": _settings.CSV_PATH
}

# Reconstruct secrets dict for compatibility with LLMHandler
secrets = {
    "neo4j": settings["neo4j"],
    "openai": settings["openai"],
    "anthropic": settings["anthropic"],
    "google": settings["google"],
    "deepseek": settings["deepseek"],
    "serpapi": {"api_key": ""} # Placeholder if needed
}
