import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.neo4j_handler import Neo4jHandler
from utils.query_processor import QueryProcessor

# Try to import folium with fallback
try:
    import folium
    from streamlit_folium import st_folium
    FOLIUM_AVAILABLE = True
except ImportError:
    # Create dummy objects to prevent NameError
    folium = None
    st_folium = None
    FOLIUM_AVAILABLE = False

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

# Initialize Neo4j
@st.cache_resource
def init_neo4j():
    return Neo4jHandler(
        uri=st.secrets["neo4j"]["uri"],
        user=st.secrets["neo4j"]["user"],
        password=st.secrets["neo4j"]["password"],
        database=st.secrets["neo4j"]["database"]
    )

neo4j_handler = init_neo4j()
query_processor = QueryProcessor(neo4j_handler, None)

st.title("📊 Grant Analytics Dashboard")
st.markdown("Explore funding trends, distributions, and insights")

# Tabs for different analytics
tab1, tab2, tab3, tab4 = st.tabs([
    "🏢 Institutions", 
    "🔬 Research Areas", 
    "📈 Funding Trends",
    "👥 Collaboration Networks"
])

with tab1:
    st.header("Top Institutions by Funding")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        top_n = st.slider("Number of institutions", 5, 20, 10, key="inst_slider")
    
    with col1:
        try:
            # Get top institutions
            data = query_processor.get_top_institutions(limit=top_n)
            
            if data:
                df = pd.DataFrame(data)
                
                # Bar chart
                fig = px.bar(
                    df,
                    x='total_funding',
                    y='institution',
                    orientation='h',
                    title=f'Top {top_n} Institutions by Total Funding',
                    labels={'total_funding': 'Total Funding ($)', 'institution': 'Institution'},
                    color='total_funding',
                    color_continuous_scale='Viridis'
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
                
                # Data table
                with st.expander("📋 View Data Table"):
                    df_display = df.copy()
                    df_display['total_funding'] = df_display['total_funding'].apply(safe_format_amount)
                    st.dataframe(df_display, use_container_width=True)
            else:
                st.info("No data available")
                
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")

with tab2:
    st.header("Research Area Distribution")
    
    try:
        # Get research area distribution
        data = query_processor.get_research_area_distribution()
        
        if data:
            df = pd.DataFrame(data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Pie chart
                fig_pie = px.pie(
                    df,
                    values='grant_count',
                    names='research_area',
                    title='Grant Distribution by Research Area'
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Bar chart
                fig_bar = px.bar(
                    df,
                    x='total_funding',
                    y='research_area',
                    orientation='h',
                    title='Total Funding by Research Area',
                    labels={'total_funding': 'Total Funding ($)', 'research_area': 'Research Area'},
                    color='total_funding',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            
            # Summary metrics
            st.subheader("Summary Statistics")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Research Areas", len(df))
            with col2:
                st.metric("Total Grants", df['grant_count'].sum())
            with col3:
                total_sum = df['total_funding'].sum() if df['total_funding'].dtype in ['int64', 'float64'] else 0
                st.metric("Total Funding", safe_format_amount(total_sum))
            
            # Detailed table
            with st.expander("📋 Detailed Breakdown"):
                df_display = df.copy()
                # Calculate average grant before formatting
                df_display['avg_grant'] = df_display.apply(lambda row: safe_format_amount(row['total_funding'] / row['grant_count'] if row['grant_count'] > 0 else 0), axis=1)
                # Format total funding after calculation
                df_display['total_funding'] = df_display['total_funding'].apply(safe_format_amount)
                st.dataframe(df_display, use_container_width=True)
        else:
            st.info("No data available")
            
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")

with tab3:
    st.header("Funding Trends Over Time")
    
    col1, col2 = st.columns(2)
    with col1:
        start_year = st.number_input("Start Year", 2020, 2030, 2025, key="start")
    with col2:
        end_year = st.number_input("End Year", 2020, 2035, 2030, key="end")
    
    try:
        data = query_processor.get_funding_trends(start_year, end_year)
        
        if data:
            df = pd.DataFrame(data)
            
            # Line charts
            col1, col2 = st.columns(2)
            
            with col1:
                fig1 = px.line(
                    df,
                    x='year',
                    y='grant_count',
                    title='Number of Grants Over Time',
                    markers=True,
                    labels={'year': 'Year', 'grant_count': 'Number of Grants'}
                )
                fig1.update_traces(line_color='#FF6B6B', line_width=3)
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                fig2 = px.line(
                    df,
                    x='year',
                    y='total_funding',
                    title='Total Funding Over Time',
                    markers=True,
                    labels={'year': 'Year', 'total_funding': 'Total Funding ($)'}
                )
                fig2.update_traces(line_color='#4ECDC4', line_width=3)
                st.plotly_chart(fig2, use_container_width=True)
            
            # Average grant size
            fig3 = px.bar(
                df,
                x='year',
                y='avg_funding',
                title='Average Grant Size Over Time',
                labels={'year': 'Year', 'avg_funding': 'Average Funding ($)'},
                color='avg_funding',
                color_continuous_scale='Greens'
            )
            st.plotly_chart(fig3, use_container_width=True)
            
            # Data table
            with st.expander("📋 View Trends Data"):
                df_display = df.copy()
                df_display['total_funding'] = df_display['total_funding'].apply(safe_format_amount)
                df_display['avg_funding'] = df_display['avg_funding'].apply(safe_format_amount)
                st.dataframe(df_display, use_container_width=True)
        else:
            st.info("No data available for the selected time period")
            
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")

with tab4:
    st.header("Researcher Collaboration Networks")
    
    st.markdown("""
    Analyze collaboration patterns between researchers working on similar grants.
    """)
    
    # Initialize session state for collaboration results
    if 'collaboration_results' not in st.session_state:
        st.session_state.collaboration_results = None
    if 'collaboration_researcher' not in st.session_state:
        st.session_state.collaboration_researcher = ""
    
    # Search for researcher
    researcher_input = st.text_input("Enter researcher name:", "")
    
    if st.button("🔍 Find Collaborations", type="primary"):
        if researcher_input:
            try:
                # Get collaboration network
                collaborations = query_processor.get_collaboration_network(researcher_input)
                
                if collaborations:
                    # Store results in session state
                    st.session_state.collaboration_results = collaborations
                    st.session_state.collaboration_researcher = researcher_input
                    
                    # Get the actual researcher name from first result
                    actual_name = collaborations[0]['r1']['name']
                    st.success(f"Found {len(collaborations)} collaborations for **{actual_name}**")
                    
                    # Process collaborations for better display
                    collab_data = []
                    unique_collaborators = set()
                    
                    for collab in collaborations:
                        try:
                            collaborator = str(collab['r2']['name'])
                            if collaborator not in unique_collaborators:
                                unique_collaborators.add(collaborator)
                                # Safely handle grant title
                                grant_title = str(collab['g'].get('title', 'Unknown Grant'))
                                if len(grant_title) > 100:
                                    grant_title = grant_title[:100] + '...'
                                
                                collab_data.append({
                                    'Collaborator': collaborator,
                                    'Role': str(collab.get('r2_role', 'Unknown')),
                                    'Grant Title': grant_title,
                                    'Grant Amount': safe_format_amount(collab['g'].get('amount'))
                                })
                        except Exception as e:
                            # Skip problematic collaboration records
                            st.warning(f"Skipped problematic collaboration record: {str(e)}")
                            continue
                    
                    # Results will be displayed outside the button block
                else:
                    # Clear previous results and show suggestions
                    st.session_state.collaboration_results = None
                    suggestions = query_processor.get_researcher_suggestions(researcher_input)
                    
                    if suggestions:
                        st.warning(f"No collaborations found for '{researcher_input}'. Did you mean:")
                        for suggestion in suggestions:
                            st.write(f"• {suggestion['name']}")
                    else:
                        st.warning("No collaborations found for this researcher")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
                st.session_state.collaboration_results = None
        else:
            st.warning("Please enter a researcher name")
    
    # Display collaboration results if available in session state
    if st.session_state.collaboration_results:
        collaborations = st.session_state.collaboration_results
        researcher_name = st.session_state.collaboration_researcher
        
        # Process collaborations for display
        collab_data = []
        unique_collaborators = set()
        
        for collab in collaborations:
            try:
                collaborator = str(collab['r2']['name'])
                if collaborator not in unique_collaborators:
                    unique_collaborators.add(collaborator)
                    # Safely handle grant title
                    grant_title = str(collab['g'].get('title', 'Unknown Grant'))
                    if len(grant_title) > 100:
                        grant_title = grant_title[:100] + '...'
                    
                    collab_data.append({
                        'Collaborator': collaborator,
                        'Role': str(collab.get('r2_role', 'Unknown')),
                        'Grant Title': grant_title,
                        'Grant Amount': safe_format_amount(collab['g'].get('amount'))
                    })
            except Exception as e:
                # Skip problematic collaboration records
                continue
        
        # Create DataFrame for display
        df = pd.DataFrame(collab_data)
        
        st.divider()
        
        # Add map visualization
        st.subheader("🗺️ Collaborator Locations")
        
        if FOLIUM_AVAILABLE:
            # Get collaborator locations
            try:
                locations = query_processor.get_collaborator_locations(researcher_name)
                
                if locations:
                    # Create map centered on Australia
                    map_center = [-25.2744, 133.7751]  # Australia center
                    m = folium.Map(location=map_center, zoom_start=5)
                    
                    # Add markers for each collaborator location
                    for loc in locations:
                        popup_text = f"""
                        <b>{loc['collaborator']}</b><br>
                        Institution: {loc['institution']}<br>
                        City: {loc['city']}, {loc['state']}<br>
                        Collaborations: {loc['collaboration_count']}
                        """
                        
                        # Color code by collaboration count
                        if loc['collaboration_count'] >= 5:
                            color = 'red'
                        elif loc['collaboration_count'] >= 3:
                            color = 'orange'
                        else:
                            color = 'blue'
                        
                        folium.Marker(
                            location=[loc['latitude'], loc['longitude']],
                            popup=folium.Popup(popup_text, max_width=300),
                            tooltip=f"{loc['collaborator']} ({loc['city']})",
                            icon=folium.Icon(color=color, icon='user')
                        ).add_to(m)
                    
                    # Display map
                    map_data = st_folium(m, width=700, height=500)
                    
                    # Add legend
                    st.markdown("""
                    **Map Legend:**
                    - 🔴 Red: 5+ collaborations
                    - 🟠 Orange: 3-4 collaborations  
                    - 🔵 Blue: 1-2 collaborations
                    """)
                    
                    # Location summary
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        unique_cities = len(set(loc['city'] for loc in locations))
                        st.metric("Cities", unique_cities)
                    
                    with col2:
                        unique_states = len(set(loc['state'] for loc in locations))
                        st.metric("States/Territories", unique_states)
                    
                    with col3:
                        total_collabs = sum(loc['collaboration_count'] for loc in locations)
                        st.metric("Total Collaborations", total_collabs)
                    
                else:
                    st.info("No location data available for collaborators. This may be because institutions are not recognized in our database.")
            
            except Exception as e:
                st.warning(f"Could not load location data: {str(e)}")
        else:
            # Fallback: Show location data in a table format
            try:
                locations = query_processor.get_collaborator_locations(researcher_name)
                
                if locations:
                    st.info("Interactive map not available. Showing location data in table format:")
                    
                    # Create DataFrame for location data
                    location_df = pd.DataFrame(locations)
                    location_df = location_df[['collaborator', 'institution', 'city', 'state', 'collaboration_count']]
                    location_df.columns = ['Collaborator', 'Institution', 'City', 'State', 'Collaborations']
                    
                    st.dataframe(location_df, use_container_width=True)
                    
                    # Location summary
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        unique_cities = len(set(loc['city'] for loc in locations))
                        st.metric("Cities", unique_cities)
                    
                    with col2:
                        unique_states = len(set(loc['state'] for loc in locations))
                        st.metric("States/Territories", unique_states)
                    
                    with col3:
                        total_collabs = sum(loc['collaboration_count'] for loc in locations)
                        st.metric("Total Collaborations", total_collabs)
                else:
                    st.info("No location data available for collaborators.")
            
            except Exception as e:
                st.warning(f"Could not load location data: {str(e)}")
        
        st.subheader(f"🤝 Unique Collaborators ({len(unique_collaborators)})")
        st.dataframe(df, use_container_width=True)
        
        # Show all collaborations in expandable section
        with st.expander("📋 View All Collaboration Details"):
            all_collab_data = []
            for collab in collaborations:
                try:
                    all_collab_data.append({
                        'Researcher': str(collab['r1']['name']),
                        'Researcher Role': str(collab.get('r1_role', 'Unknown')),
                        'Collaborator': str(collab['r2']['name']),
                        'Collaborator Role': str(collab.get('r2_role', 'Unknown')),
                        'Grant Title': str(collab['g'].get('title', 'Unknown Grant')),
                        'Grant Amount': safe_format_amount(collab['g'].get('amount'))
                    })
                except Exception as e:
                    # Skip problematic records
                    continue
            all_df = pd.DataFrame(all_collab_data)
            st.dataframe(all_df, use_container_width=True)
        
        st.info("💡 Switch to the Graph Visualization page for interactive network view")
    
    # Example queries
    st.divider()
    st.subheader("💡 Example Analytics Queries")
    
    examples = {
        "Most Collaborative Institution": "Which institution has the most grant collaborations?",
        "Research Area Growth": "Which research area has grown the most in recent years?",
        "High-Value Grants": "What are the largest grants by funding amount?",
        "Emerging Researchers": "Who are the researchers with the most recent grants?"
    }
    
    for title, question in examples.items():
        with st.expander(f"📌 {title}"):
            st.markdown(f"**Question:** {question}")
            st.markdown("*Use the main query page to explore this question*")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>Analytics powered by Neo4j Graph Database</p>
</div>
""", unsafe_allow_html=True)
