from typing import List
from sentence_transformers import SentenceTransformer

import config

class EmbeddingService:
    """Local embedding service using SentenceTransformer (singleton)."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance.model = None
        return cls._instance

    def _get_model(self):
        if self.model is None:
            self.model = SentenceTransformer(config.EMBEDDING_MODEL)
        return self.model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Batch encode documents."""
        model = self._get_model()
        embeddings = model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query."""
        model = self._get_model()
        prefix = 'Represent this sentence for searching relevant passages: '
        embedding = model.encode(prefix + query, normalize_embeddings=True)
        return embedding.tolist()
