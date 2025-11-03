"""
Configuration management for the GraphRAG system
"""

import os
from typing import Dict, Any
import streamlit as st


class Config:
    """Centralized configuration management"""
    
    # Neo4j Configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
    
    # Embedding Configuration
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384
    
    # LLM Models
    LLM_MODELS = {
        "Claude 3.5 Sonnet": {
            "provider": "anthropic",
            "model_id": "claude-3-5-sonnet-20241022",
            "max_tokens": 4096
        },
        "Claude 4.0 Sonnet": {
            "provider": "anthropic",
            "model_id": "claude-4-sonnet-20250514",
            "max_tokens": 4096
        },
        "Claude 4.5 Sonnet": {
            "provider": "anthropic",
            "model_id": "claude-sonnet-4-5-20250929",
            "max_tokens": 8192
        },
        "GPT-4o": {
            "provider": "openai",
            "model_id": "gpt-4o",
            "max_tokens": 4096
        },
        "Gemini 2.0 Flash": {
            "provider": "google",
            "model_id": "gemini-2.0-flash-exp",
            "max_tokens": 8192
        },
        "DeepSeek": {
            "provider": "deepseek",
            "model_id": "deepseek-chat",
            "max_tokens": 4096
        }
    }
    
    # Query Configuration
    DEFAULT_QUERY_LIMIT = 20
    MAX_QUERY_LIMIT = 100
    
    # Visualization Configuration
    VIZ_DEFAULT_NODES = 15
    VIZ_MAX_NODES = 50
    VIZ_COLORS = {
        "Grant": "#FF6B6B",
        "Researcher": "#4ECDC4",
        "Institution": "#95E1D3",
        "ResearchArea": "#FFD93D",
        "ResearchField": "#A8E6CF"
    }
    
    # Application Settings
    APP_TITLE = "GraphRAG Grant Explorer"
    APP_ICON = "🔍"
    PAGE_LAYOUT = "wide"
    
    @classmethod
    def get_neo4j_config(cls) -> Dict[str, str]:
        """Get Neo4j connection configuration"""
        try:
            return {
                "uri": st.secrets["neo4j"]["uri"],
                "user": st.secrets["neo4j"]["user"],
                "password": st.secrets["neo4j"]["password"]
            }
        except:
            return {
                "uri": cls.NEO4J_URI,
                "user": cls.NEO4J_USER,
                "password": cls.NEO4J_PASSWORD
            }
    
    @classmethod
    def get_llm_config(cls, model_name: str) -> Dict[str, Any]:
        """Get LLM configuration for a specific model"""
        return cls.LLM_MODELS.get(model_name, cls.LLM_MODELS["Claude 3.5 Sonnet"])
    
    @classmethod
    def get_api_key(cls, provider: str) -> str:
        """Get API key for a specific provider"""
        try:
            return st.secrets.get(provider, {}).get("api_key", "")
        except:
            return os.getenv(f"{provider.upper()}_API_KEY", "")
    
    @classmethod
    def validate_config(cls) -> Dict[str, bool]:
        """Validate configuration"""
        validation = {
            "neo4j": False,
            "anthropic": False,
            "openai": False,
            "google": False,
            "deepseek": False
        }
        
        try:
            # Check Neo4j
            neo4j_config = cls.get_neo4j_config()
            validation["neo4j"] = all([
                neo4j_config["uri"],
                neo4j_config["user"],
                neo4j_config["password"]
            ])
            
            # Check API keys
            for provider in ["anthropic", "openai", "google", "deepseek"]:
                api_key = cls.get_api_key(provider)
                validation[provider] = bool(api_key and len(api_key) > 10)
                
        except Exception as e:
            print(f"Configuration validation error: {str(e)}")
        
        return validation


# Cypher query templates
CYPHER_TEMPLATES = {
    "all_grants": """
        MATCH (g:Grant)
        RETURN g
        LIMIT $limit
    """,
    
    "grants_by_researcher": """
        MATCH (r:Researcher {name: $name})-[:PRINCIPAL_INVESTIGATOR]->(g:Grant)
        RETURN r, g
    """,
    
    "grants_by_institution": """
        MATCH (g:Grant)-[:HOSTED_BY]->(i:Institution)
        WHERE i.name CONTAINS $name
        RETURN g, i
    """,
    
    "grants_by_area": """
        MATCH (g:Grant)-[:IN_AREA]->(a:ResearchArea)
        WHERE a.name = $area
        RETURN g, a
    """,
    
    "grants_by_keyword": """
        MATCH (g:Grant)
        WHERE g.title CONTAINS $keyword 
           OR g.description CONTAINS $keyword
        RETURN g
        LIMIT $limit
    """,
    
    "high_value_grants": """
        MATCH (g:Grant)
        WHERE g.amount >= $min_amount
        RETURN g
        ORDER BY g.amount DESC
        LIMIT $limit
    """,
    
    "collaboration_network": """
        MATCH (r1:Researcher)-[:PRINCIPAL_INVESTIGATOR]->(g:Grant)
              <-[:PRINCIPAL_INVESTIGATOR]-(r2:Researcher)
        WHERE r1 <> r2
        RETURN r1, r2, g
        LIMIT $limit
    """,
    
    "institution_summary": """
        MATCH (g:Grant)-[:HOSTED_BY]->(i:Institution)
        RETURN i.name as institution,
               count(g) as grant_count,
               sum(g.amount) as total_funding,
               avg(g.amount) as avg_funding
        ORDER BY total_funding DESC
        LIMIT $limit
    """
}


# Example queries for user guidance
EXAMPLE_QUERIES = [
    {
        "category": "Search by Topic",
        "queries": [
            "Find grants related to cancer research",
            "Show me all grants about climate change",
            "Which grants focus on artificial intelligence?",
            "Find research on mental health"
        ]
    },
    {
        "category": "Search by Institution",
        "queries": [
            "What grants are at University of Melbourne?",
            "Show all grants at Monash University",
            "Which institutions have the most funding?"
        ]
    },
    {
        "category": "Search by Amount",
        "queries": [
            "Find grants with funding over $2 million",
            "What are the largest grants?",
            "Show grants between $500k and $1M"
        ]
    },
    {
        "category": "Search by Researcher",
        "queries": [
            "Find all grants by Dr Smith",
            "Which researchers work on neuroscience?",
            "Show me grants with multiple investigators"
        ]
    },
    {
        "category": "Time-based",
        "queries": [
            "What grants started in 2026?",
            "Show recent grants from the last year",
            "Find grants ending in 2030"
        ]
    }
]


# Application constants
class AppConstants:
    """Application-wide constants"""
    
    # Status messages
    MSG_PROCESSING = "Processing your query..."
    MSG_SUCCESS = "✅ Query completed successfully"
    MSG_ERROR = "❌ An error occurred"
    MSG_NO_RESULTS = "No results found"
    MSG_GENERATING_VIZ = "Creating visualization..."
    
    # Help text
    HELP_QUERY = """
    Enter a natural language question about research grants. Examples:
    - "Which grants focus on cancer research?"
    - "Show me all grants at University of Melbourne"
    - "Find grants with funding over $1 million"
    """
    
    HELP_CYPHER = """
    Write a Cypher query to explore the graph. Available node labels:
    - Grant, Researcher, Institution, ResearchArea, ResearchField
    
    Common patterns:
    - MATCH (g:Grant) WHERE g.amount > 1000000 RETURN g
    - MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR]->(g:Grant) RETURN r, g
    """
    
    # Color schemes
    COLOR_SCHEMES = {
        "default": ["#FF6B6B", "#4ECDC4", "#95E1D3", "#FFD93D", "#A8E6CF"],
        "blue": ["#0077B6", "#00B4D8", "#90E0EF", "#CAF0F8", "#ADE8F4"],
        "green": ["#2D6A4F", "#40916C", "#52B788", "#74C69D", "#95D5B2"],
        "purple": ["#5A189A", "#7209B7", "#9D4EDD", "#C77DFF", "#E0AAFF"]
    }


if __name__ == "__main__":
    # Test configuration
    print("Configuration Test")
    print("=" * 50)
    
    validation = Config.validate_config()
    print("\nConfiguration Status:")
    for key, value in validation.items():
        status = "✅" if value else "❌"
        print(f"{status} {key}: {value}")
    
    print("\nAvailable LLM Models:")
    for model_name in Config.LLM_MODELS.keys():
        print(f"  - {model_name}")
