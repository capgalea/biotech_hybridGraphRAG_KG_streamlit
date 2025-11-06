import anthropic
import openai
import google.generativeai as genai
from typing import Dict, Any, List
import logging
import requests
import json
from urllib.parse import quote

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_format_amount(amount):
    """Safely format amount as currency, handling string/int/float/None values"""
    if amount is None:
        return "N/A"
    try:
        # Convert to float first, then format
        if isinstance(amount, str):
            # Remove any existing currency symbols and commas
            amount_clean = amount.replace('$', '').replace(',', '').strip()
            if amount_clean == '' or amount_clean.lower() == 'n/a':
                return "N/A"
            amount_float = float(amount_clean)
        else:
            amount_float = float(amount)
        return f"${amount_float:,.0f}"
    except (ValueError, TypeError):
        return "N/A"


class LLMHandler:
    """Handler for multiple LLM providers"""
    
    def __init__(self, model_name: str, secrets: Dict):
        """Initialize LLM handler with selected model"""
        self.model_name = model_name
        self.secrets = secrets
        self.provider = "openai"  # Default to openai (Anthropic has API issues)
        self.client = None
        self.model_id = "claude-3-5-sonnet-20240620" 
        self._init_client()
    
    def _init_client(self):
        """Initialize the appropriate client based on model"""
        try:
            if "Claude" in self.model_name:
                self.provider = "anthropic"
                self.client = anthropic.Anthropic(
                    api_key=self.secrets.get("anthropic", {}).get("api_key")
                )
                # Map model names to correct available models  
                if "3.5" in self.model_name:
                    self.model_id = "claude-3-7-sonnet-20250219"  # Use latest 3.7 instead of 3.5
                elif "3.7" in self.model_name:
                    self.model_id = "claude-3-7-sonnet-20250219"  # Latest Claude 3.7 model
                elif "4.0" in self.model_name:
                    self.model_id = "claude-sonnet-4-20250514"  # Latest Claude 4.0 model
                elif "4.5" in self.model_name:
                    self.model_id = "claude-sonnet-4-5-20250929"  # Claude 4.5 model
                else:
                    self.model_id = "claude-3-7-sonnet-20250219"  # Default to latest 3.7 model
                    
            elif "GPT" in self.model_name:
                self.provider = "openai"
                self.client = openai.OpenAI(
                    api_key=self.secrets.get("openai", {}).get("api_key")
                )
                self.model_id = "gpt-4o"
                
            elif "DeepSeek" in self.model_name:
                self.provider = "deepseek" 
                self.client = openai.OpenAI(
                    api_key=self.secrets.get("deepseek", {}).get("api_key"),
                    base_url="https://api.deepseek.com/v1"  # Fixed endpoint
                )
                self.model_id = "deepseek-chat"
                
            elif "Gemini" in self.model_name:
                self.provider = "google"
                api_key = self.secrets.get("google", {}).get("api_key")
                if api_key:
                    genai.configure(api_key=api_key)
                    self.client = genai.GenerativeModel('gemini-2.0-flash-exp')
                    self.model_id = "gemini-2.0-flash-exp"
                else:
                    logger.error("Google API key not found")
                    self.client = None
                    
            else:
                # Default fallback to OpenAI (most reliable)
                self.provider = "openai"
                self.client = openai.OpenAI(
                    api_key=self.secrets.get("openai", {}).get("api_key")
                )
                self.model_id = "gpt-4o"
        except Exception as e:
            logger.error(f"Error initializing LLM client: {str(e)}")
            # Set to None if initialization fails
            self.client = None
    
    def _search_google(self, query: str, num_results: int = 3) -> List[Dict[str, str]]:
        """
        Search Google using Custom Search Engine API or SerpAPI
        Returns list of search results with title, snippet, and link
        """
        try:
            # Try Google Custom Search Engine first
            google_api_key = self.secrets.get("google", {}).get("search_api_key")
            google_cse_id = self.secrets.get("google", {}).get("cse_id")
            
            if google_api_key and google_cse_id:
                # Use Google Custom Search Engine API
                url = "https://www.googleapis.com/customsearch/v1"
                params = {
                    'key': google_api_key,
                    'cx': google_cse_id,
                    'q': query,
                    'num': num_results
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for item in data.get('items', []):
                        results.append({
                            'title': item.get('title', ''),
                            'snippet': item.get('snippet', ''),
                            'link': item.get('link', ''),
                            'source': 'Google'
                        })
                    
                    return results
            
            # Fallback to SerpAPI if available
            serpapi_key = self.secrets.get("serpapi", {}).get("api_key")
            if serpapi_key:
                url = "https://serpapi.com/search"
                params = {
                    'api_key': serpapi_key,
                    'engine': 'google',
                    'q': query,
                    'num': num_results
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    
                    for item in data.get('organic_results', []):
                        results.append({
                            'title': item.get('title', ''),
                            'snippet': item.get('snippet', ''),
                            'link': item.get('link', ''),
                            'source': 'SerpAPI'
                        })
                    
                    return results
            
            logger.warning("No Google Search API credentials found")
            return []
            
        except Exception as e:
            logger.error(f"Error searching Google: {str(e)}")
            return []
    
    def generate_cypher(self, natural_query: str, schema_text: str) -> str:
        """
        Generate Cypher query from natural language using LLM
        """
        # If no client is available, use rule-based fallbacks
        if not self.client:
            return self._generate_fallback_cypher(natural_query)
        
        prompt = f"""You are a Neo4j Cypher query expert. Convert the natural language query into a valid Cypher query.

Database Schema:
{schema_text}

Natural Language Query: {natural_query}

Important Instructions:
1. Return ONLY the Cypher query, no explanations
2. Use proper Cypher syntax
3. ALWAYS order results by start_year DESC and LIMIT to 20 (show most recent grants first)
4. Match node labels and relationship types from the schema
5. Use WHERE clauses for filtering with CONTAINS for partial matches
6. For researcher names, use CONTAINS to match partial names (researchers may have titles like "Prof", "Dr", etc.)
7. Return relevant properties including descriptions, amounts, dates
8. Include ORDER BY g.start_year DESC LIMIT 20 in all grant queries

Example queries (always return the 20 most recent grants):
- For "grants about cancer": MATCH (g:Grant) WHERE g.title CONTAINS 'cancer' OR g.description CONTAINS 'cancer' RETURN DISTINCT g ORDER BY g.start_year DESC LIMIT 20
- For "grants for Glenn King": MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant) WHERE (r.name CONTAINS 'Glenn King' OR (r.name CONTAINS 'Glenn' AND r.name CONTAINS 'King') OR r.name CONTAINS 'King, Glenn') OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution) RETURN DISTINCT g.title, g.amount, g.description, g.start_year, r.name, i.name ORDER BY g.start_year DESC LIMIT 20
- For "find grants for 'raymond norton'": MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant) WHERE (r.name CONTAINS 'raymond norton' OR (r.name CONTAINS 'Raymond' AND r.name CONTAINS 'Norton') OR r.name CONTAINS 'Norton, Raymond') OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution) RETURN DISTINCT g.title, g.amount, g.description, g.start_year, r.name, i.name ORDER BY g.start_year DESC LIMIT 20
- For "researchers at University of Melbourne": MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR]->(g:Grant)-[:HOSTED_BY]->(i:Institution) WHERE i.name CONTAINS 'Melbourne' RETURN DISTINCT r, g, i ORDER BY g.start_year DESC LIMIT 20

Cypher Query:"""

        try:
            cypher = ""
            
            if self.provider == "anthropic" and self.client:
                # Use type: ignore to bypass static analysis issues
                response = self.client.messages.create(  # type: ignore
                    model=self.model_id,
                    max_tokens=1024,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                if hasattr(response, 'content') and response.content:
                    raw_text = response.content[0].text  # type: ignore
                    if raw_text:
                        cypher = str(raw_text).strip()
                        # Clean up any potential formatting issues
                        cypher = ' '.join(cypher.split())
                
            elif (self.provider == "openai" or self.provider == "deepseek") and self.client:
                response = self.client.chat.completions.create(  # type: ignore
                    model=self.model_id,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    max_tokens=1024
                )
                if hasattr(response, 'choices') and response.choices:
                    content = response.choices[0].message.content
                    if content:
                        cypher = str(content).strip()
                        # Clean up any potential formatting issues
                        cypher = ' '.join(cypher.split())
                        
            elif self.provider == "google" and self.client:
                response = self.client.generate_content(prompt)  # type: ignore
                if hasattr(response, 'text') and response.text:
                    cypher = str(response.text).strip()
                    # Clean up any potential formatting issues
                    cypher = ' '.join(cypher.split())
            
            # Clean up the response
            if cypher:
                cypher = cypher.replace("```cypher", "").replace("```", "").strip()
            
            # If no valid response, provide a fallback
            if not cypher:
                cypher = self._generate_fallback_cypher(natural_query)
            
            logger.info(f"Generated Cypher: {cypher}")
            return cypher
            
        except Exception as e:
            logger.error(f"Error generating Cypher: {str(e)}")
            # Return a fallback query instead of raising
            return self._generate_fallback_cypher(natural_query)
    
    def _generate_fallback_cypher(self, natural_query: str) -> str:
        """Generate enhanced Cypher queries based on keywords and context"""
        query_lower = natural_query.lower()
        
        # Extract researcher names from quotes or common patterns
        import re
        
        # Look for names in quotes like 'raymond norton' or "raymond norton"
        quoted_names = re.findall(r"['\"]([^'\"]+)['\"]", natural_query)
        
        # Check for specific researcher name patterns
        if quoted_names:
            # Handle quoted researcher names
            researcher_name = quoted_names[0].strip()
            name_parts = researcher_name.split()
            
            if len(name_parts) >= 2:
                # Generate flexible name matching for any researcher
                first_name = name_parts[0]
                last_name = name_parts[-1]  # Use last word as surname
                
                return f"""
                MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant)
                WHERE (r.name CONTAINS '{researcher_name}' 
                       OR (r.name CONTAINS '{first_name}' AND r.name CONTAINS '{last_name}')
                       OR r.name CONTAINS '{last_name}, {first_name}'
                       OR r.name CONTAINS '{first_name.title()} {last_name.title()}'
                       OR r.name CONTAINS '{last_name.title()}, {first_name.title()}')
                OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution)
                OPTIONAL MATCH (g)-[:IN_AREA]->(ra:ResearchArea)
                OPTIONAL MATCH (g)-[:HAS_FIELD]->(rf:ResearchField)
                RETURN DISTINCT g.title, g.amount, g.start_year, g.end_date, g.description, g.funding_body, 
                       i.name as institution, ra.name as research_area, rf.name as research_field, 
                       r.name as researcher, g.grant_status, g.date_announced
                ORDER BY g.start_year DESC
                LIMIT 20
                """
            else:
                # Single name - search broadly
                return f"""
                MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant)
                WHERE r.name CONTAINS '{researcher_name}'
                OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution)
                RETURN DISTINCT g.title, g.amount, g.start_year, g.description, g.funding_body,
                       r.name as researcher, i.name as institution
                ORDER BY g.start_year DESC
                LIMIT 20
                """
        elif 'glenn king' in query_lower:
            return """
            MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant)
            WHERE r.name CONTAINS 'Glenn King' OR (r.name CONTAINS 'Glenn' AND r.name CONTAINS 'King')
            OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution)
            OPTIONAL MATCH (g)-[:IN_AREA]->(ra:ResearchArea)
            OPTIONAL MATCH (g)-[:HAS_FIELD]->(rf:ResearchField)
            RETURN DISTINCT g.title, g.amount, g.start_year, g.end_date, g.description, g.funding_body, 
                   i.name as institution, ra.name as research_area, rf.name as research_field, 
                   r.name as researcher, g.grant_status, g.date_announced
            ORDER BY g.start_year DESC
            LIMIT 20
            """
        elif any(name in query_lower for name in ['king', 'glenn']):
            return """
            MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant)
            WHERE r.name CONTAINS 'King' OR r.name CONTAINS 'Glenn'
            OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution)
            RETURN DISTINCT g.title, g.amount, g.start_year, g.description, g.funding_body, 
                   r.name as researcher, i.name as institution
            ORDER BY g.start_year DESC
            LIMIT 20
            """
        elif any(word in query_lower for word in ['grant', 'funding', 'award']):
            return """
            MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR]->(g:Grant)
            OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution)
            RETURN DISTINCT g.title, g.amount, g.start_year, g.description, g.funding_body,
                   r.name as researcher, i.name as institution
            ORDER BY g.start_year DESC
            LIMIT 20
            """
        elif any(word in query_lower for word in ['cancer', 'oncology', 'tumor']):
            return "MATCH (g:Grant) WHERE toLower(g.title) CONTAINS 'cancer' OR toLower(g.description) CONTAINS 'cancer' RETURN g ORDER BY g.start_year DESC LIMIT 20"
        elif any(word in query_lower for word in ['researcher', 'scientists', 'investigator']):
            return "MATCH (r:Researcher) RETURN r LIMIT 20"
        elif any(word in query_lower for word in ['institution', 'university', 'college']):
            return "MATCH (i:Institution) RETURN i LIMIT 20"
        elif any(word in query_lower for word in ['collaboration', 'network', 'partner']):
            return "MATCH (r1:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant)<-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]-(r2:Researcher) WHERE r1 <> r2 RETURN r1, r2, g ORDER BY g.start_year DESC LIMIT 20"
        else:
            return "MATCH (g:Grant) RETURN g ORDER BY g.start_year DESC LIMIT 20"
    
    def generate_summary(self, query: str, results: list, include_search: bool = True) -> str:
        """
        Generate a natural language summary of the query results
        Args:
            query: The search query
            results: Database query results
            include_search: Whether to include Google Search context
        """
        # Fallback to simple summary if no client or if LLM fails
        if not self.client:
            return self._generate_fallback_summary(query, results, include_search)
        
        # Prepare a better sample of results for analysis
        total_results = len(results)
        sample_size = min(5, total_results)  # Use up to 5 results as sample
        sample_results = results[:sample_size]
        
        # Format sample results for better readability
        formatted_sample = []
        for i, result in enumerate(sample_results, 1):
            formatted_sample.append(f"Result {i}: {dict(result)}")
        results_text = "\n".join(formatted_sample)
        
        # Get Google Search results for additional context (if enabled)
        search_results = []
        search_context = ""
        if include_search:
            search_results = self._search_google(query, num_results=3)
        if search_results:
            search_context = "\n\nAdditional Context from Web Search:\n"
            for i, result in enumerate(search_results, 1):
                search_context += f"Search Result {i}: {result['title']}\n"
                search_context += f"Summary: {result['snippet']}\n"
                search_context += f"Source: {result['link']}\n\n"
        
        prompt = f"""Analyze the following biotech/medical research database query results and provide a well-structured summary with additional web context.

Original Query: {query}
Total Results Found: {total_results}
Sample Results (showing {sample_size} of {total_results}):
{results_text}{search_context}

Create a comprehensive summary using the following structure with clear markdown headers:

## Overview
State the exact number of results found ({total_results}) and main research focus areas.

## Grant Portfolio 
List specific grants with funding amounts, years, and purposes (if available).

## Research Impact
Explain how these grants advance medical science, drug development, or healthcare.

## Key Research Themes
Identify major research areas, methodologies, or breakthrough potential.

## Practical Applications
Describe real-world benefits, therapeutic targets, or clinical outcomes.

## Innovation Highlights
Highlight novel approaches, technologies, or collaborations.

## External References
If web search results are available, include relevant external information and cite the sources with links.

IMPORTANT FORMATTING RULES:
- Use proper number formatting (e.g., $2,981,630 not $2,981,630)
- Ensure no character separation in words or numbers
- Use clear section headers with ##
- Be accurate about the total count: {total_results} results
- Write in complete, well-formed sentences
- Include clickable links for external references in markdown format: [Title](URL)

Summary:"""

        try:
            summary = ""
            
            if self.provider == "anthropic" and self.client:
                response = self.client.messages.create(  # type: ignore
                    model=self.model_id,
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}]
                )
                if hasattr(response, 'content') and response.content:
                    raw_text = response.content[0].text  # type: ignore
                    if raw_text:
                        # Gentle text cleaning - preserve formatting but fix encoding issues
                        summary = str(raw_text).strip()
                        # Only remove invalid characters but preserve normal spaces and newlines
                        summary = ''.join(c for c in summary if ord(c) >= 32 or c in '\n\r\t')
                        # Fix any doubled spaces but preserve line breaks
                        import re
                        summary = re.sub(r' +', ' ', summary)  # Multiple spaces -> single space
                        summary = re.sub(r'\n +', '\n', summary)  # Remove spaces after newlines
                
            elif (self.provider == "openai" or self.provider == "deepseek") and self.client:
                response = self.client.chat.completions.create(  # type: ignore
                    model=self.model_id,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1500
                )
                if hasattr(response, 'choices') and response.choices:
                    content = response.choices[0].message.content
                    if content:
                        # Gentle text cleaning - preserve formatting but fix encoding issues
                        summary = str(content).strip()
                        # Only remove invalid characters but preserve normal spaces and newlines
                        summary = ''.join(c for c in summary if ord(c) >= 32 or c in '\n\r\t')
                        # Fix any doubled spaces but preserve line breaks
                        import re
                        summary = re.sub(r' +', ' ', summary)  # Multiple spaces -> single space
                        summary = re.sub(r'\n +', '\n', summary)  # Remove spaces after newlines
                        
            elif self.provider == "google" and self.client:
                response = self.client.generate_content(prompt)  # type: ignore
                if hasattr(response, 'text') and response.text:
                    # Gentle text cleaning - preserve formatting but fix encoding issues
                    summary = str(response.text).strip()
                    # Only remove invalid characters but preserve normal spaces and newlines
                    summary = ''.join(c for c in summary if ord(c) >= 32 or c in '\n\r\t')
                    # Fix any doubled spaces but preserve line breaks
                    import re
                    summary = re.sub(r' +', ' ', summary)  # Multiple spaces -> single space
                    summary = re.sub(r'\n +', '\n', summary)  # Remove spaces after newlines
            
            # Fallback summary if no response
            if not summary:
                summary = self._generate_fallback_summary(query, results, include_search)
            
            return summary
                
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return self._generate_fallback_summary(query, results, include_search)
    
    def _generate_fallback_summary(self, query: str, results: list, include_search: bool = True) -> str:
        """Generate an enhanced fallback summary with structured information and actual data"""
        count = len(results)
        if count == 0:
            return f"## Overview\nNo results found for query: {query}\n\nNo matching grants, researchers, or institutions were found in the database."
        
        # Generate structured fallback summary with real data
        summary_parts = []
        
        # Overview section
        summary_parts.append(f"## Overview")
        summary_parts.append(f"Found {count} results for query: {query}")
        
        # Extract actual data from results
        if results:
            # Collect data for analysis
            grants_data = []
            seen_grants = set()  # Track unique grants to avoid duplicates
            researchers = set()
            institutions = set()
            total_funding = 0
            years = []
            
            for result in results:
                if isinstance(result, dict):
                    # Extract grant information
                    title = result.get('g.title') or result.get('title') or result.get('grant_title', '')
                    amount = result.get('g.amount') or result.get('amount', 0)
                    researcher = result.get('researcher') or result.get('r.name') or result.get('pi_name', '')
                    institution = result.get('institution') or result.get('i.name', '')
                    year = result.get('g.start_year') or result.get('start_year') or result.get('year', '')
                    
                    if title:
                        # Create a unique key for deduplication
                        grant_key = (str(title).strip().lower(), str(amount), str(year).strip())
                        
                        # Only add if we haven't seen this grant before
                        if grant_key not in seen_grants:
                            seen_grants.add(grant_key)
                            grants_data.append({
                                'title': str(title).strip(),
                                'amount': amount,
                                'researcher': str(researcher).strip(),
                                'institution': str(institution).strip(),
                                'year': str(year).strip()
                            })
                    
                    # Collect summary statistics
                    if researcher:
                        researchers.add(str(researcher).strip())
                    if institution:
                        institutions.add(str(institution).strip())
                    if amount and str(amount).replace(',', '').replace('$', '').replace('.', '').isdigit():
                        try:
                            total_funding += float(str(amount).replace(',', '').replace('$', ''))
                        except:
                            pass
                    if year:
                        years.append(str(year).strip())
            
            # Grant Portfolio section with actual grants
            summary_parts.append(f"\n## Grant Portfolio")
            if grants_data:
                summary_parts.append(f"The portfolio includes {len(grants_data)} research grants:\n")
                
                # Show top 5 grants with details
                for i, grant in enumerate(grants_data[:5]):
                    # Format each grant on its own line with clear structure
                    grant_title = grant['title'][:80] + "..." if len(grant['title']) > 80 else grant['title']
                    grant_info = f"• **{grant_title}**"
                    
                    # Add funding amount if available
                    if grant['amount']:
                        try:
                            amount_val = float(str(grant['amount']).replace(',', '').replace('$', ''))
                            if amount_val > 0:
                                grant_info += f" — ${amount_val:,.0f}"
                        except:
                            grant_info += f" — {grant['amount']}"
                    
                    # Add year if available
                    if grant['year'] and grant['year'].isdigit():
                        grant_info += f" — {grant['year']}"
                    
                    summary_parts.append(grant_info)
                
                if len(grants_data) > 5:
                    summary_parts.append(f"• ... and {len(grants_data) - 5} additional grants")
            else:
                summary_parts.append(f"Found {count} grant-related records with detailed research information.")
            
            # Research Impact section with funding details
            summary_parts.append(f"\n## Research Impact")
            if total_funding > 0:
                summary_parts.append(f"Total funding identified: **${total_funding:,.0f}**\n")
            
            if researchers:
                researcher_list = ', '.join(list(researchers)[:3])
                summary_parts.append(f"Research team includes {len(researchers)} researcher(s): {researcher_list}")
                if len(researchers) > 3:
                    summary_parts.append(f"... and {len(researchers) - 3} additional researchers\n")
                else:
                    summary_parts.append("")
            
            if institutions:
                institution_list = ', '.join(list(institutions)[:2])
                summary_parts.append(f"Affiliated with {len(institutions)} institution(s): {institution_list}")
                if len(institutions) > 2:
                    summary_parts.append(f"... and {len(institutions) - 2} additional institutions")
                else:
                    summary_parts.append("")
            
            # Key Findings with time range
            summary_parts.append(f"\n## Key Findings")
            if years:
                clean_years = [y for y in years if y and y.isdigit()]
                if clean_years:
                    year_range = f"{min(clean_years)}-{max(clean_years)}" if len(set(clean_years)) > 1 else clean_years[0]
                    summary_parts.append(f"Research activity spans from **{year_range}**.")
            
            summary_parts.append(f"Database search identified **{count}** relevant records with comprehensive grant and researcher information.")
            
            # Add External References section with Google Search results (if enabled)
            if include_search:
                search_results = self._search_google(query, num_results=3)
            else:
                search_results = []
            if search_results:
                summary_parts.append(f"\n## External References")
                summary_parts.append("Additional information from web search:")
                summary_parts.append("")
                
                for i, result in enumerate(search_results, 1):
                    ref_title = result['title'][:100] + "..." if len(result['title']) > 100 else result['title']
                    summary_parts.append(f"{i}. **[{ref_title}]({result['link']})**")
                    if result['snippet']:
                        snippet = result['snippet'][:200] + "..." if len(result['snippet']) > 200 else result['snippet']
                        summary_parts.append(f"   {snippet}")
                    summary_parts.append("")
            
        return "\n".join(summary_parts)
    
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
            # Convert amounts to float safely before summing
            valid_amounts = []
            for amount in amounts:
                try:
                    if isinstance(amount, str):
                        amount_clean = amount.replace('$', '').replace(',', '').strip()
                        valid_amounts.append(float(amount_clean))
                    else:
                        valid_amounts.append(float(amount))
                except (ValueError, TypeError):
                    continue
            
            if valid_amounts:
                total = sum(valid_amounts)
                avg = total / len(valid_amounts)
                insights.append(f"Total funding: {safe_format_amount(total)}")
                insights.append(f"Average grant size: {safe_format_amount(avg)}")
        
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
