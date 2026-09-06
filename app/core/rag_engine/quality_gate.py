import logging
import re
from typing import List, Dict, Any, Tuple
from app.core.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

class HybridQualityGate:
    """Two-Tier Cascading Quality Gate for RAG responses."""
    
    def __init__(self, intent_llm: LLMProvider):
        self.intent_llm = intent_llm

    def _calculate_keyword_overlap(self, query: str, text: str) -> float:
        """Simple heuristic to calculate keyword overlap between query and text."""
        # Extract alphanumeric words > 3 chars
        query_words = set(re.findall(r'\b[a-zA-Z0-9]{4,}\b', query.lower()))
        if not query_words:
            return 0.0
            
        text_lower = text.lower()
        matched = sum(1 for word in query_words if word in text_lower)
        return matched / len(query_words)

    async def evaluate(self, query: str, retrieved_chunks: List[Dict[str, Any]]) -> Tuple[bool, str, str]:
        """
        Evaluate retrieved chunks against the query.
        Returns: (is_sufficient: bool, reason: str, status: str)
        status can be "REFUSAL", "PASS", or "AGENT_FALLBACK"
        """
        if not retrieved_chunks:
            return False, "No chunks retrieved", "REFUSAL"
            
        # Try to get reranker score, fallback to BM25 or RRF score if reranker is off
        top_chunk = retrieved_chunks[0]
        top_score = top_chunk.get('rerank_score', 0.0)
        
        # If there's no rerank score (e.g. reranker is disabled), we skip Tier 1 score thresholds
        # but for this implementation we assume reranker is active as per specs
        if 'rerank_score' not in top_chunk:
            logger.warning("No rerank_score found in top chunk. Defaulting to Entailment Gate.")
            return await self._evaluate_tier2(query, retrieved_chunks)

        logger.info(f"Quality Gate Tier 1: Top reranker score = {top_score:.4f}")

        # Tier 1 (Fast Prune via Option A)
        if top_score < 0.35:
            return False, f"Score {top_score:.2f} < 0.35 (Total Miss)", "REFUSAL"
            
        if top_score > 0.85:
            overlap = self._calculate_keyword_overlap(query, top_chunk['text'])
            logger.info(f"Quality Gate Tier 1: Keyword overlap = {overlap:.2f}")
            if overlap > 0.7:  # Near-unanimous keyword overlap threshold
                return True, "Direct Pass (Score > 0.85, High Overlap)", "PASS"
                
        # Tier 2 (Entailment Check via Option B)
        logger.info("Quality Gate Tier 2: Triggering NLI/Entailment check...")
        return await self.evaluate_tier2(query, retrieved_chunks)
        
    async def evaluate_tier2(self, query: str, retrieved_chunks: List[Dict[str, Any]]) -> Tuple[bool, str, str]:
        """Use a small LLM to evaluate if the context entails/suffices for the query."""
        context_text = "\n\n".join([c["text"] for c in retrieved_chunks[:10]])
        
        prompt = f"""You are a strict Entailment and Sufficiency Judge for a Legal RAG system.
Evaluate whether the provided context contains sufficient information to answer the user's query.

Query: {query}

Context:
{context_text}

Output a JSON object with a single boolean field "is_sufficient" set to true or false. Output NOTHING else.
"""
        messages = [{"role": "system", "content": prompt}]
        try:
            response = await self.intent_llm.generate_json_async(messages)
            is_sufficient = response.get("is_sufficient", False)
            if isinstance(is_sufficient, str):
                is_sufficient = is_sufficient.lower() == "true"
                
            if is_sufficient:
                return True, "Tier 2: Context is sufficient", "PASS"
            else:
                return False, "Tier 2: Context insufficient", "AGENT_FALLBACK"
        except Exception as e:
            logger.error(f"Error in Tier 2 Entailment: {e}")
            # Fallback to agent if validation fails
            return False, "Tier 2: Error evaluating", "AGENT_FALLBACK"
