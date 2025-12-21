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
st.title("🔍 Research Grant Explorer")

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
            
            # Define column mapping for better headers (matching actual database fields)
            column_mapping = {
                # Grant fields (actual database properties)
                'g.title': 'Title',
                'grant_title': 'Title',
                'title': 'Title',
                'g.grant_status': 'Grant Status',
                'grant_status': 'Grant Status',
                'status': 'Grant Status',
                'g.amount': 'Amount',
                'amount': 'Amount',
                'g.description': 'Description',
                'description': 'Description',
                'g.start_year': 'Start Year',
                'start_year': 'Start Year',
                'g.end_date': 'End Date',
                'end_date': 'End Date',
                'g.grant_type': 'Grant Type',
                'grant_type': 'Grant Type',
                'g.funding_body': 'Funding Body',
                'funding_body': 'Funding Body',
                'g.broad_research_area': 'Research Area',
                'broad_research_area': 'Research Area',
                'g.field_of_research': 'Field of Research',
                'field_of_research': 'Field of Research',
                'g.application_id': 'Application ID',
                'application_id': 'Application ID',
                'g.date_announced': 'Date Announced',
                'date_announced': 'Date Announced',
                
                # Researcher fields (actual database properties)
                'r.name': 'Researcher Name',
                'researcher_name': 'Researcher Name',
                'r.orcid_id': 'ORCID ID',
                'orcid_id': 'ORCID ID',
                
                # Institution fields
                'i.name': 'Institution Name',
                'institution_name': 'Institution Name',
                'institution': 'Institution Name',
                'name': 'Name'
            }
            
            # Apply column mapping and handle potential duplicates
            df_display = df.copy()
            used_names = set()
            
            for old_col in df_display.columns:
                if old_col in column_mapping:
                    new_col = column_mapping[old_col]
                    # Handle duplicate column names by adding suffix
                    counter = 1
                    original_new_col = new_col
                    while new_col in used_names:
                        new_col = f"{original_new_col}_{counter}"
                        counter += 1
                    used_names.add(new_col)
                    df_display = df_display.rename(columns={old_col: new_col})
                else:
                    # Keep original name but ensure it's unique
                    new_col = old_col
                    counter = 1
                    original_new_col = new_col
                    while new_col in used_names:
                        new_col = f"{original_new_col}_{counter}"
                        counter += 1
                    used_names.add(new_col)
                    if new_col != old_col:
                        df_display = df_display.rename(columns={old_col: new_col})
            
            # Define preferred column order (based on actual database fields)
            preferred_columns = [
                'Title', 'Grant Status', 'Amount', 'Description', 'Start Year', 'End Date',
                'Researcher Name', 'ORCID ID', 'Institution Name', 'Grant Type', 
                'Funding Body', 'Research Area', 'Field of Research', 
                'Application ID', 'Date Announced'
            ]
            
            # Get available columns from the data
            available_columns = [col for col in preferred_columns if col in df_display.columns]
            other_columns = [col for col in df_display.columns if col not in preferred_columns]
            all_available_columns = available_columns + other_columns
            
            # Options interface first (to define variables)
            col1, col2 = st.columns([2, 1])
            
            with col2:
                # Options for table behavior
                show_index = st.checkbox("Show row numbers", value=False)
                enable_column_select = st.checkbox("Enable column selection", value=True,
                                                 help="Show/hide the column selection interface")
                enable_reorder = st.checkbox("Enable column reordering", value=True, 
                                           help="Allow click-to-reorder columns by selection order")
            
            # Column selection interface (conditional)
            # Default to all columns if column selection is disabled
            if enable_column_select:
                with col1:
                    selected_columns = st.multiselect(
                        "Select columns to display:",
                        options=all_available_columns,
                        default=all_available_columns[:8] if len(all_available_columns) > 8 else all_available_columns,
                        help="Choose which columns to show in the table"
                    )
            else:
                # When column selection is disabled, use all available columns
                selected_columns = all_available_columns
                with col1:
                    st.info(f"📊 Showing all {len(selected_columns)} available columns. Enable column selection to customize.")
            
            # Column reordering interface (if enabled and columns are selected)
            if enable_reorder and selected_columns:
                st.markdown("**📋 Click to reorder columns:**")
                reordered_columns = st.multiselect(
                    "Select columns in your preferred order:",
                    options=selected_columns,
                    default=selected_columns,
                    help="Click to select/deselect columns. The order you select them will be the display order in the table.",
                    key="column_order"
                )
                if reordered_columns:
                    selected_columns = reordered_columns            # Display the filtered dataframe
            if selected_columns:
                df_filtered = df_display[selected_columns]                # Configure dataframe display
                column_config = {}
                for col in selected_columns:
                    if 'Amount' in col:
                        column_config[col] = st.column_config.NumberColumn(
                            col,
                            format="$%.2f",
                            help="Grant amount in dollars"
                        )
                    elif 'Year' in col:
                        column_config[col] = st.column_config.NumberColumn(
                            col,
                            format="%d",
                            help="Year"
                        )
                    elif 'Description' in col:
                        column_config[col] = st.column_config.TextColumn(
                            col,
                            width="large",
                            help="Grant description"
                        )
                    elif col == 'Title':
                        column_config[col] = st.column_config.TextColumn(
                            col,
                            width="medium",
                            help="Grant title"
                        )
                    elif col in ['Researcher Name', 'Institution Name']:
                        column_config[col] = st.column_config.TextColumn(
                            col,
                            width="medium",
                            help="Name or institution"
                        )
                    elif col == 'Funding Body':
                        column_config[col] = st.column_config.TextColumn(
                            col,
                            width="medium",
                            help="Funding organization"
                        )
                    elif col == 'ORCID ID':
                        column_config[col] = st.column_config.TextColumn(
                            col,
                            width="small",
                            help="ORCID identifier"
                        )
                    elif col == 'Application ID':
                        column_config[col] = st.column_config.TextColumn(
                            col,
                            width="small",
                            help="Grant application ID"
                        )
                    elif 'Date' in col:
                        column_config[col] = st.column_config.TextColumn(
                            col,
                            width="small",
                            help="Date information"
                        )
                
                st.dataframe(
                    df_filtered,
                    use_container_width=True,
                    height=400,
                    column_config=column_config,
                    hide_index=not show_index,
                    column_order=selected_columns
                )
                
                # Display table stats
                st.caption(f"Showing {len(df_filtered)} records with {len(selected_columns)} columns")
                
                # Show helpful tips based on enabled features
                tips = []
                if enable_column_select:
                    tips.append("Select specific columns using the multiselect above")
                if enable_reorder:
                    tips.append("Click columns in the order you want them to appear (not drag-and-drop)")
                if not enable_column_select and not enable_reorder:
                    tips.append("Enable column selection or reordering for more customization options")
                
                if tips:
                    tip_text = " • ".join(tips)
                    st.info(f"💡 Tips: {tip_text}")
                
                # Download button for filtered data
                csv = df_filtered.to_csv(index=show_index)
                st.download_button(
                    label="📥 Download Filtered Results as CSV",
                    data=csv,
                    file_name="grant_results_filtered.csv",
                    mime="text/csv"
                )
                
            else:
                st.warning("Please select at least one column to display.")
                # Fallback download for original data
                csv = df_display.to_csv(index=False)
                st.download_button(
                    label="📥 Download All Results as CSV",
                    data=csv,
                    file_name="grant_results_all.csv",
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
