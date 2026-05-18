import streamlit as st

def apply_styles():
    st.markdown("""
    <style>
    .stApp {
        background-color: #050505;
        color: white;
    }

    [data-testid="stSidebar"] {
        background-color: #111111;
    }

    .chart-card {
        background-color: #000000;
        border: 1px solid #222222;
        border-radius: 16px;
        padding: 18px;
        min-height: 340px;
        margin-bottom: 24px;
    }
    </style>
    """, unsafe_allow_html=True)