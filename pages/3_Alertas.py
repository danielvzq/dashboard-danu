import streamlit as st
# Volvemos a importar nuestra pieza de lego
from components.alertas import tarjeta_overstock

# 1. Configuración de la página
st.set_page_config(page_title="Centro de Alertas", page_icon="🔔", layout="wide")

st.title("Centro de Alertas")
st.markdown("Monitoreo en tiempo real de anomalías operativas y sobreinventario.")
st.divider()

# 2. Categorización visual de los problemas
st.subheader("🔴 Criticidad Alta: Riesgo de Obsolescencia")
st.markdown("Productos con más de 90 días sin movimiento. Requieren acción inmediata.")

# Invocamos el componente para un producto crítico
tarjeta_overstock(
    producto="Raqueta de Tenis Máster V2", 
    cantidad_exceso=45, 
    dias_estancado=95, 
    perdida_estimada=2100.00
)

st.write("---") # Una línea divisoria sutil

st.subheader("🟡 Criticidad Media: Excedente en Crecimiento")
st.markdown("Productos acumulando stock sin llegar aún a niveles críticos.")

# Invocamos el mismo componente para otro producto, simulando pesas estancadas
tarjeta_overstock(
    producto="Set de Mancuernas 10kg", 
    cantidad_exceso=30, 
    dias_estancado=45, 
    perdida_estimada=850.00
)

# 3. Otra sección para alertas diferentes (Ej: Proveedores, Logística)
st.divider()
st.subheader("🔵 Otras Notificaciones")
st.info("El envío del proveedor 'Deportes Globales' está retrasado por 2 días.")
st.warning("Se detectó una discrepancia de 5 unidades en el conteo de 'Playeras de Entrenamiento'.")