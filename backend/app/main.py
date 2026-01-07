from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import analytics, collaboration, graph, query

app = FastAPI(title="Biotech GraphRAG API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(query.router, prefix="/api/query", tags=["query"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(collaboration.router, prefix="/api/collaboration", tags=["collaboration"])
app.include_router(graph.router, prefix="/api/graph", tags=["graph"])

@app.get("/api/test")
async def test():
    return {"status": "ok", "version": "new"}

@app.get("/")
async def root():
    return {"message": "Biotech GraphRAG API is running"}
