import logging
from typing import Dict, Any, List, Optional
from app.core.vector_store import VectorStore
from app.core.llm_provider import LLMProvider
from .llm_caller import call_llm

logger = logging.getLogger(__name__)

class RAGTools:
    """Tool implementations for the RAG Agent."""
    
    def __init__(self, vector_store: VectorStore, llm_provider: LLMProvider):
        self.vector_store = vector_store
        self.llm_provider = llm_provider

    async def fetch_case_section(self, kanoon_doc_id: str, target_section: str) -> str:
        """
        Fetch a specific procedural part of an identified judgment docket.
        If section metadata doesn't exist natively, fetches full docket and uses LLM to extract.
        """
        logger.info(f"Tool: fetch_case_section called for {kanoon_doc_id}, section: {target_section}")
        docs = self.vector_store.get_complete_documents([kanoon_doc_id])
        if not docs:
            return f"Error: Document {kanoon_doc_id} not found."
            
        full_text = docs[0]["text"]
        
        # Use LLM to extract the section
        system_prompt = f"You are a legal assistant. Extract the '{target_section}' section from the provided judgment. If the section is not clearly identifiable, provide the most relevant parts. Output ONLY the extracted text."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Document Text:\n{full_text}"}
        ]
        
        try:
            extracted = await call_llm(messages, self.llm_provider)
            return f"--- SECTION: {target_section} ---\n{extracted}"
        except Exception as e:
            logger.error(f"Error extracting section: {e}")
            return f"Error extracting section from {kanoon_doc_id}."

    async def fetch_surrounding_paragraphs(self, chunk_id: str, window_size: int = 3) -> str:
        """
        Fetches +N and -N paragraphs around a specific retrieved chunk ID.
        Expected chunk_id format: "<kanoon_doc_id>_<chunk_index>" or metadata passing.
        """
        logger.info(f"Tool: fetch_surrounding_paragraphs called for {chunk_id}")
        
        # Parse chunk_id to get doc_id and index
        # Fallback if chunk_id is not exactly doc_id_index
        parts = chunk_id.rsplit('_', 1)
        if len(parts) != 2 or not parts[1].isdigit():
            return f"Error: Invalid chunk_id format '{chunk_id}'. Expected '<doc_id>_<index>'."
            
        kanoon_doc_id = parts[0]
        chunk_index = int(parts[1])
        
        min_idx = max(0, chunk_index - window_size)
        max_idx = chunk_index + window_size
        
        try:
            results = self.vector_store.kanoon_collection.get(
                where={
                    "$and": [
                        {"kanoon_doc_id": kanoon_doc_id},
                        {"chunk_index": {"$gte": min_idx}},
                        {"chunk_index": {"$lte": max_idx}}
                    ]
                },
                include=['documents', 'metadatas']
            )
            
            if not results or not results['documents']:
                return f"No surrounding chunks found for {chunk_id}."
                
            chunks_with_meta = list(zip(results['documents'], results['metadatas']))
            sorted_chunks = sorted(chunks_with_meta, key=lambda x: x[1].get('chunk_index', 0))
            
            full_text = "\n\n".join([f"[Chunk {meta.get('chunk_index')}]: {doc}" for doc, meta in sorted_chunks])
            return f"--- SURROUNDING PARAGRAPHS FOR {chunk_id} ---\n{full_text}"
            
        except Exception as e:
            logger.error(f"Error fetching surrounding paragraphs: {e}")
            return f"Error fetching surrounding paragraphs."

    async def fetch_full_docket(self, kanoon_doc_id: str) -> str:
        """
        Fetch the entire judgment text.
        """
        logger.info(f"Tool: fetch_full_docket called for {kanoon_doc_id}")
        docs = self.vector_store.get_complete_documents([kanoon_doc_id])
        if not docs:
            return f"Error: Document {kanoon_doc_id} not found."
            
        return f"--- FULL DOCKET: {kanoon_doc_id} ---\n{docs[0]['text']}"
