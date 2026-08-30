from typing import Dict, Any, List

def extract_sources(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract formatted source metadata from retrieved chunks."""
    sources = []
    for i, chunk in enumerate(chunks):
        meta = chunk.get('metadata', {})
        source_type = meta.get('source_type', 'unknown')
        
        if 'rrf_score' in chunk:
            relevance_score = chunk['rrf_score'] * 100  # Scale up RRF for readability
        else:
            relevance_score = 1.0 - chunk.get('distance', 0.0)
            
        source = {
            "source_type": source_type,
            "relevance_score": relevance_score,
            "snippet": chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text'],
            "full_text": chunk['text']
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
