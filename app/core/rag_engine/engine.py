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

import uuid

class RAGEngine:
    """Main RAG pipeline engine."""
    def __init__(self, vector_store: VectorStore, llm_provider: LLMProvider, intent_llm: LLMProvider, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.llm_provider = llm_provider
        self.intent_llm = intent_llm

    async def query(self, user_query: str, user_id: int, case_id: Optional[int] = None, client_info: Optional[Dict] = None, chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Process user query and return RAG response."""
        query_uuid = str(uuid.uuid4())
        
        # Step 1: Classify Intent
        from .intent_classifier import classify_intent
        intent_ctx = {"query_uuid": query_uuid, "query": user_query, "step": "intent_classification"}
        intent_data = await classify_intent(user_query, self.intent_llm, telemetry_ctx=intent_ctx)
        # Step 2 & 3: Retrieve context using orchestrator
        from .retrievers import RetrievalOrchestrator
        orchestrator = RetrievalOrchestrator(self.vector_store, self.embedding_service)
        retrieved_chunks = orchestrator.retrieve(user_query, intent_data, user_id, case_id)
        
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
        answer_ctx = {"query_uuid": query_uuid, "query": user_query, "step": "answer_generation"}
        answer = await call_llm(messages, self.llm_provider, telemetry_ctx=answer_ctx)
        
        # Step 7: Parse response & extract sources
        sources = extract_sources(retrieved_chunks)
        
        return {
            "answer": answer,
            "sources": sources,
            "query_uuid": query_uuid
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
