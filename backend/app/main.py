from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import analytics, collaboration, graph, query

app = FastAPI(title="Biotech GraphRAG API")

# Configure CORS
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*",  # fallback for any other local dev origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(query.router, prefix="/api/query", tags=["query"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(collaboration.router, prefix="/api/collaboration", tags=["collaboration"])
app.include_router(graph.router, prefix="/api/graph", tags=["graph"])

@app.get("/")
async def root():
    return {"message": "Biotech GraphRAG API is running"}
