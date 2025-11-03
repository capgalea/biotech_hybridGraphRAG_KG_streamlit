# Complete GraphRAG System Documentation

## 📚 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [File Structure](#file-structure)
4. [Setup & Installation](#setup--installation)
5. [Usage Guide](#usage-guide)
6. [API Reference](#api-reference)
7. [Deployment Options](#deployment-options)
8. [Troubleshooting](#troubleshooting)
9. [Contributing](#contributing)

---

## System Overview

This is a production-ready hybrid GraphRAG (Graph Retrieval-Augmented Generation) system that combines:

- **Graph Database**: Neo4j for structured relationship storage
- **Vector Search**: Semantic embeddings for similarity search
- **Multi-LLM Support**: Claude, GPT, Gemini, DeepSeek
- **Interactive UI**: Streamlit-based web interface
- **Visualizations**: Pyvis network graphs and Plotly charts

### Key Features

✅ Natural language to Cypher query translation  
✅ Hybrid retrieval (graph + vector)  
✅ Interactive graph visualization  
✅ Analytics dashboard  
✅ Query history and caching  
✅ Multi-page application  
✅ Docker deployment ready  
✅ Kubernetes manifests included  

---

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit Frontend                       │
│  ┌────────────┐  ┌────────────┐  ┌──────────────────────┐  │
│  │   Query    │  │   Graph    │  │     Analytics        │  │
│  │    Page    │  │    Viz     │  │     Dashboard        │  │
│  └────────────┘  └────────────┘  └──────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
              ┌───────▼────────┐
              │  Query         │
              │  Processor     │
              └───────┬────────┘
                      │
        ┏━━━━━━━━━━━━━┻━━━━━━━━━━━━━┓
        ▼                            ▼
┌───────────────┐            ┌──────────────┐
│  LLM Handler  │            │   Neo4j      │
│  Multi-model  │            │   Handler    │
└───────────────┘            └──────────────┘
        │                            │
        ▼                            ▼
┌───────────────┐            ┌──────────────┐
│  Claude       │            │   Neo4j      │
│  GPT-4        │            │   Database   │
│  Gemini       │            │              │
│  DeepSeek     │            │  Graphs +    │
│               │            │  Vectors     │
└───────────────┘            └──────────────┘
```

### Data Flow

1. **User Query** → Natural language input
2. **Schema Retrieval** → Get graph structure
3. **LLM Processing** → Convert to Cypher
4. **Query Execution** → Run on Neo4j
5. **Result Processing** → Format and analyze
6. **UI Rendering** → Display to user

### Graph Schema

```cypher
// Nodes
(:Grant {
  application_id: INT,
  title: STRING,
  description: STRING,
  amount: FLOAT,
  start_year: INT,
  embedding: LIST<FLOAT>
})

(:Researcher {
  name: STRING,
  orcid_id: STRING
})

(:Institution {
  name: STRING
})

(:ResearchArea {
  name: STRING
})

(:ResearchField {
  name: STRING
})

// Relationships
(:Researcher)-[:PRINCIPAL_INVESTIGATOR]->(:Grant)
(:Grant)-[:HOSTED_BY]->(:Institution)
(:Grant)-[:IN_AREA]->(:ResearchArea)
(:Grant)-[:HAS_FIELD]->(:ResearchField)
```

---

## File Structure

```
graphrag-system/
│
├── app.py                              # Main application entry
│
├── pages/                              # Streamlit pages
│   ├── 1_🌐_Graph_Visualization.py    # Graph viz page
│   └── 2_📊_Analytics.py              # Analytics page
│
├── utils/                              # Core utilities
│   ├── __init__.py
│   ├── neo4j_handler.py               # Neo4j operations
│   ├── llm_handler.py                 # LLM integrations
│   └── query_processor.py             # Query logic
│
├── scripts/                            # Setup scripts
│   ├── ingest_data.py                 # Data loader
│   └── generate_embeddings.py         # Vector generation
│
├── .streamlit/                         # Streamlit config
│   └── secrets.toml                   # API keys (create this)
│
├── deployment/                         # Deployment configs
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── kubernetes.yaml
│
├── config.py                          # Configuration
├── requirements.txt                   # Dependencies
├── README.md                          # Overview docs
├── QUICKSTART.md                      # Quick setup
├── COMPLETE_SYSTEM_GUIDE.md          # This file
└── combined_grants_small.csv         # Sample data
```

---

## Setup & Installation

### Prerequisites

- Python 3.8+
- Neo4j 5.11+ (for vector search)
- At least one LLM API key
- 4GB RAM minimum
- 10GB disk space

### Installation Steps

#### 1. Environment Setup

```bash
# Clone or navigate to project
cd graphrag-system

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Neo4j Setup

**Option A: Neo4j Aura (Easiest)**

```bash
# 1. Visit https://neo4j.com/cloud/aura-free/
# 2. Create free instance
# 3. Save credentials
# 4. Wait for "Running" status
```

**Option B: Neo4j Desktop**

```bash
# 1. Download from https://neo4j.com/download/
# 2. Install and launch
# 3. Create new project
# 4. Add database
# 5. Start database
```

**Option C: Docker**

```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5.15-community
```

#### 3. Configuration

Create `.streamlit/secrets.toml`:

```toml
[neo4j]
uri = "bolt://localhost:7687"
user = "neo4j"
password = "your_password"

[anthropic]
api_key = "sk-ant-xxxxx"

[openai]
api_key = "sk-xxxxx"

[google]
api_key = "xxxxx"

[deepseek]
api_key = "xxxxx"
```

#### 4. Data Ingestion

```bash
# Set environment variables
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your_password"

# Run ingestion
python scripts/ingest_data.py

# Expected output:
# ✅ Data ingestion completed successfully!
# Grants: 20
# Researchers: 19
# Institutions: 8
```

#### 5. Generate Embeddings (Optional)

```bash
python scripts/generate_embeddings.py

# This adds vector search capability
# Requires Neo4j 5.11+
```

#### 6. Launch Application

```bash
streamlit run app.py

# Opens browser at http://localhost:8501
```

---

## Usage Guide

### Main Query Page

**Features:**
- Natural language input
- LLM selection dropdown
- Query history sidebar
- Schema viewer
- Generated Cypher display
- Interactive results table
- AI-generated summaries

**Example Queries:**

```
Basic Searches:
- "Find all grants about cancer research"
- "Show me grants at University of Melbourne"
- "What are the largest grants by funding amount?"

Advanced Searches:
- "Find grants in public health with funding over $1M"
- "Which researchers work on both cancer and neuroscience?"
- "Show collaboration networks between institutions"

Time-based:
- "What grants started in 2026?"
- "Find grants ending before 2030"
```

### Graph Visualization Page

**Three Modes:**

1. **Random Sample**
   - Adjust node count (5-50)
   - Toggle node types
   - Enable/disable physics
   - Custom spring settings

2. **Node Browser**
   - Select specific node types
   - Choose relationships
   - Preview selection
   - Generate interactive graph

3. **Custom Cypher**
   - Write your own queries
   - Execute and visualize
   - Full Cypher syntax support

**Interaction:**
- Click and drag nodes
- Scroll to zoom
- Hover for details
- Click nodes for info

### Analytics Dashboard

**Four Tabs:**

1. **Institutions**: Top funding by institution
2. **Research Areas**: Distribution analysis
3. **Funding Trends**: Time-series charts
4. **Collaboration**: Network analysis

**Features:**
- Interactive Plotly charts
- Downloadable data tables
- Summary statistics
- Filter controls

---

## API Reference

### Neo4jHandler

```python
from utils.neo4j_handler import Neo4jHandler

# Initialize
handler = Neo4jHandler(uri, user, password)

# Methods
handler.get_schema()                    # Get database schema
handler.execute_cypher(query, params)   # Run Cypher query
handler.get_database_stats()            # Get statistics
handler.vector_search(embedding)        # Semantic search
handler.hybrid_search(embedding, filter) # Combined search
handler.get_grant_by_id(id)            # Get specific grant
```

### LLMHandler

```python
from utils.llm_handler import LLMHandler

# Initialize
handler = LLMHandler(model_name, secrets)

# Methods
handler.generate_cypher(query, schema)  # NL to Cypher
handler.generate_summary(query, results) # Summarize results
handler.extract_insights(results)       # Extract insights
```

### QueryProcessor

```python
from utils.query_processor import QueryProcessor

# Initialize
processor = QueryProcessor(neo4j_handler, llm_handler)

# Methods
processor.process_query(natural_query)  # Full pipeline
processor.get_similar_grants(grant_id)  # Find similar
processor.get_collaboration_network(researcher) # Network
processor.get_funding_trends(start, end) # Trends
```

---

## Deployment Options

### Development (Local)

```bash
# Simplest setup
streamlit run app.py
```

### Docker (Recommended)

```bash
# Build and start
docker-compose up -d

# Access at:
# - App: http://localhost:8501
# - Neo4j: http://localhost:7474

# Stop
docker-compose down

# View logs
docker-compose logs -f
```

### Kubernetes (Production)

```bash
# Deploy to cluster
kubectl apply -f deployment/kubernetes.yaml

# Check status
kubectl get pods -n graphrag

# Access service
kubectl port-forward -n graphrag svc/streamlit 8501:80
```

### Cloud Platforms

**Streamlit Cloud:**
```bash
# 1. Push to GitHub
# 2. Connect at share.streamlit.io
# 3. Add secrets in dashboard
# 4. Deploy
```

**AWS/GCP/Azure:**
```bash
# Use Docker image
# Deploy to ECS/Cloud Run/Container Instances
# Configure environment variables
# Set up load balancer
```

---

## Troubleshooting

### Common Issues

#### 1. Connection Refused

**Problem:** Cannot connect to Neo4j

**Solutions:**
```bash
# Check Neo4j is running
docker ps | grep neo4j

# Verify connection
python -c "from neo4j import GraphDatabase; \
  driver = GraphDatabase.driver('bolt://localhost:7687', \
  auth=('neo4j', 'password')); \
  driver.verify_connectivity(); \
  print('Connected!')"

# Check firewall
telnet localhost 7687
```

#### 2. API Key Invalid

**Problem:** LLM API errors

**Solutions:**
```bash
# Verify key format
# Anthropic: sk-ant-...
# OpenAI: sk-...
# Check secrets.toml has no extra spaces
# Verify key is active in provider dashboard
```

#### 3. Import Errors

**Problem:** Module not found

**Solutions:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python version
python --version  # Should be 3.8+

# Verify installation
pip list | grep streamlit
```

#### 4. Empty Results

**Problem:** Queries return nothing

**Solutions:**
```bash
# Verify data ingestion
python scripts/ingest_data.py

# Check in Neo4j Browser
MATCH (n) RETURN count(n)

# Try simpler query
MATCH (g:Grant) RETURN g LIMIT 5
```

#### 5. Slow Performance

**Problem:** Queries are slow

**Solutions:**
```bash
# Create indexes
# In Neo4j Browser:
CREATE INDEX grant_title FOR (g:Grant) ON (g.title)
CREATE INDEX grant_amount FOR (g:Grant) ON (g.amount)

# Optimize queries
# Use LIMIT clauses
# Index frequently queried properties
```

### Debug Mode

```bash
# Enable debug logging
streamlit run app.py --logger.level=debug

# Check logs
tail -f ~/.streamlit/logs/*.log
```

### Getting Help

1. Check error messages carefully
2. Review logs in terminal
3. Test components individually
4. Consult documentation
5. Check Neo4j/Streamlit forums

---

## Contributing

### Development Setup

```bash
# Fork and clone
git clone your-fork-url
cd graphrag-system

# Create branch
git checkout -b feature/your-feature

# Make changes
# Test thoroughly

# Commit
git commit -m "Add feature: description"

# Push and create PR
git push origin feature/your-feature
```

### Code Standards

- Follow PEP 8 for Python
- Add docstrings to functions
- Include type hints
- Write descriptive commit messages
- Add tests for new features

### Testing

```bash
# Run tests
python -m pytest tests/

# Check coverage
pytest --cov=utils tests/

# Lint code
flake8 .
black .
```

---

## Additional Resources

### Documentation

- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)
- [Streamlit Docs](https://docs.streamlit.io/)
- [Anthropic API](https://docs.anthropic.com/)
- [OpenAI API](https://platform.openai.com/docs)

### Tutorials

- [GraphRAG Concepts](https://neo4j.com/docs/graph-data-science/)
- [Vector Search in Neo4j](https://neo4j.com/docs/cypher-manual/current/indexes-for-vector-search/)
- [Streamlit Multipage Apps](https://docs.streamlit.io/library/get-started/multipage-apps)

### Community

- Neo4j Community Forum
- Streamlit Forum
- GitHub Discussions

---

## License

MIT License - See LICENSE file

---

## Changelog

### v1.0.0 (Current)
- Initial release
- Multi-LLM support
- Graph visualization
- Analytics dashboard
- Docker deployment
- Kubernetes support

---

**Built with ❤️ using Neo4j, Streamlit, and modern LLMs**

For questions or issues, please refer to the documentation or open an issue on GitHub.
