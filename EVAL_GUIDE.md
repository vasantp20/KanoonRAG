# KanoonRAG Evaluation Guide

This guide outlines the end-to-end process for generating a synthetic "golden" dataset and running the Ragas evaluation pipeline to benchmark KanoonRAG's hybrid retrieval, cross-encoder reranking, and generation performance.

---

## 0. Hard Reset (Optional)

If you want to completely start over from a clean slate, you can wipe all databases and evaluation CSVs using this command from the root directory:

```bash
# Stop any running uvicorn servers first!
rm -rf data/chroma_db
rm -f data/kanoonrag.db
rm -f tests/golden_dataset_ragas.csv
rm -f tests/ragas_evaluation_ready.csv
rm -f tests/kannon_final_report_local_*.csv

# Re-initialize the basic SQLite database structure
python3 scripts/init_db.py
```

## 1. Seed the Vector Database

Before generating an evaluation dataset, you must seed documents into your vector database. The dataset generator queries ChromaDB to find valid documents.

```bash
python3 scripts/seed_kaggle.py
```

## 2. Generate the Golden Dataset

The `generate_golden_dataset.py` script asks the LLM to read chunks of your seeded legal PDFs and generate highly specific legal questions to act as ground truth.

> **Important:** Run this from within the `tests/` directory.

```bash
cd tests
# You can use --provider ollama (uses mistral:7b as per config) or --provider sarvam
python3 ../scripts/generate_golden_dataset.py --provider ollama
cd ..
```

This outputs a file named `tests/golden_dataset_ragas.csv`.

## 3. Run the Evaluation Loop

This step actually asks KanoonRAG the synthetic questions and records its answers and retrieved contexts. 

Because this script tests the system over HTTP, **your FastAPI backend must be running**.

**Terminal 1 (Start the Backend):**
```bash
# Make sure to run this from the project root!
uvicorn app.main:app --reload
```
*(Note: When the backend starts, it will automatically load the `BAAI/bge-reranker-base` Cross-Encoder model into memory).*

**Terminal 2 (Run the Loop):**
```bash
# Run this from the project root!
cd tests
python3 run_evaluation_loop.py
cd ..
```

This script will fire the questions at your backend. The backend will use Hybrid Search, Cross-Encoder Reranking, and the Strict Grounding Prompt to answer. It outputs a new file named `tests/ragas_evaluation_ready.csv`.

## 4. Run the Ragas Judge

Finally, we use the `ragas` library to evaluate KanoonRAG's generated answers against the ground truth.

**Terminal 2 (Run the Judge):**
```bash
cd tests
python3 evaluate_with_ragas_local.py
cd ..
```

This script outputs the final scores (Faithfulness, Answer Relevance, Context Precision, Context Recall) to the terminal and saves a detailed row-by-row breakdown to a timestamped CSV file like `tests/kannon_final_report_local_<timestamp>.csv`.
