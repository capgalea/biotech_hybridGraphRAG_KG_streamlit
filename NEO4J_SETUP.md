# Neo4j Setup Guide

This app supports **both local and cloud Neo4j instances**. Choose the setup that works best for you.

## Option 1: Local Neo4j (Recommended for Development)

### Using Docker

**Prerequisites:** Docker installed

```powershell
# Start a local Neo4j container
docker run -d --name neo4j-local \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

**Then update `.env`:**

```env
# Comment out the cloud (Aura) section
# NEO4J_URI=neo4j+s://be477acd.databases.neo4j.io
# NEO4J_USER=neo4j
# NEO4J_PASSWORD=...

# Uncomment the local section
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_DATABASE=neo4j
```

**Access Neo4j Browser:**
- Open: http://localhost:7474
- Login with `neo4j` / `password`

### Using Neo4j Desktop

1. Download from https://neo4j.com/download/
2. Create a new database project
3. Start the database
4. Note the connection details (bolt URI, username, password)
5. Update `.env` with your values:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
```

---

## Option 2: Cloud Neo4j Aura

This app currently uses **Neo4j Aura** (cloud-hosted).

### Access Your Aura Instance

1. Go to https://console.neo4j.io/
2. Log in to your account
3. Click on your instance (`be477acd.databases.neo4j.io`)
4. View connection details and manage passwords

### Update `.env`

```env
# Aura configuration (already set)
NEO4J_URI=neo4j+s://be477acd.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-current-password
NEO4J_DATABASE=neo4j
```

---

## Switching Between Local and Cloud

### To Switch from Cloud → Local:

1. **Comment out** the cloud section in `.env`
2. **Uncomment** the local section in `.env`
3. **Ensure Docker/Desktop Neo4j is running**
4. **Restart the backend:**
   ```powershell
   # Backend auto-reloads with --reload flag
   # Or manually stop/start if needed
   ```

### To Switch from Local → Cloud:

1. **Comment out** the local section in `.env`
2. **Uncomment** the cloud section in `.env`
3. **Ensure your Aura password is current**
4. **Restart the backend**

---

## Resetting Your Neo4j Database

### Local (Docker):

```powershell
# Remove the container
docker rm -f neo4j-local

# Start fresh
docker run -d --name neo4j-local \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:latest
```

### Aura Cloud:

1. Log in to https://console.neo4j.io/
2. Go to your instance
3. Look for "Delete" or "Reset" option
4. Create a new instance if needed

---

## Verify Connection

After updating `.env` and restarting the backend:

```powershell
# Check backend logs
# Should show: "Application startup complete" with no connection errors
```

**Test from frontend:**
- Open http://localhost:5173
- Try a query
- If successful, your connection is working!

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| `Connection refused` | Ensure local Neo4j is running or Aura credentials are correct |
| `Unauthorized` / `Authentication failed` | Check Neo4j password in `.env` is current |
| `Connection timeout` | Verify `NEO4J_URI` is correct (bolt:// for local, neo4j+s:// for cloud) |

---

## Database URI Formats

| Type | URI Format | Example |
|------|-----------|---------|
| **Local** | `bolt://host:port` | `bolt://localhost:7687` |
| **Local (encrypted)** | `bolt+s://host:port` | `bolt+s://localhost:7687` |
| **Cloud Aura** | `neo4j+s://id.databases.neo4j.io` | `neo4j+s://be477acd.databases.neo4j.io` |

