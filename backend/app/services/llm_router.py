from google import genai
from google.genai import types
from app.core.config import settings

class GeminiService:
    def __init__(self):
        # Initializes Gemini Client with API key from settings
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-2.5-flash"

    def generate_response(self, user_query: str, retrieved_context: str) -> str:
        system_instruction = """
            You are an expert AI Assistant specialized in Indian Standards (BIS) and e-Procurement specification drafting.
            Analyze the user's procurement query alongside the retrieved context from PostgreSQL.

            You MUST format your response with the following explicit sections:
            1. Recommended Primary Indian Standard(s) (Include IS Code, Title, and Latest Published Year)
            2. Amendments & Revisions Status (Highlight latest active amendments)
            3. Mandatory Certification Requirements (Specify if QCO applies, and identify scheme e.g., ISI Mark, CRS, Hallmarking)
            4. Allied & Normative Cross-References (List test methods, safety standards, and normative reference standards)
            5. Suggested Tender Specification Clause Snippet
            """

        prompt = f"""
        User Procurement Query: {user_query}

        Retrieved Context from PostgreSQL:
        {retrieved_context}
        """

        # Explicitly disable AFC in generate_content to suppress SDK warnings
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config
        )
        return response.text

gemini_service = GeminiService()