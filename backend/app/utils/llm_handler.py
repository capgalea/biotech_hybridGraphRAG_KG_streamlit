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
14. DO NOT query non-existent fields like g.start_date, r.title, g.agency, g.end_year - use only the actual properties listed above

Example queries using ONLY actual database properties (always return comprehensive grant information from the 20 most recent grants):
- For "grants about cancer": MATCH (g:Grant) OPTIONAL MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g) OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution) WHERE g.title CONTAINS 'cancer' OR g.description CONTAINS 'cancer' WITH g.title as grant_title, g.grant_status as status, g.amount as amount, g.description as description, g.start_year as start_year, g.end_date as end_date, g.grant_type as grant_type, g.funding_body as funding_body, g.broad_research_area as broad_research_area, g.field_of_research as field_of_research, g.application_id as application_id, g.date_announced as date_announced, collect(DISTINCT r.name)[0] as researcher_name, collect(DISTINCT r.orcid_id)[0] as researcher_orcid, collect(DISTINCT i.name)[0] as institution_name RETURN DISTINCT grant_title, status, amount, description, start_year, end_date, grant_type, funding_body, broad_research_area, field_of_research, application_id, date_announced, researcher_name, researcher_orcid as orcid_id, institution_name ORDER BY start_year DESC LIMIT 20
- For "grants for Glenn King": MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant) WHERE (toLower(r.name) = 'glenn king' OR toLower(r.name) = 'king, glenn' OR toLower(r.name) = 'dr glenn king' OR toLower(r.name) = 'prof glenn king') OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution) WITH g.title as grant_title, g.grant_status as status, g.amount as amount, g.description as description, g.start_year as start_year, g.end_date as end_date, g.grant_type as grant_type, g.funding_body as funding_body, g.broad_research_area as broad_research_area, g.field_of_research as field_of_research, g.application_id as application_id, g.date_announced as date_announced, collect(DISTINCT r.name)[0] as researcher_name, collect(DISTINCT r.orcid_id)[0] as researcher_orcid, collect(DISTINCT i.name)[0] as institution_name RETURN DISTINCT grant_title, status, amount, description, start_year, end_date, grant_type, funding_body, broad_research_area, field_of_research, application_id, date_announced, researcher_name, researcher_orcid as orcid_id, institution_name ORDER BY start_year DESC LIMIT 20
- For "all grants": MATCH (g:Grant) OPTIONAL MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g) OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution) WITH g.title as grant_title, g.grant_status as status, g.amount as amount, g.description as description, g.start_year as start_year, g.end_date as end_date, g.grant_type as grant_type, g.funding_body as funding_body, g.broad_research_area as broad_research_area, g.field_of_research as field_of_research, g.application_id as application_id, g.date_announced as date_announced, collect(DISTINCT r.name)[0] as researcher_name, collect(DISTINCT r.orcid_id)[0] as researcher_orcid, collect(DISTINCT i.name)[0] as institution_name RETURN DISTINCT grant_title, status, amount, description, start_year, end_date, grant_type, funding_body, broad_research_area, field_of_research, application_id, date_announced, researcher_name, researcher_orcid as orcid_id, institution_name ORDER BY start_year DESC LIMIT 20

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
            MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant)
            OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution)
            WITH g.title as grant_title, g.amount as amount, g.start_year as start_year, g.description as description, g.funding_body as funding_body,
                 collect(DISTINCT r.name)[0] as researcher_name, collect(DISTINCT i.name)[0] as institution_name
            RETURN DISTINCT grant_title, amount, start_year, description, funding_body,
                   researcher_name as researcher, institution_name as institution
            ORDER BY start_year DESC
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
            
    def _get_related_papers_html(self, title: str, grant_id: str = None, funder: str = None, pi_name: str = None, start_year: int = None) -> str:
        """Helper to fetch related papers from OpenAlex using Targeted Prompt (ID + Funder + PI) or Title, filtering by start_year"""
        try:
            import requests
            import urllib.parse
            
            logger.info(f"Searching OpenAlex. Title: {title}, ID: {grant_id}, Funder: {funder}, PI: {pi_name}, Start Year: {start_year}")
            
            p_results = []
            
            # 1. Targeted Search: Grant ID + PI (Extremely Precise)
            if grant_id:
                # Clean ID: OpenAlex IDs usually don't have spaces, but might have prefixes.
                # User's ID might be "APP12345" or "12345".
                clean_id = grant_id.strip()
                
                # Strategy A: Strict Filter on Award ID + Author Name
                if pi_name:
                    try:
                        # filter=grants.award_id:X,authorships.author.display_name:Y
                        # Note: OpenAlex filters use comma for AND.
                        pi_term = f"authorships.author.display_name:{pi_name}"
                        grant_term = f"grants.award_id:{clean_id}"
                        url = f"https://api.openalex.org/works?filter={grant_term},{pi_term}&per-page=3"
                        resp = requests.get(url, timeout=4)
                        if resp.status_code == 200:
                            p_results = resp.json().get('results', [])
                            if p_results:
                                logger.info(f"Found {len(p_results)} papers via Strict Filter (ID+PI)")
                    except Exception as e:
                        logger.warning(f"Strict filter failed: {e}")

                # Strategy B: Strict Filter on Award ID only (if A failed or no PI)
                if not p_results:
                    try:
                        grant_term = f"grants.award_id:{clean_id}"
                        url = f"https://api.openalex.org/works?filter={grant_term}&per-page=3"
                        resp = requests.get(url, timeout=4)
                        if resp.status_code == 200:
                            p_results = resp.json().get('results', [])
                            if p_results:
                                logger.info(f"Found {len(p_results)} papers via Grant ID Filter")
                    except:
                        pass
                
                # Strategy C: Full Text Search for Grant ID (Fallback)
                if not p_results:
                     try:
                        # Quote the ID to ensure it's treated as a phrase token if it has spaces/hyphens
                        query = f'"{clean_id}"'
                        if funder:
                             # Adding funder name helps disambiguate short IDs
                             query += f' {funder}'
                        
                        safe_query = urllib.parse.quote(query)
                        url = f"https://api.openalex.org/works?search={safe_query}&per-page=3"
                        resp = requests.get(url, timeout=4)
                        if resp.status_code == 200:
                            p_results = resp.json().get('results', [])
                            if p_results:
                                logger.info(f"Found {len(p_results)} papers via Grant ID Search")
                     except:
                        pass

            # 2. Fallback: Title Search (ONLY if Grant ID was not provided/found)
            # If we have a Grant ID, strict search rules apply: only return papers linked to that ID.
            if not grant_id and not p_results and title:
                try:
                    if pi_name:
                        # Use Filter: Title Search AND Author Name
                        # This avoids finding papers with same title but different authors
                        safe_title = title.replace(",", " ") # Remove commas for filter syntax
                        url = f"https://api.openalex.org/works?filter=title.search:{safe_title},authorships.author.display_name:{pi_name}&per-page=3"
                    else:
                        safe_title = urllib.parse.quote(title)
                        url = f"https://api.openalex.org/works?search={safe_title}&per-page=3"
                        
                    resp = requests.get(url, timeout=3)
                    if resp.status_code == 200:
                        data = resp.json()
                        if not p_results: 
                             p_results = data.get('results', [])
                except:
                   pass
                
            if p_results:
                # 1. Filter by PI Name (if provided)
                if pi_name:
                    # Clean PI name for matching (e.g. "Glenn F. King" -> "King")
                    # We'll use a loose surname match or exact full string check
                    # Strategy: Split PI name, match last name against author display names
                    pi_parts = pi_name.replace(".", "").split()
                    pi_surname = pi_parts[-1].lower() if pi_parts else ""
                    
                    if pi_surname:
                        pi_filtered = []
                        for work in p_results:
                            authors = work.get('authorships', [])
                            # Check if ANY author matches the PI surname
                            is_match = False
                            for auth_entry in authors:
                                author_name = auth_entry.get('author', {}).get('display_name', '').lower()
                                if pi_surname in author_name:
                                    # Optional: Check first initial if available
                                    is_match = True
                                    break
                            
                            if is_match:
                                pi_filtered.append(work)
                        
                        if not pi_filtered and p_results:
                             logger.info(f"Filtered out {len(p_results)} papers due to PI mismatch (PI: {pi_name})")
                        
                        p_results = pi_filtered

                # 2. Filter by publication year if start_year is provided
                if start_year:
                    # Allow papers from the same year or later. 
                    filtered_results = []
                    for work in p_results:
                         pub_year = work.get('publication_year')
                         if pub_year and pub_year >= start_year:
                             filtered_results.append(work)
                    
                    if not filtered_results and p_results:
                        logger.info(f"Filtered out {len(p_results)} papers due to invalid year (Start: {start_year})")
                    
                    p_results = filtered_results

            if p_results:
                label = "Research Output (Directly Linked to Grant)" if grant_id else "Related Research Papers (Title Match)"
                html = f"<br><br><details class='bg-blue-50 p-2 rounded border border-blue-100 text-sm mt-1'><summary class='cursor-pointer font-semibold text-blue-700 hover:text-blue-900'>📚 {label}</summary><ul class='list-disc pl-5 mt-2 space-y-1'>"
                for work in p_results:
                    w_title = work.get('title') or "Untitled Work"
                    # Prefer DOI link, then ID
                    link = work.get('doi') or work.get('id') or "#"
                    
                    # Add publication year if available
                    year = work.get('publication_year', '')
                    year_str = f" ({year})" if year else ""
                    
                    html += f"<li><a href='{link}' target='_blank' class='text-blue-600 hover:underline'>{w_title}</a>{year_str}</li>"
                html += "</ul></details>"
                return html
            else:
                 return "<br><span class='text-xs text-gray-400 italic mt-1 block ml-4'>— No directly derived papers found. —</span>"
        except Exception as e:
            logger.error(f"OpenAlex Error: {str(e)}")
            return ""
    
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
        
        # Get additional context using BioMCP (PubMed) if researchers are found
        pubmed_context = ""
        pubmed_articles = []
        
        # Extract researcher names from results to search PubMed
        researchers_to_search = set()
        for res in sample_results:
            if isinstance(res, dict):
                r_name = res.get('researcher') or res.get('r.name') or res.get('pi_name') or res.get('researcher_name')
                if r_name:
                    researchers_to_search.add(r_name)
        
        # Search PubMed for the first 1-2 researchers found
        if researchers_to_search and self.biomcp.available:
            for researcher in list(researchers_to_search)[:2]:
                logger.info(f"Searching PubMed for researcher: {researcher}")
                articles = self.biomcp.search_pubmed_by_researcher(researcher, limit=3)
                if articles:
                    pubmed_articles.extend(articles)
        
        if pubmed_articles:
            pubmed_context = "\n\n### Relevant PubMed Articles (via BioMCP):\n"
            for article in pubmed_articles:
                citation = self.biomcp.format_article_citation(article)
                pubmed_context += f"- {citation}\n"
                if article.get('abstract'):
                    pubmed_context += f"  Abstract: {article['abstract'][:200]}...\n"

        # Web search context (only if enabled and BioMCP didn't yield enough, or as supplement)
        search_context = ""
        if include_search:
             # Create enhanced search query based on actual database results
            enhanced_query = self._create_enhanced_search_query(query, sample_results)
            search_results = self._search_google(enhanced_query, num_results=3)
            
            if search_results:
                search_context = "\n\n### Additional Web Context:\n"
                for i, result in enumerate(search_results, 1):
                    search_context += f"Search Result {i}: {result['title']}\n"
                    if result.get('scraped_summary'):
                        search_context += f"LLM Summary: {result['scraped_summary']}\n"
                    elif result.get('snippet'):
                        search_context += f"Snippet: {result['snippet']}\n"
                    search_context += f"Source: {result['link']}\n\n"
        
        prompt = f"""Analyze the following biotech/medical research database query results and provide a structured summary.

Original Query: {query}
Total Results Found: {total_results}

Sample Database Results:
{results_text}

{pubmed_context}
{search_context}

Create a summary using ONLY the following headers and format. This format is MANDATORY for all grant-related queries:

## Title
A title closely matching the 'Original Query' (e.g., "Grant Analysis: [User's Query]"). Format the content line as a blockquote, starting with '> '.

## Overview
Provide a brief biography of the researcher(s) involved and a summary of their overall research focus, utilizing available web search context if provided. Focus on their scientific contributions and expertise.

## Grants
List the key grants found with a short description for each. Use the format:
1. **Grant Title** (ID: [Grant Application ID], Funder: [Funding Body Name], $Amount, Year): Short description of the grant's purpose. ([Google Scholar](https://scholar.google.com/scholar?q=keywords%20from%20title%20and%20description))

Ensure the keywords in the Google Scholar link are a combination of significant terms from both the title and the description.

## Key Research Themes
Identify the major research areas and methodologies.

IMPORTANT:
- YOU MUST FOLLOW THIS FORMAT EXACTLY.
- Use proper number formatting for currency (e.g., $1,200,000).
- Be accurate about the data provided.
- Do not make up external references; use the provided context.
"""

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
                return self._generate_fallback_summary(query, results, include_search)
            
            # Post-process summary to inject OpenAlex papers for grants
            try:
                import re
                lines = summary.split('\n')
                new_lines = []
                for line in lines:
                    new_lines.append(line)
                    # Match pattern: "1. **Grant Title**" or "1. Grant Title ("
                    # Capture title content. Handles bolding optional.
                    match = re.search(r'^\d+\.\s*(?:\*\*)?\s*(.*?)\s*(?:\*\*)?(?:\s*\(|\s*:| - |$)', line)
                    if match:
                        title = match.group(1).strip()
                        
                        # Try to find the matching grant object in `results` to get precise ID and PI
                        matched_grant = None
                        for g in results:
                            # Loose title matching
                            g_title = g.get('title', '')
                            # Check if fuzzy match (one contains the other)
                            if g_title and (g_title.lower() in title.lower() or title.lower() in g_title.lower()):
                                matched_grant = g
                                break
                        
                        grant_id = None
                        funder = None
                        pi_name = None
                        start_year = None
                        
                        if matched_grant:
                            grant_id = matched_grant.get('application_id')
                            funder = matched_grant.get('funding_body')
                            pi_name = matched_grant.get('pi_name')
                            try:
                                start_year = int(matched_grant.get('start_year'))
                            except:
                                pass
                        else:
                            # Fallback to Regex extraction
                            id_match = re.search(r'ID:\s*([^,)]+)', line)
                            funder_match = re.search(r'Funder:\s*([^,)]+)', line)
                            year_match = re.search(r'Year:\s*(\d{4})', line)
                            if id_match: grant_id = id_match.group(1).strip()
                            if funder_match: funder = funder_match.group(1).strip()
                            if year_match: start_year = int(year_match.group(1))

                        if len(title) > 5:
                            papers_html = self._get_related_papers_html(title, grant_id, funder, pi_name, start_year)
                            if papers_html:
                                # Insert after the line
                                new_lines.append(papers_html)
                
                summary = '\n'.join(new_lines)
            except Exception as e:
                logger.error(f"Error injecting papers into summary: {e}")
            
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
        
        # Title section
        summary_parts.append(f"## Title")
        summary_parts.append(f"> Grant Analysis: {query}")
        summary_parts.append("")
        
        # Overview/Stats
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
                                'year': str(year).strip(),
                                'application_id': result.get('application_id'), # Add application_id
                                'funding_body': result.get('funding_body'), # Add funding_body
                                'pi_name': result.get('pi_name') # Add pi_name
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
            
            # Overview Section
            summary_parts.append(f"\n\n## Overview")
            overview_text = "This analysis covers research conducted"
            if researchers:
                researcher_list = ', '.join(list(researchers)[:3])
                if len(researchers) > 3:
                    researcher_list += f" and {len(researchers) - 3} others"
                overview_text += f" by **{researcher_list}**"
            
            if institutions:
                inst_list = ', '.join(list(institutions)[:2])
                if len(institutions) > 2:
                    inst_list += f" and {len(institutions) - 2} other institutions"
                overview_text += f" at **{inst_list}**"
            
            overview_text += "."
            summary_parts.append(overview_text)

            # Grant Portfolio section with actual grants
            summary_parts.append(f"\n\n## Grants")
            if grants_data:
                summary_parts.append(f"The portfolio includes {len(grants_data)} research grants:\n")
                
                # Show top 5 grants with details
                for i, grant in enumerate(grants_data[:5]):
                    grant_title = grant['title'][:80] + "..." if len(grant['title']) > 80 else grant['title']
                    
                    # Create better keywords for search: Title + Researcher + Institution
                    description = str(grant.get('description', ''))
                    
                    # 1. Use cleaned title words
                    stopwords = {'the', 'and', 'for', 'with', 'from', 'into', 'study', 'research', 'analysis', 'project', 'grant', 'funding', 'investigation', 'development', 'characterisation', 'understanding', 'role', 'mechanism', 'using'}
                    title_words = [w for w in grant['title'].split() if w.lower().strip(".,()[]:-") not in stopwords and len(w) > 3]
                    search_terms = title_words[:6]
                    
                    # 2. Add Researcher Name
                    if grant.get('researcher'):
                        search_terms.append(str(grant['researcher']))
                        
                    # 3. Add Institution Name
                    if grant.get('institution'):
                        search_terms.append(str(grant['institution']))
                        
                    search_query = "+".join(search_terms).replace(" ", "+")
                    
                    grant_info = f"{i+1}. **{grant_title}**"
                    
                    # Update Fallback logic to include ID/Funder in text too, so parsing is consistent if needed, or just standard display
                    # Actually, for fallback we build grant_info directly, so we can pass ID to _get_related_papers_html later or append now.
                    # Let's keep display standard but use the data for the search.
                    
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
                    
                    # Add Google Scholar Link
                    grant_info += f" ([Google Scholar](https://scholar.google.com/scholar?q={search_query}))"

                    # Add Related Papers (via Semantic Scholar)
                    # Add Related Papers (via OpenAlex)
                    try:
                        import requests
                        import urllib.parse
                        
                        logger.info(f"Searching OpenAlex for: {grant_title}")
                        
                        # 1. Try Title Search
                        safe_title = urllib.parse.quote(grant['title'])
                        url = f"https://api.openalex.org/works?search={safe_title}&per-page=3"
                        
                        resp = requests.get(url, timeout=10)
                        p_results = []
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            p_results = data.get('results', [])
                            
                        # 2. Key Term Fallback if Title failed
                        if not p_results:
                            logger.info("Title search failed. Trying keywords.")
                            # Use top 4 keywords + "research" to ground it
                            joined_terms = " ".join(search_terms[:4])
                            safe_terms = urllib.parse.quote(joined_terms)
                            url = f"https://api.openalex.org/works?search={safe_terms}&per-page=3"
                            resp = requests.get(url, timeout=10)
                            if resp.status_code == 200:
                                p_results = resp.json().get('results', [])

                        # Build HTML
                        if p_results:
                            grant_info += "<br><br><details class='bg-blue-50 p-2 rounded border border-blue-100 text-sm mt-1'><summary class='cursor-pointer font-semibold text-blue-700 hover:text-blue-900'>📚 Related Research Papers (OpenAlex)</summary><ul class='list-disc pl-5 mt-2 space-y-1'>"
                            for work in p_results:
                                title = work.get('title') or "Untitled Work"
                                # Prefer DOI link, then ID
                                link = work.get('doi') or work.get('id') or "#"
                                grant_info += f"<li><a href='{link}' target='_blank' class='text-blue-600 hover:underline'>{title}</a></li>"
                            grant_info += "</ul></details>"
                        else:
                            # Explicitly show zero results for debugging confidence
                            grant_info += "<br><span class='text-xs text-gray-400 italic mt-1 block ml-4'>— No related public papers found. —</span>"

                    except Exception as e:
                        logger.error(f"OpenAlex Error: {str(e)}")
                        grant_info += f"<br><span class='text-xs text-red-400'>Error loading papers.</span>"
                    
                    # Add Related Papers (via OpenAlex)
                    # Use fallback data directly
                    gid = str(grant.get('application_id', ''))
                    funder_name = str(grant.get('funding_body', ''))
                    pi_name = str(grant.get('pi_name', ''))
                    start_year = None
                    try:
                        start_year = int(grant.get('start_year'))
                    except:
                        pass
                    
                    papers_html = self._get_related_papers_html(grant['title'], gid, funder_name, pi_name, start_year)
                    if papers_html:
                         grant_info += papers_html
                    
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
            
            summary_parts.append(f"Database search identified **{count}** relevant records with comprehensive grant and researcher information.")
            
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

    def process_query(self, prompt: str, **kwargs) -> str:
        """
        Process a general query/prompt with the selected LLM
        Args:
            prompt: The prompt/query to process
            **kwargs: Additional parameters (for compatibility)
        Returns:
            str: The LLM response
        """
        if not self.client:
            return "LLM client not available. Please check your configuration."

        try:
            if "claude" in self.model_name.lower():
                # Claude API
                if hasattr(self.client, 'messages'):
                    # Anthropic client (newer versions)
                    response = self.client.messages.create(
                        model=self.model_id,
                        max_tokens=8000,
                        temperature=0.7,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return response.content[0].text
                else:
                    # Older Anthropic client
                    response = self.client.completions.create(
                        model=self.model_id,
                        prompt=f"\n\nHuman: {prompt}\n\nAssistant:",
                        max_tokens_to_sample=8000,
                        temperature=0.7
                    )
                    return response.completion

            elif "gpt" in self.model_name.lower():
                response = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=8000,
                    temperature=0.7
                )
                return response.choices[0].message.content

            elif "gemini" in self.model_name.lower():
                model = genai.GenerativeModel(self.model_id)
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=8000,
                        temperature=0.7
                    )
                )
                return response.text

            elif "deepseek" in self.model_name.lower():
                response = self.client.chat.completions.create(
                    model=self.model_id,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=8000,
                    temperature=0.7
                )
                return response.choices[0].message.content

            else:
                return f"Unsupported model: {self.model_name}"

        except Exception as e:
            logger.error(f"Error processing query with {self.model_name}: {str(e)}")
            return f"Error processing query: {str(e)}"

    def _get_model_id(self) -> str:
        """Get the actual model ID for API calls"""
        model_mapping = {
            "Claude 4.5 Sonnet": "claude-sonnet-4-5",
            "Claude 3.7 Sonnet": "claude-3-7-sonnet-20250219",
            "Claude 3.5 Sonnet": "claude-3-5-sonnet-latest",
            "GPT-4o": "gpt-4o",
            "GPT-4o Mini": "gpt-4o-mini",
            "Gemini 2.0 Flash": "gemini-2.0-flash",
            "DeepSeek R1": "deepseek-reasoner",
            "DeepSeek V3": "deepseek/deepseek-v3.2"
        }
        return model_mapping.get(self.model_name, "claude-sonnet-4-5")
