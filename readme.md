# Hybrid GraphRAG System for Biotech Research

A modern full-stack hybrid GraphRAG (Graph Retrieval-Augmented Generation) system combining React frontend, FastAPI backend, and Neo4j graph database for intelligent querying and visualization of biotech research grant data.

## 🌟 Features

- **🎨 Modern React UI**: Built with React 19, TypeScript, Vite, and Tailwind CSS
- **⚡ Fast API Backend**: FastAPI with async support and automatic OpenAPI documentation
- **🤖 Multi-LLM Support**: Claude (3.5, 4.0, 4.5), GPT-4o, Gemini 2.0 Flash, DeepSeek
- **🔍 Hybrid Search**: Combines vector embeddings with graph relationships
- **📊 Interactive Visualizations**: vis-network powered graph visualizations
- **💬 Natural Language Queries**: Convert plain English to Cypher queries
- **📈 Analytics Dashboard**: Funding trends, research distributions, collaboration networks
- **🔄 Real-time Updates**: Query history and result caching

## 📋 Prerequisites

- **Node.js** 18+ (for frontend)
- **Python** 3.9+ (for backend)
- **Neo4j Database** 5.11+ (for vector search support)
- **API keys** for at least one LLM provider

## 🚀 Quick Start

### Option 1: Local Development Setup

#### 1. Clone and Setup

```bash
git clone <repository-url>
cd biotech_hybridGraphRAG_KG_streamlit
```

#### 2. Set Up Neo4j

**Option A: Neo4j Aura (Cloud - Recommended)**
- Sign up at https://neo4j.com/cloud/aura-free/
- Create a free instance
- Download credentials and save the password

**Option B: Neo4j Desktop**
- Download from https://neo4j.com/download/
- Create and start a new database
- Note the bolt URI, username, and password

#### 3. Configure Environment

Create `.env` file in the project root:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j

# LLM API Keys (at least one required)
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx
GOOGLE_API_KEY=xxxxx
DEEPSEEK_API_KEY=xxxxx

# Optional: Google Search
GOOGLE_SEARCH_API_KEY=xxxxx
GOOGLE_CSE_ID=xxxxx

# Data
CSV_PATH=data/grants.csv
```

#### 4. Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Ingest data into Neo4j
python ../scripts/ingest_data.py

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will run at: **http://localhost:8000**  
API docs available at: **http://localhost:8000/docs**

#### 5. Frontend Setup

```bash
# In a new terminal
cd frontend
npm install

# Start development server
npm run dev
```

Frontend will run at: **http://localhost:5173**

### Option 2: Docker Compose (Easiest)

```bash
# Build and start all services
docker-compose up -d

# Wait for services to start (~30 seconds)
# Then ingest data
docker-compose exec backend python scripts/ingest_data.py
```

Access:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474

### Option 3: Using Makefile

```bash
make install          # Install dependencies
make run             # Run backend (requires separate frontend start)
make docker-up       # Start with Docker
make docker-down     # Stop Docker services
make ingest          # Ingest data
```

## 📁 Project Structure

```
.
├── frontend/                      # React TypeScript frontend
│   ├── src/
│   │   ├── pages/                # Application pages
│   │   │   ├── Home.tsx          # Query interface
│   │   │   ├── GraphViz.tsx      # Graph visualization
│   │   │   ├── Analytics.tsx     # Analytics dashboard
│   │   │   └── Collaboration.tsx # Collaboration networks
│   │   ├── components/           # Reusable UI components
│   │   ├── services/             # API client
│   │   └── types/                # TypeScript type definitions
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                       # FastAPI backend
│   ├── app/
│   │   ├── main.py               # FastAPI application
│   │   ├── config.py             # Configuration management
│   │   ├── routers/              # API endpoints
│   │   │   ├── query.py          # Natural language queries
│   │   │   ├── graph.py          # Graph operations
│   │   │   ├── analytics.py      # Analytics endpoints
│   │   │   └── collaboration.py  # Collaboration networks
│   │   └── utils/                # Backend utilities
│   │       ├── neo4j_handler.py  # Neo4j operations
│   │       ├── llm_handler.py    # Multi-LLM interface
│   │       └── query_processor.py # Query processing
│   └── requirements.txt
│
├── scripts/                       # Utility scripts
│   ├── ingest_data.py            # Data ingestion
│   └── generate_embeddings.py    # Vector embeddings
│
├── data/                          # Data files
│   ├── biotech_data.csv
│   └── grants.csv
│
├── docker-compose.yml             # Docker orchestration
├── Dockerfile                     # Container image
├── Makefile                       # Development commands
└── .env                          # Environment variables (create this)
```

## 🎯 Usage Guide

### Home - Query Interface

1. **Select LLM Model**: Choose your preferred language model from the dropdown
2. **Enter Natural Language Query**: 
   - "Which grants focus on cancer research?"
   - "Show me all grants at University of Melbourne"
   - "Find grants related to CRISPR with funding over $1M"
3. **View Results**: 
   - Generated Cypher query
   - Tabular results
   - AI-powered summary
4. **Query History**: Access previous queries from the sidebar

### Graph Visualization

Visualize your knowledge graph with:
- **Random Sample**: Generate random subgraphs for exploration
- **Custom Queries**: Write Cypher queries for specific patterns
- **Interactive Network**: Zoom, pan, and click nodes for details

### Analytics Dashboard

Explore insights:
- 📊 Top institutions by funding
- 🔬 Research area distributions  
- 📈 Funding trends over time
- 🌐 Geographic distributions
- 🤝 Collaboration patterns

### Collaboration Networks

Discover:
- Researcher collaboration networks
- Institutional partnerships
- Cross-disciplinary connections

## 📊 Graph Schema

```
Nodes:
(:Grant)         - Individual research grants
(:Researcher)    - Principal investigators
(:Institution)   - Universities and organizations
(:ResearchArea)  - Broad research categories
(:ResearchField) - Specific research fields

Relationships:
(:Researcher)-[:PRINCIPAL_INVESTIGATOR]->(:Grant)
(:Grant)-[:HOSTED_BY]->(:Institution)
(:Grant)-[:IN_AREA]->(:ResearchArea)
(:Grant)-[:HAS_FIELD]->(:ResearchField)
(:Researcher)-[:AFFILIATED_WITH]->(:Institution)
```

## 🔍 Example Queries

### Natural Language (Home Page)
```
What are the highest funded grants in 2025?
Which researchers work on neuroscience?
Show collaboration between institutions
Find grants about artificial intelligence
List all grants at Stanford University
```

### Cypher (Graph Visualization)
```cypher
// Find collaboration networks
MATCH (r1:Researcher)-[:PRINCIPAL_INVESTIGATOR]->(g:Grant)
      <-[:PRINCIPAL_INVESTIGATOR]-(r2:Researcher)
WHERE r1 <> r2
RETURN r1, r2, g LIMIT 50

// Top funded research areas
MATCH (g:Grant)-[:IN_AREA]->(a:ResearchArea)
RETURN a.name, sum(g.funding) as total_funding
ORDER BY total_funding DESC

// Institution collaboration network
MATCH (i1:Institution)<-[:HOSTED_BY]-(g:Grant)
      -[:HOSTED_BY]->(i2:Institution)
WHERE i1 <> i2
RETURN i1, i2, count(g) as collaborations
ORDER BY collaborations DESC
```

## 🔌 API Endpoints

### Query API
- `POST /api/query/natural` - Natural language to Cypher
- `POST /api/query/execute` - Execute Cypher query
- `GET /api/query/history` - Query history

### Graph API
- `GET /api/graph/random` - Random subgraph sample
- `POST /api/graph/custom` - Custom graph query
- `GET /api/graph/schema` - Graph schema info

### Analytics API
- `GET /api/analytics/funding` - Funding statistics
- `GET /api/analytics/areas` - Research area distributions
- `GET /api/analytics/trends` - Temporal trends

### Collaboration API
- `GET /api/collaboration/network` - Collaboration networks
- `GET /api/collaboration/researchers` - Researcher connections

Full API documentation: http://localhost:8000/docs

## 🧪 Advanced Features

### Vector Search

Enable semantic search with embeddings:

```bash
python scripts/generate_embeddings.py
```

Requirements:
- Neo4j 5.11+
- sentence-transformers library
- Vector index (auto-created during ingestion)

### Custom LLM Integration

Add new providers in `backend/app/utils/llm_handler.py`:

```python
elif "YourModel" in self.model_name:
    self.provider = "yourprovider"
    self.client = YourProviderClient(api_key=self.api_key)
```

### Extending the API

Add new endpoints in `backend/app/routers/`:

```python
from fastapi import APIRouter
router = APIRouter()

@router.get("/your-endpoint")
async def your_function():
    return {"data": "your_result"}
```

## 🐛 Troubleshooting

### Backend Issues

**Connection Errors:**
```bash
# Test Neo4j connection
python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password')); driver.verify_connectivity(); print('✅ Connected!')"
```

**API Not Starting:**
- Check port 8000 is available
- Verify .env file exists and is properly formatted
- Check Python version: `python --version` (should be 3.9+)

### Frontend Issues

**Build Errors:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**CORS Errors:**
- Ensure backend is running on port 8000
- Check `allow_origins` in `backend/app/main.py`

### Database Issues

**Empty Results:**
- Verify data ingestion: Check Neo4j Browser for nodes
- Run: `python scripts/ingest_data.py`
- Check logs for errors

**Vector Search Not Working:**
- Requires Neo4j 5.11+
- Run: `python scripts/generate_embeddings.py`
- Verify vector index creation in Neo4j Browser

## 📚 Documentation

- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Vite Documentation](https://vitejs.dev/)
- [GraphRAG Concepts](https://neo4j.com/docs/graph-data-science/)

## 🧰 Development

### Backend Development

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm run dev
```

### Building for Production

**Frontend:**
```bash
cd frontend
npm run build
npm run preview  # Test production build
```

**Backend:**
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm run test
```

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- 🎨 Additional UI components and visualizations
- 🤖 More LLM provider integrations
- 📊 Advanced analytics features
- 🔍 Enhanced search capabilities
- 📱 Mobile responsive improvements
- 🧪 Test coverage expansion
- 📖 Documentation improvements

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- **Neo4j** - Graph database platform
- **FastAPI** - Modern Python web framework
- **React** - UI library
- **Vite** - Build tool and dev server
- **Anthropic, OpenAI, Google, DeepSeek** - LLM APIs
- **vis-network** - Network visualization library

## 📞 Support

For issues and questions:
- 📖 Check troubleshooting section
- 💬 Review documentation links
- 🐛 Open an issue on GitHub
- 📧 Contact maintainers

---

**Built with ❤️ using React + FastAPI + Neo4j GraphRAG**
