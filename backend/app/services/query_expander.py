import json
import re
from typing import Dict, Any, Optional
from google import genai
from app.core.config import settings

class QueryExpanderService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def expand_query(self, raw_input: str, user_language: Optional[str] = None) -> Dict[str, str]:
        """
        1. Detects input language (Hindi, Tamil, Marathi, Bengali, English, etc.).
        2. Translates non-English procurement queries to standard English.
        3. Enriches query with BIS technical domain terminology, material grades, and test methods.
        """
        # Fallback default (check Gujarati 0x0A80-0x0AFF, Devanagari/Hindi 0x0900-0x097F)
        if user_language:
            default_lang = user_language
        elif any(ord(c) >= 0x0A80 and ord(c) <= 0x0AFF for c in raw_input):
            default_lang = "Gujarati"
        elif any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in raw_input):
            default_lang = "Hindi"
        else:
            default_lang = "English"

        default_result = {
            "expanded_query": raw_input,
            "detected_language": default_lang,
            "english_translation": raw_input
        }

        prompt = f"""
        You are an expert in Indian Government Procurement and Bureau of Indian Standards (BIS) technical specifications.
        Analyze the following user procurement query:
        "{raw_input}"

        User Specified Language (if provided): "{user_language or 'Auto-Detect'}"

        Instructions:
        1. Identify the language of the query (e.g., "English", "Hindi", "Gujarati", "Tamil", "Marathi", "Bengali", "Telugu", etc.).
        2. Translate the query into accurate English procurement terms if it is not already in English.
        3. Formulate an enriched technical search string in English containing:
           - Specific product categories and synonyms
           - Applicable material grades, types, and classifications
           - Likely Bureau of Indian Standards (IS codes, e.g. IS 10322, IS 694, IS 456)
           - Key normative test methods, safety requirements, and performance parameters

        Output ONLY valid JSON with these exact keys:
        {{
            "detected_language": "Language Name",
            "english_translation": "Clear English translation of the user's intent",
            "expanded_query": "Enriched technical search string in English"
        }}
        """

        try:
            response = self.client.models.generate_content(
                model=settings.PRIMARY_LLM_MODEL,
                contents=prompt
            )
            raw_text = response.text.strip()
            # Clean markdown codeblocks if LLM included ```json ... ```
            cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            parsed = json.loads(cleaned)

            return {
                "expanded_query": parsed.get("expanded_query") or raw_input,
                "detected_language": user_language or parsed.get("detected_language") or default_lang,
                "english_translation": parsed.get("english_translation") or raw_input
            }
        except Exception:
            return default_result

query_expander = QueryExpanderService()