"""
BioMCP Integration for PubMed Article Retrieval
This module provides functions to search PubMed for articles related to researchers
"""
import subprocess
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class BioMCPClient:
    """Client for interacting with BioMCP to retrieve PubMed articles"""
    
    def __init__(self):
        self.available = self._check_biomcp_available()
    
    def _check_biomcp_available(self) -> bool:
        """Check if biomcp is installed and available"""
        try:
            result = subprocess.run(
                ["biomcp", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info("BioMCP is available")
                return True
            return False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("BioMCP not found. Install with: uv tool install biomcp")
            return False
    
    def search_pubmed_by_researcher(self, researcher_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search PubMed for articles by a specific researcher
        
        Args:
            researcher_name: Name of the researcher
            limit: Maximum number of articles to return
            
        Returns:
            List of article dictionaries with title, authors, journal, year, pmid, abstract
        """
        if not self.available:
            logger.warning("BioMCP not available, skipping PubMed search")
            return []
        
        try:
            # Extract last name for better search results
            name_parts = researcher_name.strip().split()
            if len(name_parts) >= 2:
                # Use last name and first initial
                last_name = name_parts[-1]
                first_initial = name_parts[0][0] if name_parts[0] else ""
                search_query = f"{last_name} {first_initial}[Author]"
            else:
                search_query = f"{researcher_name}[Author]"
            
            # Use biomcp CLI to search articles
            cmd = [
                "biomcp", "article", "search",
                "--query", search_query,
                "--limit", str(limit),
                "--format", "json"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                articles = json.loads(result.stdout)
                return self._format_articles(articles)
            else:
                logger.error(f"BioMCP search failed: {result.stderr}")
                return []
                
        except subprocess.TimeoutExpired:
            logger.error("BioMCP search timed out")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse BioMCP response: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching PubMed: {e}")
            return []
    
    def _format_articles(self, articles: List[Dict]) -> List[Dict[str, Any]]:
        """Format articles into a consistent structure"""
        formatted = []
        for article in articles:
            formatted.append({
                'title': article.get('title', ''),
                'authors': article.get('authors', []),
                'journal': article.get('journal', ''),
                'year': article.get('year', ''),
                'pmid': article.get('pmid', ''),
                'abstract': article.get('abstract', ''),
                'doi': article.get('doi', '')
            })
        return formatted
    
    def format_article_citation(self, article: Dict[str, Any]) -> str:
        """
        Format article in scientific journal citation style
        
        Args:
            article: Article dictionary
            
        Returns:
            Formatted citation string
        """
        authors = article.get('authors', [])
        if isinstance(authors, list) and len(authors) > 0:
            if len(authors) == 1:
                author_str = authors[0]
            elif len(authors) == 2:
                author_str = f"{authors[0]} and {authors[1]}"
            elif len(authors) > 2:
                # First author et al.
                author_str = f"{authors[0]} et al."
        else:
            author_str = "Unknown"
        
        title = article.get('title', 'Untitled')
        journal = article.get('journal', '')
        year = article.get('year', '')
        pmid = article.get('pmid', '')
        doi = article.get('doi', '')
        
        # Format: Authors. Title. Journal. Year. PMID: xxx. DOI: xxx
        citation = f"{author_str}. {title}. "
        if journal:
            citation += f"*{journal}*. "
        if year:
            citation += f"{year}. "
        if pmid:
            citation += f"PMID: [{pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/). "
        if doi:
            citation += f"DOI: {doi}"
        
        return citation.strip()
