"""
Wrapper classes for analyzers to work with Streamlit
"""

from .image_analyzer import analyze_image
from .video_analyzer import analyze_video
from .text_analyzer import analyze_text
from .audio_analyzer import analyze_audio


class ImageAnalyzer:
    """Wrapper for image analysis"""
    def analyze(self, file_path: str) -> dict:
        with open(file_path, "rb") as f:
            return analyze_image(f.read(), file_path)


class VideoAnalyzer:
    """Wrapper for video analysis"""
    def analyze(self, file_path: str) -> dict:
        with open(file_path, "rb") as f:
            return analyze_video(f.read(), file_path)


class AudioAnalyzer:
    """Wrapper for audio analysis"""
    def analyze(self, file_path: str) -> dict:
        with open(file_path, "rb") as f:
            return analyze_audio(f.read(), file_path)


class TextAnalyzer:
    """Wrapper for text analysis"""
    def analyze(self, text: str) -> dict:
        return analyze_text(text)
