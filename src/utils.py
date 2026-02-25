# utils.py
"""
Shared utilities.
"""

import json
import ollama

_ACTIVE_MODEL = None

def set_llm_model(model: str) -> None:
    """Set the active model used by call_llm."""
    global _ACTIVE_MODEL
    if model:
        _ACTIVE_MODEL = model

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

def call_llm(prompt: str, temperature: float = 0, model: str = None) -> str:
    """Call the LLM and return response text."""
    selected_model = model or _ACTIVE_MODEL
    if not selected_model:
        print("LLM error: no model selected. Set model via set_llm_model() or pass model=...")
        return ""

    try:
        response = ollama.chat(
            model=selected_model,
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': temperature}
        )
        return response['message']['content'].strip()
    except Exception as e:
        print(f"LLM error: {e}")
        return ""
