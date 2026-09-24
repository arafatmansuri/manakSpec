export interface RecommendationFormInputs {
  query_text: string;
  language: string;
  file?: FileList | null;
}

export interface IngestFormInputs {
  is_number: string;
  title: string;
  publication_year?: number;
  status: string;
  scope_text?: string;
  is_mandatory_qco: boolean;
  scheme_type?: string;
  committee_code?: string;
  technical_specifications?: string;
}
