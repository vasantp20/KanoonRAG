import logging
from typing import List, Dict, Any, Optional
from .base import BaseRetriever

logger = logging.getLogger(__name__)

class BroadThemeRetriever(BaseRetriever):
    """Retrieval strategy for broad thematic intent."""
    
    def retrieve(
        self, 
        query: str, 
        intent_data: Dict[str, Any], 
        user_id: int, 
        case_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        search_query = intent_data.get("expanded_query", query)
        logger.info(f"Broad Thematic Query Detected. Expanded query: {search_query}")
        
        query_embedding = self.embedding_service.embed_query(search_query)
        retrieved_chunks = self.vector_store.search_all(search_query, query_embedding, user_id, case_id)
        
        return retrieved_chunks
