# pages/4_Pronosticos.py
import streamlit as st
import streamlit_shadcn_ui as ui
import pandas as pd # Para manejar los datos de la gráfica de forma más limpia

# 1. Configuración de la página
st.set_page_config(page_title="Pronósticos", page_icon="🔮", layout="wide")

st.title("Inteligencia Predictiva de Stock")
st.markdown("Análisis de demanda futura y proyecciones de agotamiento de inventario.")
st.divider()

# 2. SECCIÓN DE INDICADORES DE CONFIANZA (shadcn)
# Usamos columnas para mostrar KPIs rápidos del modelo de IA
col1, col2, col3 = st.columns(3)

with col1:
    ui.metric_card(
        title="Precisión del Modelo", 
        content="94.2%", 
        description="Basado en los últimos 6 meses", 
        key="accuracy_kpi"
    )
with col2:
    ui.metric_card(
        title="Días para Agotamiento", 
        content="42 días", 
        description="Promedio de productos saludables", 
        key="days_kpi"
    )
with col3:
    ui.metric_card(
        title="Riesgo de Overstock", 
        content="Bajo", 
        description="Tendencia general del mes", 
        key="risk_kpi"
    )

# 3. VISUALIZACIÓN DE TENDENCIAS
st.write("")
st.subheader("📈 Proyección de Demanda vs Stock")

# Creamos datos simulados para la gráfica
# Imagina que esto viene de una inteligencia artificial en el futuro
data = {
    "Mes": ["Ene", "Feb", "Mar", "Abr", "May", "Jun"],
    "Ventas Reales": [400, 450, 500, 480, 0, 0],
    "Pronóstico Ventas": [410, 440, 490, 470, 520, 550],
    "Nivel Inventario": [800, 750, 700, 650, 600, 550]
}
df_pronostico = pd.DataFrame(data)

# st.area_chart es perfecto para dashboards porque se ve muy moderno y limpio
st.area_chart(df_pronostico, x="Mes", y=["Ventas Reales", "Pronóstico Ventas", "Nivel Inventario"])

# 4. TABLA DE RECOMENDACIONES DE COMPRA
st.divider()
st.subheader("💡 Recomendaciones de Abastecimiento")

# Simulamos lo que el sistema "recomienda" hacer para evitar overstock
recomendaciones = [
    {"Producto": "Tenis Runner Pro", "Acción": "❌ DETENER COMPRA", "Motivo": "Demanda bajando, stock alto"},
    {"Producto": "Gorra Ajustable", "Acción": "✅ COMPRA NORMAL", "Motivo": "Rotación saludable"},
    {"Producto": "Sudadera Entren.", "Acción": "⚡ PEDIDO URGENTE", "Motivo": "Riesgo de quiebre de stock"},
]

st.table(recomendaciones) # st.table es más elegante para listas cortas y estáticas