# search.py
"""
Function for search queries.
"""

from src.config import indexed_data

def search_data(parsed: dict) -> list:
    """Search indexed data using parsed query."""
    results = indexed_data.copy()

    for key in ['drugs', 'genes', 'diseases', 'cell_types', 'techniques', 'tissues']:
        if parsed.get(key) == ['any']:
            parsed[key] = 'any'

    if parsed.get('organism'):
        results = [s for s in results if s.get('organism', '').lower() == parsed['organism'].lower()]

    if parsed.get('min_samples'):
        results = [s for s in results if s.get('n_samples', 0) >= parsed['min_samples']]

    if parsed.get('max_samples'):
        results = [s for s in results if s.get('n_samples', 0) <= parsed['max_samples']]

    if parsed.get('drugs'):
        if parsed['drugs'] == 'any':
            results = [s for s in results if s.get('drugs')]
        else:
            results = [s for s in results
                       if any(drug.lower() in ' '.join(s.get('drugs', [])).lower()
                              for drug in parsed['drugs'])]

    if parsed.get('genes'):
        if parsed['genes'] == 'any':
            results = [s for s in results if s.get('genes')]
        else:
            results = [s for s in results
                       if any(gene.upper() in ' '.join(s.get('genes', [])).upper()
                              for gene in parsed['genes'])]

    if parsed.get('diseases'):
        if parsed['diseases'] == 'any':
            results = [s for s in results if s.get('diseases')]
        else:
            results = [s for s in results
                       if any(disease.lower() in ' '.join(s.get('diseases', [])).lower()
                              for disease in parsed['diseases'])]

    if parsed.get('cell_types'):
        if parsed['cell_types'] == 'any':
            results = [s for s in results if s.get('cell_types')]
        else:
            results = [s for s in results
                       if any(cell.lower() in ' '.join(s.get('cell_types', [])).lower()
                              for cell in parsed['cell_types'])]

    if parsed.get('techniques'):
        if parsed['techniques'] == 'any':
            results = [s for s in results if s.get('techniques')]
        else:
            results = [s for s in results
                       if any(tech.lower() in ' '.join(s.get('techniques', [])).lower()
                              for tech in parsed['techniques'])]

    if parsed.get('tissues'):
        if parsed['tissues'] == 'any':
            results = [s for s in results if s.get('tissues')]
        else:
            results = [s for s in results
                       if any(tissue.lower() in ' '.join(s.get('tissues', [])).lower()
                              for tissue in parsed['tissues'])]

    return results