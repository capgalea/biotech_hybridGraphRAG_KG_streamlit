import streamlit as st
from utils.neo4j_handler import Neo4jHandler
from utils.llm_handler import LLMHandler
from utils.query_processor import QueryProcessor
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="GraphRAG Grant Explorer",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'current_results' not in st.session_state:
    st.session_state.current_results = None
if 'current_cypher' not in st.session_state:
    st.session_state.current_cypher = None

# Initialize handlers
@st.cache_resource
def init_handlers():
    neo4j_handler = Neo4jHandler(
        uri=st.secrets["neo4j"]["uri"],
        user=st.secrets["neo4j"]["user"],
        password=st.secrets["neo4j"]["password"],
        database=st.secrets["neo4j"]["database"]
    )
    return neo4j_handler

try:
    neo4j_handler = init_handlers()
except Exception as e:
    st.error(f"Failed to connect to Neo4j: {str(e)}")
    st.stop()

# Sidebar
with st.sidebar:
    st.title("⚙️ Configuration")
    
    # LLM Selection
    llm_option = st.selectbox(
        "Select LLM",
        [
            "Claude 3.7 Sonnet",
            "Claude 4.0 Sonnet", 
            "Claude 4.5 Sonnet",
            "GPT-4o",
            "Gemini 2.0 Flash",
            "DeepSeek"
        ],
        index=3  # Default to GPT-4o since Anthropic has API issues
    )
    
    # Google Search Integration Toggle
    enable_search = st.checkbox(
        "🔍 Include Web Search",
        value=True,
        help="Enhance summaries with Google Search results for additional context and references"
    )
    
    st.divider()
    
    # Query History
    st.subheader("📜 Query History")
    if st.session_state.query_history:
        for i, query in enumerate(reversed(st.session_state.query_history[-10:])):
            if st.button(f"🔄 {query[:50]}...", key=f"history_{i}"):
                st.session_state.selected_query = query
    else:
        st.info("No queries yet")
    
    st.divider()
    
    # Stats
    st.subheader("📊 Database Stats")
    try:
        stats = neo4j_handler.get_database_stats()
        st.metric("Total Grants", stats.get('grants', 0))
        st.metric("Researchers", stats.get('researchers', 0))
        st.metric("Institutions", stats.get('institutions', 0))
    except:
        st.warning("Stats unavailable")

# Main content
st.title("🔍 GraphRAG Grant Explorer")
st.markdown("### Hybrid Graph + Vector Search for Research Grants")

# Schema display
with st.expander("📐 View Database Schema", expanded=False):
    try:
        schema = neo4j_handler.get_schema()
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Node Labels:**")
            for label in schema.get('node_labels', []):
                st.markdown(f"- `{label}`")
        
        with col2:
            st.markdown("**Relationship Types:**")
            for rel in schema.get('relationships', []):
                st.markdown(f"- `{rel}`")
        
        st.markdown("**Sample Cypher Queries:**")
        st.code("""
// Find all grants by researcher name
MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR]->(g:Grant)
WHERE r.name CONTAINS 'Smith'
RETURN r, g

// Find grants by research area
MATCH (g:Grant)-[:IN_AREA]->(a:ResearchArea)
WHERE a.name = 'Public Health Research'
RETURN g.title, g.amount, g.start_year

// Find collaboration networks
MATCH (r1:Researcher)-[:PRINCIPAL_INVESTIGATOR]->(g:Grant)<-[:PRINCIPAL_INVESTIGATOR]-(r2:Researcher)
RETURN r1.name, r2.name, COUNT(g) as shared_grants
        """, language="cypher")
    except Exception as e:
        st.error(f"Could not load schema: {str(e)}")

# Query input
st.subheader("💬 Ask a Question")

# Pre-populate if selected from history
if 'selected_query' in st.session_state:
    default_query = st.session_state.selected_query
    del st.session_state.selected_query
else:
    default_query = ""

query = st.text_area(
    "Enter your question about research grants:",
    value=default_query,
    height=100,
    placeholder="e.g., 'Which grants focus on cancer research?' or 'Show me all grants at University of Melbourne'"
)

# Search button
if st.button("🔎 Search", type="primary", use_container_width=True):
    if query:
        with st.spinner("Processing query..."):
            try:
                # Add to history
                if query not in st.session_state.query_history:
                    st.session_state.query_history.append(query)
                
                # Initialize LLM handler
                llm_handler = LLMHandler(llm_option, dict(st.secrets))
                
                # Initialize query processor
                query_processor = QueryProcessor(neo4j_handler, llm_handler)
                
                # Process query
                results = query_processor.process_query(query, enable_search)
                
                # Store results
                st.session_state.current_results = results
                st.session_state.current_cypher = results.get('cypher', '')
                
            except Exception as e:
                st.error(f"Error processing query: {str(e)}")
                st.exception(e)
    else:
        st.warning("Please enter a query")

# Display results
if st.session_state.current_results:
    results = st.session_state.current_results
    
    # Generated Cypher
    with st.expander("🔧 Generated Cypher Query", expanded=False):
        st.code(st.session_state.current_cypher, language="cypher")
        if st.button("📋 Copy Cypher"):
            st.toast("Cypher copied to clipboard!")
    
    st.divider()
    
    # Results table
    if results.get('data'):
        with st.expander("📊 Results Table", expanded=True):
            df = pd.DataFrame(results['data'])
            st.dataframe(df, use_container_width=True, height=400)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name="grant_results.csv",
                mime="text/csv"
            )
            
            # Footer note about result limitations
            st.markdown("""
            <div style='text-align: center; color: #888; font-size: 0.85em; margin-top: 10px; padding: 5px; background-color: #f8f9fa; border-radius: 5px;'>
                📅 <strong>Note:</strong> Results show the 20 most recent grants ordered by start year (newest first)
            </div>
            """, unsafe_allow_html=True)
    
    # Text summary
    st.subheader("📝 Summary")
    if results.get('summary'):
        st.markdown(results['summary'])
    else:
        st.info("No summary available")
    
    # Insights
    if results.get('insights'):
        st.subheader("💡 Key Insights")
        for insight in results['insights']:
            st.markdown(f"- {insight}")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Powered by Neo4j GraphRAG • Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)
