import anthropic
import openai
import google.generativeai as genai
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMHandler:
    """Handler for multiple LLM providers"""
    
    def __init__(self, model_name: str, secrets: Dict):
        """Initialize LLM handler with selected model"""
        self.model_name = model_name
        self.secrets = secrets
        self._init_client()
    
    def _init_client(self):
        """Initialize the appropriate client based on model"""
        if "Claude" in self.model_name:
            self.provider = "anthropic"
            self.client = anthropic.Anthropic(
                api_key=self.secrets.get("anthropic", {}).get("api_key")
            )
            # Map model names
            if "3.5" in self.model_name:
                self.model_id = "claude-3-5-sonnet-20241022"
            elif "4.5" in self.model_name:
                self.model_id = "claude-sonnet-4-5-20250929"
            elif "4.0" in self.model_name:
                self.model_id = "claude-4-sonnet-20250514"
            else:
                self.model_id = "claude-3-5-sonnet-20241022"
                
        elif "GPT" in self.model_name:
            self.provider = "openai"
            openai.api_key = self.secrets.get("openai", {}).get("api_key")
            self.client = openai
            self.model_id = "gpt-4o"
            
        elif "Gemini" in self.model_name:
            self.provider = "google"
            genai.configure(api_key=self.secrets.get("google", {}).get("api_key"))
            self.model_id = "gemini-2.0-flash-exp"
            self.client = genai.GenerativeModel(self.model_id)
            
        elif "DeepSeek" in self.model_name:
            self.provider = "deepseek"
            self.client = openai.OpenAI(
                api_key=self.secrets.get("deepseek", {}).get("api_key"),
                base_url="https://api.deepseek.com"
            )
            self.model_id = "deepseek-chat"
    
    def generate_cypher(self, natural_query: str, schema_text: str) -> str:
        """
        Generate Cypher query from natural language using LLM
        """
        prompt = f"""You are a Neo4j Cypher query expert. Convert the natural language query into a valid Cypher query.

Database Schema:
{schema_text}

Natural Language Query: {natural_query}

Important Instructions:
1. Return ONLY the Cypher query, no explanations
2. Use proper Cypher syntax
3. Use LIMIT clauses appropriately (default to 20 if not specified)
4. Match node labels and relationship types from the schema
5. Use WHERE clauses for filtering
6. Return relevant properties

Example queries:
- For "grants about cancer": MATCH (g:Grant) WHERE g.title CONTAINS 'cancer' OR g.description CONTAINS 'cancer' RETURN g LIMIT 20
- For "researchers at University of Melbourne": MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR]->(g:Grant)-[:HOSTED_BY]->(i:Institution) WHERE i.name CONTAINS 'Melbourne' RETURN r, g, i LIMIT 20

Cypher Query:"""

        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model_id,
                    max_tokens=1024,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                cypher = response.content[0].text.strip()
                
            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    max_tokens=1024
                )
                cypher = response.choices[0].message.content.strip()
                
            elif self.provider == "google":
                response = self.client.generate_content(prompt)
                cypher = response.text.strip()
                
            elif self.provider == "deepseek":
                response = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    max_tokens=1024
                )
                cypher = response.choices[0].message.content.strip()
            
            # Clean up the response
            cypher = cypher.replace("```cypher", "").replace("```", "").strip()
            
            logger.info(f"Generated Cypher: {cypher}")
            return cypher
            
        except Exception as e:
            logger.error(f"Error generating Cypher: {str(e)}")
            raise
    
    def generate_summary(self, query: str, results: list) -> str:
        """
        Generate a natural language summary of the query results
        """
        results_text = str(results[:5])  # Limit for context
        
        prompt = f"""Summarize the following database query results in a clear, concise manner.

Original Query: {query}

Query Results: {results_text}

Provide a brief summary (2-3 sentences) highlighting:
1. Number of results found
2. Key findings or patterns
3. Notable insights

Summary:"""

        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model_id,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()
                
            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500
                )
                return response.choices[0].message.content.strip()
                
            elif self.provider == "google":
                response = self.client.generate_content(prompt)
                return response.text.strip()
                
            elif self.provider == "deepseek":
                response = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500
                )
                return response.choices[0].message.content.strip()
                
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return "Unable to generate summary."
    
    def extract_insights(self, results: list) -> list:
        """
        Extract key insights from results
        """
        if not results:
            return ["No results found"]
        
        insights = []
        
        # Count-based insights
        insights.append(f"Found {len(results)} matching records")
        
        # Try to extract grant amounts if present
        amounts = []
        for result in results:
            if isinstance(result, dict):
                for value in result.values():
                    if isinstance(value, dict) and 'amount' in value:
                        amounts.append(value['amount'])
        
        if amounts:
            total = sum(amounts)
            avg = total / len(amounts)
            insights.append(f"Total funding: ${total:,.0f}")
            insights.append(f"Average grant size: ${avg:,.0f}")
        
        # Research areas if present
        areas = set()
        for result in results:
            if isinstance(result, dict):
                for value in result.values():
                    if isinstance(value, dict) and 'research_area' in value:
                        areas.add(value['research_area'])
        
        if areas:
            insights.append(f"Research areas: {', '.join(list(areas)[:3])}")
        
        return insights
