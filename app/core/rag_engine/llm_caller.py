from typing import Dict, List, Optional
from app.core.llm_provider import LLMProvider

async def call_llm(messages: List[Dict[str, str]], llm_provider: LLMProvider, telemetry_ctx: Optional[Dict] = None) -> str:
    """Call the primary LLM with graceful fallback."""
    try:
        return await llm_provider.generate_async(messages, telemetry_ctx)
    except Exception as e:
        print(f"Primary LLM ({llm_provider.provider}) failed: {e}. Falling back to Ollama...")
        # Fallback to local Ollama if primary fails
        fallback_provider = LLMProvider(provider="ollama")
        return await fallback_provider.generate_async(messages, telemetry_ctx)
