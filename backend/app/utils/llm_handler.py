import anthropic
import openai
import google.generativeai as genai
from typing import Dict, Any, List
import logging
import requests
import json
from urllib.parse import quote
from bs4 import BeautifulSoup
import time
import re

# Google Search API imports (with fallback handling)
try:
    from googleapiclient.discovery import build
except ImportError:
    build = None

try:
    from serpapi import GoogleSearch
except ImportError:
    GoogleSearch = None

from app.utils.biomcp_client import BioMCPClient

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
        self.model_id = "claude-3-5-sonnet-latest" 
        
        # Initialize Google Search API credentials
        self.google_search_api_key = secrets.get("google", {}).get("search_api_key")
        self.google_search_engine_id = secrets.get("google", {}).get("cse_id")
        self.serpapi_key = secrets.get("serpapi", {}).get("api_key")
        self.biomcp = BioMCPClient()
        
        self._init_client()
    
    def _init_client(self):
        """Initialize the appropriate client based on model"""
        try:
            if "Claude" in self.model_name:
                self.provider = "anthropic"
                self.client = anthropic.Anthropic(
                    api_key=self.secrets.get("anthropic", {}).get("api_key")
                )
                if "4.5" in self.model_name:
                    self.model_id = "claude-sonnet-4-5"
                else:
                    self.model_id = "claude-3-5-sonnet-latest"
                    
            elif "GPT" in self.model_name or "o3" in self.model_name:
                self.provider = "openai"
                self.client = openai.OpenAI(
                    api_key=self.secrets.get("openai", {}).get("api_key")
                )
                if "o3-mini" in self.model_name:
                    self.model_id = "o3-mini"
                else:
                    self.model_id = "gpt-4o"
                
            elif "DeepSeek" in self.model_name:
                self.provider = "deepseek" 
                api_key = self.secrets.get("deepseek", {}).get("api_key")
                
                # Detect OpenRouter key format
                if api_key and api_key.startswith("sk-or-"):
                    base_url = "https://openrouter.ai/api/v1"
                    if "R1" in self.model_name:
                        self.model_id = "deepseek/deepseek-r1"
                    else:
                        self.model_id = "deepseek/deepseek-v3.2"
                else:
                    base_url = "https://api.deepseek.com"
                    if "R1" in self.model_name:
                        self.model_id = "deepseek-reasoner"
                    else:
                        self.model_id = "deepseek-chat"
                
                self.client = openai.OpenAI(
                    api_key=api_key,
                    base_url=base_url
                )
                
            elif "Gemini" in self.model_name:
                self.provider = "google"
                api_key = self.secrets.get("google", {}).get("api_key")
                if api_key:
                    genai.configure(api_key=api_key)
                    if "2.0" in self.model_name:
                        self.model_id = "gemini-2.0-flash"
                    else:
                        self.model_id = "gemini-1.5-pro"
                    self.client = genai.GenerativeModel(self.model_id)
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
    
    def _create_enhanced_search_query(self, original_query: str, results: list) -> str:
        """
        Create an enhanced search query by extracting key terms from database results
        
        Args:
            original_query: The original user query
            results: Sample database results to extract terms from
            
        Returns:
            Enhanced search query string
        """
        try:
            # Extract key terms from results, but be more careful with researcher names
            key_terms = set()
            
            # Parse the original query to detect if it's a researcher name query
            import re
            original_lower = original_query.lower()
            quoted_names = re.findall(r"['\"]([^'\"]+)['\"]", original_query)
            is_researcher_query = any(word in original_lower for word in ['researcher', 'grants for', 'find']) or quoted_names
            
            # Extract key information from actual grant results for targeted Google search
            grant_titles = []
            researcher_names = []
            institutions = []
            
            for result in results:
                result_dict = dict(result)
                
                # Extract grant titles with full context
                title_fields = ['title', 'grant_title', 'g.title']
                for field in title_fields:
                    if field in result_dict and result_dict[field]:
                        grant_title = str(result_dict[field]).strip()
                        if len(grant_title) > 10:  # Only meaningful titles
                            grant_titles.append(grant_title)
                        break
                
                # Extract researcher/CI names
                name_fields = ['name', 'researcher_name', 'r.name', 'ci_name', 'investigator_name']
                for field in name_fields:
                    if field in result_dict and result_dict[field]:
                        researcher_name = str(result_dict[field]).strip()
                        # Clean up titles
                        clean_name = researcher_name.replace('Prof ', '').replace('Dr ', '').replace('Professor ', '')
                        if len(clean_name) > 3 and clean_name not in researcher_names:
                            researcher_names.append(clean_name)
                        break
                
                # Extract institutions
                institution_fields = ['i.name', 'institution', 'institution_name']
                for field in institution_fields:
                    if field in result_dict and result_dict[field]:
                        institution = str(result_dict[field]).strip().split(',')[0]  # Take main name
                        if len(institution) > 5 and institution not in institutions:
                            institutions.append(institution)
                        break
            
            # Create targeted search terms from actual grant data
            # Priority: 1) Grant titles (most specific), 2) Researcher names, 3) Institutions
            if grant_titles:
                # Use the most specific grant title for search
                primary_title = grant_titles[0]
                # Extract key research terms from title
                title_words = primary_title.split()[:6]  # Take more words for context
                research_keywords = []
                for word in title_words:
                    clean_word = word.strip('.,()[]:-').lower()
                    # Include meaningful research terms
                    if (len(clean_word) > 3 and 
                        clean_word not in ['the', 'and', 'for', 'with', 'from', 'into', 'study', 'research', 'analysis', 'project', 'grant']):
                        research_keywords.append(clean_word)
                key_terms.update(research_keywords[:4])  # Top 4 research terms
                
                # Add the primary researcher name for context
                if researcher_names:
                    key_terms.add(f'"{researcher_names[0]}"')
                    
                logger.info(f"DEBUG: Using grant title terms: {research_keywords[:4]}")
                logger.info(f"DEBUG: Using researcher: {researcher_names[0] if researcher_names else 'None'}")
            
            elif researcher_names:
                # If no grant titles, use researcher names with research context
                primary_researcher = researcher_names[0]
                key_terms.add(f'"{primary_researcher}"')
                key_terms.add('research')
                key_terms.add('grants')
                if institutions:
                    key_terms.add(institutions[0])
                logger.info(f"DEBUG: Using researcher-focused search: {primary_researcher}")
            
            # For quoted researcher queries, still respect the original intent but enhance with grant data
            if quoted_names and is_researcher_query and grant_titles:
                # Combine original query with actual grant context
                enhanced_query = f'"{quoted_names[0]}" {" ".join(list(key_terms)[:3])}'
                logger.info(f"DEBUG: Enhanced quoted researcher query with grant context")
                return enhanced_query
                
                # For researcher names, be very careful - only use if the original query wasn't specific
                if not is_researcher_query or not quoted_names:
                    name_fields = ['researcher', 'researcher_name', 'name']
                    for field in name_fields:
                        if field in result_dict and result_dict[field]:
                            researcher_name = str(result_dict[field]).strip()
                            # Only add researcher name if it's not too generic and matches query context
                            if (len(researcher_name.split()) == 2 and  # Full name with first and last
                                not any(generic in researcher_name.lower() for generic in ['prof', 'dr', 'professor'])):
                                key_terms.add(f'"{researcher_name}"')  # Quote full names for exact matching
                                break  # Only take one researcher name to avoid confusion
                
                # Extract institution names (but be selective)
                institution_fields = ['institution', 'institution_name']
                for field in institution_fields:
                    if field in result_dict and result_dict[field]:
                        inst_name = str(result_dict[field]).split(',')[0].strip()
                        # Only include well-known institutions, not generic terms
                        if (len(inst_name) > 8 and 
                            any(uni_word in inst_name.lower() for uni_word in ['university', 'institute', 'college', 'hospital'])):
                            key_terms.add(inst_name)
                            break  # Only one institution
                
                # Extract funding agency (if specific)
                agency_fields = ['funding_body', 'funding_agency']
                for field in agency_fields:
                    if field in result_dict and result_dict[field]:
                        agency = str(result_dict[field]).strip()
                        # Only include well-known funding agencies
                        if agency and len(agency) > 2 and len(agency) < 20:
                            key_terms.add(agency)
                            break
            
            # Create final enhanced query using grant table information
            enhanced_terms = list(key_terms)[:5]  # Take top 5 most relevant terms
            
            if enhanced_terms:
                if grant_titles and researcher_names:
                    # Best case: We have both grant content and researcher info
                    enhanced_query = f"{' '.join(enhanced_terms[:4])} research funding"
                    logger.info(f"DEBUG: Grant-focused search query created")
                elif researcher_names:
                    # Researcher-focused with research context
                    enhanced_query = f"{' '.join(enhanced_terms[:3])} research grants funding"
                    logger.info(f"DEBUG: Researcher-focused search query created")
                else:
                    # General enhancement
                    enhanced_query = f"{original_query} {' '.join(enhanced_terms[:3])}"
                    logger.info(f"DEBUG: General enhanced search query created")
            else:
                enhanced_query = original_query
                logger.info(f"DEBUG: Using original query - no enhancement possible")
            
            return enhanced_query
            
        except Exception as e:
            print(f"Error creating enhanced search query: {e}")
            return original_query
    
    def _scrape_webpage(self, url: str, max_length: int = 2000) -> str:
        """
        Scrape content from a webpage
        
        Args:
            url: URL to scrape
            max_length: Maximum length of scraped content
            
        Returns:
            Cleaned text content from the webpage
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit length
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return text
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return ""
    
    def _summarize_webpage_content(self, url: str, content: str, query_context: str) -> str:
        """
        Use LLM to summarize scraped webpage content in context of the query
        
        Args:
            url: Source URL
            content: Scraped content
            query_context: Original query context for relevance
            
        Returns:
            LLM-generated summary of the content
        """
        try:
            if not self.client or not content.strip():
                return ""
            
            prompt = f"""Summarize the following webpage content in the context of this research query: "{query_context}"

Focus on:
1. Key research findings or information relevant to the query
2. Important researchers, institutions, or grants mentioned
3. Recent developments or trends
4. Specific data points or conclusions

Keep the summary concise (2-3 sentences) and highly relevant to the research query.

Webpage URL: {url}
Content: {content}

Summary:"""

            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model_id,
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()
                
            elif self.provider == "openai" or self.provider == "deepseek":
                response = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.3
                )
                return response.choices[0].message.content.strip()
                
            elif self.provider == "google":
                response = self.client.generate_content(prompt)
                return response.text.strip()
                
        except Exception as e:
            print(f"Error summarizing webpage content: {e}")
            return ""
    
    def _search_google(self, query: str, num_results: int = 3) -> list:
        """
        Search Google for additional context using the configured search engine,
        scrape the web pages, and generate LLM summaries
        
        Args:
            query: Search query
            num_results: Number of results to return (default: 3)
            
        Returns:
            List of search results with title, original snippet, link, and LLM summary
        """
        try:
            results = []
            
            # First try Google Custom Search
            if self.google_search_api_key and self.google_search_engine_id and build:
                try:
                    service = build("customsearch", "v1", developerKey=self.google_search_api_key)
                    res = service.cse().list(
                        q=query,
                        cx=self.google_search_engine_id,
                        num=num_results
                    ).execute()
                    
                    if 'items' in res:
                        for item in res['items']:
                            result = {
                                'title': item.get('title', ''),
                                'snippet': item.get('snippet', ''),
                                'link': item.get('link', ''),
                                'scraped_summary': ''
                            }
                            
                            # Try to scrape and summarize the webpage
                            scraped_content = self._scrape_webpage(result['link'])
                            if scraped_content:
                                summary = self._summarize_webpage_content(
                                    result['link'], 
                                    scraped_content, 
                                    query
                                )
                                if summary:
                                    result['scraped_summary'] = summary
                            
                            results.append(result)
                            
                            # Add small delay to be respectful to servers
                            time.sleep(0.5)
                    
                    return results
                    
                except Exception as e:
                    print(f"Google Custom Search error: {e}")
            
            # Fallback to SerpAPI if Google Custom Search failed
            if self.serpapi_key and GoogleSearch:
                try:
                    params = {
                        "engine": "google",
                        "q": query,
                        "api_key": self.serpapi_key,
                        "num": num_results
                    }
                    
                    search = GoogleSearch(params)
                    res = search.get_dict()
                    
                    if "organic_results" in res:
                        for item in res["organic_results"][:num_results]:
                            result = {
                                'title': item.get('title', ''),
                                'snippet': item.get('snippet', ''),
                                'link': item.get('link', ''),
                                'scraped_summary': ''
                            }
                            
                            # Try to scrape and summarize the webpage
                            scraped_content = self._scrape_webpage(result['link'])
                            if scraped_content:
                                summary = self._summarize_webpage_content(
                                    result['link'], 
                                    scraped_content, 
                                    query
                                )
                                if summary:
                                    result['scraped_summary'] = summary
                            
                            results.append(result)
                            
                            # Add small delay to be respectful to servers
                            time.sleep(0.5)
                    
                    return results
                    
                except Exception as e:
                    print(f"SerpAPI error: {e}")
            
            return []
            
        except Exception as e:
            print(f"Error in Google search: {e}")
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
6. For researcher names, use case-insensitive matching with toLower()
7. For researcher names in quotes, use toLower(r.name) = 'name' or similar precise matching
8. Avoid partial matches that are too broad, but allow for "Last, First" or "First Last" variations
9. Return comprehensive grant information using ONLY the actual properties that exist in the database
10. Include ORDER BY g.start_year DESC LIMIT 20 in all grant queries
11. ACTUAL Grant properties: title, grant_status, amount, description, start_year, end_date, grant_type, funding_body, broad_research_area, field_of_research, application_id, date_announced
12. ACTUAL Researcher properties: name, orcid_id (NO title property exists)
13. Use proper aliases: g.title as grant_title, g.grant_status as status, r.name as researcher_name, i.name as institution_name
14. DO NOT query non-existent fields like g.start_date, r.title, g.agency, g.end_year, r.orcid_id - use only the actual properties listed above

Example queries using ONLY actual database properties (always return comprehensive grant information from the 20 most recent grants):
- For "grants about cancer": MATCH (g:Grant) OPTIONAL MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g) OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution) WHERE g.title CONTAINS 'cancer' OR g.description CONTAINS 'cancer' WITH g.title as grant_title, g.grant_status as status, g.amount as amount, g.description as description, g.start_year as start_year, g.end_date as end_date, g.grant_type as grant_type, g.funding_body as funding_body, g.broad_research_area as broad_research_area, g.field_of_research as field_of_research, g.application_id as application_id, g.date_announced as date_announced, collect(DISTINCT r.name)[0] as researcher_name, collect(DISTINCT r.orcid_id)[0] as researcher_orcid, collect(DISTINCT i.name)[0] as institution_name RETURN DISTINCT grant_title, status, amount, description, start_year, end_date, grant_type, funding_body, broad_research_area, field_of_research, application_id, date_announced, researcher_name, institution_name ORDER BY start_year DESC LIMIT 20
- For "grants for Glenn King": MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant) WHERE (toLower(r.name) = 'glenn king' OR toLower(r.name) = 'king, glenn' OR toLower(r.name) = 'dr glenn king' OR toLower(r.name) = 'prof glenn king') OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution) WITH g.title as grant_title, g.grant_status as status, g.amount as amount, g.description as description, g.start_year as start_year, g.end_date as end_date, g.grant_type as grant_type, g.funding_body as funding_body, g.broad_research_area as broad_research_area, g.field_of_research as field_of_research, g.application_id as application_id, g.date_announced as date_announced, collect(DISTINCT r.name)[0] as researcher_name, collect(DISTINCT r.orcid_id)[0] as researcher_orcid, collect(DISTINCT i.name)[0] as institution_name RETURN DISTINCT grant_title, status, amount, description, start_year, end_date, grant_type, funding_body, broad_research_area, field_of_research, application_id, date_announced, researcher_name, institution_name ORDER BY start_year DESC LIMIT 20
- For "all grants": MATCH (g:Grant) OPTIONAL MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g) OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution) WITH g.title as grant_title, g.grant_status as status, g.amount as amount, g.description as description, g.start_year as start_year, g.end_date as end_date, g.grant_type as grant_type, g.funding_body as funding_body, g.broad_research_area as broad_research_area, g.field_of_research as field_of_research, g.application_id as application_id, g.date_announced as date_announced, collect(DISTINCT r.name)[0] as researcher_name, collect(DISTINCT r.orcid_id)[0] as researcher_orcid, collect(DISTINCT i.name)[0] as institution_name RETURN DISTINCT grant_title, status, amount, description, start_year, end_date, grant_type, funding_body, broad_research_area, field_of_research, application_id, date_announced, researcher_name, institution_name ORDER BY start_year DESC LIMIT 20

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
                # Remove <think> tags if present (DeepSeek R1)
                cypher = re.sub(r'<think>.*?</think>', '', cypher, flags=re.DOTALL)
                cypher = cypher.replace("```cypher", "").replace("```", "").strip()
            
            # If no valid response, provide a fallback
            if not cypher:
                cypher = self._generate_fallback_cypher(natural_query)
            
            # Simple post-processing - make researcher queries very strict
            if cypher and 'jian li' in natural_query.lower():
                logger.info(f"DEBUG: Researcher query detected for 'jian li'")
                # REMOVE all CONTAINS matching - this is what's causing "Wenjian Liu" to match
                if "CONTAINS 'jian li'" in cypher:
                    cypher = cypher.replace("CONTAINS 'jian li'", "= 'jian li'")
                    logger.info(f"DEBUG: Removed CONTAINS matching to prevent partial matches")
                
                # Use VERY strict matching - only exact matches with minimal variations
                strict_condition = "(toLower(r.name) = 'jian li' OR toLower(r.name) = 'li, jian' OR toLower(r.name) = 'dr jian li' OR toLower(r.name) = 'prof jian li')"
                
                # Replace any existing conditions with our strict one
                if "toLower(r.name) = 'jian li'" in cypher:
                    cypher = cypher.replace("toLower(r.name) = 'jian li'", strict_condition)
                    logger.info(f"DEBUG: Applied strict matching condition")
            
            logger.info(f"Generated Cypher: {cypher}")
            
            return cypher
            
        except Exception as e:
            logger.error(f"Error generating Cypher: {str(e)}")
            # Return a fallback query instead of raising
            return self._generate_fallback_cypher(natural_query)
    
    def _add_researcher_fallback_suggestion(self, cypher: str, natural_query: str) -> str:
        """
        Make researcher queries more flexible but still precise
        """
        try:
            import re
            quoted_names = re.findall(r"['\"]([^'\"]+)['\"]", natural_query)
            
            if quoted_names and 'Researcher' in cypher:
                researcher_name = quoted_names[0].strip().lower()
                name_parts = researcher_name.split()
                
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = name_parts[-1]
                    
                    # Replace overly strict matching with flexible but precise matching
                    if f"toLower(r.name) = '{researcher_name}'" in cypher:
                        max_length = len(researcher_name) + 15
                        flexible_condition = f"(toLower(r.name) = '{researcher_name}' OR toLower(r.name) = '{last_name}, {first_name}' OR toLower(r.name) = 'dr {researcher_name}' OR toLower(r.name) = 'prof {researcher_name}' OR toLower(r.name) = 'professor {researcher_name}' OR (toLower(r.name) CONTAINS '{researcher_name}' AND size(r.name) <= {max_length}))"
                        
                        cypher = cypher.replace(f"toLower(r.name) = '{researcher_name}'", flexible_condition)
            
            return cypher
            
        except Exception as e:
            print(f"Error adding researcher fallback: {e}")
            return cypher
    
    def _improve_researcher_name_matching(self, cypher: str, natural_query: str) -> str:
        """
        Post-process Cypher queries to ensure precise researcher name matching
        for quoted names or specific researcher queries
        """
        try:
            import re
            
            # Check if the original query has quoted researcher names
            quoted_names = re.findall(r"['\"]([^'\"]+)['\"]", natural_query)
            
            if quoted_names and 'Researcher' in cypher:
                # Extract the quoted name
                researcher_name = quoted_names[0].strip().lower()
                
                # Check if the current Cypher uses overly broad matching
                if ('CONTAINS' in cypher and 'AND' in cypher and 
                    any(part.strip().lower() in researcher_name for part in researcher_name.split())):
                    
                    # Replace with more precise matching
                    name_parts = researcher_name.split()
                    if len(name_parts) >= 2:
                        first_name = name_parts[0]
                        last_name = name_parts[-1]
                        
                        # Create precise name matching patterns with more flexibility
                        max_length = len(researcher_name) + 15
                        precise_condition = f"(toLower(r.name) = '{researcher_name}' OR toLower(r.name) = '{last_name}, {first_name}' OR toLower(r.name) = 'dr {researcher_name}' OR toLower(r.name) = 'prof {researcher_name}' OR toLower(r.name) = 'professor {researcher_name}' OR (toLower(r.name) CONTAINS '{researcher_name}' AND size(r.name) <= {max_length}))"
                        
                        # Find and replace the WHERE clause with researcher name matching
                        # Look for patterns like: WHERE (r.name CONTAINS 'X' OR (r.name CONTAINS 'Y' AND r.name CONTAINS 'Z')...)
                        where_pattern = r'WHERE\s*\([^)]*r\.name[^)]*\)'
                        match = re.search(where_pattern, cypher, re.IGNORECASE)
                        
                        if match:
                            old_where = match.group(0)
                            new_where = f"WHERE {precise_condition}"
                            cypher = cypher.replace(old_where, new_where)
            
            return cypher
            
        except Exception as e:
            print(f"Error improving researcher name matching: {e}")
            return cypher
    
    def _generate_fallback_cypher(self, natural_query: str) -> str:
        """Generate enhanced Cypher queries based on keywords and context"""
        query_lower = natural_query.lower()
        
        # Extract researcher names from quotes or common patterns
        import re
        
        # Look for names in quotes like 'raymond norton' or "raymond norton"
        quoted_names = re.findall(r"['\"]([^'\"]+)['\"]", natural_query)
        
        # Look for common researcher name patterns without quotes
        # Pattern: "grants for [first name] [last name]" or "find [first name] [last name]"
        name_patterns = [
            r'(?:grants?\s+for|find\s+(?:grants?\s+for\s+)?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'(?:researcher|scientist|investigator)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
            r'\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:grants?|research|work)'
        ]
        
        researcher_names = []
        for pattern in name_patterns:
            matches = re.findall(pattern, natural_query, re.IGNORECASE)
            researcher_names.extend(matches)
        
        # Check for specific researcher name patterns
        if quoted_names:
            # Handle quoted researcher names
            researcher_name = quoted_names[0].strip()
            name_parts = researcher_name.split()
            
            if len(name_parts) >= 2:
                # Generate precise name matching for the specific researcher
                first_name = name_parts[0]
                last_name = name_parts[-1]  # Use last word as surname
                full_name = f"{first_name} {last_name}".lower()
                
                max_length = len(full_name) + 15
                return f"""MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant) WHERE (toLower(r.name) = '{full_name}' OR toLower(r.name) = '{last_name.lower()}, {first_name.lower()}' OR toLower(r.name) = 'dr {full_name}' OR toLower(r.name) = 'prof {full_name}' OR toLower(r.name) = 'professor {full_name}' OR (toLower(r.name) CONTAINS '{full_name}' AND size(r.name) <= {max_length})) OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution) OPTIONAL MATCH (g)-[:IN_AREA]->(ra:ResearchArea) OPTIONAL MATCH (g)-[:HAS_FIELD]->(rf:ResearchField) RETURN DISTINCT g.title, g.amount, g.start_year, g.end_date, g.description, g.funding_body, i.name as institution, ra.name as research_area, rf.name as research_field, r.name as researcher, g.grant_status, g.date_announced ORDER BY g.start_year DESC LIMIT 20"""
            else:
                # Single name - search broadly
                return f"""
                MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant)
                WHERE r.name CONTAINS '{researcher_name}'
                OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution)
                WITH g.title as grant_title, g.amount as amount, g.start_year as start_year, g.description as description, g.funding_body as funding_body,
                     collect(DISTINCT r.name)[0] as researcher_name, collect(DISTINCT i.name)[0] as institution_name
                RETURN DISTINCT grant_title, amount, start_year, description, funding_body,
                       researcher_name as researcher, institution_name as institution
                ORDER BY start_year DESC
                LIMIT 20
                """
        elif researcher_names:
            # Handle detected researcher names from patterns
            researcher_name = researcher_names[0].strip()
            name_parts = researcher_name.split()
            
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = name_parts[-1]
                full_name = f"{first_name} {last_name}".lower()
                
                return f"""
                MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant)
                WHERE toLower(r.name) CONTAINS '{full_name}' OR toLower(r.name) CONTAINS '{last_name.lower()}'
                OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution)
                WITH g.title as grant_title, g.amount as amount, g.start_year as start_year, g.description as description, g.funding_body as funding_body, g.grant_status as grant_status, g.application_id as application_id,
                     collect(DISTINCT r.name)[0] as researcher_name, collect(DISTINCT i.name)[0] as institution_name
                RETURN DISTINCT grant_title, amount, start_year, description, funding_body, grant_status, application_id,
                       researcher_name as researcher, institution_name as institution
                ORDER BY start_year DESC
                LIMIT 20
                """
        elif 'tony velkov' in query_lower or 'velkov' in query_lower:
            return """
            MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant)
            WHERE r.name CONTAINS 'Tony Velkov' OR r.name CONTAINS 'Velkov' OR r.name CONTAINS 'Toni Velkov'
            OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution)
            WITH g.title as grant_title, g.amount as amount, g.start_year as start_year, g.description as description, g.funding_body as funding_body, g.grant_status as grant_status, g.application_id as application_id,
                 collect(DISTINCT r.name)[0] as researcher_name, collect(DISTINCT i.name)[0] as institution_name
            RETURN DISTINCT grant_title, amount, start_year, description, funding_body, grant_status, application_id,
                   researcher_name as researcher, institution_name as institution
            ORDER BY start_year DESC
            LIMIT 20
            """
        elif 'glenn king' in query_lower:
            return """
            MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant)
            WHERE r.name CONTAINS 'Glenn King' OR (r.name CONTAINS 'Glenn' AND r.name CONTAINS 'King')
            OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution)
            OPTIONAL MATCH (g)-[:IN_AREA]->(ra:ResearchArea)
            OPTIONAL MATCH (g)-[:HAS_FIELD]->(rf:ResearchField)
            WITH g.title as grant_title, g.amount as amount, g.start_year as start_year, g.end_date as end_date, g.description as description, g.funding_body as funding_body, g.grant_status as grant_status, g.date_announced as date_announced,
                 collect(DISTINCT r.name)[0] as researcher_name, collect(DISTINCT i.name)[0] as institution_name, 
                 collect(DISTINCT ra.name)[0] as research_area_name, collect(DISTINCT rf.name)[0] as research_field_name
            RETURN DISTINCT grant_title, amount, start_year, end_date, description, funding_body, grant_status, date_announced,
                   institution_name as institution, research_area_name as research_area, research_field_name as research_field, 
                   researcher_name as researcher
            ORDER BY start_year DESC
            LIMIT 20
            """
        elif any(name in query_lower for name in ['king', 'glenn']):
            return """
            MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant)
            WHERE r.name CONTAINS 'King' OR r.name CONTAINS 'Glenn'
            OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution)
            WITH g.title as grant_title, g.amount as amount, g.start_year as start_year, g.description as description, g.funding_body as funding_body, 
                 collect(DISTINCT r.name)[0] as researcher_name, collect(DISTINCT i.name)[0] as institution_name
            RETURN DISTINCT grant_title, amount, start_year, description, funding_body, 
                   researcher_name as researcher, institution_name as institution
            ORDER BY start_year DESC
            LIMIT 20
            """
        elif any(word in query_lower for word in ['grant', 'funding', 'award']):
            return """
            MATCH (g:Grant)
            OPTIONAL MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR]->(g)
            OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution)
            WITH g.title as grant_title, g.amount as amount, g.start_year as start_year, g.description as description, g.funding_body as funding_body, g.grant_status as grant_status, g.application_id as application_id,
                 collect(DISTINCT r.name)[0] as researcher_name, collect(DISTINCT i.name)[0] as institution_name
            RETURN DISTINCT grant_title, amount, start_year, description, funding_body, grant_status, application_id,
                   researcher_name as researcher, institution_name as institution
            ORDER BY start_year DESC
            LIMIT 20
            """
        
    def generate_summary(self, natural_query: str, results: List[Dict], include_search: bool = True) -> str:
        """
        Generate a summary of results using LLM
        """
        if not results:
            return "No matching grants found."
        
        # If search is enabled, try to get additional context from Google
        search_context = ""
        try:
            if include_search and self.google_search_api_key and self.google_search_engine_id:
                # Create an enhanced search query based on what we found (or didn't find)
                enhanced_search_query = self._create_enhanced_search_query(natural_query, results)
                logger.info(f"Using enhanced search query: {enhanced_search_query}")
                
                search_results = self._search_google(enhanced_search_query)
                if search_results:
                    search_context = "\n\nExternal Search Context (Google):\n"
                    for res in search_results:
                        # Use the LLM-generated summary if available, otherwise fallback to snippet
                        content = res.get('scraped_summary') or res.get('snippet', '')
                        search_context += f"- [{res.get('title')}]({res.get('link')}): {content}\n"
        except Exception as e:
            logger.error(f"Search failed: {e}")
        
        # Format results for LLM context
        context = "Found Grants:\n"
        for i, res in enumerate(results[:10]):  # Limit to top 10 for context
            context += f"{i+1}. {res.get('grant_title', 'Unknown')} ({safe_format_amount(res.get('amount'))}, {res.get('start_year', 'Unknown')})\n"
            context += f"   Researcher: {res.get('researcher_name', 'Unknown')}\n"
            context += f"   Values: {str(res)}\n"
        
        # Add search context if available
        if search_context:
            context += search_context
            
        prompt = f"""Summarize the following research grant results for the query: "{natural_query}"

{context}

Please provide a concise summary that:
1. directly answers the user's question
2. highlights key findings (total funding, main researchers, years)
3. mentions specific grant titles and amounts
4. if external search results are present, integrate relevant information from them (especially about the researcher or topic)

Format with clear Markdown headers and bullet points.
"""

        try:
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
                    return response.content[0].text  # type: ignore
                    
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
                    return response.choices[0].message.content
                    
            elif self.provider == "google" and self.client:
                response = self.client.generate_content(prompt)  # type: ignore
                if hasattr(response, 'text') and response.text:
                    return response.text
                
            return "Could not generate summary."
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return "Error generating summary." 

    def extract_insights(self, results: List[Dict]) -> Dict[str, Any]:
        """
        Extract key insights from results
        """
        if not results:
            return {}
            
        total_funding = 0
        years = []
        researchers = set()
        institutions = set()
        
        for res in results:
            amount = res.get('amount')
            if amount and isinstance(amount, (int, float)):
                total_funding += amount
            elif amount and isinstance(amount, str):
                 try:
                     clean_amount = amount.replace('$', '').replace(',', '')
                     total_funding += float(clean_amount)
                 except:
                     pass
            
            if res.get('start_year'):
                years.append(res.get('start_year'))
                
            if res.get('researcher_name'):
                researchers.add(res.get('researcher_name'))
                
            if res.get('institution_name'):
                institutions.add(res.get('institution_name'))
        
        return {
            'total_funding': total_funding,
            'grant_count': len(results),
            'years_range': f"{min(years)}-{max(years)}" if years else "N/A",
            'unique_researchers': len(researchers),
            'top_institutions': list(institutions)[:3]
        }
