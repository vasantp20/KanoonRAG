from typing import Dict, Any, List, Optional
import json

from app.core.logger import setup_logger
logger = setup_logger(__name__)

from app.core.embeddings import EmbeddingService
from app.core.vector_store import VectorStore
from app.core.llm_provider import LLMProvider

from .llm_caller import call_llm
from .context_formatter import format_context
from .source_extractor import extract_sources


LEGAL_SYSTEM_PROMPT = """You are a senior Indian family law expert and legal assistant.
Your task is to provide accurate, professional, and empathetic legal answers based EXCLUSIVELY on the provided context.

CRITICAL INSTRUCTIONS:
1. Base your answer ONLY on the provided context. Do NOT use any outside or parametric knowledge to answer the question.
2. If the provided context does not contain sufficient information to answer the question, you MUST reply exactly with: "I don't know based on the provided documents." Do not attempt to guess or extrapolate.
3. When you use information from the context, you MUST cite the source precisely as follows:
   - For Kanoon documents (legal cases): [Case: <Title> | <Citation> | <Court>, <Year>]
   - For user uploaded documents: [Client File: <filename>, Page <n>]
4. If multiple cases are present in the context, ALWAYS prioritize and base your primary answer on the most recent judgment (using the Year/Date provided in the document headers). Use older cases only to show historical context if relevant, but clearly state which ruling is the latest.
"""

class RAGEngine:
    """Main RAG pipeline engine."""
    def __init__(self, vector_store: VectorStore, llm_provider: LLMProvider, intent_llm: LLMProvider, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.llm_provider = llm_provider
        self.intent_llm = intent_llm

    async def query(self, user_query: str, user_id: int, case_id: Optional[int] = None, client_info: Optional[Dict] = None, chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Process user query and return RAG response."""
        # Step 1: Classify Intent
        from .intent_classifier import classify_intent
        intent_data = await classify_intent(user_query, self.intent_llm)
        intent = intent_data.get("intent", "broad_thematic")
        
        filters = None
        search_query = user_query
        
        if intent == "specific_case":
            keywords = intent_data.get("metadata", {}).get("keywords", [])
            if keywords:
                # Construct an $and filter requiring all unique keywords to be present
                filters = {"$and": [{"title": {"$contains": kw}} for kw in keywords]}
                print(f"Specific Case Query Detected. Applying keyword filter: {filters}")
                # Also boost the search_query with the exact keywords
                search_query = " ".join(keywords) + " " + user_query
        else:
            search_query = intent_data.get("expanded_query", user_query)
            logger.info(f"Broad Thematic Query Detected. Expanded query: {search_query}")
            
        # Step 2: Embed query
        query_embedding = self.embedding_service.embed_query(search_query)
        
        # Step 3: Search collections
        retrieved_chunks = self.vector_store.search_all(search_query, query_embedding, user_id, case_id, filters=filters)
        
        # Fallback for specific case if exact filter misses
        if intent == "specific_case" and not retrieved_chunks:
            logger.warning("Specific case filter yielded no results, falling back to broad search.")
            retrieved_chunks = self.vector_store.search_all(search_query, query_embedding, user_id, case_id)
            
        # Step 3.5: Fetch complete documents for specific case intent
        if intent == "specific_case" and retrieved_chunks:
            doc_ids = []
            for chunk in retrieved_chunks:
                doc_id = chunk.get("metadata", {}).get("kanoon_doc_id")
                if doc_id and doc_id not in doc_ids:
                    doc_ids.append(doc_id)
            
            # Fetch complete documents for top 3 hits
            complete_docs = self.vector_store.get_complete_documents(doc_ids[:3])
            
            if complete_docs:
                retrieved_chunks = complete_docs
        
        # Step 4: Assemble context
        context = format_context(retrieved_chunks)
        logger.debug(f"Retrieved Context:\n{context}")
        
        # Step 5: Build prompt
        messages = [
            {"role": "system", "content": LEGAL_SYSTEM_PROMPT}
        ]
        
        if client_info:
            client_context = f"Client Info: Name={client_info.get('name', 'N/A')}, Age={client_info.get('age', 'N/A')}, Gender={client_info.get('gender', 'N/A')}"
            messages.append({"role": "system", "content": client_context})
            
        if chat_history:
            for msg in chat_history:
                messages.append({"role": "user", "content": msg["query"]})
                if msg["response"]:
                    messages.append({"role": "assistant", "content": msg["response"]})
                    
        user_message = f"Context information is below.\n\n{context}\n\nGiven the context information and not prior knowledge, answer the user's query: {user_query}"
        messages.append({"role": "user", "content": user_message})
        
        logger.debug(f"LLM Prompt Messages:\n{json.dumps(messages, indent=2)}")
        
        # Step 6: Call LLM
        answer = await call_llm(messages, self.llm_provider)
        
        # Step 7: Parse response & extract sources
        sources = extract_sources(retrieved_chunks)
        
        return {
            "answer": answer,
            "sources": sources
        }

    async def generate_document_section(self, section_name: str, case_info: Dict, context_chunks: List[Dict[str, Any]]) -> str:
        """Generate a specific section of a legal document."""
        context = format_context(context_chunks)
        
        system_prompt = (
            f"You are a legal document drafter for an Indian family court case. You are writing the '{section_name}' section. "
            "If the context documents contain multiple legal precedents, give precedence to the most recent judgments "
            "when drafting your arguments."
        )
        
        user_prompt = f"Case Information: {case_info}\n\nContext Documents:\n{context}\n\nPlease draft the '{section_name}' section based on this information."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await call_llm(messages, self.llm_provider)
