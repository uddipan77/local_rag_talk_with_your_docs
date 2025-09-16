import logging
import os
 
import streamlit as st
 
from src.chat import (  # type: ignore
    ensure_model_pulled,
    generate_response_streaming,
    get_embedding_model,
)
from src.ingestion import create_index, get_opensearch_client
from src.constants import OLLAMA_MODEL_NAME, OPENSEARCH_INDEX
from src.utils import setup_logging
 
# Initialize logger
setup_logging()  # Configures logging for the application
logger = logging.getLogger(__name__)
 
# Set page configuration
st.set_page_config(page_title="Talk to your Local Documents - Chatbot", page_icon="🤖", layout="centered")
 
# Apply custom CSS (no external config files)
st.markdown(
    """
    <style>
    /* ===== App & Header ===== */
    [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;   /* main background white */
        color: #002B5B !important;              /* default text color */
    }
    [data-testid="stHeader"] {                  /* top bar */
        background: transparent !important;
    }
 
    /* ===== Main content card ===== */
    .block-container {
        background-color: #ffffff !important;
        border-radius: 10px !important;
        padding: 20px !important;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.10) !important;
    }
 
    /* Readable text in main content (remove dark-theme fade) */
    .block-container,
    .block-container [data-testid="stMarkdownContainer"],
    .block-container p,
    .block-container li,
    .block-container span,
    .block-container small,
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
 
    /* ===== Sidebar ===== */
    [data-testid="stSidebar"] {
        background-color: #006d77 !important; /* dark cyan sidebar */
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
 
    /* Sidebar widgets (inputs, sliders) on dark bg */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] .stSlider,
    [data-testid="stSidebar"] .stNumberInput input {
        background-color: rgba(255,255,255,0.12) !important;
        color: #ffffff !important;
    }
 
    /* ===== Buttons ===== */
    .stButton > button {
        background-color: #118ab2 !important;
        color: #ffffff !important;
        border-radius: 5px !important;
        border: none !important;
        padding: 10px 20px !important;
        font-size: 16px !important;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.2) !important;
        cursor: pointer;
    }
    .stButton > button:hover {
        background-color: #07a6c2 !important;
        color: #ffffff !important;
    }
 
    /* ===== Chat area ===== */
    /* Chat message bubbles (both roles) */
    [data-testid="stChatMessage"] {
        background-color: #f5fbfc !important;
        color: #004b63 !important;
        border: 1px solid rgba(0,0,0,0.06) !important;
        border-radius: 10px !important;
        padding: 12px !important;
        margin-bottom: 10px !important;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        color: #004b63 !important;
        opacity: 1 !important;
    }
    /* Chat input bar */
    [data-testid="stChatInput"] textarea {
        background-color: #ffffff !important;
        color: #002B5B !important;
        border: 1px solid rgba(0,0,0,0.15) !important;
    }
 
    /* ===== Footer text (sidebar) ===== */
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
logger.info("Custom CSS applied.")
 
 
# Main chatbot page rendering function
def render_chatbot_page() -> None:
    # Title
    st.title("Talk to your Local Documents - Chatbot 🤖")
    model_loading_placeholder = st.empty()
 
    # Session state (defaults)
    if "use_hybrid_search" not in st.session_state:
        st.session_state["use_hybrid_search"] = True
    if "num_results" not in st.session_state:
        st.session_state["num_results"] = 5
    if "temperature" not in st.session_state:
        st.session_state["temperature"] = 0.7
 
    # OpenSearch client + index
    with st.spinner("Connecting to OpenSearch..."):
        client = get_opensearch_client()
    create_index(client)
    index_name = OPENSEARCH_INDEX  # noqa: F841 (kept for clarity/logging if needed)
 
    # Sidebar controls
    st.session_state["use_hybrid_search"] = st.sidebar.checkbox(
        "Enable RAG mode", value=st.session_state["use_hybrid_search"]
    )
    st.session_state["num_results"] = st.sidebar.number_input(
        "Number of Results in Context Window",
        min_value=1,
        max_value=10,
        value=st.session_state["num_results"],
        step=1,
    )
    st.session_state["temperature"] = st.sidebar.slider(
        "Response Temperature",
        min_value=0.0,
        max_value=1.0,
        value=st.session_state["temperature"],
        step=0.1,
    )
 
    # Sidebar logo
    
 
    # Sidebar headings + footer
    st.sidebar.markdown(
        "<h2 style='text-align: center; margin-bottom: 0;'>Talk with your documents</h2>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        "<h4 style='text-align: center; margin-top: 4px;'>Your Conversational Platform</h4>",
        unsafe_allow_html=True,
    )
    
    logger.info("Sidebar configured with headers and footer.")
 
    # Load models once
    if "embedding_models_loaded" not in st.session_state:
        with model_loading_placeholder:
            with st.spinner("Loading Embedding and Ollama models for Hybrid Search..."):
                get_embedding_model()
                ensure_model_pulled(OLLAMA_MODEL_NAME)
                st.session_state["embedding_models_loaded"] = True
        logger.info("Embedding model loaded.")
        model_loading_placeholder.empty()
 
    # Chat history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
 
    # Show history
    for message in st.session_state["chat_history"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
 
    # Input -> response
    if prompt := st.chat_input("Type your message here..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        logger.info("User input received.")
 
        with st.chat_message("assistant"):
            with st.spinner("Generating response..."):
                response_placeholder = st.empty()
                response_text = ""
 
                response_stream = generate_response_streaming(
                    prompt,
                    use_hybrid_search=st.session_state["use_hybrid_search"],
                    num_results=st.session_state["num_results"],
                    temperature=st.session_state["temperature"],
                    chat_history=st.session_state["chat_history"],
                )
 
            if response_stream is not None:
                for chunk in response_stream:
                    if (
                        isinstance(chunk, dict)
                        and "message" in chunk
                        and "content" in chunk["message"]
                    ):
                        response_text += chunk["message"]["content"]
                        response_placeholder.markdown(response_text + "▌")
                    else:
                        logger.error("Unexpected chunk format in response stream.")
 
            response_placeholder.markdown(response_text)
            st.session_state["chat_history"].append(
                {"role": "assistant", "content": response_text}
            )
            logger.info("Response generated and displayed.")
 
 
# Main execution
if __name__ == "__main__":
    render_chatbot_page()