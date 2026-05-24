import streamlit as st
import streamlit_shadcn_ui as ui

# 1. Configuración de la página (UI)
st.set_page_config(page_title="Dashboard General", page_icon="📊", layout="wide")
# Cargar estilos CSS personalizados
with open("styles/main.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("Panel de Control Principal")
st.markdown("Bienvenido al sistema. Aquí tienes un resumen visual de las operaciones.")
st.divider()

# 2. Tarjetas de Métricas (Estáticas)
col1, col2, col3 = st.columns(3)

with col1:
    ui.metric_card(
        title="Ventas del Día",
        content="$15,250.00",
        description="+12% comparado con ayer",
        key="card_ventas_ui"
    )

with col2:
    ui.metric_card(
        title="Artículos en Inventario",
        content="1,245",
        description="8 productos bajo el mínimo",
        key="card_inventario_ui"
    )

with col3:
    ui.metric_card(
        title="Alertas del Sistema",
        content="2",
        description="Revisar pronósticos de stock",
        key="card_alertas_ui"
    )

# 3. Pestañas y Visualización de Datos (Estáticos)
st.write("") 
st.markdown("### Detalles Operativos")

opciones_pestanas = ["📈 Resumen Gráfico", "📋 Últimos Movimientos"]
pestana_activa = ui.tabs(
    options=opciones_pestanas, 
    default_value=opciones_pestanas[0], 
    key="pestanas_inicio_ui"
)

if pestana_activa == "📈 Resumen Gráfico":
    st.markdown("#### Evolución de Ventas (Últimos 7 días)")
    # Datos fijos solo para que la gráfica se vea bien
    datos_grafica = {
        "Días": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"], 
        "Ventas": [120, 150, 180, 130, 200, 250, 210]
    }
    st.bar_chart(data=datos_grafica, x="Días", y="Ventas")

elif pestana_activa == "📋 Últimos Movimientos":
    st.markdown("#### Registro de Actividad Reciente")
    # Tabla fija de demostración visual
    datos_tabla = [
        {"ID": "TX-001", "Acción": "Venta", "Monto": "$150.00", "Estado": "Completado"},
        {"ID": "TX-002", "Acción": "Ingreso Stock", "Monto": "-", "Estado": "Pendiente"},
        {"ID": "TX-003", "Acción": "Venta", "Monto": "$320.00", "Estado": "Completado"},
        {"ID": "TX-004", "Acción": "Devolución", "Monto": "-$50.00", "Estado": "Revisión"},
    ]
    st.dataframe(datos_tabla, use_container_width=True)