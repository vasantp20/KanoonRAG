import os
import sys
import time
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import ast
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
)
from ragas.run_config import RunConfig
from langchain_community.chat_models import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "ragas_evaluation_ready.csv")
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(script_dir, f"kannon_final_report_local_{timestamp}.csv")

    print(f"Loading dataset from '{csv_path}'...")
    # 1. Load the CSV Data
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: '{csv_path}' not found. Please ensure the file is in the same directory as the script.")
        return

    # Toggle this to True once you're ready to evaluate the entire dataset
    EVALUATE_ALL = True

    # Safely evaluate the contexts column from stringified list to actual Python list
    print("Parsing contexts...")
    try:
        df['contexts'] = df['contexts'].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) else x
        )
    except Exception as e:
        print(f"Error parsing contexts column: {e}")
        return

    # Reduce dataset size for quick validation
    if not EVALUATE_ALL:
        print("Reducing dataset to 5 samples for quick validation...")
        df = df.head(10)

    # Convert pandas dataframe to HuggingFace Dataset object
    dataset = Dataset.from_pandas(df)

    # 2. Configure Fully Local Models
    from app.core.llm_provider import LLMProvider
    
    print("Initializing local LLM and Embeddings...")
    # Dynamically grab the configured primary LLM
    try:
        llm = LLMProvider().get_langchain_model()
    except ImportError as e:
        print(f"Error initializing LLM: {e}")
        return
        
    # Local Embeddings
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")

    # 3. Setup Metrics
    metrics = [
        Faithfulness(),
        AnswerRelevancy(),
        ContextPrecision(),
        ContextRecall()
    ]

    print("Starting evaluation with local models... This may take a while depending on your hardware.")
    
    # 4. Execute Evaluation
    # We severely restrict concurrency (max_workers=1) and increase the timeout 
    # so that the local Ollama instance doesn't get overwhelmed and timeout.
    run_config = RunConfig(timeout=600, max_workers=10)

    try:
        # In ragas >= 0.1.0, you pass llm and embeddings to evaluate()
        result = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=llm,
            embeddings=embeddings,
            raise_exceptions=False, # Robust error handling: prevent crash on single-row failures (e.g., malformed JSON)
            run_config=run_config,
        )
        
        # 5. Output Results
        print("\n=== Evaluation Completed ===")
        print("Aggregate Scores:")
        print(result)

        # Export detailed row-by-row results to CSV
        result_df = result.to_pandas()
        result_df.to_csv(output_path, index=False)
        print(f"\nDetailed results successfully exported to '{output_path}'.")
        
    except Exception as e:
        print(f"\nEvaluation failed with error: {str(e)}")
        print("Note: Local 7B models can sometimes produce malformed JSON that fails parsing in Ragas.")
        print("Consider checking if Ollama is running, or try using a different/larger model if this persists.")

if __name__ == "__main__":
    main()
