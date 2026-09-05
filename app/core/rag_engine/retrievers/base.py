from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.core.vector_store import VectorStore
from app.core.embeddings import EmbeddingService

class BaseRetriever(ABC):
    """Base class for all retrieval strategies."""
    
    def __init__(self, vector_store: VectorStore, embedding_service: EmbeddingService):
        self.vector_store = vector_store
        self.embedding_service = embedding_service

    @abstractmethod
    def retrieve(
        self, 
        query: str, 
        intent_data: Dict[str, Any], 
        user_id: int, 
        case_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context based on the strategy."""
        pass
