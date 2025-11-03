# 🚀 Quick Start Guide

Get your GraphRAG system running in 5 minutes!

## ⚡ Express Setup (5 Minutes)

### Step 1: Clone and Install (2 min)

```bash
# Navigate to your project directory
cd your-project-directory

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Set Up Neo4j (1 min)

**Easiest: Neo4j Aura (Free Cloud)**
1. Go to https://neo4j.com/cloud/aura-free/
2. Sign up and create a free instance
3. Download credentials (save the password!)

**Alternative: Neo4j Desktop**
1. Download from https://neo4j.com/download/
2. Install and create a new database
3. Start the database

### Step 3: Configure (1 min)

Create `.streamlit/secrets.toml`:

```toml
[neo4j]
uri = "neo4j+s://xxxxx.databases.neo4j.io"  # From Aura
user = "neo4j"
password = "your-password-here"  # From Aura

[anthropic]
api_key = "sk-ant-xxxxx"  # Get from console.anthropic.com
```

**Getting API Keys:**
- Anthropic (Claude): https://console.anthropic.com/
- OpenAI (GPT): https://platform.openai.com/api-keys
- Google (Gemini): https://makersuite.google.com/app/apikey
- DeepSeek: https://platform.deepseek.com/

💡 **You only need ONE API key to get started!**

### Step 4: Load Data (1 min)

```bash
# Set your Neo4j credentials
export NEO4J_URI="neo4j+s://your-instance.databases.neo4j.io"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your-password"

# Run data ingestion
python scripts/ingest_data.py
```

Expected output:
```
INFO:__main__:Found 20 records
INFO:__main__:Processed 10/20 grants
INFO:__main__:Processed 20/20 grants
INFO:__main__:Data ingestion complete!

=== Database Statistics ===
Grants: 20
Researchers: 19
Institutions: 8
Research Areas: 3
Relationships: 59
✅ Data ingestion completed successfully!
```

### Step 5: Launch! (<1 min)

```bash
streamlit run app.py
```

Visit http://localhost:8501 🎉

---

## 🎯 First Steps

### Try These Queries:

1. **Simple Search:**
   ```
   What grants are about cancer?
   ```

2. **Institution Search:**
   ```
   Show me all grants at University of Melbourne
   ```

3. **High-Value Grants:**
   ```
   Find grants with funding over $2 million
   ```

4. **Research Area:**
   ```
   Which grants focus on public health?
   ```

### Explore the Interface:

1. **Main Page**: Ask questions in natural language
2. **Graph Visualization**: See interactive network graphs
3. **Analytics**: Explore funding trends and distributions

---

## 🔧 Troubleshooting Quick Fixes

### "Connection refused" Error

```bash
# Check if Neo4j is running
# For Aura: Check status in console
# For Desktop: Start database in Neo4j Desktop
```

### "Invalid API key" Error

```bash
# Verify your API key in secrets.toml
# Make sure there are no extra spaces
# Key should start with correct prefix (sk-ant-, sk-, etc.)
```

### "No module named 'X'" Error

```bash
# Reinstall requirements
pip install -r requirements.txt --upgrade
```

### Data Import Fails

```bash
# Verify file exists
ls combined_grants_small.csv

# Check Neo4j credentials
python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('YOUR_URI', auth=('neo4j', 'YOUR_PASSWORD')); driver.verify_connectivity(); print('✅ Connected!')"
```

---

## 📝 Quick Reference

### Useful Commands

```bash
# Check Python version (needs 3.8+)
python --version

# List installed packages
pip list

# Run with debug mode
streamlit run app.py --logger.level=debug

# Clear Streamlit cache
streamlit cache clear
```

### File Structure

```
your-project/
├── app.py                    # Start here!
├── combined_grants_small.csv # Your data
├── .streamlit/
│   └── secrets.toml         # API keys (create this)
├── requirements.txt          # Dependencies
└── scripts/
    └── ingest_data.py       # Data loader
```

### Neo4j Quick Queries

Open Neo4j Browser and try:

```cypher
// Count all nodes
MATCH (n) RETURN count(n)

// View some grants
MATCH (g:Grant) RETURN g LIMIT 5

// View schema
CALL db.schema.visualization()
```

---

## 🎓 Next Steps

### Add Vector Search (Optional)

```bash
# Generate embeddings for semantic search
python scripts/generate_embeddings.py
```

### Customize the Data

1. Edit `scripts/ingest_data.py`
2. Modify graph schema
3. Re-run ingestion

### Add More LLMs

1. Get API keys from providers
2. Add to `secrets.toml`
3. Select in the app dropdown

---

## 💡 Pro Tips

1. **Query History**: Click previous queries in sidebar to reuse
2. **Copy Cypher**: Expand "Generated Cypher" to see and copy queries
3. **Download Results**: Export tables as CSV
4. **Schema View**: Check schema to understand data structure
5. **Multiple LLMs**: Try different LLMs for varying responses

---

## 🆘 Still Stuck?

1. Check `README.md` for detailed docs
2. Review Neo4j logs
3. Check Streamlit logs in terminal
4. Verify all credentials are correct
5. Try with a simpler query first

---

## ✅ Success Checklist

- [ ] Python 3.8+ installed
- [ ] Neo4j running (Aura or Desktop)
- [ ] Requirements installed
- [ ] secrets.toml configured
- [ ] Data ingested (20 grants)
- [ ] App running on localhost:8501
- [ ] First query executed successfully

**All checked? You're ready to explore! 🎉**

---

## 🚀 Advanced Features

Once comfortable, explore:

- Custom Cypher queries in visualization page
- Analytics dashboard for trends
- Generate embeddings for semantic search
- Extend schema with new node types
- Add more data sources

---

**Happy Exploring! 🔍📊**

Need help? Check the full README.md or documentation.
