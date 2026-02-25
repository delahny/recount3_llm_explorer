# page_chat.py
"""
Database Search Assistant - Chat Page
"""

import streamlit as st
import pandas as pd
import ollama 
from src.config import indexed_data, df_csv
from src.intent import detect_intent, check_ambiguity, handle_clarification
from src.search import search_data
from src.analyze import analyze
from src.parser import parse_search_query
from src.query_standardizer import standardize_search
from src.utils import set_llm_model

# Page Setup
st.set_page_config(page_title="Chat | Database Search Assistant", page_icon="💬", layout="wide")
st.header("What do you want to find? 💬")

# Helper function to discover local ollama models
def discover_local_ollama_models():
    """
    Return a sorted list of model identifiers from ollama.list(),
    e.g. ['gemma3:4b', 'gemma3:1b', 'granite4:latest', ...]
    """
    try:
        models = ollama.list()["models"]  # returns a list of Model(...) objects
    except Exception as e:
        # Ollama client not available / Ollama not running
        # Return empty list so UI can show an error and avoid crash
        return []

    names = []
    for m in models:
        # each m has attribute `model` per your printed output
        try:
            names.append(m.model)
        except Exception:
            # defensive: if structure differs, try string conversion and parse
            s = str(m)
            # a safe fallback: try to extract token before first space or comma
            token = s.split()[0].strip(",")
            if token:
                names.append(token)

    # de-duplicate and sort for stable UI behaviour
    return sorted(dict.fromkeys(names))

# LLM settings (kept minimal)
# call once at startup
available_models = discover_local_ollama_models()

# show a helpful sidebar message if empty
if not available_models:
    st.error(
        "No local Ollama models discovered. Make sure Ollama is installed and running, "
        "and that the Python `ollama` package can reach it."
    )
    st.stop()

# model selection as a dropdown in the sidebar
model = st.selectbox("Model (Qwen2.5:7b Recommended)", options=available_models, index=0)
set_llm_model(model)


st.caption(f"Searching through {len(indexed_data)} gene expression studies")

# Chat state
if 'messages' not in st.session_state:
    st.session_state.messages = []
# For user input
if 'pending_input' not in st.session_state:
    st.session_state.pending_input = None
# For ambiguous questions
if 'pending_query' not in st.session_state:
    st.session_state.pending_query = {}
if 'awaiting_clarification' not in st.session_state:
    st.session_state.awaiting_clarification = False
# For download from df display
if 'chat_selector_version' not in st.session_state:
    st.session_state.chat_selector_version = 0

def display_results(results: list):
    """
    Display results to user
    """
    if not results:
        st.warning("No studies found.")
        return

    st.success(f"Found {len(results)} studies")

    df = pd.DataFrame([{
        'Project': s.get('project', ''),
        'Title': s.get('study_title', ''),
        'Organism': s.get('organism', ''),
        'Samples': s.get('n_samples', 0),
        'Diseases': ', '.join(s.get('diseases', [])),
        'Tissue': ', '.join(s.get('tissues', [])),
        'Genes': ', '.join(s.get('genes', [])),
        'Drugs': ', '.join(s.get('drugs', [])),
        'Techniques': ', '.join(s.get('techniques', [])),
    } for s in results])

    st.dataframe(df, width='stretch', height=400, hide_index=True)

# Keywords for analyze function
ANALYZE_KEYWORDS = [
    'most common', 'most commonly', 'most frequent', 'most used',
    'how many', 'count', 'summarize', 'summary', 'top ', 'what drugs',
    'what genes', 'what techniques', 'what diseases', 'what cells'
]

PROJECT_IDS = {s.get('project', '').upper() for s in indexed_data}

def process_input(user_input: str):
    """
    Process user input - handles queries and clarification responses.
    """
    # Handle clarification response
    if st.session_state.awaiting_clarification:
        result = handle_clarification(user_input, st.session_state.pending_query)
        st.session_state.awaiting_clarification = False
        st.session_state.pending_query = {}

        if result and result.get('understood'):
            parsed = {result['category']: result['search_terms']}
            if result.get('other_filters'):
                parsed.update(result['other_filters'])
            parsed = standardize_search(parsed)
            results = search_data(parsed)
            return "results", results, None
        else:
            return "message", "I didn't quite understand. Let's start over.", None

    # Check for project ID first
    user_upper = user_input.upper().strip()
    if user_upper in PROJECT_IDS:
        matches = [s for s in indexed_data if s.get('project', '').upper() == user_upper]
        if matches:
            return "project", matches[0], None
        else:
            return "message", f"Project '{user_input}' not found.", None

    # Detect intent - check keywords before LLM
    query_lower = user_input.lower()
    if any(trigger in query_lower for trigger in ANALYZE_KEYWORDS):
        answer = analyze(user_input)
        return "message", answer, None

    # Fall back to LLM intent detection
    intent = detect_intent(user_input)
    if intent.get('intent') == 'analyze':
        answer = analyze(user_input)
        return "message", answer, None

    # Check for ambiguity
    ambiguity = check_ambiguity(user_input)

    # Ambiguous - ask for clarification
    if ambiguity.get('is_ambiguous') and not ambiguity.get('is_clear'):
        st.session_state.awaiting_clarification = True
        st.session_state.pending_query = {
            'original_query': user_input,
            'ambiguous_term': ambiguity.get('ambiguous_term'),
            'clarifying_question': ambiguity.get('clarifying_question')
        }
        return "clarification", ambiguity.get('clarifying_question'), None

    # Parse and search
    parsed = parse_search_query(user_input)
    if not parsed:
        return "message", "I couldn't understand your search.", None

    # Standardize and merge with original terms
    std_parsed = standardize_search(parsed.copy())

    # Merge original and standardized terms
    for key in ['drugs', 'genes', 'diseases', 'techniques', 'cell_types', 'tissues']:
        original = parsed.get(key) or []
        standardized = std_parsed.get(key) or []
        if isinstance(original, list) and isinstance(standardized, list):
            merged = list(set(original + standardized))
            parsed[key] = merged

    results = search_data(parsed)

    # Build "interpreted terms" from parsed terms
    interpreted_terms = []
    for key in ['drugs', 'genes', 'diseases', 'techniques', 'cell_types', 'tissues']:
        val = parsed.get(key)
        if val and val != 'any' and val != ['any']:
            interpreted_terms.extend(val if isinstance(val, list) else [val])

    input_lower = user_input.lower()
    interpreted = ', '.join(interpreted_terms) if interpreted_terms and not all(
        t.lower() in input_lower for t in interpreted_terms) else None

    return "results", results, interpreted

# Chat container for message history
chat_container = st.container(height=700)

with chat_container:
    # Chat History Display
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            if msg["type"] == "text":
                st.markdown(msg["content"])
            elif msg["type"] == "results":
                display_results(msg["content"])
            elif msg["type"] == "project":
                s = msg["content"]
                st.markdown(f"### {s['project']} | {s['study_title']}")
                # Display abstract from original csv
                row = df_csv[df_csv['project'] == s['project']]
                if not row.empty:
                    abstract = row['study_abstract'].values[0]
                    st.caption(f"ABSTRACT")
                    st.markdown(f"{abstract}")

                st.divider()

                # Add dataframe
                df = pd.DataFrame([{
                    'Project': s.get('project', ''),
                    'Title': s.get('study_title', ''),
                    'Organism': s.get('organism', ''),
                    'Samples': s.get('n_samples', 0),
                    'Diseases': ', '.join(s.get('diseases', [])),
                    'Tissue': ', '.join(s.get('tissues', [])),
                    'Drugs': ', '.join(s.get('drugs', [])),
                    'Genes': ', '.join(s.get('genes', [])),
                    'Techniques': ', '.join(s.get('techniques', [])),
                }])
                st.dataframe(df, width='stretch', hide_index=True)

                # Download button
                if st.button("View & Download in Browse Page →", key=f"browse_{s['project']}_{i}", type="primary"):
                        st.session_state.selected_studies = [s['project']]
                        st.switch_page("pages/page_browse.py")
# Chat Input
if prompt := st.chat_input("Ask me anything..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "type": "text", "content": prompt})
    st.session_state.pending_input = prompt
    st.session_state.last_results = None
    st.rerun()

# Process and respond
if 'pending_input' in st.session_state and st.session_state.pending_input:
    prompt = st.session_state.pending_input
    st.session_state.pending_input = None

    with st.spinner(text="Thinking...", show_time=True):
        response_type, response_content, interpreted = process_input(prompt)

    # Show interpreted (if different from input - for typo handling)
    if interpreted:
        st.session_state.messages.append({
            "role": "assistant",
            "type": "text",
            "content": f"🔍 Searching for: **{interpreted}**"
        })

    if response_type == "message":
        st.session_state.messages.append({"role": "assistant", "type": "text", "content": response_content})

    elif response_type == "clarification":
        st.session_state.messages.append({"role": "assistant", "type": "text", "content": f"❓ {response_content}"})

    elif response_type == "results":
        st.session_state.last_results = response_content
        st.session_state.chat_selector_version += 1
        st.session_state.messages.append({"role": "assistant", "type": "results", "content": response_content})

    elif response_type == "project":
        st.session_state.messages.append({"role": "assistant", "type": "project", "content": response_content})

    st.rerun()

# Download from displayed df
if 'last_results' in st.session_state and st.session_state.last_results:
    results = st.session_state.last_results

    st.divider()
    st.markdown(f"**Select studies to view abstract/download:**")

    df_data = [{
        'Select': s['project'] in st.session_state.get('selected_studies', []),
        'Project': s.get('project', ''),
        'Title': s.get('study_title', ''),
        'Organism': s.get('organism', ''),
        'Samples': s.get('n_samples', 0),
        'Diseases': ', '.join(s.get('diseases', [])),
        'Tissue': ', '.join(s.get('tissues', [])),
        'Genes': ', '.join(s.get('genes', [])),
        'Drugs': ', '.join(s.get('drugs', [])),
        'Techniques': ', '.join(s.get('techniques', [])),
    } for s in results]

    df = pd.DataFrame(df_data)
    edited_df = st.data_editor(
        df,
        column_config={"Select": st.column_config.CheckboxColumn("Select", default=False)},
        disabled=["Project", "Title", "Organism", "Samples", "Diseases", "Tissue", "Genes", "Drugs", "Techniques"],
        hide_index=True,
        height=400,
        key=f"chat_selector_{st.session_state.chat_selector_version}"
    )

    selected = edited_df[edited_df['Select'] == True]['Project'].tolist()
    if selected:
        st.success(f"{len(selected)} studies selected")
        if st.button("View & Download in Browse Page →", type="primary"):
            st.session_state.selected_studies = selected  # only set on button click
            st.switch_page("pages/page_browse.py")