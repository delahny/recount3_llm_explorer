# config.py
"""
Configuration settings and data loading.
"""

import json
import pandas as pd
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL = 'qwen2.5:7b'
INDEXED_FILE = os.path.join(BASE_DIR, 'data', 'mapped_parsed_data_final.json')
ORIGINAL_CSV = os.path.join(BASE_DIR, 'data', 'full_dataset.csv')
MAPPINGS_FILE = os.path.join(BASE_DIR, 'data', 'standardization_mappings_final.json')
DATA_URL_FILE = os.path.join(BASE_DIR, 'data', 'recount3_raw_and_metadata_url.csv')
ENCODING = 'utf-8'

def load_data():
    with open(INDEXED_FILE, 'r', encoding=ENCODING) as f:
        data = json.load(f)

    # Only keep studies if study_title is a non-empty string
    return [s for s in data if isinstance(s.get('study_title'), str) and s['study_title'].strip()]

# Load mapped json
indexed_data = load_data()

# Load csv
df_csv = pd.read_csv(ORIGINAL_CSV, encoding= ENCODING)

# Load mappings json
try:
    with open(MAPPINGS_FILE, 'r', encoding=ENCODING) as f:
        MAPPINGS = json.load(f)
    print(f"Loaded standardization mappings")
except FileNotFoundError:
    MAPPINGS = {}
    print("No standardization mappings found - using LLM only")

# Load URL data
try:
    url_df = pd.read_csv(DATA_URL_FILE)
except FileNotFoundError:
    url_df = None
    print("Warning: recount3_raw_and_metadata_url.csv not found.")
