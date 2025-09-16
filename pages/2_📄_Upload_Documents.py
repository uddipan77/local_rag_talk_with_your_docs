import logging
import os
import time
 
import streamlit as st
from PyPDF2 import PdfReader
 
from src.constants import OPENSEARCH_INDEX, TEXT_CHUNK_SIZE
from src.embeddings import generate_embeddings, get_embedding_model
from src.ingestion import (
    bulk_index_documents,
    create_index,
    delete_documents_by_document_name,
)
from src.opensearch import get_opensearch_client
from src.utils import chunk_text, setup_logging
 
# Initialize logger
setup_logging()  # Set up centralized logging configuration
logger = logging.getLogger(__name__)
 
# Set page config with title, icon, and layout
st.set_page_config(page_title="Jam with AI - Upload Documents", page_icon="📂", layout="centered")
 
# ===== Custom CSS (robust selectors; no external config) =====
st.markdown(
    """
    <style>
    /* -------- App & Header -------- */
    [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;   /* main background white */
        color: #002B5B !important;
    }
    [data-testid="stHeader"] {
        background: transparent !important;
    }
 
    /* -------- Main card -------- */
    .block-container {
        background-color: #ffffff !important;
        border-radius: 10px !important;
        padding: 20px !important;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.10) !important;
    }
 
    /* Ensure readable text in main content (remove dark-theme fade) */
    .block-container,
    .block-container [data-testid="stMarkdownContainer"],
    .block-container p,
    .block-container li,
    .block-container span,
    .block-container small,
    .block-container label,
    .block-container strong,
    .block-container em {
        color: #002B5B !important;
        opacity: 1 !important;
        text-shadow: none !important;
    }
    .block-container h1,
    .block-container h2,
    .block-container h3,
    .block-container h4 {
        color: #006d77 !important;
        opacity: 1 !important;
    }
    .block-container a { color: #118ab2 !important; }
 
    /* Expander header + content text colors */
    [data-testid="stExpander"] * {
        color: inherit !important;
        opacity: 1 !important;
    }
 
    /* -------- Sidebar -------- */
    [data-testid="stSidebar"] {
        background-color: #006d77 !important;
        border-right: 2px solid #003d5c !important;
    }
    .stSidebarContent {
        color: #ffffff !important;
        padding: 20px !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] li,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span {
        color: #ffffff !important;
        opacity: 1 !important;
    }
 
    /* Sidebar widgets on dark bg */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] .stSlider,
    [data-testid="stSidebar"] .stNumberInput input {
        background-color: rgba(255,255,255,0.12) !important;
        color: #ffffff !important;
    }
 
    /* -------- Buttons (avoid dark "pills") -------- */
    .stButton > button,
    button[kind="secondary"],
    button[kind="primary"],
    [data-testid="baseButton-secondary"],
    [data-testid="baseButton-primary"] {
        background-color: #118ab2 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px 14px !important;
        font-size: 14px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
        cursor: pointer;
    }
    .stButton > button:hover,
    button[kind="secondary"]:hover,
    button[kind="primary"]:hover,
    [data-testid="baseButton-secondary"]:hover,
    [data-testid="baseButton-primary"]:hover {
        background-color: #07a6c2 !important;
        color: #ffffff !important;
    }
 
    /* -------- Alerts (success/info/warning/error) text readability -------- */
    .stAlert,
    [data-testid="stNotification"] {
        opacity: 1 !important;
    }
    .stAlert p, .stAlert span, .stAlert div,
    [data-testid="stNotification"] p,
    [data-testid="stNotification"] span,
    [data-testid="stNotification"] div {
        color: #1f3b4d !important; /* dark readable text on green/info backgrounds */
        opacity: 1 !important;
    }
 
    /* -------- File uploader (fix dark dropzone) -------- */
    [data-testid="stFileUploader"] * {
        color: #002B5B !important;
        opacity: 1 !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        background-color: #ffffff !important;
        border: 1px dashed #cbd5e1 !important;   /* soft gray */
        color: #002B5B !important;
    }
    [data-testid="stFileUploaderDropzone"] * {
        color: #002B5B !important;
        opacity: 1 !important;
    }
 
    /* Footer text */
    .footer-text {
        font-size: 1.1rem;
        font-weight: bold;
        color: #000000 !important;
        text-align: center;
        margin-top: 10px;
        opacity: 1 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
 
# # Add a logo (replace with your own image file path or URL)
# logo_path = "images/jamwithai_logo.png"  # Replace with your logo file
# if os.path.exists(logo_path):
#     st.sidebar.image(logo_path, width=220)
# else:
#     st.sidebar.markdown("### Logo Placeholder")
#     logger.warning("Logo not found, displaying placeholder.")
 
st.sidebar.markdown(
    "<h4 style='text-align: center;'>Your Document Assistant</h4>",
    unsafe_allow_html=True,
)
 
def render_upload_page() -> None:
    """
    Renders the document upload page for users to upload and manage PDFs.
    Shows only the documents that are present in the OpenSearch index.
    """
 
    st.title("Upload Documents")
    # Placeholder for the loading spinner at the top
    model_loading_placeholder = st.empty()
 
    # Display the loading spinner at the top for loading the embedding model
    if "embedding_models_loaded" not in st.session_state:
        with model_loading_placeholder:
            with st.spinner("Loading models for document processing..."):
                get_embedding_model()
                st.session_state["embedding_models_loaded"] = True
        logger.info("Embedding models loaded.")
        model_loading_placeholder.empty()  # Clear the placeholder after loading
 
    UPLOAD_DIR = "uploaded_files"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
 
    # Initialize OpenSearch client
    with st.spinner("Connecting to OpenSearch..."):
        client = get_opensearch_client()
    index_name = OPENSEARCH_INDEX
 
    # Ensure the index exists
    create_index(client)
 
    # Initialize or clear the documents list in session state
    st.session_state["documents"] = []
 
    # Query OpenSearch to get the list of unique document names
    query = {
        "size": 0,
        "aggs": {"unique_docs": {"terms": {"field": "document_name", "size": 10000}}},
    }
    response = client.search(index=index_name, body=query)
    buckets = response["aggregations"]["unique_docs"]["buckets"]
    document_names = [bucket["key"] for bucket in buckets]
    logger.info("Retrieved document names from OpenSearch.")
 
    # Load document information from the index
    for document_name in document_names:
        file_path = os.path.join(UPLOAD_DIR, document_name)
        if os.path.exists(file_path):
            reader = PdfReader(file_path)
            text = "".join([page.extract_text() for page in reader.pages])
            st.session_state["documents"].append(
                {"filename": document_name, "content": text, "file_path": file_path}
            )
        else:
            st.session_state["documents"].append(
                {"filename": document_name, "content": "", "file_path": None}
            )
            logger.warning(f"File '{document_name}' does not exist locally.")
 
    if "deleted_file" in st.session_state:
        st.success(
            f"The file '{st.session_state['deleted_file']}' was successfully deleted."
        )
        del st.session_state["deleted_file"]
 
    # Allow users to upload PDF files
    uploaded_files = st.file_uploader(
        "Upload PDF documents", type="pdf", accept_multiple_files=True
    )
 
    if uploaded_files:
        with st.spinner("Uploading and processing documents. Please wait..."):
            for uploaded_file in uploaded_files:
                if uploaded_file.name in document_names:
                    st.warning(
                        f"The file '{uploaded_file.name}' already exists in the index."
                    )
                    continue
 
                file_path = save_uploaded_file(uploaded_file)
                reader = PdfReader(file_path)
                text = "".join([page.extract_text() for page in reader.pages])
                chunks = chunk_text(text, chunk_size=TEXT_CHUNK_SIZE, overlap=100)
                embeddings = generate_embeddings(chunks)
 
                documents_to_index = [
                    {
                        "doc_id": f"{uploaded_file.name}_{i}",
                        "text": chunk,
                        "embedding": embedding,
                        "document_name": uploaded_file.name,
                    }
                    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
                ]
                bulk_index_documents(documents_to_index)
                st.session_state["documents"].append(
                    {
                        "filename": uploaded_file.name,
                        "content": text,
                        "file_path": file_path,
                    }
                )
                document_names.append(uploaded_file.name)
                logger.info(f"File '{uploaded_file.name}' uploaded and indexed.")
 
        st.success("Files uploaded and indexed successfully!")
 
    if st.session_state["documents"]:
        st.markdown("### Uploaded Documents")
        with st.expander("Manage Uploaded Documents", expanded=True):
            for idx, doc in enumerate(st.session_state["documents"], 1):
                col1, col2 = st.columns([4, 1])
                with col1:
                    # Strong + readable filename text
                    st.markdown(
                        f"**{idx}. {doc['filename']}** — {len(doc['content'])} characters extracted"
                    )
                with col2:
                    delete_button = st.button(
                        "Delete",
                        key=f"delete_{doc['filename']}_{idx}",
                        help=f"Delete {doc['filename']}",
                    )
                    if delete_button:
                        if doc["file_path"] and os.path.exists(doc["file_path"]):
                            try:
                                os.remove(doc["file_path"])
                                logger.info(
                                    f"Deleted file '{doc['filename']}' from filesystem."
                                )
                            except FileNotFoundError:
                                st.error(
                                    f"File '{doc['filename']}' not found in filesystem."
                                )
                                logger.error(
                                    f"File '{doc['filename']}' not found during deletion."
                                )
                        delete_documents_by_document_name(doc["filename"])
                        st.session_state["documents"].pop(idx - 1)
                        st.session_state["deleted_file"] = doc["filename"]
                        time.sleep(0.5)
                        st.rerun()
 
 
def save_uploaded_file(uploaded_file) -> str:  # type: ignore
    """
    Saves an uploaded file to the local file system.
 
    Args:
        uploaded_file: The uploaded file to save.
 
    Returns:
        str: The file path where the uploaded file is saved.
    """
    UPLOAD_DIR = "uploaded_files"
    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    logger.info(f"File '{uploaded_file.name}' saved to '{file_path}'.")
    return file_path
 
 
if __name__ == "__main__":
    if "documents" not in st.session_state:
        st.session_state["documents"] = []
    render_upload_page()
 