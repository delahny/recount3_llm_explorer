# utils.py
"""
Shared utilities.
"""

import json
import ollama
from src.config import MODEL

def parse_json_response(response_text: str) -> dict:
    """Extract JSON from LLM response."""
    start = response_text.find('{')
    end = response_text.rfind('}') + 1
    if start != -1 and end > start:
        try:
            return json.loads(response_text[start:end])
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Raw response: {response_text[start:end]}")
            return {}
    return {}

def call_llm(prompt: str, temperature: float = 0) -> str:
    """Call the LLM and return response text."""
    try:
        response = ollama.chat(
            model=MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': temperature}
        )
        return response['message']['content'].strip()
    except Exception as e:
        print(f"LLM error: {e}")
        return ""
