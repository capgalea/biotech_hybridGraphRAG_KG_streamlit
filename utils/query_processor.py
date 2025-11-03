from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class QueryProcessor:
    """Process natural language queries and return structured results"""
    
    def __init__(self, neo4j_handler, llm_handler):
        self.neo4j = neo4j_handler
        self.llm = llm_handler
    
    def process_query(self, natural_query: str) -> Dict[str, Any]:
        """
        Process a natural language query through the full pipeline:
        1. Get schema
        2. Generate Cypher
        3. Execute query
        4. Generate summary and insights
        """
        try:
            # Step 1: Get schema
            schema_text = self.neo4j.get_schema_text()
            
            # Step 2: Generate Cypher query
            cypher_query = self.llm.generate_cypher(natural_query, schema_text)
            
            # Step 3: Execute query
            results = self.neo4j.execute_cypher(cypher_query)
            
            # Step 4: Format results for display
            formatted_data = self._format_results(results)
            
            # Step 5: Generate summary
            summary = self.llm.generate_summary(natural_query, results)
            
            # Step 6: Extract insights
            insights = self.llm.extract_insights(results)
            
            return {
                'query': natural_query,
                'cypher': cypher_query,
                'data': formatted_data,
                'raw_results': results,
                'summary': summary,
                'insights': insights,
                'count': len(results)
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise
    
    def _format_results(self, results: List[Dict]) -> List[Dict]:
        """
        Format Neo4j results into clean dictionaries for display
        """
        formatted = []
        
        for record in results:
            row = {}
            
            for key, value in record.items():
                if isinstance(value, dict):
                    # Flatten nested dictionaries
                    for sub_key, sub_value in value.items():
                        row[f"{key}_{sub_key}"] = sub_value
                else:
                    row[key] = value
            
            formatted.append(row)
        
        return formatted
    
    def validate_cypher(self, cypher: str) -> bool:
        """
        Basic validation of Cypher query
        """
        # Check for dangerous operations
        dangerous_keywords = ['DELETE', 'DROP', 'CREATE CONSTRAINT', 'CREATE INDEX']
        cypher_upper = cypher.upper()
        
        for keyword in dangerous_keywords:
            if keyword in cypher_upper:
                logger.warning(f"Dangerous keyword detected: {keyword}")
                return False
        
        return True
    
    def enhance_query_with_context(self, query: str) -> str:
        """
        Enhance the query with contextual information
        """
        # Add common synonyms and related terms
        enhancements = {
            'cancer': 'cancer OR oncology OR carcinogenesis OR tumor OR tumour',
            'heart': 'heart OR cardiac OR cardiovascular',
            'brain': 'brain OR neurological OR neuroscience',
            'diabetes': 'diabetes OR metabolic',
        }
        
        enhanced_query = query
        for term, expansion in enhancements.items():
            if term.lower() in query.lower():
                enhanced_query = enhanced_query.replace(term, expansion)
        
        return enhanced_query
    
    def get_similar_grants(self, grant_id: int, limit: int = 5) -> List[Dict]:
        """
        Find similar grants based on research area and keywords
        """
        cypher = """
        MATCH (g1:Grant {application_id: $id})-[:IN_AREA]->(a:ResearchArea)<-[:IN_AREA]-(g2:Grant)
        WHERE g1 <> g2
        RETURN g2, a
        LIMIT $limit
        """
        
        return self.neo4j.execute_cypher(cypher, {'id': grant_id, 'limit': limit})
    
    def get_collaboration_network(self, researcher_name: str) -> List[Dict]:
        """
        Get collaboration network for a researcher
        """
        cypher = """
        MATCH (r1:Researcher {name: $name})-[:PRINCIPAL_INVESTIGATOR]->(g:Grant)
              <-[:PRINCIPAL_INVESTIGATOR]-(r2:Researcher)
        WHERE r1 <> r2
        RETURN r1, r2, g
        """
        
        return self.neo4j.execute_cypher(cypher, {'name': researcher_name})
    
    def get_funding_trends(self, start_year: int, end_year: int) -> List[Dict]:
        """
        Analyze funding trends over time
        """
        cypher = """
        MATCH (g:Grant)
        WHERE g.start_year >= $start_year AND g.start_year <= $end_year
        RETURN g.start_year as year, 
               count(g) as grant_count,
               sum(g.amount) as total_funding,
               avg(g.amount) as avg_funding
        ORDER BY year
        """
        
        return self.neo4j.execute_cypher(cypher, {
            'start_year': start_year,
            'end_year': end_year
        })
    
    def get_top_institutions(self, limit: int = 10) -> List[Dict]:
        """
        Get top institutions by funding
        """
        cypher = """
        MATCH (g:Grant)-[:HOSTED_BY]->(i:Institution)
        RETURN i.name as institution,
               count(g) as grant_count,
               sum(g.amount) as total_funding
        ORDER BY total_funding DESC
        LIMIT $limit
        """
        
        return self.neo4j.execute_cypher(cypher, {'limit': limit})
    
    def get_research_area_distribution(self) -> List[Dict]:
        """
        Get distribution of grants across research areas
        """
        cypher = """
        MATCH (g:Grant)-[:IN_AREA]->(a:ResearchArea)
        RETURN a.name as research_area,
               count(g) as grant_count,
               sum(g.amount) as total_funding
        ORDER BY grant_count DESC
        """
        
        return self.neo4j.execute_cypher(cypher)
