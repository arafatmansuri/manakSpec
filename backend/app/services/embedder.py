from fastembed import TextEmbedding
from typing import List

class EmbeddingService:
    def __init__(self):
        print("Loading lightweight FastEmbed model (~90MB download)...")
        # Downloads ~90 MB and runs in fast ONNX runtime
        self.model = TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

    def generate_embedding(self, text: str) -> List[float]:
        embeddings = list(self.model.embed([text]))
        return embeddings[0].tolist()

embedder = EmbeddingService()