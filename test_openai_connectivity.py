"""
Test Litellm API connectivity.

Usage:
  1. Set your OPENAI_API_KEY environment variable.
  2. Run: python test_openai_connectivity.py
"""
import os
from dotenv import load_dotenv
import litellm

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    print("[ERROR] OPENAI_API_KEY environment variable not set.")
    exit(1)

try:
    response = litellm.completion(
        model="azure/GPT-4o-mini",
        messages=[{"role": "user", "content": "What is vector database?"}],
        api_key=API_KEY,
        api_base="https://aiportalapi.stu-platform.live/jpe",
    )
    print("[SUCCESS] Litellm API call succeeded.")
    print("Response:", response['choices'][0]['message']['content']) # type: ignore
except Exception as e:
    print("[ERROR] Litellm API call failed:", str(e))