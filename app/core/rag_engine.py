import os
import re
from typing import Dict, Any, List, Optional
import httpx
from groq import AsyncGroq

import config
from app.core.embeddings import EmbeddingService
from app.core.vector_store import VectorStore

LEGAL_SYSTEM_PROMPT = """You are a senior Indian family law expert and legal assistant.
Your task is to provide accurate, professional, and empathetic legal answers based on the provided context.
When you use information from the context, you MUST cite the source precisely as follows:
- For Kanoon documents (legal cases): [Case: <Title> | <Citation> | <Court>, <Year>]
- For user uploaded documents: [Client File: <filename>, Page <n>]

Base your answer ONLY on the provided context. If the context does not contain sufficient information, state that clearly.
"""

class RAGEngine:
    """Main RAG pipeline engine."""
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.groq_client = AsyncGroq(api_key=config.GROQ_API_KEY)
        self.http_client = httpx.AsyncClient(timeout=60.0)

    async def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """Call Groq LLM, fallback to local Ollama if it fails."""
        try:
            response = await self.groq_client.chat.completions.create(
                messages=messages,
                model=config.GROQ_MODEL,
                temperature=config.GROQ_TEMPERATURE,
                max_tokens=config.GROQ_MAX_TOKENS,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Groq API failed: {e}. Falling back to Ollama ({config.OLLAMA_MODEL})...")
            
            payload = {
                "model": config.OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": config.OLLAMA_TEMPERATURE,
                    "num_predict": config.OLLAMA_MAX_TOKENS
                }
            }
            
            try:
                response = await self.http_client.post(
                    f"{config.OLLAMA_BASE_URL.rstrip('/')}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                return data["message"]["content"]
            except Exception as ollama_e:
                print(f"Ollama fallback failed: {ollama_e}")
                raise Exception(f"Both Groq and Ollama failed. Groq error: {e}. Ollama error: {ollama_e}")

    def _enhance_query(self, query: str) -> str:
        """Enhance query with legal synonyms."""
        words = re.findall(r'\b\w+\b', query.lower())
        enhanced_terms = set(words)
        
        for word in words:
            if word in config.LEGAL_SYNONYMS:
                enhanced_terms.update(config.LEGAL_SYNONYMS[word])
                
        # Also check for multi-word phrases
        for key, synonyms in config.LEGAL_SYNONYMS.items():
            if key in query.lower():
                enhanced_terms.update(synonyms)
                
        return " ".join(list(enhanced_terms)) + " " + query

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into a single context string."""
        context_parts = []
        
        for i, chunk in enumerate(chunks):
            meta = chunk.get('metadata', {})
            source_type = meta.get('source_type', 'unknown')
            
            if source_type == 'kanoon':
                title = meta.get('title', 'Unknown Case')
                citation = meta.get('citation', 'No Citation')
                court = meta.get('court', 'Unknown Court')
                date = meta.get('date', 'Unknown Date')
                
                # Try to extract year from date
                year = "Unknown Year"
                if date:
                    year_match = re.search(r'\b(19|20)\d{2}\b', str(date))
                    if year_match:
                        year = year_match.group(0)
                        
                header = f"--- Document {i+1} [Case: {title} | {citation} | {court}, {year}] ---"
                
            elif source_type == 'upload':
                filename = meta.get('filename', 'unknown_file')
                page_num = meta.get('page_num', meta.get('chunk_index', 0) + 1)
                header = f"--- Document {i+1} [Client File: {filename}, Page {page_num}] ---"
                
            else:
                header = f"--- Document {i+1} ---"
                
            context_parts.append(f"{header}\n{chunk['text']}\n")
            
        return "\n".join(context_parts)

    def _extract_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract formatted source metadata from retrieved chunks."""
        sources = []
        for i, chunk in enumerate(chunks):
            meta = chunk.get('metadata', {})
            source_type = meta.get('source_type', 'unknown')
            
            source = {
                "source_type": source_type,
                "relevance_score": 1.0 - chunk.get('distance', 0.0),  # Convert distance to score
                "snippet": chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text']
            }
            
            if source_type == 'kanoon':
                source.update({
                    "title": meta.get('title', 'Unknown Case'),
                    "citation": meta.get('citation'),
                    "court": meta.get('court'),
                    "date": meta.get('date'),
                    "kanoon_doc_id": meta.get('kanoon_doc_id')
                })
            elif source_type == 'upload':
                source.update({
                    "title": meta.get('filename', 'Unknown File'),
                    "filename": meta.get('filename'),
                    "page_num": meta.get('page_num', meta.get('chunk_index', 0) + 1)
                })
            else:
                source["title"] = f"Unknown Source {i+1}"
                
            sources.append(source)
            
        return sources

    async def query(self, user_query: str, user_id: int, case_id: Optional[int] = None, client_info: Optional[Dict] = None, chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Process user query and return RAG response."""
        # Step 1: Enhance query
        enhanced_query = self._enhance_query(user_query)
        
        # Step 2: Embed query
        query_embedding = self.embedding_service.embed_query(enhanced_query)
        
        # Step 3: Search collections
        retrieved_chunks = self.vector_store.search_all(query_embedding, user_id, case_id)
        
        # Step 4: Assemble context
        context = self._format_context(retrieved_chunks)
        
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
        
        # Step 6: Call LLM
        answer = await self._call_llm(messages)
        
        # Step 7: Parse response & extract sources
        sources = self._extract_sources(retrieved_chunks)
        
        return {
            "answer": answer,
            "sources": sources
        }

    async def generate_document_section(self, section_name: str, case_info: Dict, context_chunks: List[Dict[str, Any]]) -> str:
        """Generate a specific section of a legal document."""
        context = self._format_context(context_chunks)
        
        system_prompt = f"You are a legal document drafter for an Indian family court case. You are writing the '{section_name}' section."
        
        user_prompt = f"Case Information: {case_info}\n\nContext Documents:\n{context}\n\nPlease draft the '{section_name}' section based on this information."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return await self._call_llm(messages)
