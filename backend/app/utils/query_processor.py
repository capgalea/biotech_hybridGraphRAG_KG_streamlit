from typing import Dict, Any, List
import logging
import math

logger = logging.getLogger(__name__)


class QueryProcessor:
    """Process natural language queries and return structured results"""
    
    def __init__(self, neo4j_handler, llm_handler):
        self.neo4j = neo4j_handler
        self.llm = llm_handler
    
    def process_query(self, natural_query: str, include_search: bool = True) -> dict:
        """
        Process a natural language query through the complete pipeline:
        1. Convert to Cypher using LLM
        2. Execute against Neo4j
        3. Format results
        4. Generate summary and insights
        
        Args:
            natural_query: The natural language query
            include_search: Whether to include Google Search context in summary
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
            summary = self.llm.generate_summary(natural_query, results, include_search)
            
            # Step 6: Extract insights
            insights = self.llm.extract_insights(results)
            

            # Create response
            response = {
                'query': natural_query,
                'cypher': cypher_query,
                'data': formatted_data,
                'raw_results': results,
                'summary': summary,
                'insights': insights,
                'count': len(results)
            }
            
            return self._sanitize_response(response)
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise

    def _sanitize_response(self, data: Any) -> Any:
        """Recursively replace NaN and Inf with None for JSON compliance"""
        if isinstance(data, dict):
            return {k: self._sanitize_response(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_response(item) for item in data]
        elif isinstance(data, float):
            if math.isnan(data) or math.isinf(data):
                return None
        return data
    
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
        Get collaboration network for a researcher (includes both PIs and investigators)
        Uses case-insensitive partial matching for researcher names
        """
        cypher = """
        MATCH (r1:Researcher)-[rel1:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant)
              <-[rel2:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]-(r2:Researcher)
        WHERE r1 <> r2 
          AND toLower(r1.name) CONTAINS toLower($name)
        RETURN r1, r2, g, type(rel1) as r1_role, type(rel2) as r2_role
        """
        
        return self.neo4j.execute_cypher(cypher, {'name': researcher_name})
    
    def get_researcher_suggestions(self, partial_name: str, limit: int = 5) -> List[Dict]:
        """
        Get researcher name suggestions based on partial name match
        """
        cypher = """
        MATCH (r:Researcher) 
        WHERE toLower(r.name) CONTAINS toLower($name)
        RETURN r.name as name 
        LIMIT $limit
        """
        
        return self.neo4j.execute_cypher(cypher, {'name': partial_name, 'limit': limit})
    
    def get_funding_trends(self, start_year: int = 2000, end_year: int = 2024) -> List[Dict]:
        """
        Analyze funding trends over time
        """
        cypher = """
        MATCH (g:Grant)
        WHERE g.start_year >= $start_year AND g.start_year <= $end_year
        AND g.amount IS NOT NULL AND g.amount > 0
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
        WHERE g.amount IS NOT NULL AND g.amount > 0
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
        WHERE g.amount IS NOT NULL AND g.amount > 0
        RETURN a.name as research_area,
               count(g) as grant_count,
               sum(g.amount) as total_funding
        ORDER BY grant_count DESC
        """
        
        return self.neo4j.execute_cypher(cypher)
    
    def get_collaborator_locations(self, researcher_name: str) -> List[Dict]:
        """
        Get locations of collaborators based on their institutions
        """
        # Australian institution coordinates mapping
        institution_coordinates = {
            'University of Melbourne': {'lat': -37.7963, 'lon': 144.9614, 'city': 'Melbourne', 'state': 'VIC'},
            'The University of Melbourne': {'lat': -37.7963, 'lon': 144.9614, 'city': 'Melbourne', 'state': 'VIC'},
            'University of Sydney': {'lat': -33.8886, 'lon': 151.1873, 'city': 'Sydney', 'state': 'NSW'},
            'The University of Sydney': {'lat': -33.8886, 'lon': 151.1873, 'city': 'Sydney', 'state': 'NSW'},
            'University of New South Wales': {'lat': -33.9173, 'lon': 151.2313, 'city': 'Sydney', 'state': 'NSW'},
            'The University of New South Wales': {'lat': -33.9173, 'lon': 151.2313, 'city': 'Sydney', 'state': 'NSW'},
            'University of Queensland': {'lat': -27.4975, 'lon': 153.0137, 'city': 'Brisbane', 'state': 'QLD'},
            'The University of Queensland': {'lat': -27.4975, 'lon': 153.0137, 'city': 'Brisbane', 'state': 'QLD'},
            'Monash University': {'lat': -37.9105, 'lon': 145.1362, 'city': 'Melbourne', 'state': 'VIC'},
            'Australian National University': {'lat': -35.2777, 'lon': 149.1185, 'city': 'Canberra', 'state': 'ACT'},
            'The Australian National University': {'lat': -35.2777, 'lon': 149.1185, 'city': 'Canberra', 'state': 'ACT'},
            'University of Adelaide': {'lat': -34.9205, 'lon': 138.6052, 'city': 'Adelaide', 'state': 'SA'},
            'The University of Adelaide': {'lat': -34.9205, 'lon': 138.6052, 'city': 'Adelaide', 'state': 'SA'},
            'University of Western Australia': {'lat': -31.9775, 'lon': 115.8170, 'city': 'Perth', 'state': 'WA'},
            'The University of Western Australia': {'lat': -31.9775, 'lon': 115.8170, 'city': 'Perth', 'state': 'WA'},
            'University of Tasmania': {'lat': -42.9019, 'lon': 147.3238, 'city': 'Hobart', 'state': 'TAS'},
            'Griffith University': {'lat': -27.5546, 'lon': 153.0526, 'city': 'Brisbane', 'state': 'QLD'},
            'Queensland University of Technology': {'lat': -27.4710, 'lon': 153.0234, 'city': 'Brisbane', 'state': 'QLD'},
            'Deakin University': {'lat': -38.1500, 'lon': 144.3000, 'city': 'Geelong', 'state': 'VIC'},
            'Macquarie University': {'lat': -33.7747, 'lon': 151.1107, 'city': 'Sydney', 'state': 'NSW'},
            'University of Technology Sydney': {'lat': -33.8830, 'lon': 151.2005, 'city': 'Sydney', 'state': 'NSW'},
            'Curtin University': {'lat': -32.0047, 'lon': 115.8950, 'city': 'Perth', 'state': 'WA'},
            'RMIT University': {'lat': -37.8136, 'lon': 144.9631, 'city': 'Melbourne', 'state': 'VIC'},
            'La Trobe University': {'lat': -37.7202, 'lon': 145.0485, 'city': 'Melbourne', 'state': 'VIC'},
            'Flinders University': {'lat': -35.0267, 'lon': 138.5685, 'city': 'Adelaide', 'state': 'SA'},
            'University of Wollongong': {'lat': -34.4054, 'lon': 150.8783, 'city': 'Wollongong', 'state': 'NSW'},
            'James Cook University': {'lat': -19.3286, 'lon': 146.7574, 'city': 'Townsville', 'state': 'QLD'},
            'University of Newcastle': {'lat': -32.8886, 'lon': 151.6947, 'city': 'Newcastle', 'state': 'NSW'},
            'The University of Newcastle': {'lat': -32.8886, 'lon': 151.6947, 'city': 'Newcastle', 'state': 'NSW'},
            'Western Sydney University': {'lat': -33.7616, 'lon': 150.7516, 'city': 'Sydney', 'state': 'NSW'},
            'The University of New England': {'lat': -30.4833, 'lon': 151.6667, 'city': 'Armidale', 'state': 'NSW'},
            'University of South Australia': {'lat': -34.9216, 'lon': 138.5965, 'city': 'Adelaide', 'state': 'SA'},
            'Swinburne University of Technology': {'lat': -37.8226, 'lon': 145.0397, 'city': 'Melbourne', 'state': 'VIC'},
            'Victoria University': {'lat': -37.7472, 'lon': 144.8942, 'city': 'Melbourne', 'state': 'VIC'},
            'Edith Cowan University': {'lat': -31.8456, 'lon': 115.8466, 'city': 'Perth', 'state': 'WA'},
            'Murdoch University': {'lat': -32.0686, 'lon': 115.8373, 'city': 'Perth', 'state': 'WA'},
            'Charles Sturt University': {'lat': -33.3648, 'lon': 147.0649, 'city': 'Bathurst', 'state': 'NSW'},
            'Bond University': {'lat': -28.0739, 'lon': 153.4285, 'city': 'Gold Coast', 'state': 'QLD'},
            'University of the Sunshine Coast': {'lat': -26.7122, 'lon': 153.0773, 'city': 'Sunshine Coast', 'state': 'QLD'},
            'Southern Cross University': {'lat': -28.7870, 'lon': 153.4615, 'city': 'Lismore', 'state': 'NSW'},
            'Charles Darwin University': {'lat': -12.3714, 'lon': 130.8748, 'city': 'Darwin', 'state': 'NT'},
            'Australian Catholic University': {'lat': -33.8688, 'lon': 151.2093, 'city': 'Sydney', 'state': 'NSW'},
            'University of Canberra': {'lat': -35.2386, 'lon': 149.0906, 'city': 'Canberra', 'state': 'ACT'}
        }
        
        cypher = """
        MATCH (r1:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant)
              <-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]-(r2:Researcher)
        MATCH (g)-[:HOSTED_BY]->(i:Institution)
        WHERE r1 <> r2 
          AND toLower(r1.name) CONTAINS toLower($name)
        RETURN DISTINCT r2.name as collaborator, i.name as institution, 
               count(g) as collaboration_count
        ORDER BY collaboration_count DESC
        """
        
        results = self.neo4j.execute_cypher(cypher, {'name': researcher_name})
        
        # Add coordinates to results
        locations = []
        for result in results:
            institution = result.get('institution', '')
            collaborator = result.get('collaborator', '')
            count = result.get('collaboration_count', 0)
            
            # Try to find coordinates for the institution
            coords = None
            for inst_name, coord_data in institution_coordinates.items():
                if inst_name.lower() in institution.lower() or institution.lower() in inst_name.lower():
                    coords = coord_data
                    break
            
            if coords:
                locations.append({
                    'collaborator': collaborator,
                    'institution': institution,
                    'collaboration_count': count,
                    'latitude': coords['lat'],
                    'longitude': coords['lon'],
                    'city': coords['city'],
                    'state': coords['state']
                })
        
        return locations
