# recount3_llm_explorer
**A Streamlit web application for searching and analyzing gene expression studies**
This app uses datasets from the [recount3 database](https://rna.recount.bio/)

## Features
- **Chat Interface** — Ask questions in plain English to search or analyze studies
- **Browse Page** — Filter, explore, and export studies interactively
- **LLM-powered search** — Intent detection, ambiguity resolution, and term standardization
- **Raw data download** — Fetch raw gene expression files and metadata directly from recount3
- **Abstract viewer** — Read full study abstracts in-app

## Pages

### 💬 Chat
Natural language interface with two query modes:

- **Search** — Find studies matching diseases, drugs, genes, techniques, tissues, organisms, or sample size  
  _e.g. "breast cancer studies using trastuzumab"_
- **Analyze** — Get statistics and summaries about the database  
  _e.g. "what are the most commonly used drugs for breast cancer?"_

Handles abbreviations (NSCLC, CRC, TNBC), ambiguous terms (BRCA, HER2), and auto-corrects typos.

### 🖥 Browse
Table view of all studies with filters for organism, minimum samples, and keyword search. Select studies to:
- View abstracts
- Export metadata as CSV
- Download raw files or URLs from recount3

## Setup

### Requirements

```
streamlit
pandas
ollama
requests
```
**Note** You will also need Ollama running with at least one local model installed. 
You will be able to choose from your local models.

**Install dependencies:**
```bash
pip install -r requirements.txt
```

## Running the App

```bash
streamlit run app.py
```
