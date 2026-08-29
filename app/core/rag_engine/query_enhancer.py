import re
import config

def enhance_query(query: str) -> str:
    """Enhance query with legal synonyms."""
    words = re.findall(r'\b\w+\b', query.lower())
    enhanced_terms = set(words)
    
    for word in words:
        if word in config.LEGAL_SYNONYMS:
            enhanced_terms.update(config.LEGAL_SYNONYMS[word])
            
    # Also check for multi-word phrases
    for key, synonyms in config.LEGAL_SYNONYMS.items():
        if key in query.lower():
            enhanced_terms.update(synonyms)
            
    return " ".join(list(enhanced_terms)) + " " + query
