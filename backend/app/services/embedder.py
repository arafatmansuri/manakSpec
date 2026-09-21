from google import genai
from google.genai import types
from app.core.config import settings
from typing import List

class GeminiEmbedderService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate_embedding(self, text: str) -> List[float]:
        """Generates a 768-dim vector using gemini-embedding-001."""
        if not text or not text.strip():
            return [0.0] * 768

        response = self.client.models.embed_content(
            model=settings.EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=768,
                task_type="RETRIEVAL_DOCUMENT"
            )
        )
        return response.embeddings[0].values

gemini_embedder = GeminiEmbedderService()