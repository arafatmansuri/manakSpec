from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.services.embedder import embedder
from app.services.llm_router import gemini_service

app = FastAPI(title="Indian Standards Engine API", version="1.0.0")

# Enable CORS for React Frontend calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

@app.get("/health")
def health_check():
    return {"status": "online", "framework": "FastAPI"}

@app.post("/api/recommend")
async def recommend_standards(payload: QueryRequest):
    # 1. Compute local query vector using FastEmbed
    query_vector = embedder.generate_embedding(payload.query)
    
    # 2. Mock context (we'll connect this to PostgreSQL pgvector next)
    retrieved_context = "IS 456:2000 covers Code of Practice for Plain and Reinforced Concrete."
    
    # 3. Call Gemini Cloud API
    answer = gemini_service.generate_response(payload.query, retrieved_context)
    
    return {
        "query": payload.query,
        "vector_dimensions": len(query_vector),
        "response": answer
    }