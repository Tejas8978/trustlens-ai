import streamlit as st
from pathlib import Path
import sys
import pandas as pd

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from database import get_history, delete_history, init_db

def show():
    """Display history page"""
    st.title("📊 Analysis History")
    
    init_db()
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        filter_type = st.selectbox(
            "Filter by type",
            ["All", "Image", "Video", "Audio", "Text"]
        )
    
    with col2:
        sort_by = st.selectbox("Sort by", ["Recent", "Risk Level"])
    
    with col3:
        if st.button("🗑️ Clear All"):
            delete_history()
            st.success("History cleared!")
            st.rerun()
    
    # Get history
    history = get_history()
    
    if not history:
        st.info("No analysis history yet. Start by analyzing some media!")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(history)
    
    # Filter
    if filter_type != "All":
        df = df[df["type"].str.lower() == filter_type.lower()]
    
    # Sort
    if sort_by == "Recent":
        df = df.sort_values("created_at", ascending=False)
    else:
        risk_order = {"high": 0, "medium": 1, "low": 2}
        df["risk_sort"] = df["risk_level"].str.lower().map(risk_order)
        df = df.sort_values("risk_sort")
    
    # Display stats
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Analyses", len(history))
    with col2:
        high_risk = len([h for h in history if h.get("risk_level", "").lower() == "high"])
        st.metric("High Risk", high_risk)
    with col3:
        avg_confidence = df["confidence"].mean() if "confidence" in df.columns else 0
        st.metric("Avg Confidence", f"{avg_confidence:.1%}")
    with col4:
        type_counts = df["type"].value_counts()
        st.metric("Most Analyzed", type_counts.index[0] if len(type_counts) > 0 else "N/A")
    
    st.markdown("---")
    
    # Display table
    st.subheader("Recent Analyses")
    
    # Prepare display data
    display_df = df[["type", "filename", "risk_level", "confidence", "created_at"]].copy()
    display_df.columns = ["Type", "File/Text", "Risk Level", "Confidence", "Date"]
    display_df["Confidence"] = display_df["Confidence"].apply(lambda x: f"{x:.1%}" if x else "N/A")
    
    # Color the risk level column
    def color_risk(val):
        if val == "HIGH":
            return "color: red"
        elif val == "MEDIUM":
            return "color: orange"
        else:
            return "color: green"
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )
    
    # Detailed view
    st.markdown("---")
    st.subheader("📈 Analysis Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Type breakdown
        type_counts = df["type"].value_counts()
        st.bar_chart(type_counts, use_container_width=True)
    
    with col2:
        # Risk level breakdown
        risk_counts = df["risk_level"].value_counts()
        st.bar_chart(risk_counts, use_container_width=True)
    
    # Export option
    st.markdown("---")
    if st.button("📥 Export as CSV"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="trustlens_history.csv",
            mime="text/csv"
        )
