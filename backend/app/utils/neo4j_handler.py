from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jHandler:
    """Handler for Neo4j database operations"""
    
    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        """Initialize Neo4j connection"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        self.verify_connection()
    
    def verify_connection(self):
        """Verify database connection"""
        try:
            with self.driver.session(database=self.database) as session:
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
        with self.driver.session(database=self.database) as session:
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
    
    def execute_cypher(self, query: str, parameters: Optional[Dict] = None) -> List[Dict]:
        """
        Execute a Cypher query and return results as list of dictionaries
        """
        try:
            with self.driver.session(database=self.database) as session:
                result = session.run(query, parameters or {})  # type: ignore
                records = []
                for record in result:
                    record_dict = {}
                    for key in record.keys():
                        value = record[key]
                        
                        # Sanitize floats for JSON compliance
                        if isinstance(value, float):
                            if value != value:  # NaN check
                                value = None
                            elif value == float('inf') or value == float('-inf'):
                                value = None
                                
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
    
    def _build_filter_clause(self, filters: Optional[Dict[str, Any]] = None, prefix: str = "g") -> str:
        """Helper to build WHERE clause from filters"""
        if not filters:
            return ""
        
        clauses = []
        for key, value in filters.items():
            if value is None or value == "":
                continue
            
            if key == "institution":
                # Strict Match (Dropdown)
                clauses.append(f"EXISTS {{ MATCH ({prefix})-[:HOSTED_BY]->(i:Institution) WHERE i.name = $institution }}")
            
            elif key == "institution_name":
                # Partial Match (Column Search)
                clauses.append(f"EXISTS {{ MATCH ({prefix})-[:HOSTED_BY]->(i:Institution) WHERE toLower(i.name) CONTAINS toLower($institution_name) }}")
                
            elif key in ["pi_name", "researcher_name", "researcher"]:
                # Partial Match on Researcher
                clauses.append(f"EXISTS {{ MATCH ({prefix})<-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]-(p:Researcher) WHERE toLower(p.name) CONTAINS toLower(${key}) }}")

            elif key == "start_year":
                clauses.append(f"{prefix}.{key} = toInteger($start_year)")
                
            elif key == "search":
                import re
                terms = re.findall(r"\w+", value)
                
                search_subclauses = []
                for term in terms:
                    term_lower = term.lower().strip()
                    if not term_lower or term_lower in ["and", "or", "&", "with"]: 
                        continue
                    
                    # Sanitize input for Cypher string injection (basic)
                    term_clean = term_lower.replace("'", "\\'")
                    
                    # 1. Check Grant Properties
                    grant_check = f"(toLower({prefix}.title) CONTAINS '{term_clean}' OR toLower({prefix}.description) CONTAINS '{term_clean}' OR toLower({prefix}.application_id) CONTAINS '{term_clean}' OR toLower({prefix}.field_of_research) CONTAINS '{term_clean}' OR toLower({prefix}.broad_research_area) CONTAINS '{term_clean}' OR toLower({prefix}.grant_type) CONTAINS '{term_clean}' OR toLower({prefix}.funding_body) CONTAINS '{term_clean}')"
                    
                    # 2. Check Researcher Name (via relationship)
                    pi_check = f"EXISTS {{ MATCH ({prefix})<-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]-(p:Researcher) WHERE toLower(p.name) CONTAINS '{term_clean}' }}"
                    
                    # 3. Check Institution Name (via relationship)
                    inst_check = f"EXISTS {{ MATCH ({prefix})-[:HOSTED_BY]->(i:Institution) WHERE toLower(i.name) CONTAINS '{term_clean}' }}"
                    
                    search_subclauses.append(f"({grant_check} OR {pi_check} OR {inst_check})")
                
                if search_subclauses:
                    clauses.append(f"({' AND '.join(search_subclauses)})")
            
            elif key in ["title", "grant_status", "funding_body", "application_id", "grant_type", "broad_research_area", "field_of_research", "description"]:
                 # Generic Partial Match for Text Properties
                clauses.append(f"toLower({prefix}.{key}) CONTAINS toLower(${key})")

            else:
                # Default Match
                clauses.append(f"{prefix}.{key} = ${key}")
        
        return " AND ".join(clauses) if clauses else ""

    def get_database_stats(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """Get database statistics with optional filtering"""
        stats = {}
        where_clause = self._build_filter_clause(filters)
        where_str = f"WHERE {where_clause}" if where_clause else ""
        
        with self.driver.session(database=self.database) as session:
            # Count grants
            result = session.run(f"MATCH (g:Grant) {where_str} RETURN count(g) as count", filters or {})
            record = result.single()
            stats['grants'] = record['count'] if record else 0
            
            # Count researchers
            # If filtered by grant properties, we need to join researchers to grants
            if where_clause:
                researcher_query = f"MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant) {where_str} RETURN count(DISTINCT r) as count"
            else:
                researcher_query = "MATCH (r:Researcher) RETURN count(r) as count"
            result = session.run(researcher_query, filters or {})
            record = result.single()
            stats['researchers'] = record['count'] if record else 0
            
            # Count institutions
            if where_clause:
                institution_query = f"MATCH (g:Grant)-[:HOSTED_BY]->(i:Institution) {where_str} RETURN count(DISTINCT i) as count"
            else:
                institution_query = "MATCH (i:Institution) RETURN count(i) as count"
            result = session.run(institution_query, filters or {})
            record = result.single()
            stats['institutions'] = record['count'] if record else 0
            
            # Sum total funding
            result = session.run(f"MATCH (g:Grant) {where_str} {'AND' if where_clause else 'WHERE'} g.amount IS NOT NULL RETURN sum(g.amount) as total", filters or {})
            record = result.single()
            total_funding = record['total'] if record and record['total'] is not None else 0
            # Handle NaN values that can occur with empty result sets
            stats['total_funding'] = 0 if total_funding != total_funding else total_funding  # NaN check

            # Count unique PIs
            if where_clause:
                pi_query = f"MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR]->(g:Grant) {where_str} RETURN count(DISTINCT r) as count"
            else:
                pi_query = "MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR]->() RETURN count(DISTINCT r) as count"
            result = session.run(pi_query, filters or {})
            record = result.single()
            stats['unique_pi'] = record['count'] if record else 0
        
        return stats
    
    def get_top_institutions(self, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        Get top institutions by funding with optional filtering
        """
        where_clause = self._build_filter_clause(filters)
        where_str = f"AND {where_clause}" if where_clause else ""
        
        cypher = f"""
        MATCH (g:Grant)-[:HOSTED_BY]->(i:Institution)
        WHERE g.amount IS NOT NULL AND g.amount \u003e 0 {where_str}
        RETURN i.name as institution,
               count(g) as grant_count,
               sum(g.amount) as total_funding
        ORDER BY total_funding DESC
        LIMIT $limit
        """
        
        params = (filters or {}).copy()
        params['limit'] = limit
        return self.execute_cypher(cypher, params)

    def get_funding_trends(self, start_year: int = 2000, end_year: int = 2024, filters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        Analyze funding trends over time with optional filtering
        """
        where_clause = self._build_filter_clause(filters)
        where_str = f"AND {where_clause}" if where_clause else ""
        
        cypher = f"""
        MATCH (g:Grant)
        WHERE g.start_year >= $start_year AND g.start_year <= $end_year
        AND g.amount IS NOT NULL AND g.amount \u003e 0 {where_str}
        RETURN g.start_year as year, 
               count(g) as grant_count,
               sum(g.amount) as total_funding,
               avg(g.amount) as avg_funding,
               percentileCont(g.amount, 0.5) as median_funding
        ORDER BY year
        """
        
        params = (filters or {}).copy()
        params.update({
            'start_year': start_year,
            'end_year': end_year
        })
        return self.execute_cypher(cypher, params)

    def get_grants_list(self, limit: int = 50, skip: int = 0, filters: Optional[Dict[str, Any]] = None, search: Optional[str] = None, sort_by: str = "start_year", order: str = "DESC") -> List[Dict]:
        """Get paginated list of grants with search and dynamic sorting"""
        # Ensure search is handled via the smart filter builder
        local_filters = (filters or {}).copy()
        if search:
            local_filters['search'] = search
            
        where_clause = self._build_filter_clause(local_filters)
        where_str = f"WHERE {where_clause}" if where_clause else ""
        
        # Allowed sort fields to prevent injection
        allowed_sorts = {
            "title": "coalesce(g.title, '')",
            "amount": "coalesce(g.amount, -1)",
            "start_year": "coalesce(g.start_year, -1)",
            "funding_body": "coalesce(g.funding_body, '')",
            "application_id": "coalesce(g.application_id, '')",
            "pi_name": "coalesce(pi.name, '')",
            "institution_name": "coalesce(i.name, '')",
            "grant_status": "coalesce(g.grant_status, '')",
            "grant_type": "coalesce(g.grant_type, '')",
            "field_of_research": "coalesce(g.field_of_research, '')",
            "broad_research_area": "coalesce(g.broad_research_area, '')",
            "description": "coalesce(g.description, '')"
        }
        sort_field = allowed_sorts.get(sort_by, "g.start_year")
        sort_order = "DESC" if order.upper() == "DESC" else "ASC"
        
        # Optimization: Move OPTIONAL MATCH after filtering IF not sorting by related entity
        sort_requires_rel = sort_by in ["pi_name", "institution_name"]
        
        if not sort_requires_rel:
            cypher = f"""
            MATCH (g:Grant)
            {where_str}
            WITH g
            ORDER BY {sort_field} {sort_order}
            SKIP $skip
            LIMIT $limit
            OPTIONAL MATCH (g)<-[:PRINCIPAL_INVESTIGATOR]-(pi:Researcher)
            OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution)
            RETURN g.title as title,
                   pi.name as pi_name,
                   i.name as institution_name,
                   g.grant_status as grant_status,
                   g.amount as amount,
                   g.description as description,
                   g.start_year as start_year,
                   g.grant_type as grant_type,
                   g.funding_body as funding_body,
                   g.field_of_research as field_of_research,
                   g.application_id as application_id
            """
        else:
            # Fallback to slower query if sorting by PI/Institution
            cypher = f"""
            MATCH (g:Grant)
            OPTIONAL MATCH (g)<-[:PRINCIPAL_INVESTIGATOR]-(pi:Researcher)
            OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution)
            WITH g, pi, i
            {where_str}
            RETURN g.title as title,
                   pi.name as pi_name,
                   i.name as institution_name,
                   g.grant_status as grant_status,
                   g.amount as amount,
                   g.description as description,
                   g.start_year as start_year,
                   g.grant_type as grant_type,
                   g.funding_body as funding_body,
                   g.field_of_research as field_of_research,
                   g.application_id as application_id
            ORDER BY {sort_field} {sort_order}
            SKIP $skip
            LIMIT $limit
            """
        
        params = local_filters.copy()
        params.update({'limit': limit, 'skip': skip, 'search': search})
        return self.execute_cypher(cypher, params)

    def get_filter_options(self) -> Dict[str, List[str]]:
        """Get unique values for filters"""
        options = {}
        properties = [
            ("grant_type", "Grant"),
            ("funding_body", "Grant"),
            ("broad_research_area", "Grant"),
            ("field_of_research", "Grant"),
            ("start_year", "Grant")
        ]
        
        with self.driver.session(database=self.database) as session:
            for prop, label in properties:
                result = session.run(f"MATCH (n:{label}) WHERE n.{prop} IS NOT NULL RETURN DISTINCT n.{prop} as value ORDER BY value LIMIT 1000")
                options[prop] = [str(record["value"]) for record in result if record["value"]]
            
            # Special case for institutions
            result = session.run("MATCH (i:Institution) RETURN DISTINCT i.name as value ORDER BY value LIMIT 1000")
            options["institution"] = [record["value"] for record in result if record["value"]]
            
        return options

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
        
        return self.execute_cypher(cypher)

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
                     cypher_filter: Optional[str] = None, limit: int = 10) -> List[Dict]:
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
    
    def get_grant_by_id(self, application_id: str) -> Dict:
        """Get a specific grant by ID"""
        cypher = """
        MATCH (g:Grant {application_id: $id})
        OPTIONAL MATCH (g)<-[:PRINCIPAL_INVESTIGATOR]-(pi:Researcher)
        OPTIONAL MATCH (g)<-[:INVESTIGATOR]-(inv:Researcher)
        OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution)
        OPTIONAL MATCH (g)-[:IN_AREA]->(a:ResearchArea)
        RETURN g, pi, collect(DISTINCT inv) as investigators, i, collect(DISTINCT a.name) as areas
        """
        
        results = self.execute_cypher(cypher, {'id': str(application_id)})
        return results[0] if results else {}
    
    def get_grants_by_researcher(self, researcher_name: str) -> List[Dict]:
        """Get all grants for a researcher (as PI or investigator)"""
        cypher = """
        MATCH (r:Researcher)-[rel:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]->(g:Grant)
        WHERE r.name CONTAINS $name
        RETURN g, r, type(rel) as role
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
    
    def get_institution_map_data(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """
        Get aggregated stats for all institutions for map visualization.
        Returns: list of dicts with name, funding, counts, etc.
        """
        where_clause = self._build_filter_clause(filters)
        where_str = f"AND {where_clause}" if where_clause else ""
        
        # We need to filter the Grants (g) first
        cypher = f"""
        MATCH (g:Grant)-[:HOSTED_BY]->(i:Institution)
        WHERE g.amount IS NOT NULL AND g.amount > 0 {where_str}
        
        WITH i, g
        ORDER BY g.amount DESC
        
        WITH i, 
             count(g) as project_count, 
             sum(g.amount) as total_funding,
             collect(g.funding_body)[0..50] as raw_funders
             
        MATCH (i)<-[:HOSTED_BY]-(g2:Grant)<-[:PRINCIPAL_INVESTIGATOR|INVESTIGATOR]-(r:Researcher)
        
        // Apply filters to the second match too? Usually map stats show "filtered view"
        // But researcher count might be tricky if we don't filter g2.
        // For consistency, let's filter g2 as well so stats match the dashboard.
        WHERE g2.amount IS NOT NULL {where_str.replace('g.', 'g2.')}
        
        WITH i, project_count, total_funding, raw_funders, count(DISTINCT r) as researcher_count
        
        RETURN i.name as institution_name,
               total_funding,
               project_count,
               researcher_count,
               raw_funders
        ORDER BY total_funding DESC
        LIMIT 100
        """
        params = (filters or {}).copy()
        try:
            results = self.execute_cypher(cypher, params)
        except Exception as e:
            logger.error(f"Map data query failed: {e}")
            return []
        
        # Post-process to deduplicate funders
        for record in results:
            seen = set()
            unique_funders = []
            for funder in record.get('raw_funders', []):
                if funder and funder not in seen:
                    unique_funders.append(funder)
                    seen.add(funder)
                    if len(unique_funders) >= 3:
                        break
            record['top_funders'] = unique_funders
            # Remove raw field
            if 'raw_funders' in record:
                del record['raw_funders']
                
        return results

    def get_grants_by_research_area(self, area_name: str) -> List[Dict]:
        """Get all grants in a research area"""
        cypher = """
        MATCH (g:Grant)-[:IN_AREA]->(a:ResearchArea)
        WHERE a.name CONTAINS $name
        RETURN g, a
        """
        
        return self.execute_cypher(cypher, {'name': area_name})

    def clear_database(self):
        """Clear all nodes and relationships from the database"""
        with self.driver.session(database=self.database) as session:
            # Delete all nodes and relationships
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Neo4j database cleared")

    def load_grants_from_dataframe(self, df: Any, progress_callback=None) -> int:
        """Alias for load_grants_dataframe for compatibility"""
        return self.load_grants_dataframe(df, progress_callback)

    def load_grants_dataframe(self, df: Any, progress_callback=None) -> int:
        """
        Load grants into Neo4j using batched UNWIND.
        Adapted to the Destination Schema:
          - Grant keyed on application_id
          - Organization -> Institution ([:HOSTED_BY])
          - Researcher ([:PRINCIPAL_INVESTIGATOR], [:INVESTIGATOR])
        """
        import pandas as pd
        if df.empty:
            return 0

        def report(msg):
            if progress_callback:
                try:
                    progress_callback(msg)
                except Exception:
                    pass

        # Helper to clean strings
        def _clean(val):
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return ""
            return str(val).strip()

        # Helper to safe float
        def _to_float_safe(val):
            s = _clean(val)
            if not s: return None
            try:
                s = s.replace(",", "").replace("$", "").replace(" ", "")
                return float(s)
            except: return None

        # Helper to safe int
        def _to_int_safe(val):
            s = _clean(val)
            if not s: return None
            try:
                return int(float(s))
            except: return None
            
        total = len(df)
        report(f"Loading {total} grants into Neo4j...")
        
        # Prepare records
        records = []
        for _, row in df.iterrows():
            records.append({
                "application_id": _clean(row.get("Application_ID")),
                "grant_title": _clean(row.get("Grant_Title")),
                "total_amount": _to_float_safe(row.get("Total_Amount")),
                "broad_research_area": _clean(row.get("Broad_Research_Area")),
                "plain_description": _clean(row.get("Plain_Description")),
                "grant_start_year": _to_int_safe(row.get("Grant_Start_Year")),
                "grant_status": _clean(row.get("Grant_Status")),
                "admin_institution": _clean(row.get("Admin_Institution")),
                "field_of_research": _clean(row.get("Field_of_Research")),
                "grant_type": _clean(row.get("Grant_Type")),
                "funding_body": _clean(row.get("Funding_Body")),
                "cia_name": _clean(row.get("CIA_Name")),
                "investigators": _clean(row.get("Investigators")),
            })

        BATCH_SIZE = 2000
        
        with self.driver.session(database=self.database) as session:
            
            # 1. Dimension Nodes
            report("Neo4j: Creating dimension nodes...")
            
            # Create Institutions
            unique_institutions = list({r["admin_institution"] for r in records if r["admin_institution"]})
            for i in range(0, len(unique_institutions), BATCH_SIZE):
                batch = [{"name": v} for v in unique_institutions[i:i+BATCH_SIZE]]
                session.run("""
                    UNWIND $batch AS row
                    MERGE (i:Institution {name: row.name})
                """, batch=batch)
                
            # Create Researchers (CIA)
            unique_researchers = list({r["cia_name"] for r in records if r["cia_name"]})
            for i in range(0, len(unique_researchers), BATCH_SIZE):
                batch = [{"name": v} for v in unique_researchers[i:i+BATCH_SIZE]]
                session.run("""
                    UNWIND $batch AS row
                    MERGE (r:Researcher {name: row.name})
                """, batch=batch)

            # Create Funding Bodies (Optional - if node exists provided by old schema)
            # Schema suggests Funding_Body is a property or separate node. 
            # In source it was a node. In destination, we might just keep as property or new node.
            # Let's create node to be safe and rich.
            unique_funders = list({r["funding_body"] for r in records if r["funding_body"]})
            for i in range(0, len(unique_funders), BATCH_SIZE):
                batch = [{"name": v} for v in unique_funders[i:i+BATCH_SIZE]]
                session.run("""
                    UNWIND $batch AS row
                    MERGE (f:FundingBody {name: row.name})
                """, batch=batch)
                
            # Create Broad Research Area (Source has this)
            unique_broad_areas = list({r["broad_research_area"] for r in records if r["broad_research_area"]})
            for i in range(0, len(unique_broad_areas), BATCH_SIZE):
                batch = [{"name": v} for v in unique_broad_areas[i:i+BATCH_SIZE]]
                session.run("""
                    UNWIND $batch AS row
                    MERGE (a:ResearchArea {name: row.name})
                """, batch=batch)

            # 2. Grant Nodes
            report("Neo4j: Creating Grant nodes...")
            for i in range(0, total, BATCH_SIZE):
                batch = records[i:i+BATCH_SIZE]
                session.run("""
                    UNWIND $batch AS row
                    MERGE (g:Grant {application_id: row.application_id})
                    SET g.title = row.grant_title,
                        g.amount = row.total_amount,
                        g.broad_research_area = row.broad_research_area,
                        g.description = row.plain_description,
                        g.start_year = row.grant_start_year,
                        g.grant_status = row.grant_status,
                        g.grant_type = row.grant_type,
                        g.funding_body = row.funding_body,
                        g.field_of_research = row.field_of_research
                """, batch=batch)
                
            # 3. Relationships
            report("Neo4j: Creating relationships...")
            for i in range(0, total, BATCH_SIZE):
                batch = records[i:i+BATCH_SIZE]
                
                # HOSTED_BY (Institution)
                session.run("""
                    UNWIND $batch AS row
                    WITH row WHERE row.admin_institution <> '' AND row.application_id <> ''
                    MATCH (g:Grant {application_id: row.application_id})
                    MATCH (i:Institution {name: row.admin_institution})
                    MERGE (g)-[:HOSTED_BY]->(i)
                """, batch=batch)
                
                # PRINCIPAL_INVESTIGATOR (Researcher)
                session.run("""
                    UNWIND $batch AS row
                    WITH row WHERE row.cia_name <> '' AND row.application_id <> ''
                    MATCH (g:Grant {application_id: row.application_id})
                    MATCH (r:Researcher {name: row.cia_name})
                    MERGE (r)-[:PRINCIPAL_INVESTIGATOR]->(g)
                """, batch=batch)

                # IN_AREA (ResearchArea)
                session.run("""
                    UNWIND $batch AS row
                    WITH row WHERE row.broad_research_area <> '' AND row.application_id <> ''
                    MATCH (g:Grant {application_id: row.application_id})
                    MATCH (a:ResearchArea {name: row.broad_research_area})
                    MERGE (g)-[:IN_AREA]->(a)
                """, batch=batch)
                
        report(f"Neo4j load complete. {total} grants processed.")
        return total
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()
