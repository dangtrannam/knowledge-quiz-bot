"""
Test OpenAI API connectivity.

Usage:
  1. Set your OPENAI_API_KEY environment variable.
  2. Run: python test_openai_connectivity.py
"""
import os
from pyexpat import model
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    print("[ERROR] OPENAI_API_KEY environment variable not set.")
    exit(1)

try:
    client = OpenAI(api_key=API_KEY, base_url="https://aiportalapi.stu-platform.live/jpe", )
    response = client.chat.completions.create(
        model="GPT-4o-mini",
        messages=[{"role": "user", "content": "Hello!"}],
        max_tokens=10
    )
    print("[SUCCESS] OpenAI API call succeeded.")
    print("Response:", response.choices[0].message.content)
except Exception as e:
    print("[ERROR] OpenAI API call failed:", str(e)) 