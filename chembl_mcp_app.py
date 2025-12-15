import streamlit as st
from utils.llm_handler import LLMHandler
import pandas as pd
import json
from typing import Dict, Any, List, Optional
import logging
import asyncio
import subprocess
import os

# MCP ChEMBL Tool Integration
# Note: MCP tools are called through the MCP protocol
# In this environment, MCP tools are available as callable functions
# In production, you would use an MCP client library to call these tools

# MCP tool function mappings - these will be called via MCP protocol
# The actual implementation depends on your MCP setup
MCP_TOOL_FUNCTIONS = {
    "search_compounds": "mcp_chembl_search_compounds",
    "get_compound_info": "mcp_chembl_get_compound_info",
    "search_targets": "mcp_chembl_search_targets",
    "get_target_info": "mcp_chembl_get_target_info",
    "get_target_compounds": "mcp_chembl_get_target_compounds",
    "search_activities": "mcp_chembl_search_activities",
    "search_drugs": "mcp_chembl_search_drugs",
    "get_drug_info": "mcp_chembl_get_drug_info",
    "search_similar_compounds": "mcp_chembl_search_similar_compounds",
    "substructure_search": "mcp_chembl_substructure_search",
    "calculate_descriptors": "mcp_chembl_calculate_descriptors",
    "assess_drug_likeness": "mcp_chembl_assess_drug_likeness"
}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MCP Client imports (after logger is defined)
try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning("MCP Python SDK not available. Install with: pip install mcp")

# Page configuration
st.set_page_config(
    page_title="ChEMBL Database Explorer",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'current_results' not in st.session_state:
    st.session_state.current_results = None
if 'current_query_type' not in st.session_state:
    st.session_state.current_query_type = None

# Available ChEMBL MCP tools mapping
CHEMBL_TOOLS = {
    "search_compounds": "Search for compounds by name, synonym, or identifier",
    "get_compound_info": "Get detailed information for a specific compound",
    "search_targets": "Search for biological targets by name or type",
    "get_target_info": "Get detailed information for a specific target",
    "get_target_compounds": "Get compounds tested against a specific target",
    "search_activities": "Search bioactivity measurements and assay results",
    "search_drugs": "Search for approved drugs and clinical candidates",
    "get_drug_info": "Get drug development status and clinical trial information",
    "search_by_smiles": "Find chemically similar compounds using SMILES",
    "substructure_search": "Find compounds containing specific substructures",
    "calculate_descriptors": "Calculate molecular descriptors and properties",
    "assess_drug_likeness": "Assess drug-likeness using Lipinski Rule of Five"
}

def call_mcp_tool(tool_name: str, **kwargs):
    """
    Call an MCP ChEMBL tool
    Note: MCP tools configured in Cursor are available to the AI assistant,
    but not directly to Streamlit. This function provides a workaround.
    """
    # Map tool names to actual MCP tool function calls
    # These are the MCP tools available through the MCP server
    tool_map = {
        "search_compounds": lambda **kw: _call_mcp_tool_direct("mcp_chembl_search_compounds", **kw),
        "get_compound_info": lambda **kw: _call_mcp_tool_direct("mcp_chembl_get_compound_info", **kw),
        "search_targets": lambda **kw: _call_mcp_tool_direct("mcp_chembl_search_targets", **kw),
        "get_target_info": lambda **kw: _call_mcp_tool_direct("mcp_chembl_get_target_info", **kw),
        "get_target_compounds": lambda **kw: _call_mcp_tool_direct("mcp_chembl_get_target_compounds", **kw),
        "search_activities": lambda **kw: _call_mcp_tool_direct("mcp_chembl_search_activities", **kw),
        "search_drugs": lambda **kw: _call_mcp_tool_direct("mcp_chembl_search_drugs", **kw),
        "get_drug_info": lambda **kw: _call_mcp_tool_direct("mcp_chembl_get_drug_info", **kw),
        "search_similar_compounds": lambda **kw: _call_mcp_tool_direct("mcp_chembl_search_similar_compounds", **kw),
        "substructure_search": lambda **kw: _call_mcp_tool_direct("mcp_chembl_substructure_search", **kw),
        "calculate_descriptors": lambda **kw: _call_mcp_tool_direct("mcp_chembl_calculate_descriptors", **kw),
        "assess_drug_likeness": lambda **kw: _call_mcp_tool_direct("mcp_chembl_assess_drug_likeness", **kw)
    }
    
    if tool_name not in tool_map:
        raise ValueError(f"Unknown MCP tool: {tool_name}")
    
    # Call the tool
    return tool_map[tool_name](**kwargs)

@st.cache_resource
def init_mcp_client():
    """
    Initialize and cache MCP client connection to ChEMBL server
    """
    if not MCP_AVAILABLE:
        return None
    
    try:
        # Configure MCP server parameters based on Cursor's mcp.json config
        # The ChEMBL MCP server runs via Docker: docker run -i chembl-mcp-server
        server_params = StdioServerParameters(
            command="docker",
            args=["run", "-i", "chembl-mcp-server"],
            env=None
        )
        
        # Note: stdio_client is async, so we'll need to handle this differently
        # For Streamlit, we'll use a synchronous wrapper
        return server_params
    except Exception as e:
        logger.error(f"Failed to initialize MCP client: {e}")
        return None

def _call_mcp_tool_direct(tool_func_name: str, **kwargs):
    """
    Internal function to call MCP tools using MCP Python client
    """
    if not MCP_AVAILABLE:
        return {
            "status": "error",
            "message": "MCP Python SDK not installed. Install with: pip install mcp",
            "tool": tool_func_name,
            "parameters": kwargs
        }
    
    # Map tool function names to actual MCP tool names
    # The MCP tool names in ChEMBL server are typically without the "mcp_chembl_" prefix
    tool_name_map = {
        "mcp_chembl_search_compounds": "mcp_chembl_search_compounds",
        "mcp_chembl_get_compound_info": "mcp_chembl_get_compound_info",
        "mcp_chembl_search_targets": "mcp_chembl_search_targets",
        "mcp_chembl_get_target_info": "mcp_chembl_get_target_info",
        "mcp_chembl_get_target_compounds": "mcp_chembl_get_target_compounds",
        "mcp_chembl_search_activities": "mcp_chembl_search_activities",
        "mcp_chembl_search_drugs": "mcp_chembl_search_drugs",
        "mcp_chembl_get_drug_info": "mcp_chembl_get_drug_info",
        "mcp_chembl_search_similar_compounds": "mcp_chembl_search_similar_compounds",
        "mcp_chembl_substructure_search": "mcp_chembl_substructure_search",
        "mcp_chembl_calculate_descriptors": "mcp_chembl_calculate_descriptors",
        "mcp_chembl_assess_drug_likeness": "mcp_chembl_assess_drug_likeness"
    }
    
    # Get the actual MCP tool name (use the full name as it appears in the MCP server)
    mcp_tool_name = tool_name_map.get(tool_func_name, tool_func_name)
    
    try:
        # Use async MCP client
        # Since Streamlit doesn't handle async well, we'll use asyncio.run
        async def call_tool_async():
            server_params = init_mcp_client()
            if server_params is None:
                raise RuntimeError("MCP client not initialized")
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    await session.initialize()
                    
                    # List available tools (for debugging)
                    # tools = await session.list_tools()
                    # logger.info(f"Available MCP tools: {[t.name for t in tools.tools]}")
                    
                    # Call the tool - MCP tools expect arguments as a dict
                    result = await session.call_tool(mcp_tool_name, kwargs)
                    
                    # Extract the actual result content
                    if hasattr(result, 'content'):
                        # Result is a ToolResult object with content
                        if result.content:
                            # Content is typically a list of TextContent or ImageContent
                            content_items = []
                            for item in result.content:
                                if hasattr(item, 'text'):
                                    content_items.append(item.text)
                                elif hasattr(item, 'type') and item.type == 'text':
                                    content_items.append(item.text)
                            
                            if content_items:
                                # Try to parse as JSON if possible
                                try:
                                    return json.loads(''.join(content_items))
                                except json.JSONDecodeError:
                                    return ''.join(content_items)
                    
                    # Fallback: return the result object as-is
                    return result
        
        # Run the async function
        result = asyncio.run(call_tool_async())
        return result
        
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": f"Failed to start MCP server. Ensure Docker is running and 'chembl-mcp-server' image is available.",
            "error": str(e),
            "tool": tool_func_name,
            "parameters": kwargs
        }
    except Exception as e:
        logger.error(f"Error calling MCP tool {tool_func_name}: {e}")
        return {
            "status": "error",
            "message": f"Error calling MCP tool: {str(e)}",
            "tool": tool_func_name,
            "parameters": kwargs
        }

class ChEMBLMCPHandler:
    """Handler for ChEMBL MCP queries"""
    
    def __init__(self, llm_handler: LLMHandler):
        self.llm = llm_handler
    
    def interpret_query(self, user_query: str) -> Dict[str, Any]:
        """
        Use LLM to interpret the user query and determine which MCP tools to use
        """
        prompt = f"""You are a ChEMBL database query assistant. Analyze the following user query and determine:
1. What type of ChEMBL query this is (compound search, target search, drug search, activity search, etc.)
2. What parameters are needed for the query
3. Which MCP tool(s) should be used

Available MCP Tools:
- search_compounds: Search for compounds by name, synonym, or identifier
- get_compound_info: Get detailed info for a compound by ChEMBL ID (e.g., CHEMBL59)
- search_targets: Search for biological targets by name or type
- get_target_info: Get detailed info for a target by ChEMBL ID
- get_target_compounds: Get compounds tested against a target
- search_activities: Search bioactivity measurements
- search_drugs: Search for approved drugs and clinical candidates
- get_drug_info: Get drug development status
- search_similar_compounds: Find similar compounds using SMILES
- substructure_search: Find compounds with specific substructures
- calculate_descriptors: Calculate molecular properties
- assess_drug_likeness: Assess drug-likeness metrics

User Query: {user_query}

Respond in JSON format with:
{{
    "query_type": "compound_search|target_search|drug_search|activity_search|compound_info|target_info|similarity_search|substructure_search|descriptors|drug_likeness",
    "tool": "tool_name",
    "parameters": {{
        "param1": "value1",
        "param2": "value2"
    }},
    "extracted_info": {{
        "compound_name": "...",
        "chembl_id": "...",
        "target_name": "...",
        "smiles": "...",
        "activity_type": "..."
    }}
}}

Only return valid JSON, no additional text."""

        try:
            response = self.llm.process_query(prompt)
            # Try to extract JSON from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            result = json.loads(response)
            return result
        except Exception as e:
            logger.error(f"Error interpreting query: {e}")
            # Fallback interpretation
            return self._fallback_interpretation(user_query)
    
    def _fallback_interpretation(self, user_query: str) -> Dict[str, Any]:
        """Simple fallback query interpretation"""
        query_lower = user_query.lower()
        
        # Check for ChEMBL IDs
        import re
        chembl_id_match = re.search(r'CHEMBL\d+', user_query, re.IGNORECASE)
        if chembl_id_match:
            chembl_id = chembl_id_match.group(0).upper()
            if 'target' in query_lower or 'protein' in query_lower:
                return {
                    "query_type": "target_info",
                    "tool": "get_target_info",
                    "parameters": {"chembl_id": chembl_id},
                    "extracted_info": {"chembl_id": chembl_id}
                }
            else:
                return {
                    "query_type": "compound_info",
                    "tool": "get_compound_info",
                    "parameters": {"chembl_id": chembl_id},
                    "extracted_info": {"chembl_id": chembl_id}
                }
        
        # Check for drug-related queries
        if any(word in query_lower for word in ['drug', 'approved', 'clinical', 'fda']):
            return {
                "query_type": "drug_search",
                "tool": "search_drugs",
                "parameters": {"query": user_query},
                "extracted_info": {"query": user_query}
            }
        
        # Check for target-related queries
        if any(word in query_lower for word in ['target', 'protein', 'receptor', 'enzyme']):
            return {
                "query_type": "target_search",
                "tool": "search_targets",
                "parameters": {"query": user_query},
                "extracted_info": {"target_name": user_query}
            }
        
        # Check for activity-related queries
        if any(word in query_lower for word in ['activity', 'ic50', 'ki', 'kd', 'assay']):
            return {
                "query_type": "activity_search",
                "tool": "search_activities",
                "parameters": {"query": user_query},
                "extracted_info": {"query": user_query}
            }
        
        # Default to compound search
        return {
            "query_type": "compound_search",
            "tool": "search_compounds",
            "parameters": {"query": user_query},
            "extracted_info": {"compound_name": user_query}
        }
    
    def execute_mcp_query(self, interpretation: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the MCP query based on interpretation
        Note: In a real implementation, this would call MCP tools directly
        For now, we'll use the available MCP functions
        """
        tool = interpretation.get("tool")
        params = interpretation.get("parameters", {})
        
        try:
            # Map tool names to actual MCP function calls
            # Note: These would be actual MCP tool calls in production
            if tool == "search_compounds":
                # This would call: mcp_chembl_search_compounds
                return {
                    "status": "success",
                    "tool": tool,
                    "message": f"Would search compounds with: {params}",
                    "note": "MCP tool call would be made here"
                }
            elif tool == "get_compound_info":
                # This would call: mcp_chembl_get_compound_info
                return {
                    "status": "success",
                    "tool": tool,
                    "message": f"Would get compound info for: {params}",
                    "note": "MCP tool call would be made here"
                }
            elif tool == "search_targets":
                # This would call: mcp_chembl_search_targets
                return {
                    "status": "success",
                    "tool": tool,
                    "message": f"Would search targets with: {params}",
                    "note": "MCP tool call would be made here"
                }
            else:
                return {
                    "status": "success",
                    "tool": tool,
                    "message": f"Would execute {tool} with: {params}",
                    "note": "MCP tool call would be made here"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "tool": tool
            }

# Initialize handlers
@st.cache_resource
def init_llm_handler(model_name: str, _secrets: Dict):
    """Initialize LLM handler"""
    return LLMHandler(model_name, _secrets)

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
        index=3  # Default to GPT-4o
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
    
    # ChEMBL Info
    st.subheader("🧪 About ChEMBL")
    st.info("""
    ChEMBL is a manually curated database of bioactive molecules with drug-like properties.
    
    Search for:
    - Compounds and drugs
    - Biological targets
    - Bioactivity data
    - Drug development status
    """)

# Main content
st.title("🧪 ChEMBL Database Explorer")
st.markdown("Query the ChEMBL database using natural language with MCP integration")

# Info banner about MCP integration
with st.expander("ℹ️ About MCP Integration", expanded=True):
    st.info("""
    **Current Status**: MCP tools are configured in Cursor but not directly accessible in Streamlit.
    
    **How to Use**:
    - **Option 1 (Recommended)**: Ask the Cursor AI assistant to query ChEMBL directly
      - Example: "Search ChEMBL for aspirin" or "Get compound info for CHEMBL59"
    - **Option 2**: This app runs in demo mode, showing query interpretations
      - The app will interpret your queries and show what MCP tools would be called
      - Use the Cursor AI assistant to actually execute the queries
    
    **To Enable Direct MCP Access in Streamlit**:
    - Install MCP Python SDK: `pip install mcp`
    - Set up MCP client connection (see `CHEMBL_MCP_SETUP.md`)
    """)

# Initialize LLM handler
try:
    llm_handler = init_llm_handler(llm_option, dict(st.secrets))
    chembl_handler = ChEMBLMCPHandler(llm_handler)
except Exception as e:
    st.error(f"Failed to initialize LLM handler: {str(e)}")
    st.stop()

# Query input
st.subheader("💬 Ask a Question")

# Pre-populate if selected from history
if 'selected_query' in st.session_state:
    default_query = st.session_state.selected_query
    del st.session_state.selected_query
else:
    default_query = ""

query = st.text_area(
    "Enter your question about compounds, drugs, targets, or bioactivity:",
    value=default_query,
    height=100,
    placeholder="e.g., 'Find information about aspirin' or 'Search for compounds targeting EGFR' or 'Get details for CHEMBL59'"
)

# Example queries
with st.expander("📚 Example Queries", expanded=False):
    st.markdown("""
    **Compound Searches:**
    - "Find aspirin"
    - "Search for metformin"
    - "Get information about CHEMBL59"
    
    **Target Searches:**
    - "Find targets related to EGFR"
    - "Search for kinase targets"
    - "Get compounds targeting insulin receptor"
    
    **Drug Searches:**
    - "Find approved drugs for diabetes"
    - "Search for clinical candidates in oncology"
    
    **Activity Searches:**
    - "Find compounds with IC50 < 100nM for EGFR"
    - "Search for Ki values for dopamine receptor"
    """)

# Search button
if st.button("🔎 Search", type="primary", use_container_width=True):
    if query:
        with st.spinner("Processing query..."):
            try:
                # Add to history
                if query not in st.session_state.query_history:
                    st.session_state.query_history.append(query)
                
                # Step 1: Interpret query using LLM
                with st.spinner("Interpreting query..."):
                    interpretation = chembl_handler.interpret_query(query)
                
                # Display interpretation
                with st.expander("🔍 Query Interpretation", expanded=False):
                    st.json(interpretation)
                
                # Step 2: Execute MCP query using available MCP tools
                with st.spinner(f"Executing {interpretation.get('tool', 'query')}..."):
                    tool_name = interpretation.get("tool")
                    params = interpretation.get("parameters", {})
                    
                    results = None
                    error = None
                    
                    try:
                        # Call MCP tool using helper function
                        # Filter out None values from params
                        clean_params = {k: v for k, v in params.items() if v is not None}
                        results = call_mcp_tool(tool_name, **clean_params)
                        
                        # Check if result indicates MCP tools need proper setup
                        if isinstance(results, dict) and results.get("status") == "info":
                            # MCP tools not directly available - show helpful message
                            st.info("ℹ️ " + results.get("message", ""))
                            st.warning("""
                            **Note**: MCP tools are configured in Cursor but not directly accessible in Streamlit.
                            
                            **Options to use ChEMBL MCP tools:**
                            1. **Use Cursor AI Assistant**: Ask the AI assistant to query ChEMBL (e.g., "Search ChEMBL for aspirin")
                            2. **Set up MCP Python Client**: Install `mcp` Python package and configure client connection
                            3. **Use Demo Mode**: The app will show what queries would be executed
                            
                            For now, the app is running in demo mode showing query interpretations.
                            """)
                            # Store demo results
                            results = {
                                "demo_mode": True,
                                "tool": tool_name,
                                "parameters": clean_params,
                                "interpretation": interpretation
                            }
                            
                    except ValueError as e:
                        error = str(e)
                        st.error(f"Invalid tool or parameters: {error}")
                    except Exception as e:
                        error = str(e)
                        logger.error(f"Error calling MCP tool {tool_name}: {error}")
                        st.error(f"Error calling MCP tool: {error}")
                        # Show helpful troubleshooting info
                        with st.expander("🔧 Troubleshooting"):
                            st.markdown("""
                            **MCP Tools Not Available**
                            
                            MCP tools configured in Cursor are available to the AI assistant, but not directly to Streamlit apps.
                            
                            **To fix this:**
                            1. Install MCP Python SDK: `pip install mcp`
                            2. Set up MCP client connection in the app
                            3. Or use the Cursor AI assistant to query ChEMBL directly
                            
                            See `CHEMBL_MCP_SETUP.md` for detailed instructions.
                            """)
                
                # Store results
                st.session_state.current_results = {
                    "query": query,
                    "interpretation": interpretation,
                    "results": results,
                    "error": error
                }
                st.session_state.current_query_type = interpretation.get("query_type")
                
            except Exception as e:
                st.error(f"Error processing query: {str(e)}")
                st.exception(e)
    else:
        st.warning("Please enter a query")

# Display results
if st.session_state.current_results:
    results_data = st.session_state.current_results
    
    # Show query interpretation
    st.subheader("📊 Results")
    
    if results_data.get("error"):
        st.error(f"**Error:** {results_data['error']}")
    else:
        interpretation = results_data.get("interpretation", {})
        results = results_data.get("results")
        
        # Handle None or empty results
        if results is None:
            st.warning("No results returned. This might be because MCP tools are not directly accessible in Streamlit.")
            st.info("Try asking the Cursor AI assistant directly to query ChEMBL.")
        else:
            # Display tool used
            st.info(f"**Tool Used:** {interpretation.get('tool', 'Unknown')}")
            
            # Format and display results based on query type
            query_type = interpretation.get("query_type")
            
            # Handle string results (might be file paths or error messages)
            if isinstance(results, str):
                if results.startswith("c:\\") or results.startswith("/") or "\\" in results:
                    st.warning("Results were written to a file. This typically happens when MCP tools are called through the AI assistant.")
                    st.info(f"File path: {results}")
                    st.markdown("""
                    **Note:** When MCP tools return large results, they're written to files.
                    The Cursor AI assistant can read these files and display the results.
                    """)
                else:
                    st.write(results)
            else:
                # Check for demo mode
                if isinstance(results, dict) and results.get("demo_mode"):
                    st.warning("⚠️ Demo Mode: MCP tools are not directly accessible in Streamlit")
                    st.info(f"**Tool that would be called:** {results.get('tool', 'Unknown')}")
                    st.info(f"**Parameters:** {results.get('parameters', {})}")
                    st.markdown("""
                    **To actually execute this query:**
                    - Ask the Cursor AI assistant: "Search ChEMBL for [your query]"
                    - Or set up MCP Python client integration (see CHEMBL_MCP_SETUP.md)
                    """)
                elif query_type == "compound_search" or query_type == "compound_info":
                    st.subheader("🧬 Compound Information")
                    # Handle ChEMBL API response format
                    if isinstance(results, dict):
                        # Check if it's a ChEMBL API response with 'molecules' array
                        if "molecules" in results:
                            molecules = results["molecules"]
                            if molecules:
                                # Create a formatted display for compounds
                                for i, mol in enumerate(molecules[:10]):  # Show first 10
                                    with st.expander(f"🔬 {mol.get('molecule_chembl_id', f'Compound {i+1}')}", expanded=(i==0)):
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            st.markdown("**Basic Information:**")
                                            st.write(f"**ChEMBL ID:** {mol.get('molecule_chembl_id', 'N/A')}")
                                            st.write(f"**Preferred Name:** {mol.get('pref_name', 'N/A')}")
                                            
                                            if mol.get('molecule_properties'):
                                                props = mol['molecule_properties']
                                                st.markdown("**Molecular Properties:**")
                                                st.write(f"- Formula: {props.get('full_molformula', 'N/A')}")
                                                st.write(f"- MW: {props.get('full_mwt', 'N/A')} g/mol")
                                                st.write(f"- LogP: {props.get('alogp', 'N/A')}")
                                                st.write(f"- HBA: {props.get('hba', 'N/A')}, HBD: {props.get('hbd', 'N/A')}")
                                        
                                        with col2:
                                            if mol.get('molecule_structures'):
                                                structs = mol['molecule_structures']
                                                st.markdown("**Structure:**")
                                                st.code(f"SMILES: {structs.get('canonical_smiles', 'N/A')}", language=None)
                                                if structs.get('standard_inchi'):
                                                    st.code(f"InChI Key: {structs.get('standard_inchi_key', 'N/A')}", language=None)
                                        
                                        # Show synonyms if available
                                        if mol.get('molecule_synonyms'):
                                            st.markdown("**Synonyms:**")
                                            syns = [s.get('molecule_synonym', '') for s in mol['molecule_synonyms'][:5]]
                                            st.write(", ".join(syns))
                                            if len(mol['molecule_synonyms']) > 5:
                                                st.caption(f"... and {len(mol['molecule_synonyms']) - 5} more")
                                        
                                        # Show drug info if available
                                        if mol.get('max_phase'):
                                            st.markdown("**Drug Status:**")
                                            st.write(f"- Max Phase: {mol.get('max_phase', 'N/A')}")
                                            st.write(f"- First Approval: {mol.get('first_approval', 'N/A')}")
                                            if mol.get('availability_type'):
                                                st.write(f"- Availability: {mol.get('availability_type', 'N/A')}")
                                
                                if len(molecules) > 10:
                                    st.info(f"Showing 10 of {len(molecules)} compounds. Use the expanders above to view details.")
                                
                                # Also show as table for quick overview
                                st.subheader("📋 Quick Overview Table")
                                table_data = []
                                for mol in molecules[:20]:  # First 20 for table
                                    row = {
                                        "ChEMBL ID": mol.get('molecule_chembl_id', 'N/A'),
                                        "Name": mol.get('pref_name', 'N/A'),
                                        "Formula": mol.get('molecule_properties', {}).get('full_molformula', 'N/A'),
                                        "MW": mol.get('molecule_properties', {}).get('full_mwt', 'N/A'),
                                        "Max Phase": mol.get('max_phase', 'N/A'),
                                        "First Approval": mol.get('first_approval', 'N/A')
                                    }
                                    table_data.append(row)
                                
                                if table_data:
                                    df = pd.DataFrame(table_data)
                                    st.dataframe(df, use_container_width=True, hide_index=True)
                            else:
                                st.info("No compounds found")
                        else:
                            # Regular dict - show as JSON
                            st.json(results)
                    elif isinstance(results, list):
                        if results:
                            # Try to create DataFrame
                            try:
                                df = pd.DataFrame(results)
                                st.dataframe(df, use_container_width=True)
                            except Exception:
                                # If DataFrame creation fails, show as JSON
                                st.json(results)
                        else:
                            st.info("No compounds found")
                    else:
                        st.json(results)
                        
                elif query_type == "target_search" or query_type == "target_info":
                    st.subheader("🎯 Target Information")
                    if isinstance(results, dict):
                        # Handle ChEMBL target response format
                        if "targets" in results or "target" in results:
                            targets = results.get("targets") or [results.get("target")]
                            if targets and isinstance(targets, list):
                                for i, target in enumerate(targets[:10]):
                                    with st.expander(f"🎯 {target.get('target_chembl_id', f'Target {i+1}')}", expanded=(i==0)):
                                        st.write(f"**ChEMBL ID:** {target.get('target_chembl_id', 'N/A')}")
                                        st.write(f"**Name:** {target.get('pref_name', 'N/A')}")
                                        st.write(f"**Type:** {target.get('target_type', 'N/A')}")
                                        if target.get('organism'):
                                            st.write(f"**Organism:** {target.get('organism', 'N/A')}")
                                # Also show table
                                table_data = []
                                for target in targets[:20]:
                                    table_data.append({
                                        "ChEMBL ID": target.get('target_chembl_id', 'N/A'),
                                        "Name": target.get('pref_name', 'N/A'),
                                        "Type": target.get('target_type', 'N/A'),
                                        "Organism": target.get('organism', 'N/A')
                                    })
                                if table_data:
                                    df = pd.DataFrame(table_data)
                                    st.dataframe(df, use_container_width=True, hide_index=True)
                            else:
                                st.json(results)
                        else:
                            st.json(results)
                    elif isinstance(results, list):
                        if results:
                            try:
                                df = pd.DataFrame(results)
                                st.dataframe(df, use_container_width=True)
                            except Exception:
                                st.json(results)
                        else:
                            st.info("No targets found")
                    else:
                        st.json(results)
                        
                elif query_type == "drug_search" or query_type == "drug_info":
                    st.subheader("💊 Drug Information")
                    if isinstance(results, dict):
                        # Handle ChEMBL drug response format
                        if "drugs" in results or "drug" in results:
                            drugs = results.get("drugs") or [results.get("drug")]
                            if drugs and isinstance(drugs, list):
                                for i, drug in enumerate(drugs[:10]):
                                    with st.expander(f"💊 {drug.get('molecule_chembl_id', f'Drug {i+1}')}", expanded=(i==0)):
                                        st.write(f"**ChEMBL ID:** {drug.get('molecule_chembl_id', 'N/A')}")
                                        st.write(f"**Name:** {drug.get('pref_name', 'N/A')}")
                                        st.write(f"**Max Phase:** {drug.get('max_phase', 'N/A')}")
                                        st.write(f"**First Approval:** {drug.get('first_approval', 'N/A')}")
                                        if drug.get('indications'):
                                            st.write(f"**Indications:** {', '.join([ind.get('mesh_heading', '') for ind in drug.get('indications', [])[:3]])}")
                                # Table view
                                table_data = []
                                for drug in drugs[:20]:
                                    table_data.append({
                                        "ChEMBL ID": drug.get('molecule_chembl_id', 'N/A'),
                                        "Name": drug.get('pref_name', 'N/A'),
                                        "Max Phase": drug.get('max_phase', 'N/A'),
                                        "First Approval": drug.get('first_approval', 'N/A')
                                    })
                                if table_data:
                                    df = pd.DataFrame(table_data)
                                    st.dataframe(df, use_container_width=True, hide_index=True)
                            else:
                                st.json(results)
                        else:
                            st.json(results)
                    elif isinstance(results, list):
                        if results:
                            try:
                                df = pd.DataFrame(results)
                                st.dataframe(df, use_container_width=True)
                            except Exception:
                                st.json(results)
                        else:
                            st.info("No drugs found")
                    else:
                        st.json(results)
                    
                elif query_type == "activity_search":
                    st.subheader("📈 Bioactivity Data")
                    if isinstance(results, dict):
                        # Handle ChEMBL activity response format
                        if "activities" in results or "activity" in results:
                            activities = results.get("activities") or [results.get("activity")]
                            if activities and isinstance(activities, list):
                                try:
                                    df = pd.DataFrame(activities)
                                    st.dataframe(df, use_container_width=True)
                                except Exception:
                                    st.json(results)
                            else:
                                st.json(results)
                        else:
                            st.json(results)
                    elif isinstance(results, list):
                        if results:
                            try:
                                df = pd.DataFrame(results)
                                st.dataframe(df, use_container_width=True)
                            except Exception:
                                st.json(results)
                        else:
                            st.info("No activity data found")
                    else:
                        st.json(results)
                        
                else:
                    # Generic results display - try to format nicely
                    if isinstance(results, dict):
                        # Check for common ChEMBL response structures
                        if any(key in results for key in ['molecules', 'targets', 'drugs', 'activities']):
                            st.json(results)  # Show full JSON for complex nested structures
                        else:
                            # Simple dict - show as formatted
                            for key, value in results.items():
                                st.write(f"**{key}:**")
                                if isinstance(value, (dict, list)):
                                    st.json(value)
                                else:
                                    st.write(value)
                    elif isinstance(results, list):
                        try:
                            df = pd.DataFrame(results)
                            st.dataframe(df, use_container_width=True)
                        except Exception:
                            st.json(results)
                    else:
                        st.json(results)
        
        # Raw results (collapsible)
        with st.expander("🔧 Raw Results", expanded=False):
            st.json(results_data)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Powered by ChEMBL MCP • Built with Streamlit</p>
</div>
""", unsafe_allow_html=True)

