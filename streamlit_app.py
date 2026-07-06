"""
TrustLens AI - Streamlit App
AI-powered deepfake & scam detection application
"""

import streamlit as st
from pages import home, analyze, history

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
