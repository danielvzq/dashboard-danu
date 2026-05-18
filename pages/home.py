import streamlit as st
from components.card import chart_card

def home_page():
    st.title("Dashboard")

    col1, col2 = st.columns(2)

    with col1:
        chart_card("El mayor riesgo de inventario se concentra en pocos productos", "Aquí va gráfica 1")

    with col2:
        chart_card("Días de inventario promedio por categoría", "Aquí va gráfica 2")