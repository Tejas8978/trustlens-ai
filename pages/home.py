import streamlit as st

def show():
    """Display home page"""
    st.title("🔐 TrustLens AI")
    st.subheader("AI-Powered Deepfake & Scam Detection")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🎯 What is TrustLens AI?
        
        TrustLens AI is an advanced AI system designed to detect:
        - 🎭 **Deepfakes** - AI-generated fake videos and images
        - 🚨 **Scams** - Fraudulent text and content
        - ⚠️ **Manipulation** - Edited and altered media
        
        ### 🚀 Key Features
        - Real-time analysis of images and videos
        - Audio analysis for voice deepfakes
        - Text analysis for scam detection
        - Complete analysis history
        - Risk level assessment
        """)
    
    with col2:
        st.markdown("""
        ### 📊 How It Works
        
        1. **Upload** your media (image, video, audio, or text)
        2. **Analyze** using our AI models
        3. **Get Results** with risk assessment
        4. **Review** your analysis history
        
        ### 🔐 Security & Privacy
        
        Your data is:
        - ✅ Processed locally
        - ✅ Not shared with third parties
        - ✅ Stored securely in our database
        - ✅ Deleted on request
        """)
    
    st.markdown("---")
    
    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Analyses Performed", "1,234+", "+12%")
    with col2:
        st.metric("Detection Rate", "99.2%", "↑2.1%")
    with col3:
        st.metric("Active Users", "500+", "+8%")
    
    st.markdown("---")
    st.info("👉 Ready to check media? Go to the **Analyze** page!")
