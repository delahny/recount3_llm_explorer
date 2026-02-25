# initial_data_parse.py
"""
Extract keywords from title and study_abstract column and save for fast queries.
Args:
    start_idx: Start from this row index
    end_idx: End at this row index
    chunk: Process this many entries then stop
Usage:
    python initial_data_parse.py -chunk n
"""

import pandas as pd
import json
import ollama
import time
import datetime
import os

# I/O
INPUT_FILE = '../data/full_dataset.csv'
ENCODING = 'utf-8'
OUTPUT_FILE = '../data/parsed_data_final.json'
PROGRESS_FILE = 'parsed_data_progress.json'
MODEL = 'qwen2.5:7b'
BATCH_SIZE = 10  # Save progress every N abstracts


def rowwise_extract(row) -> dict:
    """
    Extract structured information from each row.
    """
    # Load your categorized dictionaries
    from src.abbreviations import CANCER, OTHER_DISEASES, TECHNIQUES, CELLTYPES

    # Format each category for the prompt
    techniques_list = [f"{values[0]} = {values[-1]}" for key, values in TECHNIQUES.items()]
    diseases_list = [f"{values[0]} = {values[-1]}" for key, values in {**CANCER, **OTHER_DISEASES}.items()]
    cells_list = [f"{values[0]} = {values[-1]}" for key, values in CELLTYPES.items()]

    # Build reference text
    reference = f"""
    KNOWN TECHNIQUE ABBREVIATIONS (these are NOT genes - put in "techniques"):
    {chr(10).join(techniques_list)}

    KNOWN DISEASE/CANCER ABBREVIATIONS (put in "diseases"):
    {chr(10).join(diseases_list)}

    KNOWN CELL TYPE ABBREVIATIONS (put in "cell_types"):
    {chr(10).join(cells_list)}
    """

    prompt = f"""
    Extract entities from this gene expression study abstract.

    CATEGORIZATION GUIDE (use these to categorize correctly):
    {reference}
    
    For Drugs and Genes:
    DRUG EXAMPLES:
    - Chemotherapy: Cisplatin, Doxorubicin, Paclitaxel, 5-Fluorouracil
    - Targeted therapy: Vemurafenib, Imatinib, Erlotinib, Trastuzumab
    - Immunotherapy: Pembrolizumab, Nivolumab, Ipilimumab
    - Other: Tamoxifen, Metformin, Dexamethasone
    
    GENE EXAMPLES:
    - Oncogenes: KRAS, BRAF, EGFR, MYC, HER2/ERBB2
    - Tumor suppressors: TP53, BRCA1, BRCA2, RB1, PTEN
    - Immune markers: CD8, CD4, FOXP3, PD1, PDL1
    - Other common: GAPDH, ACTB, IL6, TNF, VEGF
    
    RULES: 
    - ONLY extract entities EXPLICITLY MENTIONED in the title or abstract below
    - The abbreviations above are for categorization only - do NOT extract them unless they appear in the text
    - WES, WGS, RRBS, scRNA-seq, etc. are TECHNIQUES, not genes
    - Gene symbols look like: TP53, BRAF, EGFR, KRAS, MYC, CD8, IL6
    - Database names (CCLE, TCGA, GEO) are neither genes nor techniques - ignore them
    
    Title: {row['study_title']}
    
    Abstract: {row['study_abstract']}

    Return ONLY a JSON object:
    {{
        "drugs": ["drug names mentioned"],
        "genes": ["gene symbols mentioned - NOT techniques"],
        "cell_types": ["cell types mentioned"],
        "diseases": ["diseases/conditions mentioned"],
        "techniques": ["experimental techniques mentioned"],
        "tissues": ["tissues/organs mentioned"]
    }}

    JSON:"""

    try:
        response = ollama.chat(
            model=MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0}
        )

        response_text = response['message']['content'].strip()

        # Parse JSON
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start != -1 and end > start:
            response_text = response_text[start:end]

        extracted = json.loads(response_text)

    except Exception as e:
        print(f"  Error: {e}")
        extracted = {
            'drugs': [],
            'genes': [],
            'cell_types': [],
            'diseases': [],
            'techniques': [],
            'tissues': [],
            'error': str(e)
        }

    # Add original metadata
    extracted['project'] = row['project']
    extracted['organism'] = row['organism']
    extracted['n_samples'] = row['n_samples']
    extracted['study_title'] = row['study_title']

    return extracted


# Indexing function
def index_abstracts(start_idx: int = None, end_idx: int = None, chunk: int = None):
    """
    Process abstracts and save extracted data.
    """

    # Load data
    print(f"Loading {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE, encoding= ENCODING)
    total_rows = len(df)
    print(f"Total entries: {total_rows}\n")

    # Load existing progress
    all_extracted = []
    processed_ids = set()

    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            all_extracted = json.load(f)
            processed_ids = {item['project'] for item in all_extracted}
        print(f"Already processed: {len(all_extracted)}")

    # Determine range to process
    if start_idx is not None and end_idx is not None:
        # Specific range
        df_to_process = df.iloc[start_idx:end_idx]
        print(f"Processing range: {start_idx} to {end_idx}")
    elif chunk is not None:
        # Next N unprocessed entries
        unprocessed = df[~df['project'].isin(processed_ids)]
        df_to_process = unprocessed.head(chunk)
        print(f"Processing next {len(df_to_process)} unprocessed entries")
    else:
        # All remaining
        df_to_process = df[~df['project'].isin(processed_ids)]
        print(f"Processing all {len(df_to_process)} remaining entries")

    remaining = len(df_to_process)

    if remaining == 0:
        print("\nAll entries processed!")
        # Save final file
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(all_extracted, f, indent=2, ensure_ascii=False)
        print(f"Saved to {OUTPUT_FILE}")
        return all_extracted

    # Time estimate
    est_seconds = remaining * 7 # estimating 7 seconds per abstract
    est_minutes = est_seconds / 60
    est_hours = est_minutes / 60
    current_datetime = datetime.datetime.now()

    print(f"\nTo process: {remaining} entries")
    print(f"Estimated time: {est_minutes:.0f} min ({est_hours:.1f} hours)")
    print(f"Run start: {current_datetime})")
    print("\nStarting... (Ctrl+C to pause and save)\n")

    start_time = time.time()
    processed_this_run = 0

    try:
        for idx, row in df_to_process.iterrows():
            # Skip if already done
            if row['project'] in processed_ids:
                continue

            # Progress display
            progress = len(all_extracted) + 1
            print(f"[{progress}/{total_rows}] {row['project']}: {str(row.get('study_title', ''))[:50]}...")

            # Extract
            extracted = rowwise_extract(row)
            all_extracted.append(extracted)
            processed_ids.add(row['project'])
            processed_this_run += 1

            # Save progress
            if processed_this_run % BATCH_SIZE == 0:
                with open(PROGRESS_FILE, 'w') as f:
                    json.dump(all_extracted, f, ensure_ascii=False)

                elapsed = time.time() - start_time
                rate = processed_this_run / elapsed if elapsed > 0 else 0
                remaining_count = remaining - processed_this_run
                eta = remaining_count / rate if rate > 0 else 0

                print(f"  → Saved. ETA: {eta / 60:.0f} min\n")

                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nPaused! Saving progress...")
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(all_extracted, f, ensure_ascii=False)
        print(f"Progress saved: {len(all_extracted)} total ({processed_this_run} this run)")
        print("Run again to resume.")
        return all_extracted

    # Save final
    print("\nChunk complete! Saving...")

    with open(PROGRESS_FILE, 'w') as f:
        json.dump(all_extracted, f, ensure_ascii=False)

    # If all complete, save to final file
    if len(all_extracted) >= total_rows:
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(all_extracted, f, indent=2, ensure_ascii=False)
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
        print(f"All done! Saved to {OUTPUT_FILE}")
    else:
        print(f"Progress saved: {len(all_extracted)}/{total_rows}")
        print(f"Run again to continue.")

    elapsed = time.time() - start_time
    print(f"\nProcessed: {processed_this_run} entries in {elapsed / 60:.1f} min")
    print(f"Ended at: {current_datetime})")

    return all_extracted

def show_summary():
    """
    Show progress summary of extracted data.
    """
    if not os.path.exists(OUTPUT_FILE):
        print(f"{OUTPUT_FILE} not found. Run indexing first.")
        return

    with open(OUTPUT_FILE, 'r') as f:
        data = json.load(f)

    print(f"\n{'-' * 50}")
    print(f"EXTRACTION SUMMARY")
    print(f"{'-' * 50}")
    print(f"Total studies indexed: {len(data)}")

    # Count totals
    from collections import Counter

    all_drugs = Counter()
    all_genes = Counter()
    all_cells = Counter()
    all_diseases = Counter()
    all_techniques = Counter()

    for study in data:
        for drug in study.get('drugs', []):
            all_drugs[drug.lower()] += 1
        for gene in study.get('genes', []):
            all_genes[gene.upper()] += 1
        for cell in study.get('cell_types', []):
            all_cells[cell.lower()] += 1
        for disease in study.get('diseases', []):
            all_diseases[disease.lower()] += 1
        for tech in study.get('techniques', []):
            all_techniques[tech.lower()] += 1

    print(f"\nUnique entities found:")
    print(f"Drugs: {len(all_drugs)}")
    print(f"Genes: {len(all_genes)}")
    print(f"Cell types: {len(all_cells)}")
    print(f"Diseases: {len(all_diseases)}")
    print(f"Techniques: {len(all_techniques)}")

    print(f"\nTop 10 drugs:")
    for drug, count in all_drugs.most_common(10):
        print(f"{drug}: {count}")

    print(f"\nTop 10 genes:")
    for gene, count in all_genes.most_common(10):
        print(f"{gene}: {count}")

    print(f"\nTop 10 diseases:")
    for disease, count in all_diseases.most_common(10):
        print(f"{disease}: {count}")


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-chunk", type=int, help="Process only N entries")
    parser.add_argument("-start", type=int, help="Start index")
    parser.add_argument("-end", type=int, help="End index")
    parser.add_argument("mode", nargs="?", default="run")

    args = parser.parse_args()

    if len(sys.argv) > 1 and sys.argv[1] == 'summary':
        show_summary()
    else:
        index_abstracts(
            start_idx=args.start,
            end_idx=args.end,
            chunk=args.chunk
        )