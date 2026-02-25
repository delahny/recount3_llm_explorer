# app.py
"""
Database Search Assistant Main App
"""

import streamlit as st
from src.config import indexed_data

st.title("Database Search Assistant 🔬")
chat_page = st.Page("pages/page_chat.py", title="Chat", icon="💬")
browse_page = st.Page("pages/page_browse.py", title="Browse Database", icon="🖥")
pg = st.navigation([chat_page, browse_page])
pg.run()

# Sidebar
with st.sidebar:

    st.header("Database Stats 📊")
    total = len(indexed_data)
    human_count = sum(1 for s in indexed_data if s.get('organism', '').lower() == 'human')
    mouse_count = sum(1 for s in indexed_data if s.get('organism', '').lower() == 'mouse')
    col1, col2, col3 = st.columns(3)
    col1.metric("Human", human_count)
    col2.metric("Mouse", mouse_count)
    col3.metric("Total", total)
    st.divider()

    st.header("Examples 🔎")
    st.markdown("""
    **Search:**
    - breast cancer studies using trastuzumab
    - show me human melanoma studies
    - SRP123456

    **Analyze:**
    - what are the most commonly used drugs for breast cancer treatment?
    - summarize the techniques in this database
    - how many studies mention CRC?
    """)

    if st.button("Clear Chat 🗑️"):
        st.session_state.messages.clear()
        st.session_state.awaiting_clarification = False
        st.session_state.pending_query = {}
        st.rerun()