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

    def _build_prompt(self, query: str, context: Dict[str, Any], history: List[Dict[str, str]]) -> str:
        history_str = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in history])
        
        return f"""
        You are an expert AI assistant specialized in Bureau of Indian Standards (BIS) procurement.
        
        Conversation History:
        {history_str}

        Current User Query: "{query}"

        Retrieved Standard Context:
        Primary Standards: {context.get('primary_standards', [])}
        Allied References: {context.get('allied_references', [])}

        Task: Provide a structured recommendation considering the ongoing context.
        """

    def _build_system_instruction(self) -> str:
        return """
        You are an expert AI assistant specialized in Bureau of Indian Standards (BIS) and Indian Government Procurement Quality Control Orders (QCO).
        You must analyze the user specification and return a structured JSON matching the required schema.
        Ensure all certification details, normative references, and tender clause items are extracted cleanly into lists and key-value fields.
        """

    async def generate_response(
        self, query: str, context: Dict[str, Any], history: List[Dict[str, str]]
    ) -> Tuple[StructuredSynthesisSchema, str]:
        prompt = f"""
        User Specification Query: "{query}"

        Retrieved Database Context:
        Primary Standards: {context.get('primary_standards', [])}
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
                    system_instruction=self._build_prompt(query, context, history),
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
                f"{self._build_system_instruction()}\n"
                f"Required Output JSON Schema:\n{json_schema_str}\n"
                "Return ONLY valid JSON matching this schema."
            )

            failover_model = getattr(settings, "FAILOVER_LLM_MODEL", None) or getattr(settings, "FALLBACK_LLM_MODEL", "llama-3.3-70b-versatile")

            groq_response = self.groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": groq_system_msg},
                    {"role": "user", "content": f"{self._build_prompt(query, context, history)}\n\n{prompt}"}
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