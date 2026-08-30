import re
from typing import Dict, Any, List

def format_context(chunks: List[Dict[str, Any]]) -> str:
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
            filename = meta.get('kanoon_doc_id', '')
            
            # Try to extract year from date
            year = "Unknown Year"
            if date:
                year_match = re.search(r'\b(19|20)\d{2}\b', str(date))
                if year_match:
                    year = year_match.group(0)
            
            if filename:
                header = f"--- Document {i+1} [Case: {title} | {citation} | {court}, {year} | File: {filename}] ---"
            else:
                header = f"--- Document {i+1} [Case: {title} | {citation} | {court}, {year}] ---"
            
        elif source_type == 'upload':
            filename = meta.get('filename', 'unknown_file')
            page_num = meta.get('page_num', meta.get('chunk_index', 0) + 1)
            header = f"--- Document {i+1} [Client File: {filename}, Page {page_num}] ---"
            
        else:
            header = f"--- Document {i+1} ---"
            
        context_parts.append(f"{header}\n{chunk['text']}\n")
        
    return "\n".join(context_parts)
