from sentence_transformers import SentenceTransformer
from shared.logger import get_logger

logger = get_logger("Embeddings")

MODEL_NAME = "all-MiniLM-L6-v2"

class EmbeddingService:
    def __init__(self) -> None:
        self.model = SentenceTransformer(MODEL_NAME)
        logger.info("Loaded embedding model: %s", MODEL_NAME)

    def generate(self, text: str) -> list[float]:
        logger.info("Generating embedding for text: %s", text[:50])
        embedding = self.model.encode(text)
        return embedding.tolist()


embedding_service = EmbeddingService()