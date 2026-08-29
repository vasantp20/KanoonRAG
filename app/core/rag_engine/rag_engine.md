# RAG Engine Specification

## Overview
The RAG (Retrieval-Augmented Generation) engine is the core component responsible for processing legal queries, retrieving relevant case files and user documents, and generating accurate, source-backed responses using LLMs.

## Components

### 1. `RAGEngine` (`rag_engine.py`)
The main orchestrator class that provides the high-level API for the application.

#### Methods
- `query(user_query, user_id, case_id=None, client_info=None, chat_history=None) -> Dict`:
  1. Enhances the user query using legal synonyms.
  2. Embeds the enhanced query.
  3. Searches vector collections (Kanoon cases and uploaded documents) using the embedding.
  4. Assembles retrieved chunks into formatted context.
  5. Builds an LLM prompt using a legal system prompt, client context, and chat history.
  6. Calls the LLM to generate the answer.
  7. Extracts and returns the answer alongside cited sources.
- `generate_document_section(section_name, case_info, context_chunks) -> str`:
  1. Formats context chunks into a document string.
  2. Prompts the LLM to draft a specific section of an Indian family court case document.
  3. Returns the generated section text.

### 2. Query Enhancer (`query_enhancer.py`)
- **Function**: `enhance_query(query: str) -> str`
- **Purpose**: Expands the initial query using a predefined dictionary of legal synonyms (`config.LEGAL_SYNONYMS`) to improve retrieval recall. Matches both single words and multi-word phrases.

### 3. Context Formatter (`context_formatter.py`)
- **Function**: `format_context(chunks: List[Dict]) -> str`
- **Purpose**: Converts raw vector store chunks into a structured text format for the LLM. 
- **Handling**: 
  - **Kanoon Sources**: Formats with title, citation, court, and extracted year.
  - **Upload Sources**: Formats with client filename and page number.

### 4. Source Extractor (`source_extractor.py`)
- **Function**: `extract_sources(chunks: List[Dict]) -> List[Dict]`
- **Purpose**: Parses retrieval chunks and constructs a list of metadata for citations.
- **Data Points**:
  - `relevance_score` (derived from RRF or vector distance).
  - `snippet` (truncated to 200 characters).
  - Source-specific details (Court/Citation for Kanoon docs, Filenames/Page Numbers for user uploads).

### 5. LLM Caller (`llm_caller.py`)
- **Function**: `call_llm(messages: List[Dict], llm_provider: LLMProvider) -> str`
- **Purpose**: Wraps LLM interactions with a fallback mechanism. Attempts primary LLM generation first, and seamlessly falls back to a local `ollama` instance if the primary provider fails.

## Dependencies
- `app.core.embeddings.EmbeddingService`: Used for query vectorization.
- `app.core.vector_store.VectorStore`: Used for similarity search across Kanoon and User Uploads.
- `app.core.llm_provider.LLMProvider`: Abstraction for calling language models.