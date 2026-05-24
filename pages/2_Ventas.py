import streamlit as st

# 1. Configuración de la página
st.set_page_config(page_title="Gestión de Ventas", page_icon="🛒", layout="wide")

st.title("Registro de Ventas")
st.markdown("Agrega nuevas transacciones al sistema. *(Modo Demostración Visual)*")

# 2. Creación del formulario estático
with st.form(key="form_nueva_venta_ui"):
    st.subheader("Nueva Venta")
    
    col_input1, col_input2 = st.columns(2)
    
    with col_input1:
        producto_input = st.text_input("Nombre del producto")
        
    with col_input2:
        monto_input = st.number_input("Monto ($)", min_value=0.0, step=10.0)
        
    boton_guardar = st.form_submit_button(label="Guardar Venta")

# Si el usuario presiona el botón, solo mostramos un mensaje visual de éxito simulado
if boton_guardar:
    st.success("Simulación: El botón funciona y el formulario se envió.")

# 3. Visualizar una tabla de demostración
st.divider()
st.markdown("### Historial Reciente")

datos_tabla_ventas = [
    {"Producto": "Monitor 24 pulgadas", "Monto": "$250.00"},
    {"Producto": "Teclado Mecánico", "Monto": "$85.00"},
    {"Producto": "Cable HDMI 2m", "Monto": "$15.00"}
]

st.dataframe(datos_tabla_ventas, use_container_width=True)