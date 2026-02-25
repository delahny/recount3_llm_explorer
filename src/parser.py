# parser.py
"""
Query parsing functions.
"""

from src.utils import call_llm, parse_json_response


def parse_search_query(user_query: str) -> dict:
    """Parse natural language queries into structured search parameters."""
    prompt = f"""
    Extract ONLY the biological/technical entities from this search query.

    Query: "{user_query}"
    TYPO HANDLING:
    - Auto-correct obvious typos: "brest cancer" → "breast cancer", "melonoma" → "melanoma"
    - Fix common misspellings: "tamoxifin" → "tamoxifen", "trastuzumob" → "trastuzumab"
    - If a word is close to a known term, use the correct term
    - Only flag as unrecognized if you truly cannot guess the intent
    
    CRITICAL RULES:
    - DISCARD words like "studies", "research", "find", "show me", "data", "results", "analysis", "datasets".
    - DISCARD any punctuation.
    - "human" and "mouse" are ORGANISMS, nothing else.
    - If a user says "human melanoma", return organism: "human", diseases: ["melanoma"]
    - If a user says "breast cancer studies", return ONLY "breast cancer".
    - If a user says "studies with tamoxifen", return ONLY "tamoxifen".
    - Use null for any field the user did NOT explicitly mention. Never return "any" unless the user said "any"
    
    Return ONLY a JSON object with search filters. Use null for any field not mentioned:
    {{
        "drugs": ["drug names if mentioned"],
        "genes": ["gene symbols if mentioned"],
        "cell_types": ["cell types if mentioned"],
        "diseases": ["diseases if mentioned"],
        "techniques": ["techniques if mentioned"],
        "tissues": ["tissues if mentioned"],
        "organism": "human" or "mouse",
        "min_samples": number,
        "max_samples": number
    }}
    All fields default to null if not mentioned.
    
    IMPORTANT: Return ONLY the JSON object. No explanation before or after, NO extra text, NO comments, NO trailing commas.
    JSON:"""

    response = call_llm(prompt)
    return parse_json_response(response)


def parse_analyze_query(user_query: str) -> dict:
    """Parse analysis question to extract filters."""
    prompt = f"""
    You are analyzing the full dataset. Extract filters from the user's analysis question.

    Question: "{user_query}"
    
    IMPORTANT QUERIES TO LOOK FOR ANALYSIS:
    - "How many" or "top" or "most common" or "most commonly used" = count from the database
    
    CRITICAL RULES:
    - Extract ONLY the specific entity. 
    - DISCARD conversational filler: "studies", "research", "analyze", "show me", "data", "expression".
    - DISCARD any punctuation.
    
    Examples:
    - "Analyze breast cancer studies" = {{"disease": "breast cancer"}}
    - "Top genes in human lung cancer" = {{"organism": "human", "disease": "lung cancer"}}
    - "How many studies mention CRC?" = {{"disease": "colorectal cancer"}}
    - "What are the most commonly used drugs for PDAC treatment?" = {{"disease": "PDAC"}}
    
    Return ONLY a JSON object with analysis filters (fields default to null if not mentioned):
    {{
        "question": "the core question",
        "organism": "human" or "mouse",
        "disease": "disease name",
        "drugs": "drug name",
        "genes": "gene name",
        "cell_types": "cell types",
        "tissues": "tissues"
    }}
    
    JSON:"""

    response = call_llm(prompt)
    result = parse_json_response(response)
    return result if result else {'question': user_query,
                                  'organism': None,
                                  'disease': None,
                                  'drugs': None,
                                  'genes': None,
                                  'cell_types': None,
                                  'tissues': None}
