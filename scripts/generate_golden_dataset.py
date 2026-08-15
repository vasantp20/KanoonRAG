import os
import sys
import csv
import json
import random
import time
import re
import argparse
import urllib.request
import urllib.error
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config

try:
    import pandas as pd
except ImportError:
    print("Error: pandas is not installed. Please install it using `pip3 install pandas`")
    sys.exit(1)

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF is not installed. Please install it using `pip3 install pymupdf`")
    sys.exit(1)

try:
    from groq import Groq
except ImportError:
    print("Warning: groq is not installed. `--provider groq` will not work.")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import chromadb
except ImportError:
    print("Error: Missing chromadb dependency. Please install it using `pip3 install chromadb`")
    sys.exit(1)

KAGGLE_DIR = Path("data/kaggle")
CSV_PATH = KAGGLE_DIR / "judgments.csv"
PDF_DIR = KAGGLE_DIR / "pdfs"
OUTPUT_FILE = "golden_dataset_ragas.csv"

BATCH_SIZE = 20
MIN_TEXT_LENGTH = 10000  # Minimum characters to be considered a "robust" document
RATE_LIMIT_DELAY = 5.0 # Seconds to wait between Groq API calls to avoid rate limiting


def extract_full_text(pdf_path: Path) -> str:
    """Extract full text from a PDF file."""
    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path.name}: {e}")
    return text


def get_default_ollama_model() -> str:
    """Fetch the first available model from local Ollama instance."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            models = data.get("models", [])
            if models:
                return models[0]["name"]
    except Exception as e:
        print(f"Error communicating with local Ollama: {e}")
    return None


def generate_qa_pair_ollama(text: str, model_name: str, index: int) -> dict:
    """Uses Local Ollama LLM to generate a question, ground_truth, and contexts from the text."""
    prompt = f"""You are an expert Indian legal assistant. Based on the following legal document excerpt, generate a single robust, highly specific Q&A pair suitable for a Ragas evaluation dataset.

The output MUST be a valid JSON object with EXACTLY the following keys and structure:
{{
  "question": "A highly specific, complex legal question that a lawyer might ask, which is perfectly answered by the text.",
  "ground_truth": "The ideal, comprehensive correct answer based solely on the provided document.",
  "contexts": ["Exact verbatim text chunk 1 from the document that contains the answer", "Exact verbatim text chunk 2 from the document..."]
}}

Document Excerpt:
{text[:15000]}

Output STRICTLY valid JSON and nothing else.
"""
    print(f"[{index}/{BATCH_SIZE}] Sending request to local Ollama (Model: {model_name})...")
    
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_ctx": 8192
        }
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        # Local LLMs can take a long time to process large contexts, setting a high timeout
        with urllib.request.urlopen(req, timeout=600) as response:
            raw_response = response.read().decode()
            if not raw_response.strip():
                print(f"[{index}/{BATCH_SIZE}] Error: Received empty response from Ollama. The model might have crashed or exceeded context limits.")
                return None
                
            try:
                result = json.loads(raw_response)
            except json.JSONDecodeError:
                print(f"[{index}/{BATCH_SIZE}] Error: Failed to parse JSON. Raw response: {raw_response[:500]}")
                return None
                
            content = result.get("response", "{}")
            
            try:
                parsed_data = json.loads(content)
            except json.JSONDecodeError:
                # Sometimes the LLM wraps the JSON in markdown blocks
                content = content.replace("```json", "").replace("```", "").strip()
                try:
                    parsed_data = json.loads(content)
                except json.JSONDecodeError:
                    print(f"[{index}/{BATCH_SIZE}] Error: Model output is not valid JSON. Output: {content[:200]}")
                    return None
            
            if "question" in parsed_data and "ground_truth" in parsed_data and "contexts" in parsed_data:
                print(f"[{index}/{BATCH_SIZE}] Successfully generated QA pair.")
                return parsed_data
            else:
                print(f"[{index}/{BATCH_SIZE}] Error: Missing keys in JSON output.")
                return None
    except Exception as e:
        print(f"[{index}/{BATCH_SIZE}] Error generating QA with Ollama: {e}")
        return None


def generate_qa_pair_groq(text: str, client: Groq, index: int) -> dict:
    """Uses Groq LLM to generate a question, ground_truth, and contexts from the text."""
    prompt = f"""You are an expert Indian legal assistant. Based on the following legal document excerpt, generate a single robust, highly specific Q&A pair suitable for a Ragas evaluation dataset.

The output MUST be a valid JSON object with EXACTLY the following keys and structure:
{{
  "question": "A highly specific, complex legal question that a lawyer might ask, which is perfectly answered by the text.",
  "ground_truth": "The ideal, comprehensive correct answer based solely on the provided document.",
  "contexts": ["Exact verbatim text chunk 1 from the document that contains the answer", "Exact verbatim text chunk 2 from the document..."]
}}

Document Excerpt:
{text[:25000]}

Output STRICTLY valid JSON and nothing else.
"""
    
    max_retries = 3
    for attempt in range(max_retries):
        print(f"[{index}/{BATCH_SIZE}] Sending request to Groq... (Attempt {attempt + 1})")
        try:
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=config.GROQ_MODEL,
                temperature=0.1,
                response_format={"type": "json_object"},
                max_tokens=2000
            )
            content = response.choices[0].message.content
            data = json.loads(content)
            
            # Validate basic schema
            if "question" in data and "ground_truth" in data and "contexts" in data:
                print(f"[{index}/{BATCH_SIZE}] Successfully generated QA pair.")
                return data
            else:
                print(f"[{index}/{BATCH_SIZE}] Error: Missing keys in JSON output.")
                return None
                
        except Exception as e:
            error_str = str(e)
            if "rate_limit_exceeded" in error_str or "Rate limit reached" in error_str or "429" in error_str:
                match = re.search(r'Please try again in (?:(\d+)h)?(?:(\d+)m)?(?:([\d.]+)s)?', error_str)
                wait_time = 60.0 # Default fallback
                if match:
                    h = float(match.group(1) or 0)
                    m = float(match.group(2) or 0)
                    s = float(match.group(3) or 0)
                    wait_time = h * 3600 + m * 60 + s
                    wait_time += 2.0
                
                print(f"[{index}/{BATCH_SIZE}] Rate limit hit! Waiting for {wait_time:.1f} seconds before retrying...")
                time.sleep(wait_time)
            else:
                print(f"[{index}/{BATCH_SIZE}] Error generating QA: {e}")
                return None
                
    print(f"[{index}/{BATCH_SIZE}] Max retries reached for this document.")
    return None


def main():
    parser = argparse.ArgumentParser(description="Generate Golden Dataset for RAG Evaluation")
    parser.add_argument("--provider", type=str, choices=["groq", "ollama"], default="groq", 
                        help="LLM provider to use (default: groq)")
    parser.add_argument("--ollama_model", type=str, default=None, 
                        help="Ollama model to use. If not provided, it auto-detects the first downloaded model.")
    args = parser.parse_args()

    client_groq = None
    ollama_model_name = None

    if args.provider == "groq":
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("Error: GROQ_API_KEY environment variable is missing. Please set it.")
            sys.exit(1)
        if 'Groq' not in globals():
            print("Error: groq library is missing. Install with pip3 install groq")
            sys.exit(1)
        client_groq = Groq(api_key=api_key)
    else:
        ollama_model_name = args.ollama_model
        if not ollama_model_name:
            ollama_model_name = get_default_ollama_model()
            if not ollama_model_name:
                print("Error: Could not detect a local Ollama model. Ensure Ollama is running and has a model downloaded.")
                sys.exit(1)
            print(f"Auto-detected Ollama model: {ollama_model_name}")

    if not CSV_PATH.exists() or not PDF_DIR.exists():
        print(f"Error: Dataset not found in {KAGGLE_DIR}")
        sys.exit(1)
        
    print("Connecting to ChromaDB to retrieve processed matrimonial documents...")
    try:
        client_chroma = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
        collection = client_chroma.get_collection(config.KANOON_COLLECTION)
        results = collection.get(include=['metadatas'])
        
        processed_doc_ids = set()
        if results and results.get('metadatas'):
            for meta in results['metadatas']:
                if meta and 'kanoon_doc_id' in meta:
                    processed_doc_ids.add(meta['kanoon_doc_id'])
    except Exception as e:
        print(f"Error accessing ChromaDB: {e}")
        sys.exit(1)

    print(f"Found {len(processed_doc_ids)} matrimonial documents in the database.")
    
    if not processed_doc_ids:
        print("No processed documents found in the database. Please run seed_kaggle.py first.")
        sys.exit(1)

    # STATE MANAGEMENT: Load already generated dataset to skip processed PDFs
    already_evaluated_pdfs = set()
    if os.path.exists(OUTPUT_FILE):
        try:
            existing_df = pd.read_csv(OUTPUT_FILE)
            if "source_pdf" in existing_df.columns:
                already_evaluated_pdfs = set(existing_df["source_pdf"].dropna().tolist())
            print(f"State tracking: Found {len(already_evaluated_pdfs)} PDFs already processed in {OUTPUT_FILE}.")
        except Exception as e:
            print(f"Error reading existing CSV state: {e}")

    print(f"Reading dataset from {CSV_PATH} and filtering...")
    valid_pdfs = []
    
    # Read the CSV to find valid PDFs
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            diary_no = row.get("diary_no", "")
            temp_link = row.get("temp_link", "")
            if not temp_link:
                continue
            
            safe_link = temp_link.replace("/", "__")
            pdf_filename = f"{diary_no}___{safe_link}"
            
            # Skip if not in the Chroma database
            if pdf_filename not in processed_doc_ids:
                continue
                
            # Skip if already evaluated in previous runs
            if pdf_filename in already_evaluated_pdfs:
                continue
                
            pdf_path = PDF_DIR / pdf_filename
            
            if pdf_path.exists():
                valid_pdfs.append(pdf_path)

    print(f"Found {len(valid_pdfs)} unprocessed PDFs. Filtering for robust documents...")
    
    # Shuffle to ensure random selection
    random.shuffle(valid_pdfs)
    
    robust_docs = []
    for pdf_path in valid_pdfs:
        text = extract_full_text(pdf_path)
        if len(text) >= MIN_TEXT_LENGTH:
            robust_docs.append({"path": pdf_path, "text": text})
            
        if len(robust_docs) == BATCH_SIZE:
            break
            
    if not robust_docs:
        print("No more robust unprocessed documents found. You may have finished the entire dataset!")
        sys.exit(0)
        
    print(f"Starting synchronous LLM generation for {len(robust_docs)} documents using {args.provider.upper()}...")
    
    valid_results = []
    for i, doc_info in enumerate(robust_docs):
        text = doc_info["text"]
        pdf_path = doc_info["path"]
        
        if args.provider == "groq":
            result = generate_qa_pair_groq(text, client_groq, i + 1)
        else:
            result = generate_qa_pair_ollama(text, ollama_model_name, i + 1)
            
        if result is not None:
            result["source_pdf"] = pdf_path.name
            valid_results.append(result)
            
        # Add rate limiter delay except for the last iteration (Groq only)
        if args.provider == "groq" and i < len(robust_docs) - 1:
            print(f"Rate limiting: Waiting {RATE_LIMIT_DELAY} seconds before next call...")
            time.sleep(RATE_LIMIT_DELAY)
    
    print(f"\nSuccessfully generated {len(valid_results)}/{len(robust_docs)} golden QA pairs in this batch.")
    
    if valid_results:
        print(f"Appending results to pandas DataFrame and saving to {OUTPUT_FILE}...")
        df = pd.DataFrame(valid_results)
        
        if os.path.exists(OUTPUT_FILE):
            # Append without header
            df.to_csv(OUTPUT_FILE, mode='a', header=False, index=False, encoding="utf-8")
        else:
            # Create new with header
            df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
            
        print("Done! You can run the script again to process the next batch.")
    else:
        print("Failed to generate any valid QA pairs in this batch.")

if __name__ == "__main__":
    main()
