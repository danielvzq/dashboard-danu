# pages/1_Inventario.py
import streamlit as st
import streamlit_shadcn_ui as ui
from components.alertas import tarjeta_overstock
from src.database import obtener_datos_inventario # 1. Importamos nuestra función de datos

st.set_page_config(page_title="Inventario", page_icon="📦", layout="wide")

st.title("Gestión de Inventario")
st.markdown("Consulta el estado actual de tu stock y detecta productos sin rotación.")
st.divider()

st.subheader("⚠️ Atención Requerida (Exceso de Inventario)")
st.markdown("Los siguientes productos han superado el límite de almacenamiento recomendado:")

tarjeta_overstock(
    producto="Tenis Deportivos Runner Pro", 
    cantidad_exceso=150, 
    dias_estancado=120, 
    perdida_estimada=4500.00
)

tarjeta_overstock(
    producto="Raqueta de Tenis Máster V2", 
    cantidad_exceso=45, 
    dias_estancado=95, 
    perdida_estimada=2100.00
)

st.divider()
st.subheader("📋 Inventario General")

col_filtro1, col_filtro2 = st.columns(2)
with col_filtro1:
    st.text_input("🔍 Buscar producto por nombre o SKU...")
with col_filtro2:
    st.selectbox("Filtrar por Categoría", ["Todas", "Calzado", "Equipamiento", "Ropa Deportiva"])

# 2. Reemplazamos la lista gigante por una simple llamada a nuestra función
catálogo_productos = obtener_datos_inventario()

st.dataframe(catálogo_productos, use_container_width=True)