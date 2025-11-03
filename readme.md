# Hybrid GraphRAG System for Research Grants

A comprehensive hybrid GraphRAG (Graph Retrieval-Augmented Generation) system that combines Neo4j graph database with multiple LLM providers for intelligent querying and visualization of research grant data.

## 🌟 Features

- **Multi-LLM Support**: Claude (3.5, 4.0, 4.5), GPT-4o, Gemini 2.0 Flash, DeepSeek
- **Hybrid Search**: Combines vector embeddings with graph relationships
- **Interactive Visualizations**: Pyvis-based network graphs
- **Natural Language Queries**: Convert plain English to Cypher
- **Analytics Dashboard**: Funding trends, research area distributions, collaboration networks
- **Query History**: Track and reuse previous queries

## 📋 Prerequisites

- Python 3.8+
- Neo4j Database (5.11+ recommended for vector search)
- API keys for at least one LLM provider

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Neo4j

**Option A: Neo4j Desktop**
- Download from https://neo4j.com/download/
- Create a new database
- Note the bolt URI, username, and password

**Option B: Neo4j Aura (Cloud)**
- Sign up at https://neo4j.com/cloud/aura/
- Create a free instance
- Download connection credentials

### 3. Configure Secrets

Create `.streamlit/secrets.toml`:

```toml
[neo4j]
uri = "bolt://localhost:7687"
user = "neo4j"
password = "your_password"

[anthropic]
api_key = "sk-ant-your-key"

[openai]
api_key = "sk-your-key"

[google]
api_key = "your-key"

[deepseek]
api_key = "your-key"
```

### 4. Ingest Data

```bash
# Set environment variables (or update script directly)
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your_password"
export CSV_PATH="combined_grants_small.csv"

# Run ingestion
python scripts/ingest_data.py
```

### 5. Run Application

```bash
streamlit run app.py
```

Visit http://localhost:8501 in your browser.

## 📁 Project Structure

```
.
├── app.py                          # Main Streamlit application
├── pages/
│   ├── 1_🌐_Graph_Visualization.py # Graph visualization page
│   └── 2_📊_Analytics.py           # Analytics dashboard
├── utils/
│   ├── neo4j_handler.py            # Neo4j database operations
│   ├── llm_handler.py              # Multi-LLM interface
│   └── query_processor.py          # Query processing logic
├── scripts/
│   ├── ingest_data.py              # Data ingestion script
│   └── generate_embeddings.py      # Generate vector embeddings
├── .streamlit/
│   └── secrets.toml                # Configuration (create this)
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## 🎯 Usage Guide

### Main Query Page

1. **Select LLM**: Choose your preferred language model
2. **Enter Query**: Type natural language questions like:
   - "Which grants focus on cancer research?"
   - "Show me all grants at University of Melbourne"
   - "Find grants related to climate change with funding over $1M"
3. **View Results**: See generated Cypher, data tables, and AI summaries
4. **Query History**: Click previous queries in sidebar to reuse them

### Graph Visualization

Three visualization modes:

1. **Random Sample**: Generate random subgraphs
2. **Node Browser**: Select specific node types and relationships
3. **Custom Query**: Write your own Cypher queries

### Analytics Dashboard

Explore:
- Top institutions by funding
- Research area distributions
- Funding trends over time
- Collaboration networks

## 📊 Graph Schema

The system creates the following graph structure:

```
(:Grant) - Nodes representing individual grants
(:Researcher) - Principal investigators
(:Institution) - Universities and research organizations
(:ResearchArea) - Broad research categories
(:ResearchField) - Detailed research fields

Relationships:
(:Researcher)-[:PRINCIPAL_INVESTIGATOR]->(:Grant)
(:Grant)-[:HOSTED_BY]->(:Institution)
(:Grant)-[:IN_AREA]->(:ResearchArea)
(:Grant)-[:HAS_FIELD]->(:ResearchField)
```

## 🔍 Example Queries

### Natural Language (Main Page)
- "What are the highest funded grants?"
- "Which researchers work on neuroscience?"
- "Show grants at Monash University starting in 2026"

### Cypher (Visualization Page)
```cypher
// Find collaboration networks
MATCH (r1:Researcher)-[:PRINCIPAL_INVESTIGATOR]->(g:Grant)
      <-[:PRINCIPAL_INVESTIGATOR]-(r2:Researcher)
WHERE r1 <> r2
RETURN r1, r2, g
LIMIT 20

// Grants by research area
MATCH (g:Grant)-[:IN_AREA]->(a:ResearchArea)
WHERE a.name = 'Public Health Research'
RETURN g, a
LIMIT 15
```

## 🧪 Advanced Features

### Vector Search (Optional)

Generate embeddings for semantic search:

```bash
python scripts/generate_embeddings.py
```

This requires:
- Neo4j 5.11+
- `sentence-transformers` library
- Vector index creation (done by ingestion script)

### Custom LLM Integration

Add new LLM providers in `utils/llm_handler.py`:

```python
elif "YourLLM" in self.model_name:
    self.provider = "yourllm"
    # Initialize your LLM client
```

### Extending the Schema

Modify `scripts/ingest_data.py` to add new node types or relationships:

```python
# Example: Add funding body as separate node
funding_cypher = """
MERGE (fb:FundingBody {name: $name})
WITH fb
MATCH (g:Grant {application_id: $application_id})
MERGE (g)-[:FUNDED_BY]->(fb)
"""
```

## 🐛 Troubleshooting

### Connection Issues

```bash
# Test Neo4j connection
python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password')); driver.verify_connectivity(); print('Connected!')"
```

### LLM API Errors

- Verify API keys in secrets.toml
- Check rate limits
- Ensure internet connectivity

### Vector Search Not Working

- Requires Neo4j 5.11+
- Run embedding generation script
- Verify vector index creation

### Empty Results

- Check data ingestion completed
- Verify Cypher query syntax
- Try simpler queries first

## 📚 Documentation

- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [GraphRAG Concepts](https://neo4j.com/docs/graph-data-science/)

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Additional LLM providers
- Enhanced analytics visualizations
- Better embedding models
- Query optimization
- UI/UX improvements

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Neo4j for the graph database
- Streamlit for the web framework
- Anthropic, OpenAI, Google, DeepSeek for LLM APIs
- Pyvis for network visualizations

## 📞 Support

For issues and questions:
- Check troubleshooting section
- Review Neo4j and Streamlit docs
- Open an issue on GitHub

---

**Built with ❤️ using Neo4j GraphRAG**
