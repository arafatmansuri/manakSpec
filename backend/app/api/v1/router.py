from fastapi import APIRouter
from app.api.v1.endpoints import router as standard_router
from app.api.v1.sessionEndpoints import router as session_router

api_router = APIRouter()
api_router.include_router(standard_router, prefix="/standards", tags=["Indian Standards Recommendations"])
api_router.include_router(session_router, prefix="/sessions", tags=["Chat Sessions"])