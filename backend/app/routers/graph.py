from fastapi import APIRouter, HTTPException
from app.utils.neo4j_handler import Neo4jHandler
from app.config import settings

router = APIRouter()

def get_neo4j_handler():
    return Neo4jHandler(
        uri=settings["neo4j"]["uri"],
        user=settings["neo4j"]["user"],
        password=settings["neo4j"]["password"],
        database=settings["neo4j"]["database"]
    )

@router.get("/data")
async def get_graph_data(limit: int = 100):
    try:
        handler = get_neo4j_handler()
        # This is a simplified query, you might want to adapt the logic from graphrag_viz_page.py
        query = f"""
        MATCH (n)-[r]->(m)
        RETURN n, r, m
        LIMIT {limit}
        """
        results = handler.execute_cypher(query)
        
        # Transform to node/link format for frontend
        nodes = {}
        links = []
        
        for record in results:
            n = record['n']
            m = record['m']
            r = record['r']
            
            # Process nodes
            for node in [n, m]:
                # Neo4j node to dict, handling ID and labels
                # Note: This depends on how the driver returns nodes. 
                # Usually it's an object with .id, .labels, and properties (as dict-like)
                node_id = str(node.element_id) if hasattr(node, 'element_id') else str(node.id)
                if node_id not in nodes:
                    nodes[node_id] = {
                        "id": node_id,
                        "labels": list(node.labels),
                        "properties": dict(node)
                    }
            
            # Process relationship
            links.append({
                "source": str(n.element_id) if hasattr(n, 'element_id') else str(n.id),
                "target": str(m.element_id) if hasattr(m, 'element_id') else str(m.id),
                "type": r.type,
                "properties": dict(r)
            })
            
        return {"nodes": list(nodes.values()), "links": links}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
