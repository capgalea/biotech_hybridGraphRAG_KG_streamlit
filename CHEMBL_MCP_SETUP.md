# ChEMBL MCP Streamlit App Setup Guide

This guide explains how to set up and run the ChEMBL MCP Streamlit app that queries the ChEMBL database using MCP (Model Context Protocol) and LLMs.

## Overview

The `chembl_mcp_app.py` Streamlit app allows you to:
- Query the ChEMBL database using natural language
- Use an LLM to interpret queries and select appropriate MCP tools
- Display results from ChEMBL in a user-friendly interface

## Prerequisites

1. **MCP ChEMBL Server**: The ChEMBL MCP server must be running (via Docker)
2. **MCP Configuration**: MCP must be configured in your environment (see `~/.cursor/mcp.json`)
3. **MCP Python SDK**: Install the MCP Python client library
4. **LLM API Keys**: You need API keys for at least one LLM provider (OpenAI, Anthropic, or Google)
5. **Docker**: Docker must be installed and running to launch the ChEMBL MCP server

## MCP Configuration

Ensure your MCP configuration file (`~/.cursor/mcp.json`) includes the ChEMBL server:

```json
{
  "mcpServers": {
    "chembl": {
      "command": "docker",
      "args": ["run", "-i", "chembl-mcp-server"],
      "env": {}
    }
  }
}
```

## Installation

1. **Install MCP Python SDK**:
   ```bash
   pip install mcp
   ```
   
   Or install all requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify Docker is Running**:
   ```bash
   docker --version
   docker ps
   ```

3. **Pull/Prepare ChEMBL MCP Server Image**:
   Ensure the `chembl-mcp-server` Docker image is available. If not, you may need to build it or pull it from a registry.

## Running the App

1. **Start the ChEMBL MCP Server** (if not already running):
   The MCP server will be started automatically by the app when needed, but you can also start it manually:
   ```bash
   docker run -i chembl-mcp-server
   ```

2. **Configure Streamlit Secrets**:
   Create a `.streamlit/secrets.toml` file with your LLM API keys:
   ```toml
   [openai]
   api_key = "your-openai-api-key"

   [anthropic]
   api_key = "your-anthropic-api-key"

   [google]
   api_key = "your-google-api-key"
   ```

3. **Run the Streamlit App**:
   ```bash
   streamlit run chembl_mcp_app.py
   ```

## How It Works

1. **Query Input**: User enters a natural language query about compounds, drugs, targets, or bioactivity
2. **LLM Interpretation**: The LLM analyzes the query and determines:
   - What type of ChEMBL query it is
   - Which MCP tool to use
   - What parameters are needed
3. **MCP Tool Execution**: The appropriate MCP ChEMBL tool is called with the extracted parameters
4. **Results Display**: Results are formatted and displayed in the Streamlit interface

## Available Query Types

- **Compound Searches**: "Find aspirin", "Search for metformin", "Get information about CHEMBL59"
- **Target Searches**: "Find targets related to EGFR", "Search for kinase targets"
- **Drug Searches**: "Find approved drugs for diabetes", "Search for clinical candidates"
- **Activity Searches**: "Find compounds with IC50 < 100nM for EGFR"
- **Similarity Searches**: "Find compounds similar to [SMILES string]"
- **Substructure Searches**: "Find compounds containing [substructure SMILES]"

## MCP Tool Integration

The app uses the following MCP ChEMBL tools:
- `mcp_chembl_search_compounds`: Search for compounds
- `mcp_chembl_get_compound_info`: Get compound details
- `mcp_chembl_search_targets`: Search for biological targets
- `mcp_chembl_get_target_info`: Get target details
- `mcp_chembl_get_target_compounds`: Get compounds for a target
- `mcp_chembl_search_activities`: Search bioactivity data
- `mcp_chembl_search_drugs`: Search for drugs
- `mcp_chembl_get_drug_info`: Get drug information
- `mcp_chembl_search_similar_compounds`: Find similar compounds
- `mcp_chembl_substructure_search`: Substructure search
- `mcp_chembl_calculate_descriptors`: Calculate molecular descriptors
- `mcp_chembl_assess_drug_likeness`: Assess drug-likeness

## Troubleshooting

### MCP Tools Not Available

If you see "MCP tools not available" errors:
1. Ensure the ChEMBL MCP server Docker container is running
2. Check that MCP is properly configured in `~/.cursor/mcp.json`
3. Verify that the MCP client can connect to the server

### LLM API Errors

If you see LLM-related errors:
1. Check that your API keys are correctly set in `.streamlit/secrets.toml`
2. Verify that you have sufficient API credits/quota
3. Try switching to a different LLM provider

### No Results Returned

If queries return no results:
1. Try rephrasing your query
2. Check that compound names or ChEMBL IDs are spelled correctly
3. Verify that the ChEMBL database is accessible through the MCP server

## Important: MCP Tools in Streamlit

**Current Limitation**: MCP tools configured in Cursor are available to the AI assistant, but **not directly accessible** to Streamlit apps running as separate processes.

### Why This Happens

- MCP tools in Cursor are available to the AI assistant through the MCP protocol
- Streamlit apps run as separate Python processes that don't have direct access to MCP tools
- MCP tools need to be called through an MCP client library, not as direct Python functions

### Solutions

#### Option 1: Use Cursor AI Assistant (Easiest)
Simply ask the AI assistant in Cursor to query ChEMBL:
- "Search ChEMBL for aspirin"
- "Get compound info for CHEMBL59"
- "Find targets related to EGFR"

The AI assistant has direct access to MCP tools.

#### Option 2: Set Up MCP Python Client (For Streamlit Integration) ✅ **NOW IMPLEMENTED**

The app now includes MCP Python client integration! Here's what's been set up:

1. **MCP Python SDK**: Added to `requirements.txt`
   ```bash
   pip install mcp
   ```

2. **Automatic MCP Client**: The app automatically:
   - Detects if MCP SDK is installed
   - Connects to the ChEMBL MCP server via Docker
   - Calls MCP tools directly through the MCP protocol
   - Handles errors gracefully if MCP is not available

3. **How It Works**:
   - The app uses `StdioServerParameters` to connect to the Docker-based MCP server
   - MCP tools are called asynchronously and wrapped for Streamlit
   - Results are automatically formatted and displayed

4. **Troubleshooting**:
   - If you see "MCP Python SDK not available", run: `pip install mcp`
   - If Docker errors occur, ensure Docker is running and the `chembl-mcp-server` image exists
   - Check that your `~/.cursor/mcp.json` configuration matches the Docker command

#### Option 3: Create an API Bridge

Create a separate service that:
- Connects to MCP server
- Exposes MCP tools via REST API
- Streamlit app calls the API instead of MCP directly

#### Option 4: Demo Mode (Current Implementation)

The app currently runs in "demo mode" where it:
- Interprets queries using LLM
- Shows what MCP tools would be called
- Displays the parameters that would be used
- Provides instructions for actual execution

## Notes

- The MCP tools are called through the MCP protocol, not as direct Python functions
- In production, you would use an MCP client library to make these calls
- The current implementation shows query interpretations in demo mode
- Results are displayed in tables and JSON format for easy inspection
- For actual ChEMBL queries, use the Cursor AI assistant or set up proper MCP client integration

