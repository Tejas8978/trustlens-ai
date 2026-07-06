"""
TrustLens AI - Streamlit App
AI-powered deepfake & scam detection application
"""

import streamlit as st
from pathlib import Path
import sys

# Add backend to path
backend_path = Path(__file__).parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Import pages
try:
    from pages import home, analyze, history
except ImportError as e:
    st.error(f"Error importing pages: {e}")
    st.stop()

# Configure page
st.set_page_config(
    page_title="TrustLens AI",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main { padding-top: 2rem; }
    .metric-card { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("🔐 TrustLens AI")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["Home", "Analyze", "History"],
    icons=["🏠", "🔍", "📊"]
)

# Route to pages
if page == "Home":
    home.show()
elif page == "Analyze":
    analyze.show()
elif page == "History":
    history.show()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown(
    "Made with ❤️ by TrustLens AI Team | [GitHub](https://github.com/Tejas8978/trustlens_ai)"
)
