import json
from google import genai
from google.genai import types
from groq import Groq
from app.core.config import settings
from app.schemas.response import StructuredSynthesisSchema
from typing import Dict, Any, Tuple, List

def _clean_schema_additional_properties(schema_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively removes 'additionalProperties' from the Pydantic schema dictionary 
    to prevent Gemini Developer API schema validation errors.
    """
    if isinstance(schema_dict, dict):
        schema_dict.pop("additionalProperties", None)
        for key, value in schema_dict.items():
            _clean_schema_additional_properties(value)
    elif isinstance(schema_dict, list):
        for item in schema_dict:
            _clean_schema_additional_properties(item)
    return schema_dict

class SynthesisGeneratorService:
    def __init__(self):
        self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)

    def _build_prompt(self, query: str, context: Dict[str, Any], history: List[Dict[str, str]], target_language: str = "English") -> str:
        history_str = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history])
        
        return f"""
        You are an expert AI assistant specialized in Bureau of Indian Standards (BIS) procurement and Indian Government Tender Drafting.
        
        Language Preference: {target_language}
        (Note: If {target_language} is non-English, draft the executive overview and descriptive tender explanations in {target_language} while preserving standard numbers like IS 16106:2023 and technical SI units intact).

        Conversation History:
        {history_str}

        Current User Query: "{query}"

        Retrieved Standard Context:
        DB Standards (retrieved from database, may or may not be relevant): {context.get('primary_standards', [])}
        Web-Sourced Standards (supplementary, from live web search): {context.get('web_standards', [])}
        Allied References: {context.get('allied_references', [])}

        CRITICAL RELEVANCE FILTER — YOU MUST FOLLOW THESE RULES EXACTLY:
        1. Critically evaluate EVERY standard in "DB Standards" against the user query "{query}".
           Include a DB standard in primary_standards_summary ONLY IF it is genuinely and directly
           applicable to the queried product, material, or domain. Discard any DB standard that
           is unrelated, even if it was retrieved.
        2. If "Web-Sourced Standards" are provided, treat them as primary candidates.
           For EACH web-sourced standard, evaluate if it is relevant to the query.
           All relevant web-sourced standards MUST be included in primary_standards_summary
           — populate all available fields (is_number, title, publication_year, status,
           scope_text, is_mandatory_qco, scheme_type) from the data provided.
           Set similarity_score to 0.0 for web-sourced standards.
        3. Merge DB-relevant + web-relevant standards into a single primary_standards_summary list.
           Deduplicate by is_number if the same standard appears in both.
        4. If NO standard from either source is applicable to the query, you MUST:
           - Return primary_standards_summary as an empty list [].
           - Write an overview clearly stating "No applicable BIS/IS standards could be
             identified for [the queried product/domain]."
        5. NEVER fabricate, invent, or guess IS numbers or titles. Only include standards
           explicitly provided in "DB Standards" or "Web-Sourced Standards" above.
           Web-sourced standards are NOT fabrication — they are real search results.

        Classification Directive for Allied References:
        Categorize each item in 'allied_references' into one of these exact relation_type categories:
        - "Test Method" (for sampling, testing, chemical/mechanical analysis)
        - "Safety Standard" (for fire, shock, hazardous materials, electric protection)
        - "Terminology Standard" (for definitions, glossary, symbols)
        - "Installation / Code of Practice" (for erection, laying, maintenance guidelines)
        - "Related Product Standard" (for complementary parts, fittings, raw materials)
        - "Normative Reference" (general normative citations)

        Task: Provide a structured recommendation and ready-to-use tender specification clauses.
        """

    def _build_system_instruction(self, target_language: str = "English") -> str:
        return f"""
        You are an expert AI assistant specialized in Bureau of Indian Standards (BIS) and Indian Government Procurement Quality Control Orders (QCO).
        You must analyze the user specification and return a structured JSON matching the required schema.
        Language requirement: Output explanations in {target_language} if specified, keeping standard IS codes intact.
        Ensure all certification details, normative references, and tender clause items are extracted cleanly into lists and key-value fields.
        IMPORTANT: Only include standards in primary_standards_summary that are genuinely relevant to the user query.
        If no standards are relevant, return primary_standards_summary as an empty list and explain in the overview.
        Never fabricate IS numbers or titles.
        """

    async def generate_response(
        self, query: str, context: Dict[str, Any], history: List[Dict[str, str]], target_language: str = "English"
    ) -> Tuple[StructuredSynthesisSchema, str]:
        prompt = f"""
        User Specification Query: "{query}"
        Target Response Language: {target_language}

        Retrieved Context:
        DB Standards (from database, evaluate relevance carefully): {context.get('primary_standards', [])}
        Web-Sourced Standards (supplementary): {context.get('web_standards', [])}
        Allied References: {context.get('allied_references', [])}
        """
        # Prepare Gemini-safe schema by scrubbing additionalProperties
        raw_schema = StructuredSynthesisSchema.model_json_schema()
        gemini_safe_schema = _clean_schema_additional_properties(raw_schema)

        # 1. Attempt Primary Execution via Gemini with Cleaned Structured JSON Output
        try:
            response = self.gemini_client.models.generate_content(
                model=settings.PRIMARY_LLM_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self._build_prompt(query, context, history, target_language=target_language),
                    response_mime_type="application/json",
                    response_schema=gemini_safe_schema,
                )
            )
            structured_data = StructuredSynthesisSchema.model_validate_json(response.text)
            return structured_data, "Google Gemini API"

        except Exception as gemini_err:
            print(f"Gemini Error: {str(gemini_err)}\n")
        # 2. Failover Execution via Groq API with Explicit Schema Enforcement
        try:
            # Provide explicit schema in failover prompt to prevent structure mismatch
            json_schema_str = json.dumps(raw_schema)
            groq_system_msg = (
                f"{self._build_system_instruction(target_language=target_language)}\n"
                f"Required Output JSON Schema:\n{json_schema_str}\n"
                "Return ONLY valid JSON matching this schema."
            )

            failover_model = getattr(settings, "FAILOVER_LLM_MODEL", None) or getattr(settings, "FALLBACK_LLM_MODEL", "llama-3.3-70b-versatile")

            groq_response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": groq_system_msg},
                    {"role": "user", "content": f"{self._build_prompt(query, context, history, target_language=target_language)}\n\n{prompt}"}
                ],
                model=failover_model,
                response_format={"type": "json_object"}
            )
            raw_json = groq_response.choices[0].message.content
            structured_data = StructuredSynthesisSchema.model_validate_json(raw_json)
            return structured_data, f"Groq API Failover ({failover_model})"
            
        except Exception as groq_err:
            raise RuntimeError(
                f"Both Primary and Failover providers failed:\n"
                f"Groq Error: {str(groq_err)}"
            )

generator_service = SynthesisGeneratorService()