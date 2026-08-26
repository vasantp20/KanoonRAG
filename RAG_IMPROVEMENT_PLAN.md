# KanoonRAG Improvement Plan

This document outlines the architectural changes required to address the bottlenecks identified in the recent Ragas evaluation run (low Faithfulness, low Context Precision/Recall, and Parametric Bleed).

## 1. Advanced Document Chunking & Segmentation
**Goal:** Prevent mid-sentence and mid-statute truncation to ensure complete legal context is passed to the LLM.
- **Action:** Replace arbitrary character-length splitting with a `RecursiveCharacterTextSplitter`.
- **Separators:** Prioritize legal structural boundaries: `["\n\n", "\n", "Section", "Rule", "Article", "(1)", "(2)", "(a)", "(b)", ". "]`.
- **Sizing:** Increase chunk size to 600–800 tokens with a 150-token overlap to ensure paragraphs and long legal sentences remain intact.
- **(Optional) Parent-Child Chunking:** Index smaller chunks for high-granularity dense matching, but retrieve and pass the full parent paragraph/section to the LLM.

## 2. Hybrid Retrieval (Dense Vectors + Sparse BM25)
**Goal:** Guarantee retrieval of exact alphanumeric statutory references (e.g., "Section 304B", "TRF Ltd.") which dense embeddings often map too broadly.
- **Action:** Implement a dual-retrieval system.
- **Dense Layer:** Keep the existing ChromaDB `BAAI/bge-small-en-v1.5` index for semantic matching.
- **Sparse Layer:** Implement an in-memory or persisted BM25 index (e.g., using Python's `rank_bm25` library) over the document chunks for exact keyword matching.
- **Fusion:** Merge the results from both retrievers using Reciprocal Rank Fusion (RRF) to produce a single, unified list of candidate chunks.

## 3. Cross-Encoder Reranking
**Goal:** Filter out procedural court boilerplate and rank the most substantively relevant chunks at the very top.
- **Action:** Introduce a reranking step after the hybrid retrieval fusion.
- **Model:** Integrate a lightweight cross-encoder (e.g., `BAAI/bge-reranker-base` or `cross-encoder/ms-marco-MiniLM-L-6-v2`) via `sentence-transformers` or `FlashRank`.
- **Workflow:** Retrieve the top 15-20 candidates using Hybrid Search -> Pass them through the Reranker -> Return the top 4-5 strictly relevant chunks to the LLM generator.

## 4. Strict Grounding "Anti-Parametric" Prompt
**Goal:** Prevent the LLM from relying on its pre-trained weights when retrieval fails, forcing it to admit when facts are missing (improving Faithfulness).
- **Action:** Overhaul the `LEGAL_SYSTEM_PROMPT` in `app/core/rag_engine.py`.
- **Implementation:** Introduce strict constraints requiring the LLM to base its answer *exclusively* on the provided context. If a statute or fact is missing/truncated, the LLM must explicitly state that the provided record is incomplete, rather than filling in the gaps from memory.
