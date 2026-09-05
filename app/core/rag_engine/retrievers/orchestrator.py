import logging
from typing import List, Dict, Any, Optional
from app.core.vector_store import VectorStore
from app.core.embeddings import EmbeddingService
from .specific_case import SpecificCaseRetriever
from .broad_theme import BroadThemeRetriever

logger = logging.getLogger(__name__)

class RetrievalOrchestrator:
    """Orchestrates retrieval strategies based on intent."""
    
    def __init__(self, vector_store: VectorStore, embedding_service: EmbeddingService):
        self.specific_retriever = SpecificCaseRetriever(vector_store, embedding_service)
        self.broad_retriever = BroadThemeRetriever(vector_store, embedding_service)
        
    def retrieve(
        self, 
        query: str, 
        intent_data: Dict[str, Any], 
        user_id: int, 
        case_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        intent = intent_data.get("intent", "broad_thematic")
        
        if intent == "specific_case":
            retrieved_chunks = self.specific_retriever.retrieve(query, intent_data, user_id, case_id)
            if not retrieved_chunks:
                logger.warning("Specific case filter yielded no results, falling back to broad search.")
                return self.broad_retriever.retrieve(query, intent_data, user_id, case_id)
            return retrieved_chunks
        else:
            return self.broad_retriever.retrieve(query, intent_data, user_id, case_id)
