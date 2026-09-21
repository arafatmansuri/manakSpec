from pydantic import BaseModel, Field
from typing import Optional

class SearchQueryRequest(BaseModel):
    query_text: Optional[str] = Field(None, description="Natural language query, product specification, or procurement scope")
    language: Optional[str] = Field("en", description="ISO language code of input text")

class TextRecommendationRequest(BaseModel):
    query_text: str = Field(..., description="Query string or product specification text")
    session_id: Optional[str] = Field(None, description="Optional UUID to append to existing conversation thread")