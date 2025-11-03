import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.neo4j_handler import Neo4jHandler
from utils.query_processor import QueryProcessor

st.set_page_config(page_title="Analytics Dashboard", page_icon="📊", layout="wide")

# Initialize Neo4j
@st.cache_resource
def init_neo4j():
    return Neo4jHandler(
        uri=st.secrets["neo4j"]["uri"],
        user=st.secrets["neo4j"]["user"],
        password=st.secrets["neo4j"]["password"]
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
                    df['total_funding'] = df['total_funding'].apply(lambda x: f"${x:,.0f}")
                    st.dataframe(df, use_container_width=True)
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
                st.metric("Total Funding", f"${df['total_funding'].sum():,.0f}")
            
            # Detailed table
            with st.expander("📋 Detailed Breakdown"):
                df['total_funding'] = df['total_funding'].apply(lambda x: f"${x:,.0f}")
                df['avg_grant'] = (df['total_funding'].str.replace('$', '').str.replace(',', '').astype(float) / df['grant_count']).apply(lambda x: f"${x:,.0f}")
                st.dataframe(df, use_container_width=True)
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
                df_display['total_funding'] = df_display['total_funding'].apply(lambda x: f"${x:,.0f}")
                df_display['avg_funding'] = df_display['avg_funding'].apply(lambda x: f"${x:,.0f}")
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
    
    # Search for researcher
    researcher_input = st.text_input("Enter researcher name:", "")
    
    if st.button("🔍 Find Collaborations", type="primary"):
        if researcher_input:
            try:
                # Get collaboration network
                collaborations = query_processor.get_collaboration_network(researcher_input)
                
                if collaborations:
                    st.success(f"Found {len(collaborations)} potential collaborations")
                    
                    # Create network visualization data
                    df = pd.DataFrame(collaborations)
                    
                    with st.expander("📋 View Collaboration Details"):
                        st.dataframe(df, use_container_width=True)
                    
                    st.info("💡 Switch to the Graph Visualization page for interactive network view")
                else:
                    st.warning("No collaborations found for this researcher")
                    
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a researcher name")
    
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
