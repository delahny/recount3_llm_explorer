# analyze.py
"""
LLM for analyze queries.
"""

from collections import Counter
from src.config import indexed_data
from src.parser import parse_analyze_query
from src.utils import call_llm
from src.query_standardizer import standardize_search

def analyze(user_query: str):
    """Use the LLM to answer questions about the indexed data."""

    print(f"\n📊 Analyzing...\n")
    parsed = parse_analyze_query(user_query)

    # Standardize parsed terms
    for key in ['disease', 'drugs', 'genes']:
        val = parsed.get(key)
        if val and isinstance(val, str):
            parsed[key] = [val]  # standardize_search expects lists

    parsed = standardize_search(parsed)

    # Unpack back to strings if needed
    for key in ['disease', 'drugs', 'genes']:
        val = parsed.get(key)
        if isinstance(val, list) and val:
            parsed[key] = val[0]

    question = parsed.get('question', user_query)

    # Get target terms
    target_disease = parsed.get('disease')
    target_gene = parsed.get('genes')
    target_drug = parsed.get('drugs')
    organism = parsed.get('organism')

    data_to_analyze = indexed_data

    # Check if this is a counting query
    query_lower = user_query.lower()
    counting_query = any(phrase in query_lower for phrase in ['how many', 'count', 'number of'])

    # Filter by organism
    if organism:
        data_to_analyze = [s for s in data_to_analyze
                           if s.get('organism', '').lower() == organism.lower()]

    # Filter by keyword ONLY if NOT a counting query
    if not counting_query:
        filter_term = target_disease or target_drug or target_gene
        if filter_term:
            term = str(filter_term).lower()
            data_to_analyze = [s for s in data_to_analyze if
                               term in s.get('study_title', '').lower() or
                               any(term in d.lower() for d in s.get('diseases', []))]

    if len(data_to_analyze) == 0:
        return "I found no studies matching that criteria to analyze. Try a broader term!"

    print(f"Analyzing {len(data_to_analyze)} studies...")

    # Aggregate entities
    all_drugs = Counter()
    all_genes = Counter()
    all_cells = Counter()
    all_diseases = Counter()
    all_techniques = Counter()
    all_tissues = Counter()

    for study in data_to_analyze:
        for drug in study.get('drugs', []):
            all_drugs[drug.lower()] += 1
        for gene in study.get('genes', []):
            all_genes[gene.upper()] += 1
        for cell in study.get('cell_types', []):
            all_cells[cell.lower()] += 1
        for dis in study.get('diseases', []):
            all_diseases[dis.lower()] += 1
        for tech in study.get('techniques', []):
            all_techniques[tech.lower()] += 1
        for tissue in study.get('tissues', []):
            all_tissues[tissue.lower()] += 1

    data_summary = f"""
    INDEXED DATA SUMMARY ({len(data_to_analyze)} studies):
    
    DRUGS ({len(all_drugs)} unique):
    {chr(10).join(f'  - {drug}: {count} studies' for drug, count in all_drugs.most_common(30)) or '  None found'}
    
    GENES ({len(all_genes)} unique):
    {chr(10).join(f'  - {gene}: {count} studies' for gene, count in all_genes.most_common(30)) or '  None found'}
    
    CELL TYPES ({len(all_cells)} unique):
    {chr(10).join(f'  - {cell}: {count} studies' for cell, count in all_cells.most_common(30)) or '  None found'}
    
    DISEASES ({len(all_diseases)} unique):
    {chr(10).join(f'  - {dis}: {count} studies' for dis, count in all_diseases.most_common(30)) or '  None found'}
    
    TECHNIQUES ({len(all_techniques)} unique):
    {chr(10).join(f'  - {tech}: {count} studies' for tech, count in all_techniques.most_common(30)) or '  None found'}
    
    TISSUES ({len(all_tissues)} unique):
    {chr(10).join(f'  - {tissue}: {count} studies' for tissue, count in all_tissues.most_common(30)) or '  None found'}
    """

    prompt = f"""
    You are analyzing gene expression studies.
    Here is the extracted data from {len(data_to_analyze)} studies:
    
    {data_summary}
    
    User question: {question}
    
    RULES:
    - Answer the user's question in natural, conversational language
    - ONLY respond in English, NO OTHER LANGUAGES
    - Speak about "the database" or "this database", not "you" or "your dataset"
    - Include specific counts and statistics when relevant
    - Be concise but thorough
    - Do NOT return JSON or structured data - write a natural response
    
    
    Answer:"""

    answer = call_llm(prompt, temperature=0.3)

    print("-" * 50)
    print(answer)
    return answer
