from google import genai
from app.core.config import settings

class GeminiService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate_response(self, prompt: str, context: str) -> str:
        system_instruction = (
            "You are an expert Indian Standards and Procurement Specification assistant. "
            "Use the provided standards data context to answer the user query accurately."
        )
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"Context:\n{context}\n\nUser Question:\n{prompt}",
                config={'system_instruction': system_instruction}
            )
            return response.text
        except Exception as e:
            print(f"[Gemini API Error]: {str(e)}")
            raise e

gemini_service = GeminiService()