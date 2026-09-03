import json
from typing import Dict, Any, Optional

from app.core.llm_provider import LLMProvider

INTENT_CLASSIFIER_PROMPT = """You are an intelligent legal query router for an Indian law RAG system.
Your task is to analyze the user's query and classify it into one of two intents:
1. "specific_case": The user is asking about a specific judgment, citing a case number, appeal number, or party names (e.g., "Civil Appeal No. 5369 of 2017", "TRF Ltd v Energo").
2. "broad_thematic": The user is asking a general legal question or looking for precedents on a topic (e.g., "Find cases where mother was denied custody").

If the intent is "specific_case":
- Extract the most unique, distinct keywords from the case citation or name (e.g., unique surnames, specific numbers). Omit common legal words (like "v.", "vs", "State", "of").
- Output format: {"intent": "specific_case", "metadata": {"keywords": ["<keyword1>", "<keyword2>"]}}

If the intent is "broad_thematic":
- Perform an "Affirmative Query Expansion". Rewrite the query using positive affirmations and applicable legal terminology to improve vector retrieval.
- Output format: {"intent": "broad_thematic", "expanded_query": "<expanded query>"}

Respond ONLY with valid JSON matching the formats above.
"""

async def classify_intent(query: str, llm_provider: LLMProvider, telemetry_ctx: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Classify the query intent and extract metadata or expand the query.
    """
    messages = [
        {"role": "system", "content": INTENT_CLASSIFIER_PROMPT},
        {"role": "user", "content": f"Query: {query}"}
    ]
    
    try:
        response_dict = await llm_provider.generate_json_async(messages, telemetry_ctx)
        if "intent" in response_dict:
            return response_dict
    except Exception as e:
        print(f"Intent classification failed: {e}")
        
    # Fallback to broad thematic if something fails
    return {
        "intent": "broad_thematic",
        "expanded_query": query
    }
