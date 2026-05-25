# pages/3_Alertas.py
import streamlit as st
import pandas as pd
import streamlit_shadcn_ui as ui
import plotly.express as px

# 1. Configuración de la página con enfoque corporativo
st.set_page_config(page_title="Centro de Alertas", layout="wide")

st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    h1, h2, h3 { font-weight: 700 !important; color: #1e293b; }
    div[data-testid="stMetricValue"] { font-size: 1.6rem !important; font-weight: 700 !important; }
    </style>
""", unsafe_allow_html=True)

# 2. Carga y preparación optimizada de los datos
@st.cache_data
def cargar_y_limpiar_datos():
    df = pd.read_csv("data/df_Maestra.csv")
    
    df["Region"] = df["Region"].astype(str).str.strip().str.title()
    df["Category"] = df["Category"].astype(str).str.strip().str.title()
    df["Subcategory"] = df["Subcategory"].astype(str).str.strip().str.title()
    df["Product_name"] = df["Product_name"].astype(str).str.strip()
    
    df["Overstock_critico"] = df["Overstock_critico"].astype(str).str.upper() == "TRUE"
    df["Valor_Economico"] = df["Stock"] * df["Static_price"]
    
    return df

try:
    df_base = cargar_y_limpiar_datos()
except FileNotFoundError:
    st.error("No se encontró 'df_Maestra.csv' en la carpeta 'data/'.")
    st.stop()

# Inicialización del estado de navegación interactiva
if "zona_activa" not in st.session_state:
    st.session_state.zona_activa = "General"


# ==========================================
# VISTA GENERAL: PORTAL DE TARJETAS EJECUTIVAS
# ==========================================
if st.session_state.zona_activa == "General":
    
    st.title("Centro de Alertas Estratégicas")
    st.markdown("Selecciona una zona geográfica del panel para profundizar en el análisis de inventario.")
    st.divider()
    
    resumen_regiones = df_base.groupby("Region").agg({
        "Percentage": "mean",
        "Valor_Economico": "sum"
    }).reset_index()
    
    st.subheader("Estado General por Región")
    
    # Grid dinámico de 3 columnas
    num_cols = 3
    for i in range(0, len(resumen_regiones), num_cols):
        cols = st.columns(num_cols)
        for j in range(num_cols):
            if i + j < len(resumen_regiones):
                row = resumen_regiones.iloc[i + j]
                reg = row["Region"]
                pct = row["Percentage"]
                capital = row["Valor_Economico"]
                
                estado = "Riesgo Crítico" if pct >= 120 else "Precaución" if pct >= 100 else "Saludable"
                color_estado = "#ef4444" if pct >= 120 else "#f59e0b" if pct >= 100 else "#10b981"
                
                # Calculamos la diferencia contra el 100% ideal para la dirección del delta
                exceso_pct = pct - 100.0
                
                with cols[j]:
                    with st.container(height=280, border=True):
                        # Cabecera estilizada con fondo oscuro y texto en blanco para el nombre de la zona
                        st.markdown(f"""
                            <div style='background-color: #1e293b; padding: 8px; border-radius: 6px; margin-bottom: 12px;'>
                                <div style='font-size: 1.1rem; font-weight: 600; color: #ffffff; text-align: center;'>{reg}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        sub_c1, sub_c2 = st.columns(2)
                        with sub_c1:
                            st.metric(
                                label="Sobrestock", 
                                value=f"{pct:.1f}%", 
                                delta=f"{exceso_pct:+.1f}% vs ideal", 
                                delta_color="inverse"
                            )
                        with sub_c2:
                            st.metric(
                                label="Capital ($)", 
                                value=f"{capital/1000:,.0f}k" 
                            )
                        
                        st.markdown(f"<div style='text-align: center; color: {color_estado}; font-size: 0.95rem; font-weight: 600; margin-bottom: 14px;'>{estado}</div>", unsafe_allow_html=True)
                        
                        if st.button("Analizar", key=f"nav_{reg}", use_container_width=True, type="secondary"):
                            st.session_state.zona_activa = reg
                            st.rerun()


# ==========================================
# VISTA DETALLADA (DRILL-DOWN)
# ==========================================
else:
    zona_sel = st.session_state.zona_activa
    
    # Encabezado con botón de retorno minimalista sin emojis
    col_titulo, col_regresar = st.columns([5, 1])
    with col_titulo:
        st.title(f"Alertas Operativas: {zona_sel}")
        st.markdown("Análisis granular de inventarios, brechas de planeación y rotación.")
    with col_regresar:
        st.write("")
        st.write("") 
        if st.button("Volver al Resumen", use_container_width=True, type="secondary"):
            st.session_state.zona_activa = "General"
            st.rerun()
            
    st.divider()
    
    # Filtrado base de la zona seleccionada
    df_zona = df_base[df_base["Region"] == zona_sel]
    
    # NUEVA ADICIÓN: KPIs de Resumen Rápido para la Zona seleccionada
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    with col_kpi1:
        capital_zona = df_zona["Valor_Economico"].sum()
        ui.metric_card(title="Capital Total en Riesgo", content=f"${capital_zona:,.2f}", description="Inventario actual inmovilizado", key="kpi_cap_zona")
    with col_kpi2:
        criticos_zona = df_zona[df_zona["Overstock_critico"] == True].shape[0]
        ui.metric_card(title="Alertas Críticas Activas", content=str(criticos_zona), description="Productos que requieren remate inmediato", key="kpi_crit_zona")
    with col_kpi3:
        max_dias = df_zona["Days_inventory"].max()
        ui.metric_card(title="Permanencia Máxima", content=f"{max_dias:.0f} días", description="Peor registro de estancamiento", key="kpi_dias_zona")
        
    st.write("")

    # Selectores de segmentación jerárquica
    col_cat, col_sub = st.columns(2)
    with col_cat:
        cat_options = ["Todas las Categorías"] + sorted(df_zona["Category"].unique().tolist())
        categoria_sel = st.selectbox("Categoría", cat_options)
        
    df_filtrado = df_zona.copy()
    if categoria_sel != "Todas las Categorías":
        df_filtrado = df_filtrado[df_filtrado["Category"] == categoria_sel]
        
    with col_sub:
        sub_options = ["Todas las Subcategorías"] + sorted(df_filtrado["Subcategory"].unique().tolist())
        subcategoria_sel = st.selectbox("Subcategoría", sub_options)
        
    if subcategoria_sel != "Todas las Subcategorías":
        df_filtrado = df_filtrado[df_filtrado["Subcategory"] == subcategoria_sel]

    # --- Semáforo de Sub-niveles ---
    st.write("")
    eje_agrupacion = "Category" if categoria_sel == "Todas las Categorías" else "Subcategory"
    resumen_semaforo = df_filtrado.groupby(eje_agrupacion)["Percentage"].mean().reset_index()
    
    st.markdown(f"**Nivel de Exceso Actual por {eje_agrupacion}**")
    cols_sem = st.columns(min(len(resumen_semaforo), 4) if len(resumen_semaforo) > 0 else 1)
    
    for i, row in enumerate(resumen_semaforo.itertuples()):
        pct = row.Percentage
        nombre = getattr(row, eje_agrupacion)
        estado = "Riesgo Crítico" if pct >= 120 else "Precaución" if pct >= 100 else "Saludable"
        
        with cols_sem[i % 4]:
            ui.metric_card(title=nombre, content=f"{pct:.1f}%", description=estado, key=f"sub_card_{i}")

    # --- Distribución Estructural del Capital ---
    st.write("")
    st.markdown("**Distribución Estructural del Capital Estancado**")
    df_tree = df_filtrado[df_filtrado["Valor_Economico"] > 0]
    
    if not df_tree.empty:
        fig = px.treemap(
            df_tree,
            path=['Category', 'Subcategory', 'Product_name'],
            values='Valor_Economico',
            color='Percentage',
            color_continuous_scale='RdYlGn_r',
            color_continuous_midpoint=100
        )
        fig.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=350)
        st.plotly_chart(fig, use_container_width=True)

    # --- Tablas de Datos con Formato Corporativo Avanzado ---
    st.write("")
    tab1, tab2 = st.tabs(["Productos en Umbral Crítico", "Baja Rotación Prolongada"])
    
    with tab1:
        df_criticos = df_filtrado[df_filtrado["Overstock_critico"] == True].sort_values(by="Valor_Economico", ascending=False)
        col_criticos = ["Category", "Subcategory", "Product_name", "Stock", "Units_expected", "Percentage", "Valor_Economico"]
        
        st.dataframe(
            df_criticos[col_criticos].head(8), 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Category": "Categoría", "Subcategory": "Subcategoría", "Product_name": "Producto",
                "Stock": st.column_config.NumberColumn("Stock Real", format="%d"),
                "Units_expected": st.column_config.NumberColumn("Stock Ideal", format="%d"),
                "Percentage": st.column_config.NumberColumn("Porcentaje", format="%.1f%%"),
                "Valor_Economico": st.column_config.NumberColumn("Capital Inmovilizado", format="$%,.2f")
            }
        )
        
    with tab2:
        df_rotacion = df_filtrado.sort_values(by="Days_inventory", ascending=False)
        col_rotacion = ["Category", "Subcategory", "Product_name", "Stock", "Days_inventory", "Stock_turnover"]
        
        st.dataframe(
            df_rotacion[col_rotacion].head(8), 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Category": "Categoría", "Subcategory": "Subcategoría", "Product_name": "Producto",
                "Stock": st.column_config.NumberColumn("Stock Real", format="%d"),
                "Days_inventory": st.column_config.NumberColumn("Días Estancado", format="%d días"),
                "Stock_turnover": st.column_config.NumberColumn("Rotación", format="%.2f")
            }
        )

    # --- Gráficas Base ---
    st.write("")
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("**Brecha Operativa (Stock Real vs Esperado)**")
        df_brecha = df_filtrado.groupby(eje_agrupacion)[["Stock", "Units_expected"]].sum()
        st.bar_chart(df_brecha, color=["#ef4444", "#3b82f6"])
        
    with col_g2:
        st.markdown("**Comportamiento de Acumulación Histórica**")
        df_filtrado["Date"] = pd.to_datetime(df_filtrado["Date"])
        df_tiempo = df_filtrado.groupby("Date")["Stock"].sum().sort_index()
        st.area_chart(df_tiempo, color="#f59e0b")