import logging
import os
 
import streamlit as st
 
from src.utils import setup_logging
 
# Initialize logger
setup_logging()  # Set up logging configuration
logger = logging.getLogger(__name__)
 
# Set page config with title, icon, and layout
st.set_page_config(
    page_title="Your Conversational Platform with your local documents 📄",
    page_icon="🤖",
    layout="centered",
)
 
 
# Custom CSS to style the page and sidebar (no external config)
def apply_custom_css() -> None:
    """Applies custom CSS styling to the Streamlit page and sidebar (current selectors)."""
    st.markdown(
        """
<style>
        /* ===== App backgrounds ===== */
        [data-testid="stAppViewContainer"] {
            background-color: #ffffff !important; /* main background white */
            color: #002B5B !important;            /* default text color */
        }
        /* Make the top header transparent so the white background shows */
        [data-testid="stHeader"] {
            background: transparent !important;
        }
 
        /* ===== Main content card ===== */
        .block-container {
            background-color: #ffffff !important; /* white card */
            border-radius: 10px !important;
            padding: 20px !important;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.10) !important;
        }
 
        /* ===== Ensure readable text inside main content ===== */
        .block-container,
        .block-container [data-testid="stMarkdownContainer"],
        .block-container p,
        .block-container li,
        .block-container span,
        .block-container small,
        .block-container strong,
        .block-container em {
            color: #002B5B !important; /* dark blue text */
            opacity: 1 !important;     /* remove dark-theme fade */
            text-shadow: none !important;
        }
        .block-container h1,
        .block-container h2,
        .block-container h3,
        .block-container h4 {
            color: #006d77 !important; /* headings teal */
            opacity: 1 !important;
        }
        .block-container a {
            color: #118ab2 !important; /* links */
            text-decoration: none;
        }
        .block-container a:hover {
            text-decoration: underline;
        }
 
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
        [data-testid="stSidebar"] li {
            color: #ffffff !important;
            opacity: 1 !important;
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
 
        /* ===== Center helper & footer ===== */
        .centered { text-align: center; }
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
    logger.info("Applied custom CSS styling.")
 
 
# Function to display logo or placeholder
def display_logo(logo_path: str) -> None:
    """Displays the logo in the sidebar or a placeholder if the logo is not found.
 
    Args:
        logo_path (str): The file path for the logo image.
    """
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, width=220)
        logger.info("Logo displayed.")
    else:
        st.sidebar.markdown("### Logo Placeholder")
        logger.warning("Logo not found, displaying placeholder.")
 
 
# Function to display main content
def display_main_content() -> None:
    """Displays the main welcome content on the page."""
    st.title("Personal Document Assistant 📄🤖")
    st.markdown(
        """
        Welcome to the AI-Powered Document Retrieval Assistant 👋
 
        This app allows you to interact with an AI-powered assistant and upload documents for processing and retrieval.
 
        **Features:**
        - **Chatbot**: Have a conversation with the AI using the latest LLM model.
        - **Document Upload**: Upload PDFs and retrieve data from them using OpenSearch as a Hybrid RAG System.
 
        **Choose a page from the sidebar to begin!**
        """
    )
    logger.info("Displayed main welcome content.")
 
 
# Function to display sidebar content
def display_sidebar_content() -> None:
    """Displays headers and footer content in the sidebar."""
    st.sidebar.markdown(
        "<h2 style='text-align: center; margin-bottom: 0;'>Chat with your local documents</h2>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        "<h4 style='text-align: center; margin-top: 4px;'>Your Conversational Platform</h4>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        """
<div class="footer-text">
            © 2025 Talk with AI
</div>
        """,
        unsafe_allow_html=True,
    )
    logger.info("Displayed sidebar content.")
 
 
# Main execution
if __name__ == "__main__":
    apply_custom_css()
    #display_logo("images/jamwithai_logo.png")
    display_sidebar_content()
    display_main_content()