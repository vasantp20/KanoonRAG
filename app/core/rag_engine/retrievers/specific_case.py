import logging
from typing import List, Dict, Any, Optional
from .base import BaseRetriever

logger = logging.getLogger(__name__)

class SpecificCaseRetriever(BaseRetriever):
    """Retrieval strategy for specific case intent."""
    
    def retrieve(
        self, 
        query: str, 
        intent_data: Dict[str, Any], 
        user_id: int, 
        case_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        keywords = intent_data.get("metadata", {}).get("keywords", [])
        filters = None
        search_query = query
        
        if keywords:
            # Construct an $and filter requiring all unique keywords to be present
            filters = {"$and": [{"title": {"$contains": kw}} for kw in keywords]}
            logger.info(f"Specific Case Query Detected. Applying keyword filter: {filters}")
            # Also boost the search_query with the exact keywords
            search_query = " ".join(keywords) + " " + query
            
        query_embedding = self.embedding_service.embed_query(search_query)
        retrieved_chunks = self.vector_store.search_all(search_query, query_embedding, user_id, case_id, filters=filters)
        
        # Fetch complete documents for specific case intent
        if retrieved_chunks:
            doc_ids = []
            for chunk in retrieved_chunks:
                doc_id = chunk.get("metadata", {}).get("kanoon_doc_id")
                if doc_id and doc_id not in doc_ids:
                    doc_ids.append(doc_id)
            
            # Fetch complete documents for top 3 hits
            complete_docs = self.vector_store.get_complete_documents(doc_ids[:3])
            
            if complete_docs:
                retrieved_chunks = complete_docs
                
        return retrieved_chunks
