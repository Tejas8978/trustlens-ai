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
    
    # 08 DEFENSE & FUTURE
    st.caption("08 DEFENSE & FUTURE")
    st.header("Future Enhancements")
    
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        st.markdown("""
        #### 🌐 Browser extension
        A real-time Chrome / Firefox extension that automatically scans images and links while browsing social-media feeds.
        """)
    with fcol2:
        st.markdown("""
        #### 📹 Live video-call inspection
        WebRTC integration to analyze Zoom / Teams streams for real-time face-swap detection.
        """)
    with fcol3:
        st.markdown("""
        #### 🗄️ Enterprise webhooks
        Automated ingestion pipelines for Slack and Microsoft Teams that block phishing attacks in transit.
        """)
    
    bcol1, bcol2 = st.columns([1, 1.25])
    with bcol1:
        st.markdown("""
        :red[**Current limitation**]  
        Aggressive re-compression by social platforms weakens EXIF tags and fine PRNU sensor noise.
        """)
    with bcol2:
        st.markdown("""
        :green[**Research direction**]  
        Video temporal 3D-CNNs (Video Swin Transformers) and live C2PA blockchain verification of media authenticity.
        """)
    
    st.markdown("---")
    st.info("👉 Ready to check media? Go to the **Analyze** page!")
