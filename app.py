import streamlit as st
from styles.main import apply_styles
from components.sidebar import sidebar
from pages.home import home_page

st.set_page_config(page_title="RocketData", page_icon="🚀", layout="wide")

apply_styles()
sidebar()
home_page()