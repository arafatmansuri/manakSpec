from datetime import datetime
from typing import List, Optional, Dict, Any
import json
from pydantic import BaseModel, Field, field_validator


# --- Session & History Schemas ---
class CreateSessionRequest(BaseModel):
    user_id: Optional[str] = None
    title: Optional[str] = "New Chat"


class CreateSessionResponse(BaseModel):
    user_id: str
    session_id: str
    title: str
    created_at: datetime


class SessionSummary(BaseModel):
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ChatMessageSchema(BaseModel):
    message_id: str
    role: str
    content: Any  # Accepts JSON string or parsed dict
    execution_provider: Optional[str] = None
    created_at: datetime

    @field_validator("content", mode="before")
    def parse_json_content(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return v
        return v


class ChatHistoryResponse(BaseModel):
    session_id: str
    title: str
    messages: List[ChatMessageSchema]

class PrimaryStandardSchema(BaseModel):
    is_number: str = Field(..., description="IS standard number, e.g., IS 16106:2023")
    title: str = Field(..., description="Title of the Indian Standard")
    publication_year: Optional[int] = Field(None, description="Year of publication")
    status: Optional[str] = Field("Active", description="Active/Withdrawn status")
    latest_amendment: Optional[str] = Field(None, description="Latest amendment number/year")
    amendment_details: Optional[str] = Field(None, description="Key updates introduced by amendments")
    scope_text: Optional[str] = Field(None, description="Brief scope description")
    is_mandatory_qco: bool = Field(False, description="Whether covered under a mandatory QCO")
    scheme_type: Optional[str] = Field(None, description="Certification scheme, e.g., CRS Scheme-II")
    committee_code: Optional[str] = Field(None, description="BIS Technical Committee Code")
    gazette_notice_id: Optional[str] = Field(None, description="Gazette notification ID if applicable")
    reaffirmation_year: Optional[int] = Field(None, description="Year standard was last reaffirmed")
    technical_specifications: Dict[str, Any] = Field(default_factory=dict, description="JSONB technical parameters")
    similarity_score: float = Field(0.0, description="Vector search similarity score")

    @field_validator("technical_specifications", mode="before")
    def parse_technical_specifications(cls, value):
        """Converts stringified JSON string '{}' or nulls into a valid dict."""
        if value is None:
            return {}
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {}
        return value

    @field_validator("is_mandatory_qco", mode="before")
    def parse_is_mandatory_qco(cls, value):
        """Coerces None/Null database values to False."""
        if value is None:
            return False
        return bool(value)

class AlliedReferenceSchema(BaseModel):
    parent_is_number: str
    relation_type: str = Field(..., description="Type of reference: Test Method, Safety, EMC, Normative Reference, Amendment, etc.")
    related_is_number: Optional[str] = None
    title_or_description: str
    amendment_no: Optional[int] = Field(None, description="Amendment number if applicable")
    amendment_year: Optional[int] = Field(None, description="Year amendment was issued if applicable")

class CertificationDetailSchema(BaseModel):
    scheme_name: str
    governing_body_or_order: str
    mark_type: str
    requirements: List[str] = Field(default_factory=list)

class TenderClauseSchema(BaseModel):
    title: str
    standard_compliance: str
    mandatory_cert_clause: str
    technical_specifications: List[str]
    testing_and_documentation: str

class StructuredSynthesisSchema(BaseModel):
    overview: str
    primary_standards_summary: List[PrimaryStandardSchema]
    certification_details: CertificationDetailSchema
    allied_references: List[AlliedReferenceSchema]
    tender_clause: TenderClauseSchema

class RecommendationOutput(BaseModel):
    session_id: str = Field(..., description="UUID of the chat session where this message was logged")
    user_id: str = Field(..., description="User ID associated with the session")
    query_expansion_used: str
    primary_standards: List[PrimaryStandardSchema]
    allied_references: List[AlliedReferenceSchema]
    structured_synthesis: StructuredSynthesisSchema
    execution_provider: str