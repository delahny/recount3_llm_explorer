# data_mapping.py
"""
Standardize entities in parsed_data.json using LLM.
"""

import json
import ollama
from collections import Counter

# Configuration
MODEL = 'qwen2.5:7b'
INPUT_FILE = '../data/parsed_data_final.json'
ENCODING = 'utf-8'
OUTPUT_FILE = '../data/mapped_parsed_data_final.json'

# Key mappings for LLM reference
KEY_MAPPINGS = """
    DRUG STANDARDS:
    - Capitalize properly: "cisplatin" = "Cisplatin"
    - If brand names are used, convert to generic names: "Keytruda" = "Pembrolizumab"
    - Standardize variations: "5-FU", "5FU" = "5-Fluorouracil"
    - Drugs include: Herceptin, Keytruda, tamoxifen, pembrolizumab, trastuzumab, etc. (include chemotherapy agents, 
    small molecules, antibodies, inhibitors)
    
    GENE STANDARDS:
    - Human genes uppercase: TP53, KRAS, EGFR, BRCA1
    - Mouse genes capitalize first letter: "Braf", "Kras"
    - WES, WGS, RRBS, scRNA-seq, RNA-seq are TECHNIQUES, not genes
    
    DISEASE STANDARDS:
    - lung adenocarcinoma, NSCLC, non-small cell lung cancer = "lung cancer"
    - HCC, hepatocellular carcinoma = "liver cancer"
    - gastric cancer, stomach cancer = "gastric cancer"
    - renal cell carcinoma, RCC = "kidney cancer"
    - TNBC = "triple-negative breast cancer" (keep separate)
    - uveal melanoma = "uveal melanoma" (keep separate)
    - acral melanoma = "acral melanoma" (keep separate)
    - AML, acute myeloid leukemia = "AML"
    - GBM, glioblastoma multiforme = "glioblastoma"
    - PDAC, pancreatic ductal adenocarcinoma = "pancreatic cancer"
    
    TECHNIQUE STANDARDS:
    - single-cell RNA-seq, scRNAseq, single cell RNA sequencing = "scRNA-seq"
    - RNA-Seq, RNA sequencing, RNAseq, RNA-sequencing = "RNA-seq"
    - spatial transcriptomics, ST, 10X Genomics, Xenium, Visium, NanoString, GeoMx = "spatial transcriptomics"
    - single-nucleus RNA-seq, snRNAseq = "snRNA-seq"
    - whole exome sequencing = "WES"
    - whole genome sequencing = "WGS"
    - ATAC sequencing, ATACseq = "ATAC-seq"
    - single-cell ATAC-seq = "scATAC-seq"
    - ChIP sequencing = "ChIP-seq"
    - whole genome bisulfite sequencing = "WGBS"
    
    CELL TYPE STANDARDS:
    - T-cells, T lymphocytes = "T cells"
    - regulatory T cells, Treg = "Tregs"
    - tumor-associated macrophages, TAM = "TAMs"
    - tumor-infiltrating lymphocytes, TIL = "TILs"
    - cancer-associated fibroblasts, CAF = "CAFs"
    - myeloid-derived suppressor cells, MDSC = "MDSCs"
    - natural killer cells, NK cell = "NK cells"
    - peripheral blood mononuclear cells, PBMC = "PBMCs"
    
    TISSUE STANDARDS:
    - tumour, tumor tissue = "tumor"
    - peripheral blood, whole blood = "blood"
    - metastatic tumor, metastasis = "metastasis"
"""

def get_unique_values(data: list, category: str) -> Counter:
    """Get unique values and counts from each category."""
    values = Counter()
    for study in data:
        for item in study.get(category, []):
            values[item] += 1
    return values

def create_mapping(category: str, values: Counter) -> dict:
    """
    Use LLM to create standardization mapping in batches.
    """
    all_mappings = {}
    items = list(values.most_common())
    batch_size = 100

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        value_list = [f'"{val}" ({count})' for val, count in batch]

        print(f"Processing batch {i // batch_size + 1} ({len(batch)} terms)...")

        prompt = f"""
        Create a standardization mapping for these {category}.
    
        STANDARDIZATION RULES TO FOLLOW:
        {KEY_MAPPINGS}
        
        For terms NOT in the rules above, use your knowledge to standardize them similarly.
        
        Here are the {category} to standardize (with counts):
        {chr(10).join(value_list)}
        
        Return ONLY a JSON object mapping each ORIGINAL term (exactly as shown, without the count) to its STANDARDIZED form.
        If a term is already standard, map it to itself.
        
        Example format:
        {{"lung adenocarcinoma": "lung cancer", "breast cancer": "breast cancer", "HCC": "liver cancer"}}
        
        JSON:"""

        try:
            response = ollama.chat(
                model=MODEL,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0}
            )

            response_text = response['message']['content'].strip()

            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > start:
                response_text = response_text[start:end]

            batch_mapping = json.loads(response_text)
            all_mappings.update(batch_mapping)

        except Exception as e:
            print(f"    Error in batch: {e}")

    return all_mappings


def apply_mapping(data: list, category: str, mapping: dict) -> list:
    """Apply standardization mapping to all studies."""

    for study in data:
        if study.get(category):
            standardized = set()
            for item in study[category]:
                # Try exact match first, then lowercase
                std = mapping.get(item) or mapping.get(item.lower()) or item
                standardized.add(std)
            study[category] = list(standardized)

    return data


def main():
    # Load data
    print(f"Loading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding=ENCODING) as f:
        data = json.load(f)
    print(f"Loaded {len(data)} studies\n")

    # Categories to standardize
    categories = ['diseases', 'drugs', 'techniques', 'cell_types', 'tissues', 'genes']

    all_mappings = {}

    for category in categories:
        print(f"\n{'-'*50}")
        print(f"Processing: {category}")

        # Get unique values
        values = get_unique_values(data, category)
        print(f"Found {len(values)} unique values")

        if len(values) == 0:
            print("  Skipping (no values)")
            continue

        # Show top 10 before
        print(f"\nTop 10 before standardization:")
        for val, count in values.most_common(10):
            print(f"  {val}: {count}")

        # Create mapping with LLM
        print(f"\nCreating standardization mapping with LLM...")
        mapping = create_mapping(category, values)
        all_mappings[category] = mapping
        print(f"Created mapping for {len(mapping)} terms")

        # Apply mapping
        print(f"Applying mapping...")
        data = apply_mapping(data, category, mapping)

        # Show top 10 after
        new_values = get_unique_values(data, category)
        print(f"\nTop 10 after standardization:")
        for val, count in new_values.most_common(10):
            print(f"  {val}: {count}")

        print(f"\nReduced: {len(values)} = {len(new_values)} unique values")

    # Save mappings for reference/editing
    print(f"\n{'-'*50}")
    print("Saving files...")
    print(f"{'-'*50}")

    with open('../data/standardization_mappings_final.json', 'w', encoding=ENCODING) as f:
        json.dump(all_mappings, f, indent=2, ensure_ascii=False)
    print(f"Saved mappings to: standardization_mappings_final.json")

    # Save standardized data
    with open(OUTPUT_FILE, 'w', encoding=ENCODING) as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved standardized data to: {OUTPUT_FILE}")

    # Final summary
    print(f"\n{'-'*50}")
    print("SUMMARY")
    print(f"{'-'*50}")

    with open(INPUT_FILE, 'r', encoding=ENCODING) as f:
        original_data = json.load(f)
    for category in categories:
        before = len(get_unique_values(original_data, category))
        after = len(get_unique_values(data, category))
        print(f"  {category}: {before} = {after} (-{before - after})")

    print(f"\nDone! Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()