# page_browse.py
"""
Database Search Assistant - Browse Page
"""

import streamlit as st
import pandas as pd
import datetime
from src.config import indexed_data, url_df, df_csv

# Page Setup
st.set_page_config(page_title="Browse | Database Search Assistant", page_icon="🖥", layout="wide")
current_time = datetime.datetime.now()
st.header("All Studies 📑")

# Initialize selected studies in session state
if 'selected_studies' not in st.session_state:
    st.session_state.selected_studies = []
if 'selector_version' not in st.session_state:
    st.session_state.selector_version = 0

# Filters
col1, col2, col3 = st.columns(3)

with col1:
    organism_filter = st.selectbox("Organism", ["All", "human", "mouse"], key="organism_filter")
with col2:
    min_samples = st.number_input("Min Samples", min_value=0, key="min_samples", step=100)
with col3:
    search_text = st.text_input("Search (project/title/disease/gene/drugs)", key="search_text", help= " Use commas to separate terms")

# Filter data
filtered_data = indexed_data.copy()

if organism_filter != "All":
    filtered_data = [s for s in filtered_data if s.get('organism', '').lower() == organism_filter.lower()]
if min_samples > 0:
    filtered_data = [s for s in filtered_data if s.get('n_samples', 0) >= min_samples]
if search_text:
    search_terms = [t.strip() for t in search_text.split(',')]
    # If all terms look like project IDs, return exact matches
    project_prefixes = ('SRP', 'GSE', 'PRJNA', 'ERP', 'DRP')
    if all(t.upper().startswith(project_prefixes) for t in search_terms):
        search_upper = [t.upper() for t in search_terms]
        filtered_data = [s for s in filtered_data if s.get('project', '').upper() in search_upper]
    else:
        filtered_data = [s for s in filtered_data if
                         all(t.lower() in s.get('study_title', '').lower() or
                             t.upper() in s.get('project', '').upper() or
                             t.lower() in ' '.join(s.get('diseases', [])).lower() or
                             t.lower() in ' '.join(s.get('tissues', [])).lower() or
                             t.lower() in ' '.join(s.get('drugs', [])).lower() or
                             t.lower() in ' '.join(s.get('genes', [])).lower() or
                             t.lower() in ' '.join(s.get('techniques', [])).lower()
                             for t in search_terms)]

st.markdown(f"**Showing {len(filtered_data)} studies**")

# Function to clear all filters
def clear_all_selection():
    st.session_state.selected_studies = []
    st.session_state.selector_version += 1
    # Delete internal state
    if "study_selector" in st.session_state:
        del st.session_state["study_selector"]

# Function to clear all filters
def clear_all_filters():
    st.session_state.organism_filter = "All"
    st.session_state.min_samples = 0
    st.session_state.search_text = ""

# Selection/Clear Buttons
col_select1, col_select2, col_select3 = st.columns([1,6,0.5], gap="medium")

with col_select1:
    if st.button("Select All"):
        st.session_state.selected_studies = [s['project'] for s in filtered_data]

with col_select2:
    if st.button("Clear Selection", on_click = clear_all_selection):
        pass

with col_select3:
    if st.button("Clear All Filters", on_click = clear_all_filters):
        pass

# Df with selection
df_data = []
for s in filtered_data:
    df_data.append({
        'Select': s['project'] in st.session_state.selected_studies,
        'Project': s.get('project', ''),
        'Title': s.get('study_title', ''),
        'Organism': s.get('organism', ''),
        'Samples': s.get('n_samples', 0),
        'Diseases': ', '.join(s.get('diseases', [])),
        'Tissue': ', '.join(s.get('tissues', [])),
        'Drugs': ', '.join(s.get('drugs', [])),
        'Genes': ', '.join(s.get('genes', [])),
        'Techniques': ', '.join(s.get('techniques', [])),
    })

df = pd.DataFrame(df_data)

edited_df = st.data_editor(
    df,
    column_config={
        "Select": st.column_config.CheckboxColumn(
            "Select",
            help="Select studies to download",
            default=False,
        ),
        "Project": st.column_config.TextColumn("Project", width="small"),
        "Title": st.column_config.TextColumn("Title", width="large"),
    },
    disabled=["Project", "Title", "Organism", "Samples", "Diseases", "Tissue", "Drugs", "Genes", "Techniques"],
    hide_index=True,
    width='stretch',
    height=500,
    key=f"study_selector_{st.session_state.selector_version}"
)

# Update selected studies to session state
if not df.empty and 'Select' in df.columns:
    selected_studies = edited_df[edited_df['Select'] == True]['Project'].tolist()
else:
    selected_studies = []


# Study Selection and Download
st.divider()

num_selected = len(selected_studies)
st.subheader(f":green-background[***Selected: {num_selected} studies***]")

# Function to get abstracts as pop up
@st.dialog("Abstracts 📄", width="large")
def show_abstracts_popup(selected_studies):
    for project in selected_studies:
        row = df_csv[df_csv['project'] == project]
        if not row.empty:
            title = row['study_title'].values[0] if 'study_title' in row.columns else proj
            abstract = row['study_abstract'].values[0]
            with st.expander(f"**{project}** | {title}"):
                st.markdown(abstract)

# For selected studies
if num_selected > 0:
    st.write(", ".join(selected_studies))

    # Warning for large selections
    if num_selected > 10:
        st.warning(f"⚠️ You selected {num_selected} studies. Download may take a while and produce a large file.")

    # View Abstracts after selection
    if st.button("View Abstracts 📄", type="secondary"):
        show_abstracts_popup(selected_studies)

    # Export selected studies as CSV
    if selected_studies:
        export_df = df[df['Project'].isin(selected_studies)].drop(columns=['Select'])
        csv = export_df.to_csv(index=False)
        st.download_button(
            label=f"Export selected studies as CSV 📥 ",
            data=csv,
            file_name=f"studyinfo_{current_time}.csv",
            mime="text/csv"
        )
    else:
        st.info("Select studies to export as CSV")

    # Prepare ZIP file for download
    if st.button("Get Raw Files and Metadata 🧬", type="secondary"):

        import zipfile
        import requests
        from io import BytesIO

        # Get URLs and raw files
        if url_df is None:
            st.error("recount3_raw_and_metadata_url.csv not found.")
            st.stop()

        url_columns = [
            'raw_gene', 'raw_exon', 'raw_jxn_MM', 'raw_jxn_RR', 'raw_jxn_ID',
            'project_meta', 'recount_project', 'recount_qc', 'recount_seq_qc', 'recount_pred'
        ]

        # Create zips in memory
        raw_zip_buffer = BytesIO()
        urls_zip_buffer = BytesIO()

        progress_bar = st.progress(0)
        status_text = st.empty()

        st.session_state.selected_studies = selected_studies
        total = len(st.session_state.selected_studies)
        failed_downloads = []

        with zipfile.ZipFile(raw_zip_buffer, 'w', zipfile.ZIP_DEFLATED) as raw_zip, \
             zipfile.ZipFile(urls_zip_buffer, 'w', zipfile.ZIP_DEFLATED) as urls_zip:

            for i, project_id in enumerate(st.session_state.selected_studies):
                status_text.text(f"Fetching {project_id}... ({i + 1}/{total})")
                progress_bar.progress((i + 1) / total)

                # Get URLs for this project
                row = url_df[url_df['project'] == project_id]
                if row.empty:
                    failed_downloads.append(project_id)
                    continue

                # Get study title for URL txt filename
                study_match = [s for s in indexed_data if s.get('project') == project_id]
                if study_match:
                    project_name = study_match[0].get('project', project_id)
                    safe_title = "".join(c for c in project_name if c.isalnum() or c in (' ', '-', '_'))[:50]
                    txt_filename = f"{safe_title}.txt"
                else:
                    txt_filename = f"{project_id}.txt"

                # Collect URLs for txt file
                url_lines = [f"# {project_id}"]

                # Download each URL
                for col in url_columns:
                    if col not in row.columns:
                        continue

                    url = row[col].values[0]
                    if pd.isna(url) or not str(url).startswith('http'):
                        continue

                    # Add to URL list
                    url_lines.append(url)

                    try:
                        response = requests.get(url, timeout=60)
                        response.raise_for_status()
                        filename = url.split('/')[-1] if '/' in url else f"{col}.txt"
                        zip_path = f"{project_id}/{filename}"
                        raw_zip.writestr(zip_path, response.content)

                    except Exception as e:
                        print(f"Failed to download {col} for {project_id}: {e}")

                # Write URL txt file
                urls_zip.writestr(txt_filename, "\n".join(url_lines))

        progress_bar.empty()
        status_text.empty()

        raw_zip_buffer.seek(0)
        urls_zip_buffer.seek(0)

        successful = total - len(failed_downloads)

        if successful > 0:
            st.success(f"{successful} datasets ready for download ⬇️")

            col1, col2 = st.columns([1, 8])

            with col1:
                st.download_button(
                    label="Download Raw Files \n(local) 🗂️",
                    data=raw_zip_buffer.getvalue(),
                    file_name=f"raw_{current_time}.zip",
                    mime="application/zip",
                    type="primary",
                    on_click="ignore"
                )
            with col2:
                st.download_button(
                    label="Download URLs as TXT 🔗",
                    data=urls_zip_buffer.getvalue(),
                    file_name=f"urls_{current_time}.zip",
                    mime="application/zip",
                    on_click = "ignore"
                )

        if failed_downloads:
            st.warning(f"⚠️ Could not find data for {len(failed_downloads)} studies")
            with st.expander("Show failed"):
                for proj in failed_downloads:
                    st.write(f"• {proj}")

else:
    st.info("Select studies to view abstracts or enable download.")