from pydantic import BaseModel, Field
from typing import List, Optional

class PrimaryStandardSchema(BaseModel):
    is_number: str = Field(..., description="IS standard number, e.g., IS 16106:2023")
    title: str = Field(..., description="Title of the Indian Standard")
    publication_year: Optional[int] = Field(None, description="Year of publication")
    status: Optional[str] = Field("Active", description="Active/Withdrawn status")
    latest_amendment: Optional[str] = Field(None, description="Latest amendment number/year, e.g., Amendment No. 2 (2024)")
    amendment_details: Optional[str] = Field(None, description="Key technical scope updates introduced by recent amendments")
    scope_text: str = Field(..., description="Brief scope description")
    is_mandatory_qco: bool = Field(..., description="Whether covered under a mandatory QCO")
    scheme_type: Optional[str] = Field(None, description="Certification scheme, e.g., CRS Scheme-II")
    similarity_score: float = Field(0.0, description="Vector search similarity score")

class AlliedReferenceSchema(BaseModel):
    parent_is_number: str
    relation_type: str = Field(..., description="Type of reference: Test Method, Safety, EMC, etc.")
    related_is_number: Optional[str] = None
    title_or_description: str

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
    query_expansion_used: str
    primary_standards: List[PrimaryStandardSchema]
    allied_references: List[AlliedReferenceSchema]
    structured_synthesis: StructuredSynthesisSchema
    execution_provider: str