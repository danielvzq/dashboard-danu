# components/alertas.py
import streamlit as st
import streamlit_shadcn_ui as ui 

def tarjeta_overstock(producto, cantidad_exceso, dias_estancado, perdida_estimada, nivel="Crítico"):
    """
    Dibuja una alerta visual estandarizada para productos con sobreinventario.
    Combina la estabilidad de Streamlit nativo con el diseño de shadcn-ui.
    """
    with st.container(border=True):
        
        col_titulo, col_badge = st.columns([4, 1])
        
        with col_titulo:
            st.markdown(f"#### 📦 {producto}")
            
        with col_badge:
            # Los badges de shadcn funcionan perfecto, los conservamos
            variante_badge = "destructive" if nivel == "Crítico" else "secondary"
            ui.badges(
                badge_list=[(nivel, variante_badge)], 
                key=f"badge_{producto}"
            )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Exceso", value=f"{cantidad_exceso} un.")
        with col2:
            st.metric(label="Días estancado", value=f"{dias_estancado} días")
        with col3:
            st.metric(label="Capital Estancado", value=f"${perdida_estimada:,.2f}")
        
        # SOLUCIÓN: Usamos st.popover nativo en lugar del alert_dialog de shadcn
        with st.popover(f"Generar remate para {producto}"):
            st.markdown(f"**¿Confirmar remate de {producto}?**")
            st.write("Esta acción notificará al equipo de ventas inmediatamente.")
            
            # Botón de confirmación dentro del pop-up
            if st.button("Confirmar Remate", key=f"conf_{producto}", type="primary"):
                st.success("✅ Orden generada exitosamente")