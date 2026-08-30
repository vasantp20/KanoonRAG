import os
import re
from typing import List, Dict, Any, Optional
import chromadb

import config

class VectorStore:
    """ChromaDB and BM25 operations for RAG pipeline (singleton)."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
            
            # Initialize ChromaDB persistent client
            os.makedirs(config.CHROMA_PERSIST_DIR, exist_ok=True)
            cls._instance.client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
            
            # Initialize collections
            cls._instance.kanoon_collection = cls._instance.client.get_or_create_collection(
                name=config.KANOON_COLLECTION,
                metadata={"hnsw:space": "cosine"}
            )
            cls._instance.uploads_collection = cls._instance.client.get_or_create_collection(
                name=config.USER_UPLOADS_COLLECTION,
                metadata={"hnsw:space": "cosine"}
            )
            
            # Initialize BM25 state
            cls._instance.kanoon_bm25 = None
            cls._instance.kanoon_bm25_docs = []
            cls._instance.kanoon_bm25_meta = []
            cls._instance._build_bm25()
            
            # Initialize Cross-Encoder
            try:
                from sentence_transformers import CrossEncoder
                print("Loading BAAI/bge-reranker-base...")
                cls._instance.reranker = CrossEncoder('BAAI/bge-reranker-base')
                print("Reranker loaded successfully!")
            except Exception as e:
                print(f"Error loading reranker: {e}")
                cls._instance.reranker = None
                
        return cls._instance

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenizer for BM25."""
        if not text:
            return []
        return re.findall(r'\w+', text.lower())

    def _build_bm25(self):
        """Build the in-memory BM25 index from Chroma documents."""
        try:
            from rank_bm25 import BM25Okapi
            
            data = self.kanoon_collection.get(include=['documents', 'metadatas'])
            if data and data['documents']:
                self.kanoon_bm25_docs = data['documents']
                self.kanoon_bm25_meta = data['metadatas']
                tokenized_corpus = [self._tokenize(doc) for doc in self.kanoon_bm25_docs]
                self.kanoon_bm25 = BM25Okapi(tokenized_corpus)
        except Exception as e:
            print(f"Error building BM25 index: {e}")

    def add_kanoon_chunks(self, chunks: List[Dict[str, Any]]):
        """Add chunks to the kanoon collection and rebuild BM25."""
        if not chunks:
            return
            
        ids = []
        embeddings = []
        metadatas = []
        documents = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{chunk['metadata'].get('kanoon_doc_id', 'unknown')}_{chunk['metadata'].get('chunk_index', i)}"
            ids.append(chunk_id)
            if 'embedding' in chunk:
                embeddings.append(chunk['embedding'])
            metadatas.append(chunk['metadata'])
            documents.append(chunk['text'])
            
        if embeddings:
            self.kanoon_collection.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)
        else:
            self.kanoon_collection.upsert(ids=ids, metadatas=metadatas, documents=documents)
            
        # Rebuild BM25 index after adding new chunks
        self._build_bm25()

    def add_upload_chunks(self, chunks: List[Dict[str, Any]]):
        """Add chunks to the uploads collection."""
        if not chunks:
            return
            
        ids = []
        embeddings = []
        metadatas = []
        documents = []
        
        for i, chunk in enumerate(chunks):
            # Require user_id and case_id for uploads
            user_id = chunk['metadata'].get('user_id')
            case_id = chunk['metadata'].get('case_id')
            file_id = chunk['metadata'].get('file_id', 'unknown')
            chunk_idx = chunk['metadata'].get('chunk_index', i)
            
            chunk_id = f"{user_id}_{case_id}_{file_id}_{chunk_idx}"
            ids.append(chunk_id)
            
            if 'embedding' in chunk:
                embeddings.append(chunk['embedding'])
                
            # Filter out None values in metadatas as ChromaDB doesn't allow them
            clean_metadata = {k: v for k, v in chunk['metadata'].items() if v is not None}
            metadatas.append(clean_metadata)
            documents.append(chunk['text'])
            
        if embeddings:
            self.uploads_collection.upsert(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents)
        else:
            self.uploads_collection.upsert(ids=ids, metadatas=metadatas, documents=documents)

    def search_kanoon_dense(self, query_embedding: List[float], top_k: int, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search kanoon collection using Dense Vectors."""
        results = self.kanoon_collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filters,
            include=['documents', 'metadatas', 'distances']
        )
        
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "dense_distance": results['distances'][0][i] if 'distances' in results and results['distances'] else 0.0
                })
                
        return formatted_results

    def search_kanoon_sparse(self, query: str, top_k: int, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search kanoon collection using Sparse BM25."""
        if not self.kanoon_bm25:
            return []
            
        tokenized_query = self._tokenize(query)
        scores = self.kanoon_bm25.get_scores(tokenized_query)
        
        scored_docs = [(idx, score) for idx, score in enumerate(scores) if score > 0]
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for idx, score in scored_docs:
            meta = self.kanoon_bm25_meta[idx]
            
            # Apply filters
            if filters:
                def _evaluate_filter(f_dict, metadata):
                    if "$or" in f_dict:
                        return any(_evaluate_filter(sub_f, metadata) for sub_f in f_dict["$or"])
                    if "$and" in f_dict:
                        return all(_evaluate_filter(sub_f, metadata) for sub_f in f_dict["$and"])
                    
                    for k, v in f_dict.items():
                        if isinstance(v, dict):
                            if "$contains" in v:
                                if v["$contains"].lower() not in str(metadata.get(k, "")).lower():
                                    return False
                        elif metadata.get(k) != v:
                            return False
                    return True

                if not _evaluate_filter(filters, meta):
                    continue
                    
            results.append({
                "text": self.kanoon_bm25_docs[idx],
                "metadata": meta,
                "bm25_score": score
            })
            
            if len(results) >= top_k:
                break
                
        return results

    def search_uploads(self, query_embedding: List[float], user_id: int, case_id: Optional[int] = None, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search uploads collection."""
        if top_k is None:
            top_k = config.TOP_K_UPLOADS
            
        where_filter = {"user_id": user_id}
        if case_id is not None:
            where_filter["case_id"] = case_id
            
        try:
            results = self.uploads_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter,
                include=['documents', 'metadatas', 'distances']
            )
        except Exception:
            return []
            
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "distance": results['distances'][0][i] if 'distances' in results and results['distances'] else 0.0
                })
                
        return formatted_results

    def reciprocal_rank_fusion(self, dense_results: List[Dict], sparse_results: List[Dict], k=60) -> List[Dict]:
        """Fuse dense and sparse results using RRF."""
        fused_scores = {}
        chunk_map = {}
        
        def get_key(res):
            meta = res.get('metadata', {})
            return meta.get('parent_id') or meta.get('kanoon_doc_id') or hash(res['text'])

        for rank, res in enumerate(dense_results):
            key = get_key(res)
            chunk_map[key] = res
            fused_scores[key] = fused_scores.get(key, 0.0) + (1.0 / (k + rank))
            
        for rank, res in enumerate(sparse_results):
            key = get_key(res)
            if key not in chunk_map:
                chunk_map[key] = res
            fused_scores[key] = fused_scores.get(key, 0.0) + (1.0 / (k + rank))
            
        ranked_keys = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)
        
        final_results = []
        for key in ranked_keys:
            res = chunk_map[key]
            res['rrf_score'] = fused_scores[key]
            final_results.append(res)
            
        return final_results

    def search_all(self, query: str, query_embedding: List[float], user_id: int, case_id: Optional[int] = None, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search both collections using Hybrid Search, RRF, and Cross-Encoder Reranking."""
        fusion_k = config.TOP_K_KANOON * 3 
        
        dense_results = self.search_kanoon_dense(query_embedding, fusion_k, filters=filters)
        sparse_results = self.search_kanoon_sparse(query, fusion_k, filters=filters)
        
        kanoon_results = self.reciprocal_rank_fusion(dense_results, sparse_results)
        
        upload_results = self.search_uploads(query_embedding, user_id, case_id, config.TOP_K_UPLOADS * 3)
        
        combined = kanoon_results + upload_results
        
        if getattr(self, 'reranker', None) and combined:
            pairs = [[query, res['text']] for res in combined]
            scores = self.reranker.predict(pairs)
            for res, score in zip(combined, scores):
                res['rerank_score'] = float(score)
            combined.sort(key=lambda x: x['rerank_score'], reverse=True)
            
        final_limit = config.TOP_K_KANOON + config.TOP_K_UPLOADS
        return combined[:final_limit]

    def get_complete_documents(self, doc_ids: List[str]) -> List[Dict[str, Any]]:
        """Fetch all chunks for given kanoon_doc_ids and stitch them together."""
        completed_docs = []
        for doc_id in doc_ids:
            try:
                results = self.kanoon_collection.get(
                    where={"kanoon_doc_id": doc_id},
                    include=['documents', 'metadatas']
                )
                if not results['documents']:
                    continue
                
                chunks_with_meta = list(zip(results['documents'], results['metadatas']))
                sorted_chunks = sorted(chunks_with_meta, key=lambda x: x[1].get('chunk_index', 0))
                
                full_text = "\n\n".join([chunk[0] for chunk in sorted_chunks])
                completed_docs.append({
                    "text": full_text,
                    "metadata": sorted_chunks[0][1] if sorted_chunks else {}
                })
            except Exception as e:
                print(f"Error fetching complete doc {doc_id}: {e}")
                
        return completed_docs

    def delete_upload_chunks(self, user_id: int, case_id: Optional[int] = None):
        """Delete chunks from uploads collection."""
        where_filter = {"user_id": user_id}
        if case_id is not None:
            where_filter["case_id"] = case_id
            
        self.uploads_collection.delete(where=where_filter)
