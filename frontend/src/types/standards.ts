export interface PrimaryStandard {
  is_number: string;
  title: string;
  publication_year?: number | null;
  status?: string;
  latest_amendment?: string | null;
  amendment_details?: string | null;
  scope_text?: string | null;
  is_mandatory_qco: boolean;
  scheme_type?: string | null;
  committee_code?: string | null;
  gazette_notice_id?: string | null;
  reaffirmation_year?: number | null;
  technical_specifications: Record<string, any>;
  similarity_score: number;
}

export interface AlliedReference {
  parent_is_number: string;
  relation_type: string;
  related_is_number?: string | null;
  title_or_description: string;
  amendment_no?: number | null;
  amendment_year?: number | null;
}

export interface CertificationDetail {
  scheme_name: string;
  governing_body_or_order: string;
  mark_type: string;
  requirements: string[];
}

export interface TenderClause {
  title: string;
  standard_compliance: string;
  mandatory_cert_clause: string;
  technical_specifications: string[];
  testing_and_documentation: string;
}

export interface StructuredSynthesis {
  overview: string;
  primary_standards_summary: PrimaryStandard[];
  certification_details: CertificationDetail;
  allied_references: AlliedReference[];
  tender_clause: TenderClause;
}

export interface RecommendationOutput {
  session_id: string;
  user_id: string;
  detected_language?: string;
  query_expansion_used: string;
  allied_references: AlliedReference[];
  structured_synthesis: StructuredSynthesis;
  execution_provider: string;
}
