import csv
import os
import time
from datetime import datetime

TELEMETRY_FILE = "telemetry.csv"
LATENCY_FILE = "latency.csv"

def _ensure_csv_headers(filename, headers):
    file_exists = os.path.isfile(filename)
    if not file_exists:
        with open(filename, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

def log_llm_usage(query_uuid: str, query: str, step: str, input_tokens: int, output_tokens: int, provider: str):
    """
    Log token usage for an LLM generation step to a CSV file.
    """
    _ensure_csv_headers(TELEMETRY_FILE, ["Timestamp", "UUID", "Query", "Step", "Input Tokens", "Output Tokens", "Provider"])
    with open(TELEMETRY_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            query_uuid,
            query,
            step,
            input_tokens,
            output_tokens,
            provider
        ])

def log_endpoint_latency(endpoint: str, latency: float, query_uuid: str):
    """
    Log endpoint latency.
    """
    _ensure_csv_headers(LATENCY_FILE, ["Timestamp", "Endpoint", "Latency (s)", "UUID"])
    with open(LATENCY_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            endpoint,
            f"{latency:.4f}",
            query_uuid
        ])
