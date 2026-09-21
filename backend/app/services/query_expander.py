from google import genai
from app.core.config import settings

class QueryExpanderService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def expand_query(self, raw_input: str) -> str:
        """Enriches raw/brief user inputs into a detailed domain-specific search prompt."""
        if len(raw_input.split()) > 40:
            return raw_input  # Already comprehensive

        prompt = f"""
        You are a Bureau of Indian Standards (BIS) technical procurement expert.
        Enrich the following procurement request or product query with relevant technical terminology, material grades, potential subtypes, normative test requirements, and Indian Standard contexts.
        Output ONLY the enriched search string in plain text without markdown formatting or conversational text.

        Original Input: "{raw_input}"
        Enriched Output:
        """
        try:
            response = self.client.models.generate_content(
                model=settings.PRIMARY_LLM_MODEL,
                contents=prompt
            )
            return response.text.strip()
        except Exception:
            return raw_input

query_expander = QueryExpanderService()