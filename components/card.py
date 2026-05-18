import streamlit as st

def chart_card(title, content):
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.subheader(title)
    st.write(content)
    st.markdown('</div>', unsafe_allow_html=True)