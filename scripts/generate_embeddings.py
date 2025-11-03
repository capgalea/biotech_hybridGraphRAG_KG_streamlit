"""
Generate vector embeddings for grants to enable semantic search
This script adds embedding vectors to Grant nodes for hybrid retrieval
"""

from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase
import logging
from typing import List
import os
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate and store embeddings for graph nodes"""
    
    def __init__(self, uri: str, user: str, password: str, 
                 model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize with Neo4j connection and embedding model
        
        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
            model_name: HuggingFace model for embeddings
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.embedding_dim}")
    
    def close(self):
        """Close database connection"""
        self.driver.close()
    
    def create_text_representation(self, grant: dict) -> str:
        """
        Create a text representation of a grant for embedding
        
        Args:
            grant: Dictionary containing grant properties
            
        Returns:
            Combined text string for embedding
        """
        parts = []
        
        # Title (most important)
        if grant.get('title'):
            parts.append(f"Title: {grant['title']}")
        
        # Description
        if grant.get('description'):
            parts.append(f"Description: {grant['description']}")
        
        # Research area
        if grant.get('broad_research_area'):
            parts.append(f"Research Area: {grant['broad_research_area']}")
        
        # Field of research
        if grant.get('field_of_research'):
            parts.append(f"Fields: {grant['field_of_research']}")
        
        # Grant type
        if grant.get('grant_type'):
            parts.append(f"Type: {grant['grant_type']}")
        
        return " ".join(parts)
    
    def fetch_grants(self) -> List[dict]:
        """
        Fetch all grants from database
        
        Returns:
            List of grant dictionaries
        """
        cypher = """
        MATCH (g:Grant)
        RETURN g.application_id as id,
               g.title as title,
               g.description as description,
               g.broad_research_area as broad_research_area,
               g.field_of_research as field_of_research,
               g.grant_type as grant_type
        """
        
        with self.driver.session() as session:
            result = session.run(cypher)
            grants = [dict(record) for record in result]
        
        logger.info(f"Fetched {len(grants)} grants")
        return grants
    
    def generate_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of text strings
            batch_size: Batch size for encoding
            
        Returns:
            Array of embeddings
        """
        logger.info(f"Generating embeddings for {len(texts)} texts...")
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        return embeddings
    
    def store_embedding(self, grant_id: int, embedding: List[float]):
        """
        Store embedding in Neo4j for a grant
        
        Args:
            grant_id: Grant application ID
            embedding: Embedding vector as list
        """
        cypher = """
        MATCH (g:Grant {application_id: $id})
        SET g.embedding = $embedding
        """
        
        with self.driver.session() as session:
            session.run(cypher, {
                'id': grant_id,
                'embedding': embedding
            })
    
    def process_all_grants(self, batch_size: int = 32):
        """
        Main processing function: fetch grants, generate embeddings, store them
        
        Args:
            batch_size: Batch size for processing
        """
        # Fetch grants
        grants = self.fetch_grants()
        
        if not grants:
            logger.warning("No grants found in database")
            return
        
        # Create text representations
        logger.info("Creating text representations...")
        texts = [self.create_text_representation(grant) for grant in grants]
        
        # Generate embeddings
        embeddings = self.generate_embeddings(texts, batch_size=batch_size)
        
        # Store embeddings
        logger.info("Storing embeddings in Neo4j...")
        for i, (grant, embedding) in enumerate(zip(grants, embeddings)):
            try:
                self.store_embedding(grant['id'], embedding.tolist())
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Stored {i + 1}/{len(grants)} embeddings")
                    
            except Exception as e:
                logger.error(f"Error storing embedding for grant {grant['id']}: {str(e)}")
        
        logger.info("✅ All embeddings generated and stored!")
    
    def verify_embeddings(self):
        """Verify embeddings were stored correctly"""
        cypher = """
        MATCH (g:Grant)
        WHERE g.embedding IS NOT NULL
        RETURN count(g) as count
        """
        
        with self.driver.session() as session:
            result = session.run(cypher)
            count = result.single()['count']
        
        logger.info(f"Grants with embeddings: {count}")
        return count
    
    def test_similarity_search(self, query_text: str, limit: int = 5):
        """
        Test similarity search with a query
        
        Args:
            query_text: Text to search for
            limit: Number of results to return
        """
        logger.info(f"Testing similarity search for: {query_text}")
        
        # Generate query embedding
        query_embedding = self.model.encode(query_text).tolist()
        
        # Search (requires vector index)
        cypher = """
        CALL db.index.vector.queryNodes('grant_embeddings', $limit, $embedding)
        YIELD node, score
        RETURN node.title as title, 
               node.broad_research_area as area,
               score
        ORDER BY score DESC
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(cypher, {
                    'embedding': query_embedding,
                    'limit': limit
                })
                
                logger.info("\nTop matches:")
                for record in result:
                    logger.info(f"  {record['title'][:60]}... (Score: {record['score']:.3f})")
                    
        except Exception as e:
            logger.error(f"Similarity search failed: {str(e)}")
            logger.error("Make sure vector index 'grant_embeddings' exists")


def main():
    """Main execution"""
    # Configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    
    logger.info("Starting embedding generation...")
    logger.info(f"Neo4j URI: {NEO4J_URI}")
    logger.info(f"Model: {MODEL_NAME}")
    
    generator = EmbeddingGenerator(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, MODEL_NAME)
    
    try:
        # Generate and store embeddings
        generator.process_all_grants(batch_size=32)
        
        # Verify
        count = generator.verify_embeddings()
        logger.info(f"✅ Successfully generated embeddings for {count} grants")
        
        # Test search (optional)
        test_queries = [
            "cancer research and treatment",
            "climate change and environmental impact",
            "artificial intelligence and machine learning"
        ]
        
        logger.info("\n" + "="*50)
        logger.info("Testing similarity search...")
        logger.info("="*50)
        
        for query in test_queries:
            generator.test_similarity_search(query, limit=3)
            print()
        
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        raise
    finally:
        generator.close()


if __name__ == "__main__":
    main()
