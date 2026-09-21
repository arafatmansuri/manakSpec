import json
from google import genai
from google.genai import types
from groq import Groq
from app.core.config import settings
from app.schemas.response import StructuredSynthesisSchema
from typing import Dict, Any, Tuple, List

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

    async def generate_response(self, query: str, context: Dict[str, Any],history: List[Dict[str, str]]) -> Tuple[StructuredSynthesisSchema, str]:
        prompt = f"""
        User Specification Query: "{query}"

        Retrieved Database Context:
        Primary Standards: {context.get('primary_standards', [])}
        Allied References: {context.get('allied_references', [])}
        """

        # 1. Attempt Primary Execution via Gemini with Structured JSON Output
        try:
            response = self.gemini_client.models.generate_content(
                model=settings.PRIMARY_LLM_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self._build_prompt(query, context, history),
                    response_mime_type="application/json",
                    response_schema=StructuredSynthesisSchema,
                )
            )
            structured_data = StructuredSynthesisSchema.model_validate_json(response.text)
            return structured_data, "Google Gemini API"

        except Exception as gemini_err:
            # 2. Failover to Groq API with JSON mode
            try:
                groq_prompt = f"{self._build_system_instruction()}\n\n{prompt}\nReturn ONLY valid JSON."
                groq_response = self.groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": groq_prompt}],
                    model=settings.FALLBACK_LLM_MODEL,
                    response_format={"type": "json_object"}
                )
                raw_json = groq_response.choices[0].message.content
                structured_data = StructuredSynthesisSchema.model_validate_json(raw_json)
                return structured_data, "Groq API (Failover Llama-3.3)"
            except Exception as groq_err:
                raise RuntimeError(f"Both Primary and Failover providers failed: {str(gemini_err)} | {str(groq_err)}")

generator_service = SynthesisGeneratorService()