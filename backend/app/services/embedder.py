from fastembed import TextEmbedding
from typing import List

class EmbeddingService:
    def __init__(self):
        print("Loading local FastEmbed model (BAAI/bge-small-en-v1.5)...")
        # Downloads/loads ~130MB ONNX lightweight model locally
        self.model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

    def generate_embedding(self, text: str) -> List[float]:
        """Generates a 384-dimensional vector for input text."""
        if not text or not text.strip():
            # Return zero vector fallback
            return [0.0] * 384
        embeddings = list(self.model.embed([text]))
        return embeddings[0].tolist()

embedder = EmbeddingService()