from neo4j import GraphDatabase
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jHandler:
    """Handler for Neo4j database operations"""
    
    def __init__(self, uri: str, user: str, password: str):
        """Initialize Neo4j connection"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.verify_connection()
    
    def verify_connection(self):
        """Verify database connection"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            logger.info("Neo4j connection successful")
        except Exception as e:
            logger.error(f"Neo4j connection failed: {str(e)}")
            raise
    
    def close(self):
        """Close the driver connection"""
        if self.driver:
            self.driver.close()
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get database schema information
        Returns node labels, relationship types, and properties
        """
        with self.driver.session() as session:
            # Get node labels
            node_result = session.run("CALL db.labels()")
            node_labels = [record["label"] for record in node_result]
            
            # Get relationship types
            rel_result = session.run("CALL db.relationshipTypes()")
            relationships = [record["relationshipType"] for record in rel_result]
            
            # Get property keys
            prop_result = session.run("CALL db.propertyKeys()")
            properties = [record["propertyKey"] for record in prop_result]
            
            return {
                "node_labels": node_labels,
                "relationships": relationships,
                "properties": properties
            }
    
    def get_schema_text(self) -> str:
        """
        Get schema as formatted text for LLM context
        """
        schema = self.get_schema()
        
        text = "Neo4j Graph Schema:\n\n"
        text += "Node Labels:\n"
        for label in schema['node_labels']:
            text += f"  - {label}\n"
        
        text += "\nRelationship Types:\n"
        for rel in schema['relationships']:
            text += f"  - {rel}\n"
        
        text += "\nCommon Properties:\n"
        for prop in schema['properties'][:20]:  # Limit to first 20
            text += f"  - {prop}\n"
        
        # Add sample queries
        text += "\nSample Query Patterns:\n"
        text += "  - MATCH (g:Grant) RETURN g\n"
        text += "  - MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR]->(g:Grant) RETURN r, g\n"
        text += "  - MATCH (g:Grant)-[:HOSTED_BY]->(i:Institution) RETURN g, i\n"
        
        return text
    
    def execute_cypher(self, query: str, parameters: Dict = None) -> List[Dict]:
        """
        Execute a Cypher query and return results as list of dictionaries
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                records = []
                for record in result:
                    record_dict = {}
                    for key in record.keys():
                        value = record[key]
                        # Convert Neo4j nodes/relationships to dictionaries
                        if hasattr(value, '__dict__'):
                            record_dict[key] = dict(value)
                        elif hasattr(value, '_properties'):
                            record_dict[key] = dict(value._properties)
                        else:
                            record_dict[key] = value
                    records.append(record_dict)
                return records
        except Exception as e:
            logger.error(f"Cypher execution error: {str(e)}")
            logger.error(f"Query: {query}")
            raise
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        stats = {}
        
        with self.driver.session() as session:
            # Count grants
            result = session.run("MATCH (g:Grant) RETURN count(g) as count")
            stats['grants'] = result.single()['count']
            
            # Count researchers
            result = session.run("MATCH (r:Researcher) RETURN count(r) as count")
            stats['researchers'] = result.single()['count']
            
            # Count institutions
            result = session.run("MATCH (i:Institution) RETURN count(i) as count")
            stats['institutions'] = result.single()['count']
            
            # Count relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            stats['relationships'] = result.single()['count']
        
        return stats
    
    def vector_search(self, query_embedding: List[float], limit: int = 10) -> List[Dict]:
        """
        Perform vector similarity search
        Requires vector index to be created on Grant nodes
        """
        cypher = """
        CALL db.index.vector.queryNodes('grant_embeddings', $limit, $embedding)
        YIELD node, score
        RETURN node, score
        ORDER BY score DESC
        """
        
        try:
            return self.execute_cypher(cypher, {
                'embedding': query_embedding,
                'limit': limit
            })
        except Exception as e:
            logger.warning(f"Vector search failed: {str(e)}")
            return []
    
    def hybrid_search(self, query_embedding: List[float], 
                     cypher_filter: str = None, limit: int = 10) -> List[Dict]:
        """
        Perform hybrid search combining vector similarity and graph traversal
        """
        if cypher_filter:
            # Combine vector search with Cypher filtering
            cypher = f"""
            CALL db.index.vector.queryNodes('grant_embeddings', $limit * 3, $embedding)
            YIELD node, score
            WITH node, score
            WHERE {cypher_filter}
            RETURN node, score
            ORDER BY score DESC
            LIMIT $limit
            """
        else:
            # Just vector search
            cypher = """
            CALL db.index.vector.queryNodes('grant_embeddings', $limit, $embedding)
            YIELD node, score
            RETURN node, score
            ORDER BY score DESC
            """
        
        try:
            return self.execute_cypher(cypher, {
                'embedding': query_embedding,
                'limit': limit
            })
        except Exception as e:
            logger.warning(f"Hybrid search failed: {str(e)}")
            return []
    
    def get_grant_by_id(self, application_id: int) -> Dict:
        """Get a specific grant by ID"""
        cypher = """
        MATCH (g:Grant {application_id: $id})
        OPTIONAL MATCH (g)<-[:PRINCIPAL_INVESTIGATOR]-(r:Researcher)
        OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution)
        OPTIONAL MATCH (g)-[:IN_AREA]->(a:ResearchArea)
        RETURN g, r, i, collect(a.name) as areas
        """
        
        results = self.execute_cypher(cypher, {'id': application_id})
        return results[0] if results else {}
    
    def get_grants_by_researcher(self, researcher_name: str) -> List[Dict]:
        """Get all grants for a researcher"""
        cypher = """
        MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR]->(g:Grant)
        WHERE r.name CONTAINS $name
        RETURN g, r
        """
        
        return self.execute_cypher(cypher, {'name': researcher_name})
    
    def get_grants_by_institution(self, institution_name: str) -> List[Dict]:
        """Get all grants for an institution"""
        cypher = """
        MATCH (g:Grant)-[:HOSTED_BY]->(i:Institution)
        WHERE i.name CONTAINS $name
        RETURN g, i
        """
        
        return self.execute_cypher(cypher, {'name': institution_name})
    
    def get_grants_by_research_area(self, area_name: str) -> List[Dict]:
        """Get all grants in a research area"""
        cypher = """
        MATCH (g:Grant)-[:IN_AREA]->(a:ResearchArea)
        WHERE a.name CONTAINS $name
        RETURN g, a
        """
        
        return self.execute_cypher(cypher, {'name': area_name})
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()
