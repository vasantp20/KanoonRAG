import re
from typing import List, Dict, Any
import fitz  # PyMuPDF
import docx
from bs4 import BeautifulSoup

import config

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file using PyMuPDF."""
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text() + "\n"
    return text

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file using python-docx."""
    doc = docx.Document(file_path)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

def extract_text_from_kanoon_html(html: str) -> str:
    """Extract text from Kanoon HTML using BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator="\n", strip=True)

def legal_aware_chunk(text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Chunk text using legal section headings, paragraphs, and recursive character split."""
    chunks = []
    
    # Primary split on legal section headings
    section_pattern = re.compile(
        r'^\s*(FACTS|ISSUES|ARGUMENTS|JUDGMENT|ORDER|HELD|SUBMISSIONS|CONTENTIONS)\b', 
        re.IGNORECASE | re.MULTILINE
    )
    
    sections = []
    last_idx = 0
    current_section = "INTRODUCTION"
    
    for match in section_pattern.finditer(text):
        start = match.start()
        if start > last_idx:
            sections.append((current_section, text[last_idx:start].strip()))
        current_section = match.group(1).upper()
        last_idx = start
        
    if last_idx < len(text):
        sections.append((current_section, text[last_idx:].strip()))
        
    chunk_index = 0
    
    # Process each section
    for section_type, section_text in sections:
        if not section_text:
            continue
            
        # Secondary split on paragraphs
        paragraphs = re.split(r'\n\s*\n', section_text)
        
        current_chunk = ""
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            if len(current_chunk) + len(para) + 2 <= config.CHUNK_SIZE:
                current_chunk += ("\n\n" if current_chunk else "") + para
            else:
                if current_chunk:
                    chunk_meta = metadata.copy()
                    chunk_meta.update({"chunk_index": chunk_index, "section_type": section_type})
                    chunks.append({"text": current_chunk, "metadata": chunk_meta})
                    chunk_index += 1
                
                # Fallback recursive character split if a single paragraph is too large
                if len(para) > config.CHUNK_SIZE:
                    idx = 0
                    while idx < len(para):
                        end_idx = min(idx + config.CHUNK_SIZE, len(para))
                        chunk_meta = metadata.copy()
                        chunk_meta.update({"chunk_index": chunk_index, "section_type": section_type})
                        chunks.append({"text": para[idx:end_idx], "metadata": chunk_meta})
                        chunk_index += 1
                        idx += config.CHUNK_SIZE - config.CHUNK_OVERLAP
                    current_chunk = ""
                else:
                    current_chunk = para
                    
        if current_chunk:
            chunk_meta = metadata.copy()
            chunk_meta.update({"chunk_index": chunk_index, "section_type": section_type})
            chunks.append({"text": current_chunk, "metadata": chunk_meta})
            chunk_index += 1
            
    return chunks

def process_uploaded_file(file_path: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Detect file type, extract text, and chunk it."""
    file_path_lower = file_path.lower()
    
    if file_path_lower.endswith('.pdf'):
        text = extract_text_from_pdf(file_path)
    elif file_path_lower.endswith('.docx'):
        text = extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")
        
    return legal_aware_chunk(text, metadata)
