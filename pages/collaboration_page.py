import streamlit as st
import pandas as pd
from utils.neo4j_handler import Neo4jHandler
from utils.llm_handler import LLMHandler
import json

# Initialize Neo4j
@st.cache_resource
def init_neo4j():
    return Neo4jHandler(
        uri=st.secrets["neo4j"]["uri"],
        user=st.secrets["neo4j"]["user"],
        password=st.secrets["neo4j"]["password"],
        database=st.secrets["neo4j"]["database"]
    )

def get_researcher_profile(neo4j_handler, researcher_name):
    """Fetch comprehensive researcher profile including grants and details"""
    query = """
    MATCH (r:Researcher {name: $researcher_name})
    OPTIONAL MATCH (r)-[:PRINCIPAL_INVESTIGATOR]->(g:Grant)
    OPTIONAL MATCH (r)-[:AFFILIATED_WITH]->(i:Institution)
    RETURN r.name as researcher_name,
           r.title as title,
           r.department as department,
           r.email as email,
           collect(DISTINCT i.name) as institutions,
           collect(DISTINCT {
               title: g.title,
               amount: g.amount,
               start_date: g.start_date,
               end_date: g.end_date,
               agency: g.agency,
               description: g.description,
               plain_description: g.plain_description
           }) as grants
    """
    
    results = neo4j_handler.execute_cypher(query, {"researcher_name": researcher_name})
    return results[0] if results else None

def get_grant_database_sample(neo4j_handler, limit=100):
    """Get a representative sample of the grant database for collaboration analysis"""
    query = """
    MATCH (g:Grant)
    OPTIONAL MATCH (r:Researcher)-[:PRINCIPAL_INVESTIGATOR]->(g)
    OPTIONAL MATCH (r)-[:AFFILIATED_WITH]->(i:Institution)
    RETURN g.title as grant_title,
           g.amount as amount,
           g.agency as agency,
           g.description as description,
           g.plain_description as plain_description,
           g.start_date as start_date,
           g.end_date as end_date,
           r.name as ci_name,
           r.title as ci_title,
           r.department as ci_department,
           i.name as institution
    ORDER BY rand()
    LIMIT $limit
    """
    
    return neo4j_handler.execute_cypher(query, {"limit": limit})

def format_grant_database(grant_data):
    """Format grant database for LLM analysis"""
    formatted_grants = []
    
    for grant in grant_data:
        grant_info = {
            "Grant Title": grant.get("grant_title", "N/A"),
            "CI Name": grant.get("ci_name", "N/A"),
            "CI Title": grant.get("ci_title", "N/A"),
            "Department": grant.get("ci_department", "N/A"),
            "Institution": grant.get("institution", "N/A"),
            "Agency": grant.get("agency", "N/A"),
            "Amount": grant.get("amount", "N/A"),
            "Description": grant.get("description", "N/A"),
            "Plain Description": grant.get("plain_description", "N/A")
        }
        formatted_grants.append(grant_info)
    
    return formatted_grants

def format_researcher_profile(profile_data):
    """Format researcher profile for LLM analysis"""
    if not profile_data:
        return "No researcher profile found."
    
    profile = {
        "Researcher Name": profile_data.get("researcher_name", "N/A"),
        "Title": profile_data.get("title", "N/A"),
        "Department": profile_data.get("department", "N/A"),
        "Email": profile_data.get("email", "N/A"),
        "Institutions": profile_data.get("institutions", []),
        "Grants": []
    }
    
    for grant in profile_data.get("grants", []):
        if grant and grant.get("title"):  # Only include grants with titles
            grant_info = {
                "Title": grant.get("title", "N/A"),
                "Amount": grant.get("amount", "N/A"),
                "Agency": grant.get("agency", "N/A"),
                "Start Date": grant.get("start_date", "N/A"),
                "End Date": grant.get("end_date", "N/A"),
                "Description": grant.get("description", "N/A"),
                "Plain Description": grant.get("plain_description", "N/A")
            }
            profile["Grants"].append(grant_info)
    
    return profile

def create_collaboration_prompt(grant_database, researcher_profile):
    """Create the collaboration analysis prompt"""
    prompt = """You will be acting as an innovative research collaboration advisor. Your task is to analyze a researcher's profile against a grant database to identify potential collaboration opportunities that extend beyond traditional disciplinary boundaries.

<grant_database>
{grant_database}
</grant_database>

<researcher_profile>
{researcher_profile}
</researcher_profile>

CRITICAL INSTRUCTIONS:
- You MUST identify AT LEAST 6-8 diverse collaboration opportunities
- Each opportunity should explore different aspects of the researcher's expertise
- Think creatively across ALL research fields and applications
- Don't limit yourself to similar research areas - explore unexpected connections
- Consider both academic research and industry applications

Your goal is to identify creative, interdisciplinary collaboration opportunities for this researcher by analyzing their work against the grants database. You should think both within and significantly beyond their current research field to find innovative applications and partnerships.

Guidelines for identifying collaborations:
- Look for researchers whose work could complement, enhance, or find novel applications with the target researcher's expertise
- Consider cross-disciplinary applications (e.g., biomedical techniques applied to engineering problems, social science methods applied to technical challenges, computational methods applied to experimental research)
- Think about the full research pipeline from basic research to clinical/practical applications
- Consider researchers who might need the target researcher's expertise for their own projects
- Look for emerging interdisciplinary fields where multiple expertises could converge
- Explore applications in: healthcare, technology, environmental science, social sciences, engineering, materials science, data science, policy, education
- Be innovative and think outside conventional academic silos while remaining practical and feasible

For each collaboration opportunity, you must provide:
- Potential Use: A clear description of the collaborative research opportunity or application
- Collaborator: Name and institutional affiliation of the potential collaborator
- Rationale: Why this collaboration makes sense and what each party brings
- Possible Funding Mechanism: Relevant funding bodies or grant types that might support this collaboration
- Innovation Level: Whether this represents an incremental advance or breakthrough potential

Before providing your final answer, use the scratchpad below to systematically analyze the researcher's profile and identify patterns in the database that suggest collaboration opportunities.

<scratchpad>
[Use this space to:
1. Summarize the key aspects of the researcher's work
2. Identify relevant themes and techniques in the grant database
3. Brainstorm cross-disciplinary connections
4. Evaluate the feasibility and innovation potential of each opportunity]
</scratchpad>

Structure your final response with separate sections for each collaboration opportunity. You MUST identify AT LEAST 6-8 diverse collaboration opportunities that range from practical near-term partnerships to more ambitious interdisciplinary ventures. Be highly innovative and think out-of-the-box while ensuring all suggestions remain grounded in practical feasibility.

IMPORTANT: 
- Complete your analysis fully - do not truncate your response
- Provide the complete scratchpad analysis first
- Then provide all 6-8 collaboration opportunities with full details
- Each opportunity should be clearly formatted with all required sections
- Think broadly across all research domains and applications

Your final output should consist of:
1. A complete scratchpad analysis
2. 6-8 detailed collaboration opportunity sections, each clearly labeled and containing all the required details listed above."""

    return prompt.format(
        grant_database=json.dumps(grant_database, indent=2),
        researcher_profile=json.dumps(researcher_profile, indent=2)
    )

def parse_collaboration_response(response_text):
    """Parse the LLM response to extract collaboration opportunities"""
    # Split the response into sections
    sections = []
    current_section = ""
    
    lines = response_text.split('\n')
    for line in lines:
        if line.strip().startswith('#') or line.strip().startswith('**') and line.strip().endswith('**'):
            # New section header
            if current_section.strip():
                sections.append(current_section.strip())
            current_section = line + '\n'
        else:
            current_section += line + '\n'
    
    # Add the last section
    if current_section.strip():
        sections.append(current_section.strip())
    
    return sections

neo4j_handler = init_neo4j()

st.title("🤝 Potential Research Collaborations")
st.markdown("*Discover innovative interdisciplinary collaboration opportunities based on grant database analysis*")

# Researcher selection
st.subheader("Select Researcher for Collaboration Analysis")

# Get list of all researchers
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_all_researchers():
    query = "MATCH (r:Researcher) RETURN r.name ORDER BY r.name"
    results = neo4j_handler.execute_cypher(query)
    return [r["r.name"] for r in results]

researchers = get_all_researchers()

selected_researcher = st.selectbox(
    "Choose a researcher:",
    options=[""] + researchers,
    index=0,
    help="Select a researcher to analyze potential collaborations"
)

if selected_researcher:
    st.subheader(f"Collaboration Analysis for: {selected_researcher}")
    
    # Analysis parameters
    col1, col2 = st.columns(2)
    
    with col1:
        database_sample_size = st.slider(
            "Grant Database Sample Size",
            min_value=50,
            max_value=500,
            value=100,
            step=25,
            help="Number of grants to analyze for collaboration opportunities (100-150 recommended for comprehensive analysis)"
        )
    
    with col2:
        llm_option = st.selectbox(
            "Select LLM for Analysis",
            [
                "Claude 3.7 Sonnet",
                "Claude 4.0 Sonnet", 
                "Claude 4.5 Sonnet",
                "GPT-4o",
                "GPT-4o Mini",
                "Gemini 2.0 Flash",
                "DeepSeek V3"
            ],
            index=2,
            help="Choose the LLM model for collaboration analysis"
        )
    
    if st.button("🔍 Analyze Collaboration Opportunities", type="primary"):
        with st.spinner("Analyzing researcher profile and grant database..."):
            try:
                # Get researcher profile
                researcher_profile = get_researcher_profile(neo4j_handler, selected_researcher)
                if not researcher_profile:
                    st.error(f"No profile found for researcher: {selected_researcher}")
                    st.stop()
                
                # Get grant database sample
                grant_database = get_grant_database_sample(neo4j_handler, database_sample_size)
                if not grant_database:
                    st.error("No grant data found in database")
                    st.stop()
                
                # Format data for LLM
                formatted_profile = format_researcher_profile(researcher_profile)
                formatted_grants = format_grant_database(grant_database)
                
                # Create prompt
                collaboration_prompt = create_collaboration_prompt(formatted_grants, formatted_profile)
                
                # Initialize LLM handler
                llm_handler = LLMHandler(llm_option, dict(st.secrets))
                
                st.info(f"🔍 Analyzing {len(formatted_grants)} grants for collaboration opportunities...")
                st.info(f"🤖 Using {llm_option} for analysis...")
                
                # Show prompt size for debugging
                prompt_length = len(collaboration_prompt)
                st.info(f"📊 Analysis prompt size: {prompt_length:,} characters")
                
                # Get collaboration analysis
                with st.spinner("🧠 Generating comprehensive collaboration recommendations..."):
                    response = llm_handler.process_query(
                        collaboration_prompt,
                        llm_option=llm_option,
                        enable_google_search=False  # We don't need web search for this analysis
                    )
                
                # Display results
                st.success("✅ Collaboration analysis complete!")
                
                # Show researcher profile summary
                with st.expander("📋 Researcher Profile Summary", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Name:** {formatted_profile['Researcher Name']}")
                        st.write(f"**Title:** {formatted_profile['Title']}")
                        st.write(f"**Department:** {formatted_profile['Department']}")
                        
                    with col2:
                        st.write(f"**Institution(s):** {', '.join(formatted_profile['Institutions'])}")
                        st.write(f"**Number of Grants:** {len(formatted_profile['Grants'])}")
                
                # Display collaboration opportunities
                st.subheader("🎯 Collaboration Opportunities")
                
                # Parse and display the response
                collaboration_sections = parse_collaboration_response(response)
                
                if collaboration_sections:
                    for i, section in enumerate(collaboration_sections, 1):
                        with st.expander(f"Opportunity {i}", expanded=True):
                            st.markdown(section)
                else:
                    # If parsing fails, show raw response
                    st.markdown(response)
                
                # Additional analysis metrics
                st.subheader("📊 Analysis Metrics")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Grants Analyzed", len(formatted_grants))
                
                with col2:
                    st.metric("Researcher Grants", len(formatted_profile['Grants']))
                
                with col3:
                    st.metric("LLM Model", llm_option)
                
            except Exception as e:
                st.error(f"Error during collaboration analysis: {str(e)}")
                st.exception(e)

else:
    st.info("👆 Please select a researcher to begin collaboration analysis")
    
    # Show some statistics about the database
    st.subheader("📈 Database Overview")
    
    try:
        # Get basic stats
        stats_query = """
        MATCH (r:Researcher) 
        OPTIONAL MATCH (r)-[:PRINCIPAL_INVESTIGATOR]->(g:Grant)
        RETURN count(DISTINCT r) as total_researchers,
               count(DISTINCT g) as total_grants,
               count(DISTINCT r.department) as departments,
               count(DISTINCT g.agency) as agencies
        """
        
        stats = neo4j_handler.execute_cypher(stats_query)[0]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Researchers", stats["total_researchers"])
        
        with col2:
            st.metric("Total Grants", stats["total_grants"])
        
        with col3:
            st.metric("Departments", stats["departments"])
        
        with col4:
            st.metric("Funding Agencies", stats["agencies"])
            
    except Exception as e:
        st.warning("Could not load database statistics")

# Help section
with st.expander("ℹ️ How It Works"):
    st.markdown("""
    **Collaboration Discovery Process:**
    
    1. **Researcher Profile Analysis**: Extracts comprehensive information about the selected researcher including their grants, research areas, and institutional affiliations.
    
    2. **Database Sampling**: Analyzes a representative sample of grants from the database to identify potential collaboration patterns.
    
    3. **Interdisciplinary Matching**: Uses advanced LLM analysis to identify creative, cross-disciplinary collaboration opportunities that extend beyond traditional academic boundaries.
    
    4. **Innovation Assessment**: Evaluates each opportunity for both practical feasibility and breakthrough potential.
    
    **What You'll Get:**
    - **Potential Use**: Clear description of collaborative research opportunities
    - **Collaborator Details**: Names and institutional affiliations of potential partners
    - **Rationale**: Why each collaboration makes sense and what each party contributes
    - **Funding Mechanisms**: Relevant funding bodies and grant types
    - **Innovation Level**: Assessment of advancement potential
    
    **Best Practices:**
    - Use larger sample sizes for more comprehensive analysis
    - Try different LLM models for varied perspectives
    - Focus on researchers with multiple grants for richer analysis
    """)