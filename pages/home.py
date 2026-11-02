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
    
    # Real-Time Defense & Browser Extension
    st.subheader("🛡️ Real-Time Defense Suite")
    
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        st.markdown("""
        #### 🌐 Chrome & Web Extension
        Scans X/Twitter, Reddit, and web feeds in real-time. Flags phishing URLs, homoglyph domains, and deepfakes before you click.
        """)
        st.caption("📦 Extension package ready in `/extension` folder (Manifest V3).")
    with fcol2:
        st.markdown("""
        #### 📹 Live Video-Call WebRTC
        Inspect webcam and live Zoom/Teams video streams with 30fps facial landmark tracking and temporal anomaly scoring.
        """)
    with fcol3:
        st.markdown("""
        #### 🗄️ Enterprise Webhooks
        Automated ingestion endpoints (`/api/webhooks/slack` & `/api/webhooks/teams`) that quarantine phishing in transit.
        """)
    
    st.markdown("---")
    st.info("👉 Ready to test media or live video? Go to the **Analyze** page!")
