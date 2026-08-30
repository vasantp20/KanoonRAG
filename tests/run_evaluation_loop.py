import asyncio
import httpx
import pandas as pd
import json
import uuid
import os

API_URL = "http://localhost:8000"

async def register_and_get_token():
    async with httpx.AsyncClient() as client:
        # Use a random email to avoid conflicts with existing users
        email = f"test_{uuid.uuid4()}@example.com"
        password = "password123"
        
        register_payload = {
            "email": email,
            "password": password,
            "full_name": "Test Evaluator"
        }
        
        try:
            response = await client.post(f"{API_URL}/auth/register", json=register_payload)
            if response.status_code == 200:
                return response.json()["access_token"]
            elif response.status_code == 400 and "Email already registered" in response.text:
                login_payload = {"email": email, "password": password}
                login_response = await client.post(f"{API_URL}/auth/login", json=login_payload)
                login_response.raise_for_status()
                return login_response.json()["access_token"]
            else:
                response.raise_for_status()
        except Exception as e:
            print(f"Error during authentication: {e}")
            print(f"Make sure the FastAPI server is running at {API_URL}")
            raise

async def fetch_answer_and_contexts(client, query, token):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"query": query}
    
    max_retries = 5
    base_delay = 2.0
    
    for attempt in range(max_retries):
        try:
            # Use a larger timeout for LLM generation
            response = await client.post(
                f"{API_URL}/query/", 
                json=payload, 
                headers=headers, 
                timeout=240.0
            )
            
            if response.status_code == 429:
                delay = base_delay * (2 ** attempt)
                print(f"Rate limited (429) on query '{query[:30]}...'. Retrying in {delay}s...")
                await asyncio.sleep(delay)
                continue
            
            response.raise_for_status()
            data = response.json()
            
            answer = data.get("answer", "")
            # Extract actual chunks from sources
            contexts = [source.get("full_text") or source.get("snippet", "") for source in data.get("sources", [])]
            
            return answer, contexts
        except httpx.HTTPStatusError as e:
            # if it's a 50x error (like groq rate limit propagating as 500), we should also retry
            if e.response.status_code >= 500:
                delay = base_delay * (2 ** attempt)
                print(f"Server error {e.response.status_code} on query '{query[:30]}...'. Retrying in {delay}s...")
                await asyncio.sleep(delay)
                continue
            else:
                print(f"HTTP Error {e.response.status_code} on query '{query[:30]}...': {e}")
                break
        except Exception as e:
            delay = base_delay * (2 ** attempt)
            print(f"Network/Timeout Error on query '{query[:30]}...': {e}. Retrying in {delay}s...")
            await asyncio.sleep(delay)
    
    print(f"Failed to process query '{query[:30]}...' after {max_retries} attempts.")
    return "", []

async def main():
    print("Getting auth token...")
    try:
        token = await register_and_get_token()
    except Exception as e:
        print(f"Failed to get auth token. Exiting.")
        return
        
    print("Loading dataset...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "golden_dataset_ragas.csv")
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: {input_file} not found.")
        return
        
    # Process all cases in the dataset (size controlled by generate script)
    
    print(f"Processing {len(df)} questions sequentially...")
    # Use a single async client for all requests
    async with httpx.AsyncClient() as client:
        results = []
        for index, row in df.iterrows():
            question = row["question"]
            print(f"Processing question {index + 1}/{len(df)}: {question[:50]}...")
            result = await fetch_answer_and_contexts(client, question, token)
            results.append(result)
        
    answers = []
    contexts_list = []
    
    for answer, contexts in results:
        answers.append(answer)
        # Store as stringified JSON list so it's a single string in the CSV cell
        contexts_list.append(json.dumps(contexts))
        
    # Update the dataframe
    df["answer"] = answers
    df["contexts"] = contexts_list
    
    # Ensure exactly the required columns
    final_columns = ["question", "ground_truth", "contexts", "answer"]
    df_final = df[final_columns]
    
    output_filename = os.path.join(script_dir, "ragas_evaluation_ready.csv")
    df_final.to_csv(output_filename, index=False)
    print(f"Done! Evaluation dataset saved to {output_filename}")

if __name__ == "__main__":
    asyncio.run(main())
