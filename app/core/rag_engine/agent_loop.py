import logging
from typing import List, Dict, Any
from app.core.vector_store import VectorStore
from app.core.llm_provider import LLMProvider
from .tools import RAGTools
from .quality_gate import HybridQualityGate

logger = logging.getLogger(__name__)

AGENT_SYSTEM_PROMPT = """You are a Legal Research Agent acting as an Information Fetcher.
The user has asked a query, and the current context is insufficient. You have access to tools to fetch more context.

Tools:
1. `fetch_case_section`: Fetch a specific procedural part of a judgment docket.
   Args: {"kanoon_doc_id": "<doc_id>", "target_section": "operative_order | facts_and_issues | post_mortem_evidence | trial_court_findings"}
2. `fetch_surrounding_paragraphs`: Fetch +3 and -3 paragraphs around a specific retrieved chunk ID.
   Args: {"chunk_id": "<doc_id>_<index>", "window_size": 3}
3. `fetch_full_docket`: Fetch the entire judgment text. Use ONLY if the case is short or section extraction fails.
   Args: {"kanoon_doc_id": "<doc_id>"}

CRITICAL INSTRUCTIONS:
- DO NOT generate long reasoning or internal thoughts.
- Be extremely concise.
- Output ONLY a single JSON object specifying the next tool to call.
- You must NOT answer the user's query yourself.

Output Format:
{
    "action": "tool_call",
    "tool_name": "<name of tool>",
    "tool_args": { ... }
}
"""

class AgentRunner:
    def __init__(self, vector_store: VectorStore, llm_provider: LLMProvider, intent_llm: LLMProvider):
        self.vector_store = vector_store
        self.llm_provider = llm_provider
        self.intent_llm = intent_llm
        self.tools = RAGTools(vector_store, llm_provider)
        self.quality_gate = HybridQualityGate(intent_llm)

    async def run_tool_loop(self, user_query: str, initial_chunks: List[Dict[str, Any]], max_iterations: int = 3) -> Dict[str, Any]:
        """
        Run the agent loop to fetch more context using tools.
        Returns the augmented chunks dict and status.
        """
        current_chunks = list(initial_chunks[:5])
        
        for iteration in range(max_iterations):
            # Format context for the agent
            context_text = "\n\n".join([
                f"[Chunk: {c.get('metadata', {}).get('kanoon_doc_id', 'unknown')}_{c.get('metadata', {}).get('chunk_index', 'tool')}]\n{c['text']}" 
                for c in current_chunks
            ])
            
            messages = [
                {"role": "system", "content": AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": f"Query: {user_query}\n\nCurrent Context:\n{context_text}"}
            ]
            
            logger.info(f"Agent Loop Iteration {iteration+1}/{max_iterations}")
            try:
                response = await self.llm_provider.generate_json_async(messages)
            except Exception as e:
                logger.error(f"Agent LLM error: {e}")
                return {"status": "REFUSAL", "chunks": current_chunks}
                
            action = response.get("action")
            
            if action == "tool_call":
                tool_name = response.get("tool_name")
                tool_args = response.get("tool_args", {})
                
                logger.info(f"Agent calling tool: {tool_name} with args: {tool_args}")
                tool_result = ""
                
                try:
                    if tool_name == "fetch_case_section":
                        tool_result = await self.tools.fetch_case_section(**tool_args)
                    elif tool_name == "fetch_surrounding_paragraphs":
                        tool_result = await self.tools.fetch_surrounding_paragraphs(**tool_args)
                    elif tool_name == "fetch_full_docket":
                        tool_result = await self.tools.fetch_full_docket(**tool_args)
                    else:
                        tool_result = f"Error: Tool {tool_name} not found."
                except Exception as e:
                    tool_result = f"Error executing {tool_name}: {e}"
                    
                # Append the tool result as a pseudo-chunk
                pseudo_chunk = {
                    "text": f"[Tool Result from {tool_name}]:\n{tool_result}",
                    "metadata": {"source": "agent_tool", "chunk_index": f"tool_{iteration}"}
                }
                current_chunks.append(pseudo_chunk)
                
                # Option B: Run Strict Quality Gate Re-Evaluation on updated context
                is_sufficient, gate_reason, gate_status = await self.quality_gate.evaluate_tier2(user_query, current_chunks)
                logger.info(f"Agent Loop Quality Gate Check: {gate_status} (Reason: {gate_reason})")
                
                if is_sufficient:
                    logger.info("Context is now sufficient. Breaking out of Agent Loop.")
                    return {"status": "PASS", "chunks": current_chunks}
                
            else:
                logger.warning(f"Unknown agent action: {action}")
                return {"status": "REFUSAL", "chunks": current_chunks}
                
        # If max iterations reached and still not sufficient
        logger.warning("Max tool iterations reached. Context remains insufficient.")
        return {"status": "REFUSAL", "chunks": current_chunks}
