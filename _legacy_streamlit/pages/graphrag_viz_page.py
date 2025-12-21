import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network
from utils.neo4j_handler import Neo4jHandler
import tempfile
import os

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

st.set_page_config(page_title="Graph Visualization", page_icon="🌐", layout="wide")

# Initialize Neo4j handler
@st.cache_resource
def init_neo4j():
    return Neo4jHandler(
        uri=st.secrets["neo4j"]["uri"],
        user=st.secrets["neo4j"]["user"],
        password=st.secrets["neo4j"]["password"],
        database=st.secrets["neo4j"]["database"]
    )

neo4j_handler = init_neo4j()

st.title("🌐 Interactive Graph Visualization")
st.markdown("Explore the research grants knowledge graph")

# Sidebar controls
with st.sidebar:
    st.header("Visualization Options")
    
    viz_mode = st.radio(
        "Visualization Mode",
        ["Random Sample", "Node Browser", "Custom Query"],
        index=0
    )
    
    st.divider()
    
    # Physics settings
    st.subheader("Physics Settings")
    physics_enabled = st.checkbox("Enable Physics", value=True)
    
    repulsion = 200
    spring_length = 150
    if physics_enabled:
        repulsion = st.slider("Node Repulsion", 50, 500, 200)
        spring_length = st.slider("Edge Length", 50, 300, 150)

# Main content
if viz_mode == "Random Sample":
    st.subheader("Random Sample Visualization")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        num_nodes = st.slider("Number of nodes", 5, 50, 15)
    with col2:
        include_researchers = st.checkbox("Include Researchers", value=True)
    with col3:
        include_institutions = st.checkbox("Include Institutions", value=True)
    
    if st.button("🔄 Generate Visualization", type="primary"):
        with st.spinner("Creating graph visualization..."):
            try:
                # Build Cypher query
                cypher_parts = ["MATCH (g:Grant)"]
                
                if include_researchers:
                    cypher_parts.append("OPTIONAL MATCH (g)<-[:PRINCIPAL_INVESTIGATOR]-(r:Researcher)")
                if include_institutions:
                    cypher_parts.append("OPTIONAL MATCH (g)-[:HOSTED_BY]->(i:Institution)")
                
                cypher_parts.append(f"WITH g, r, i LIMIT {num_nodes}")
                cypher_parts.append("RETURN g, r, i")
                
                cypher_query = "\n".join(cypher_parts)
                
                # Show query
                with st.expander("📋 Generated Cypher Query"):
                    st.code(cypher_query, language="cypher")
                
                # Get data
                data = neo4j_handler.execute_cypher(cypher_query)
                
                # Create network
                net = Network(height="700px", width="100%", bgcolor="#222222")
                
                if physics_enabled:
                    net.barnes_hut(gravity=-5000, central_gravity=0.3, 
                                  spring_length=spring_length, 
                                  spring_strength=0.001,
                                  damping=0.09)
                
                # Add nodes and edges
                for record in data:
                    grant = None
                    # Add grant node
                    if record.get('g'):
                        grant = record['g']
                        net.add_node(
                            grant['application_id'],
                            label=grant.get('title', 'Unknown')[:50],
                            color="#FF6B6B",
                            title=f"<b>{grant.get('title', 'Unknown')}</b><br>Amount: {safe_format_amount(grant.get('amount'))}",
                            shape="dot",
                            size=20
                        )
                    
                    # Add researcher node
                    if record.get('r') and include_researchers and grant:
                        researcher = record['r']
                        r_id = f"r_{researcher.get('name', 'unknown')}"
                        net.add_node(
                            r_id,
                            label=researcher.get('name', 'Unknown'),
                            color="#4ECDC4",
                            title=f"<b>Researcher:</b> {researcher.get('name', 'Unknown')}",
                            shape="triangle",
                            size=15
                        )
                        net.add_edge(r_id, grant['application_id'], 
                                   title="Principal Investigator")
                    
                    # Add institution node
                    if record.get('i') and include_institutions and grant:
                        institution = record['i']
                        i_id = f"i_{institution.get('name', 'unknown')}"
                        net.add_node(
                            i_id,
                            label=institution.get('name', 'Unknown'),
                            color="#95E1D3",
                            title=f"<b>Institution:</b> {institution.get('name', 'Unknown')}",
                            shape="square",
                            size=25
                        )
                        net.add_edge(grant['application_id'], i_id,
                                   title="Hosted By")
                
                # Save and display
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w') as f:
                        temp_file_path = f.name
                    
                    net.save_graph(temp_file_path)
                    
                    with open(temp_file_path, 'r', encoding='utf-8') as file:
                        html_content = file.read()
                    
                    # Safe cleanup with retry logic for Windows
                    try:
                        os.unlink(temp_file_path)
                    except PermissionError:
                        # File might still be in use, schedule for cleanup later
                        pass
                except Exception as temp_error:
                    st.warning(f"Temporary file handling warning: {temp_error}")
                    # Fallback: create HTML content directly without temp file
                    html_content = net.generate_html()
                
                components.html(html_content, height=720, scrolling=True)
                
                st.success(f"✅ Visualized {len(data)} nodes")
                
            except Exception as e:
                st.error(f"Error creating visualization: {str(e)}")
                st.exception(e)

elif viz_mode == "Node Browser":
    st.subheader("Node and Relationship Browser")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Select Node Types:**")
        node_grants = st.checkbox("Grants", value=True, key="node_grants")
        node_researchers = st.checkbox("Researchers", value=True, key="node_researchers")
        node_institutions = st.checkbox("Institutions", value=True, key="node_institutions")
        node_areas = st.checkbox("Research Areas", value=False, key="node_areas")
    
    with col2:
        st.markdown("**Select Relationships:**")
        rel_pi = st.checkbox("Principal Investigator", value=True, key="rel_pi")
        rel_hosted = st.checkbox("Hosted By", value=True, key="rel_hosted")
        rel_area = st.checkbox("In Research Area", value=False, key="rel_area")
    
    # Build visualization preview
    st.markdown("**Selected Schema Preview:**")
    preview_parts = []
    if node_grants:
        preview_parts.append("🔴 Grants")
    if node_researchers:
        preview_parts.append("🔵 Researchers")
    if node_institutions:
        preview_parts.append("🟢 Institutions")
    if node_areas:
        preview_parts.append("🟡 Research Areas")
    
    st.info(" → ".join(preview_parts))
    
    if st.button("🎨 Create Visualization", type="primary"):
        with st.spinner("Building graph..."):
            try:
                # Build dynamic Cypher query
                match_clauses = []
                if node_grants:
                    match_clauses.append("(g:Grant)")
                if node_researchers and rel_pi:
                    match_clauses.append("(g)<-[:PRINCIPAL_INVESTIGATOR]-(r:Researcher)")
                if node_institutions and rel_hosted:
                    match_clauses.append("(g)-[:HOSTED_BY]->(i:Institution)")
                if node_areas and rel_area:
                    match_clauses.append("(g)-[:IN_AREA]->(a:ResearchArea)")
                
                cypher_query = f"MATCH {', '.join(match_clauses)} RETURN * LIMIT 30"
                
                with st.expander("📋 Generated Cypher Query"):
                    st.code(cypher_query, language="cypher")
                
                data = neo4j_handler.execute_cypher(cypher_query)
                
                # Create visualization
                net = Network(height="700px", width="100%", bgcolor="#1E1E1E")
                
                if physics_enabled:
                    net.barnes_hut(gravity=-3000, spring_length=spring_length)
                
                # Process results and add to network
                added_nodes = set()
                for record in data:
                    for key, value in record.items():
                        if value and hasattr(value, 'get'):
                            node_id = value.get('application_id') or value.get('name') or str(hash(str(value)))
                            if node_id not in added_nodes:
                                # Determine node properties based on type
                                if 'Grant' in str(key) or 'amount' in value:
                                    color = "#FF6B6B"
                                    shape = "dot"
                                elif 'Researcher' in str(key) or 'orcid' in str(value):
                                    color = "#4ECDC4"
                                    shape = "triangle"
                                elif 'Institution' in str(key):
                                    color = "#95E1D3"
                                    shape = "square"
                                else:
                                    color = "#FFD93D"
                                    shape = "star"
                                
                                label = value.get('name') or value.get('title', str(node_id))[:40]
                                net.add_node(node_id, label=label, color=color, shape=shape)
                                added_nodes.add(node_id)
                
                # Save and display
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w') as f:
                        temp_file_path = f.name
                    
                    net.save_graph(temp_file_path)
                    
                    with open(temp_file_path, 'r', encoding='utf-8') as file:
                        html_content = file.read()
                    
                    # Safe cleanup with retry logic for Windows
                    try:
                        os.unlink(temp_file_path)
                    except PermissionError:
                        # File might still be in use, schedule for cleanup later
                        pass
                except Exception as temp_error:
                    st.warning(f"Temporary file handling warning: {temp_error}")
                    # Fallback: create HTML content directly without temp file
                    html_content = net.generate_html()
                
                components.html(html_content, height=720, scrolling=True)
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

else:  # Custom Query
    st.subheader("Custom Cypher Query")
    
    st.markdown("Write your own Cypher query to visualize specific patterns:")
    
    custom_query = st.text_area(
        "Cypher Query",
        value="""MATCH (g:Grant)-[:HOSTED_BY]->(i:Institution)
WHERE g.amount > 1000000
RETURN g, i
LIMIT 20""",
        height=150
    )
    
    if st.button("▶️ Execute and Visualize", type="primary"):
        with st.spinner("Executing query..."):
            try:
                data = neo4j_handler.execute_cypher(custom_query)
                
                net = Network(height="700px", width="100%", bgcolor="#222222")
                
                if physics_enabled:
                    net.barnes_hut()
                
                # Add nodes from results
                added_nodes = set()
                for record in data:
                    for value in record.values():
                        if value and hasattr(value, 'get'):
                            node_id = str(value.get('application_id') or value.get('name') or hash(str(value)))
                            if node_id not in added_nodes:
                                label = str(value.get('name') or value.get('title', node_id))[:40]
                                net.add_node(node_id, label=label)
                                added_nodes.add(node_id)
                
                # Save and display
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.html', mode='w') as f:
                        temp_file_path = f.name
                    
                    net.save_graph(temp_file_path)
                    
                    with open(temp_file_path, 'r', encoding='utf-8') as file:
                        html_content = file.read()
                    
                    # Safe cleanup with retry logic for Windows
                    try:
                        os.unlink(temp_file_path)
                    except PermissionError:
                        # File might still be in use, schedule for cleanup later
                        pass
                except Exception as temp_error:
                    st.warning(f"Temporary file handling warning: {temp_error}")
                    # Fallback: create HTML content directly without temp file
                    html_content = net.generate_html()
                
                components.html(html_content, height=720, scrolling=True)
                
                st.success(f"✅ Query returned {len(data)} results")
                
            except Exception as e:
                st.error(f"Query error: {str(e)}")

# Legend
with st.expander("🎨 Visualization Legend"):
    st.markdown("""
    **Node Colors:**
    - 🔴 **Red**: Grants
    - 🔵 **Cyan**: Researchers
    - 🟢 **Green**: Institutions
    - 🟡 **Yellow**: Research Areas
    
    **Node Shapes:**
    - ⚫ **Circle**: Grants
    - 🔺 **Triangle**: Researchers
    - ⬛ **Square**: Institutions
    - ⭐ **Star**: Research Areas
    
    **Interaction:**
    - Click and drag nodes to rearrange
    - Scroll to zoom in/out
    - Hover over nodes for details
    """)
