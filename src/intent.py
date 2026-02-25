# intent.py
"""
Intent detection and ambiguity checking.
"""

from src.utils import call_llm, parse_json_response


def detect_intent(user_query: str) -> dict:
    """Detect if user wants to SEARCH or ANALYZE."""
    prompt = f"""
    Classify this query about gene expression studies.

    Query: "{user_query}"
    
    SEARCH queries = Looking for specific studies/datasets
    Examples: "breast cancer studies", "find tamoxifen data", "show me melanoma", "SRP123456"
    
    ANALYZE queries = Asking questions ABOUT the database contents (statistics, summaries, counts)
    Examples: "what drugs are most common?", "summarize techniques", "how many studies?", "top genes", "count diseases", "what are the most frequently used", "what are the most commonly used drugs for breast cancer", "what are the most commonly used drugs for PDAC treatment"
    
    CRITICAL: Questions with "what", "how many", "summarize", "top", "most common", "most commonly used", "count" are ALWAYS ANALYZE queries, 
    even if they mention specific diseases, drugs, or abbreviations.
    
    Return ONLY: {{"intent": "search" or "analyze"}}
    
    JSON:"""

    response = call_llm(prompt)
    result = parse_json_response(response)
    return result if result else {"intent": "search"}


def check_ambiguity(user_query: str) -> dict:
    """Check if query is ambiguous and needs clarification."""
    prompt = f"""
    Analyze this search query for a gene expression database.

    Query: "{user_query}"

    TYPO HANDLING (DO THIS FIRST):
    - "shoe mw" = "show me" (common typo, IGNORE these filler words)
    - "brest" = "breast", "melonoma" = "melanoma", "tamoxifin" = "tamoxifen"
    - Auto-correct obvious typos before analyzing
    - NEVER ask for clarification on typos you can reasonably guess
    
    CRITICAL RULES:
    1. If the query is an ANALYSIS question (e.g., "what drugs", "how many", "summarize", "top", "count"), set is_ambiguous: false.
    2. If the query contains a specific disease, drug, or technique (even with typos), it is NOT ambiguous.
    3. IGNORE filler words and typos like "shoe mw" (show me), "find", "studies", "data"
    4. Focus ONLY on the biological/scientific terms
    5. ONLY return is_ambiguous: true if a SCIENTIFIC TERM is in the KNOWN AMBIGUOUS list below.

    KNOWN AMBIGUOUS TERMS (Ask for clarification ONLY if context is missing):
    - BRCA or brca (Could be genes OR breast cancer) -> Ask: "Are you looking for BRCA genes (BRCA1/BRCA2) or breast cancer studies?"
    - HER2 or her2 (Could be ERBB2 gene OR HER2+ subtype) -> Ask: "Are you looking for HER2 gene or HER2-positive cancer studies?"
    - ER or er (Could be ESR1 gene OR ER+ subtype) -> Ask: "Are you looking for ER gene or estrogen receptor-positive studies?"
    - PD-1, PD-L1, PD1, PDL1 (Could be genes OR drugs) -> Ask: "Are you looking for PD-1/PD-L1 genes or immunotherapy drugs?"

    NOT AMBIGUOUS (Always set is_ambiguous: false):
    - Analysis questions: "what drugs", "how many", "summarize", "top genes", "count"
    - "ovarian cancer", "breast cancer", "lung cancer"
    - "Herceptin", "tamoxifen"
    - "BRCA1", "TP53"
    - "scRNA-seq"
    
    Example interpretations:
    - "shoe mw Keytruda studies" = "show me Keytruda studies" = NOT ambiguous, search for Keytruda
    - "brest cancer" = "breast cancer" = NOT ambiguous
    - "show me BRCA studies" = is ambiguous = Ask: "Are you looking for BRCA genes (BRCA1/BRCA2) or breast cancer studies?"
    
    Return ONLY a JSON object:
    {{
        "is_ambiguous": boolean,
        "is_clear": boolean,
        "query_type": "search" or "analyze",
        "ambiguous_term": string or null,
        "clarifying_question": string or null (MUST provide a question if is_ambiguous is true)
    }}

    JSON:"""

    response = call_llm(prompt)
    result = parse_json_response(response)
    # Fallback to safe defaults if LLM fails
    return result if result else {'is_ambiguous': False, 'is_clear': True, 'query_type': 'search'}

def handle_clarification(user_response: str, pending_query: dict) -> dict:
    """Process user's response to a clarifying question."""
    ambiguous_term = pending_query.get('ambiguous_term', '')

    prompt = f"""The user was asked a clarifying question about their search.

    Original query: "{pending_query.get('original_query', '')}"
    Ambiguous term: "{ambiguous_term}"
    Clarifying question: "{pending_query.get('clarifying_question', '')}"
    User's response: "{user_response}"
    
    INTERPRETATION RULES:
    - If ambiguous term is "BRCA":
      - Response like "gene", "genes", "BRCA1", "BRCA2" = genes: ["BRCA1", "BRCA2"] (Note: ignore diseases: ["breast cancer"])
      - Response like "cancer", "disease", "breast cancer", "TCGA" = diseases: ["breast cancer"] (Note: ignore genes: ["BRCA1", "BRCA2"])
    
    - If ambiguous term is "PD-1" or "PD-L1":
      - Response like "gene", "PDCD1", "CD274" = genes: ["PDCD1"] or ["CD274"]
      - Response like "drug", "inhibitor", "immunotherapy" = drugs: ["anti-PD-1", "pembrolizumab", "nivolumab"] or ["anti-PD-L1", "atezolizumab"]
    
    Based on their response, determine what they want to search for.
    
    Return ONLY a JSON object:
    {{
        "understood": true or false,
        "category": "drugs" or "genes" or "diseases" or "techniques" or "cell_types" or "tissues",
        "search_terms": ["term1", "term2"],
        "other_filters": {{}}
    }}
    
    Examples:
    Ambiguous: "BRCA", Response: "genes" = {{"understood": true, "category": "genes", "search_terms": ["BRCA1", "BRCA2"], "other_filters": {{}}}}
    Ambiguous: "BRCA", Response: "cancer" = {{"understood": true, "category": "diseases", "search_terms": ["breast cancer"], "other_filters": {{}}}}
    Ambiguous: "BRCA", Response: "breast cancer" = {{"understood": true, "category": "diseases", "search_terms": ["breast cancer"], "other_filters": {{}}}}
    Ambiguous: "HER2", Response: "the gene" = {{"understood": true, "category": "genes", "search_terms": ["HER2", "ERBB2"], "other_filters": {{}}}}
    Ambiguous: "PD-1", Response: "drug" = {{"understood": true, "category": "drugs", "search_terms": ["anti-PD-1", "pembrolizumab", "nivolumab"], "other_filters": {{}}}}
    
    JSON:"""

    response = call_llm(prompt)
    return parse_json_response(response)