# query_standardizer.py
"""
Standardize search terms using mappings file or LLM.
"""

import json
from src.utils import call_llm, parse_json_response
from src.config import MAPPINGS

def standardize_term(term: str, category: str) -> str:
    """Standardize terms using mappings file."""
    if not MAPPINGS or category not in MAPPINGS:
        return None

    category_mappings = MAPPINGS[category]

    # Try exact match
    if term in category_mappings:
        return category_mappings[term]

    # Try lowercase match
    term_lower = term.lower()
    if term_lower in category_mappings:
        return category_mappings[term_lower]

    # Try case-insensitive search
    for key, value in category_mappings.items():
        if key.lower() == term_lower:
            return value

    return None  # Not found in mappings

def standardize_search(parsed: dict) -> dict:
    """
    Check mappings file for standardized terms.
    If it does not exist, use LLM for unknown terms.
    """
    terms_needing_llm = {}

    for category in ['drugs', 'diseases', 'techniques', 'cell_types', 'tissues']:
        if parsed.get(category) and parsed[category] != 'any':
            standardized = []
            unknown = []

            for term in parsed[category]:
                # Check mappings first
                mapped = standardize_term(term, category)

                if mapped:
                    if mapped.lower() != term.lower():
                        print(f"  → {category}: '{term}' → '{mapped}' (from mappings)")
                    standardized.append(mapped)
                else:
                    # Need LLM for unknown term
                    unknown.append(term)

            # Update parsed with mapped terms
            if standardized:
                parsed[category] = standardized

            # Collect unknown terms for LLM
            if unknown:
                terms_needing_llm[category] = unknown

    # Use LLM for unknown terms
    if terms_needing_llm:
        llm_results = standardize_with_llm(terms_needing_llm)

        for category, terms in llm_results.items():
            if category in parsed:
                # Add LLM results to existing
                existing = parsed[category] if isinstance(parsed[category], list) else []
                parsed[category] = list(set(existing + terms))
            else:
                parsed[category] = terms

    return parsed

def standardize_with_llm(terms: dict) -> dict:
    """Use LLM to standardize unknown terms."""

    prompt = f"""
    Standardize these search terms for a gene expression database.

    Terms: {json.dumps(terms)}

    CRITICAL RULES:
    1. DRUGS - Convert ALL brand names to generic names
        Examples:
       - Herceptin/herceptin = trastuzumab
       - Keytruda/keytruda = pembrolizumab
       - Opdivo/opdivo = nivolumab
    2. DISEASES - Use standard names
        Examples:
       - NSCLC = lung cancer
       - HCC = liver cancer
    3. TECHNIQUES - Use standard abbreviations
    Examples:
       - single-cell RNA-seq = scRNA-seq
    4. CELL_TYPES - Use standard names
    Examples:
       - regulatory T cells = Tregs
    5. TISSUES - Use standard names
    Examples:
       - tumour = tumor
    
    Return ONLY a JSON object with LOWERCASE keys (drugs, diseases, techniques, cell_types, tissues).
    
    Example input: {{"drugs": ["Herceptin"]}}
    Example output: {{"drugs": ["trastuzumab"]}}
    
    JSON:"""

    response = call_llm(prompt)
    standardized = parse_json_response(response)

    if standardized:
        for category in ['drugs', 'diseases', 'techniques', 'cell_types', 'tissues']:
            if category in standardized:
                original = terms.get(category, [])
                if original != standardized[category]:
                    print(f"  {category}: {original} ➡️ {standardized[category]} (from LLM)")
        return standardized  # Return the standardized dict

    return terms  # Return original if LLM failed
