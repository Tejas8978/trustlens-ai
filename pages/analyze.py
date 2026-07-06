import streamlit as st
import tempfile
import os
from pathlib import Path
import sys

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Import utils
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import get_risk_status, get_confidence_percentage

try:
    from analyzers.image_analyzer import analyze_image
    from analyzers.video_analyzer import analyze_video
    from analyzers.audio_analyzer import analyze_audio
    from analyzers.text_analyzer import analyze_text
    from database import add_history, init_db
except ImportError as e:
    st.error(f"Error loading analyzers: {e}")
    st.info("Make sure all backend dependencies are installed.")
    st.stop()

def show():
    """Display analyze page"""
    st.title("🔍 Analyze Media")
    
    init_db()
    
    # Tabs for different analysis types
    tab1, tab2, tab3, tab4 = st.tabs(["🖼️ Image", "🎬 Video", "🎵 Audio", "📝 Text"])
    
    # Image Analysis
    with tab1:
        st.subheader("Image Deepfake Detection")
        uploaded_image = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])
        
        if uploaded_image and st.button("Analyze Image"):
            with st.spinner("Analyzing image..."):
                try:
                    # Save temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                        tmp.write(uploaded_image.getbuffer())
                        tmp_path = tmp.name
                    
                    # Read back as bytes
                    with open(tmp_path, "rb") as f:
                        image_bytes = f.read()
                    
                    result = analyze_image(image_bytes, uploaded_image.name)
                    
                    # Display results
                    col1, col2 = st.columns(2)
                    with col1:
                        st.image(uploaded_image, caption="Uploaded Image")
                    with col2:
                        display_results(result, "Image")
                    
                    # Save to history
                    add_history({
                        "type": "image",
                        "filename": uploaded_image.name,
                        "risk_level": result.get("risk_level", "unknown"),
                        "confidence": result.get("confidence", 0),
                        "details": str(result)
                    })
                    
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
    
    # Video Analysis
    with tab2:
        st.subheader("Video Deepfake Detection")
        uploaded_video = st.file_uploader("Upload a video", type=["mp4", "avi", "mov"])
        
        if uploaded_video and st.button("Analyze Video"):
            with st.spinner("Analyzing video (this may take a few minutes)..."):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                        tmp.write(uploaded_video.getbuffer())
                        tmp_path = tmp.name
                    
                    # Read back as bytes
                    with open(tmp_path, "rb") as f:
                        video_bytes = f.read()
                    
                    result = analyze_video(video_bytes, uploaded_video.name)
                    
                    display_results(result, "Video")
                    
                    add_history({
                        "type": "video",
                        "filename": uploaded_video.name,
                        "risk_level": result.get("risk_level", "unknown"),
                        "confidence": result.get("confidence", 0),
                        "details": str(result)
                    })
                    
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
    
    # Audio Analysis
    with tab3:
        st.subheader("Voice Deepfake Detection")
        uploaded_audio = st.file_uploader("Upload audio", type=["mp3", "wav", "m4a"])
        
        if uploaded_audio and st.button("Analyze Audio"):
            with st.spinner("Analyzing audio..."):
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                        tmp.write(uploaded_audio.getbuffer())
                        tmp_path = tmp.name
                    
                    # Read back as bytes
                    with open(tmp_path, "rb") as f:
                        audio_bytes = f.read()
                    
                    result = analyze_audio(audio_bytes, uploaded_audio.name)
                    
                    display_results(result, "Audio")
                    
                    add_history({
                        "type": "audio",
                        "filename": uploaded_audio.name,
                        "risk_level": result.get("risk_level", "unknown"),
                        "confidence": result.get("confidence", 0),
                        "details": str(result)
                    })
                    
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
    
    # Text Analysis
    with tab4:
        st.subheader("Scam & Fraud Detection")
        text_input = st.text_area("Paste text to analyze", height=150)
        
        if text_input and st.button("Analyze Text"):
            with st.spinner("Analyzing text..."):
                result = analyze_text(text_input)
                
                display_results(result, "Text")
                
                add_history({
                    "type": "text",
                    "filename": "text_analysis",
                    "risk_level": result.get("risk_level", "unknown"),
                    "confidence": result.get("confidence", 0),
                    "details": str(result)
                })


def display_results(result, analysis_type):
    """Display analysis results"""
    st.markdown("---")
    st.subheader("📊 Analysis Results")
    
    risk_level = result.get("risk_level", "unknown")
    confidence = result.get("confidence", 0)
    
    # Get display status
    status = get_risk_status(risk_level)
    confidence_pct = get_confidence_percentage(confidence)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Detection Status", status)
    with col2:
        st.metric("Confidence", confidence_pct)
    with col3:
        st.metric("Type Analyzed", analysis_type)
    
    # Details
    if "details" in result:
        with st.expander("📝 Detailed Analysis"):
            st.write(result["details"])
