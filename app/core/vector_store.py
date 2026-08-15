import os
from typing import List, Dict, Any, Optional
import chromadb

import config

class VectorStore:
    """ChromaDB operations for RAG pipeline (singleton)."""
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
            
        return cls._instance

    def add_kanoon_chunks(self, chunks: List[Dict[str, Any]]):
        """Add chunks to the kanoon collection."""
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

    def search_kanoon(self, query_embedding: List[float], top_k: int, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search kanoon collection."""
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
                    "distance": results['distances'][0][i] if 'distances' in results and results['distances'] else 0.0
                })
                
        return formatted_results

    def search_uploads(self, query_embedding: List[float], user_id: int, case_id: Optional[int] = None, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search uploads collection."""
        if top_k is None:
            top_k = config.TOP_K_UPLOADS
            
        where_filter = {"user_id": user_id}
        if case_id is not None:
            where_filter["case_id"] = case_id
            
        # Handle case where collection might be empty
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

    def search_all(self, query_embedding: List[float], user_id: int, case_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search both collections and merge results."""
        kanoon_results = self.search_kanoon(query_embedding, config.TOP_K_KANOON)
        upload_results = self.search_uploads(query_embedding, user_id, case_id, config.TOP_K_UPLOADS)
        
        # Combine and sort by distance (lower is better for cosine distance)
        combined = kanoon_results + upload_results
        combined.sort(key=lambda x: x['distance'])
        
        return combined

    def delete_upload_chunks(self, user_id: int, case_id: Optional[int] = None):
        """Delete chunks from uploads collection."""
        where_filter = {"user_id": user_id}
        if case_id is not None:
            where_filter["case_id"] = case_id
            
        self.uploads_collection.delete(where=where_filter)
