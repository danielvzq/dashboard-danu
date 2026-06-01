# pages/3_Alertas.py
import streamlit as st
import pandas as pd
import streamlit_shadcn_ui as ui
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Centro de Alertas", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    h1, h2, h3 { font-weight: 700 !important; color: #1e293b; }

    /* ---- Centrado de st.metric ---- */
    [data-testid="stMetric"] { display: flex !important; flex-direction: column !important; align-items: center !important; }
    [data-testid="stMetricLabel"] { display: flex !important; justify-content: center !important; width: 100% !important; }
    [data-testid="stMetricValue"] { display: flex !important; justify-content: center !important; font-size: 1.6rem !important; font-weight: 700 !important; width: 100% !important; }
    [data-testid="stMetricDelta"] { display: flex !important; justify-content: center !important; width: 100% !important; }

    /* ---- Wrapper externo de Tarjetas Generales ---- */
    .card-wrapper {
        border-radius: 14px;
        padding: 2px;
        margin-bottom: 1.5rem;
        background: #e2e8f0;
        transition: background 0.35s ease, box-shadow 0.35s ease, transform 0.35s ease;
    }
    .card-wrapper:hover {
        box-shadow: 0 18px 32px rgba(0,0,0,0.12);
        transform: translateY(-10px);
    }
    .card-wrapper.border-healthy:hover  { background: #10b981; box-shadow: 0 20px 35px rgba(16,185,129,0.30); }
    .card-wrapper.border-warning:hover  { background: #f59e0b; box-shadow: 0 20px 35px rgba(245,158,11,0.30); }
    .card-wrapper.border-critical:hover { background: #ef4444; box-shadow: 0 20px 35px rgba(239,68,68,0.30); }

    /* ---- Inner ---- */
    .card-inner {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 12px;
        overflow: hidden;
        transition: background 0.35s ease;
    }
    .card-wrapper:hover .card-inner {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    }

    /* ---- Tarjeta interior ---- */
    .executive-card {
        padding: 22px 22px 18px 22px;
        display: flex;
        flex-direction: column;
        gap: 16px;
    }

    /* ---- Header azul con shimmer ---- */
    .card-header {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        padding: 11px 14px;
        border-radius: 8px;
        position: relative;
        overflow: hidden;
    }
    .card-header::before {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.28), transparent);
        animation: shimmer 2.4s infinite;
    }
    @keyframes shimmer { 0% { left: -100%; } 100% { left: 100%; } }
    .card-header h3 {
        font-size: 1.05rem; font-weight: 700; color: #fff;
        margin: 0; text-align: center; position: relative; z-index: 1;
    }

    /* ---- Grid de metricas ---- */
    .card-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
    .metric-item {
        background: linear-gradient(135deg, #f0f4f8 0%, #e8eef7 100%);
        padding: 11px 12px;
        border-radius: 8px;
        border-left: 4px solid #2563eb;
        transition: transform 0.3s ease, background 0.3s ease;
    }
    .card-wrapper:hover .metric-item {
        background: linear-gradient(135deg, #e0e9f8 0%, #d4e1f5 100%);
        transform: translateX(3px);
    }
    .metric-label  { font-size: 0.72rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 3px; }
    .metric-value  { font-size: 1.45rem; font-weight: 700; color: #1e293b; }
    .delta-value   { font-size: 0.82rem; font-weight: 600; margin-top: 3px; }
    .delta-positive { color: #ef4444; }
    .delta-negative { color: #10b981; }
    .action-label  { font-size: 0.72rem; color: #2563eb; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 3px; }

    /* ---- Area del boton ---- */
    .card-btn-area { padding: 0 16px 16px 16px; }

    /* ---- Boton Analizar ---- */
    [data-testid="stButton"] button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        width: 100% !important;
        padding: 10px 16px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 8px rgba(37,99,235,0.30) !important;
        color: white !important;
        font-size: 0.95rem !important;
    }
    [data-testid="stButton"] button:hover {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        box-shadow: 0 6px 16px rgba(37,99,235,0.50) !important;
        transform: translateY(-1px) !important;
    }
    [data-testid="stButton"] button p,
    [data-testid="stButton"] button span { color: white !important; margin: 0 !important; }

    /* ---- Hero unificado y estricto (Evita los brincos de tamaño) ---- */
    .hero-section {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 60%, #1e3a8a 100%);
        border-radius: 16px;
        height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .hero-section::before {
        content: ''; position: absolute; top: -60px; right: -60px; width: 240px; height: 240px;
        background: radial-gradient(circle, rgba(37,99,235,0.35) 0%, transparent 70%); border-radius: 50%;
    }
    .hero-section::after {
        content: ''; position: absolute; bottom: -40px; left: -40px; width: 180px; height: 180px;
        background: radial-gradient(circle, rgba(16,185,129,0.20) 0%, transparent 70%); border-radius: 50%;
    }
    .hero-title {
        font-size: 2.4rem !important; font-weight: 800 !important; color: #ffffff !important; margin: 0 0 12px 0 !important; line-height: 1.2; z-index: 1; text-align: center !important;
    }
    .hero-subtitle {
        font-size: 1.05rem; color: #94a3b8; max-width: 550px; line-height: 1.5; z-index: 1; text-align: center;
    }
    .hero-divider {
        width: 60px; height: 3px; background: linear-gradient(90deg, #2563eb, #10b981); border-radius: 2px; margin-top: 18px; z-index: 1;
    }

    /* ---- Títulos de Sección (Blue Theme) ---- */
    .section-title {
        color: #1e3a8a !important;
        border-left: 4px solid #2563eb;
        padding-left: 14px;
        font-size: 1.25rem !important;
        font-weight: 800 !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1.2rem !important;
        background: linear-gradient(90deg, #eff6ff 0%, transparent 100%);
        padding-top: 8px;
        padding-bottom: 8px;
        border-radius: 0 8px 8px 0;
    }
    </style>
""", unsafe_allow_html=True)

# ---- Datos ----
@st.cache_data
def cargar_y_limpiar_datos():
    df = pd.read_csv("data/df_Maestra.csv")
    df["Region"]       = df["Region"].astype(str).str.strip().str.title()
    df["Category"]     = df["Category"].astype(str).str.strip().str.title()
    df["Subcategory"]  = df["Subcategory"].astype(str).str.strip().str.title()
    df["Product_name"] = df["Product_name"].astype(str).str.strip()
    df["Overstock_critico"] = df["Overstock_critico"].astype(str).str.upper() == "TRUE"
    df["Valor_Economico"]   = df["Stock"] * df["Static_price"]
    
    if "Priority_action" in df.columns:
        df["Priority_action"] = df["Priority_action"].astype(str).str.replace("OFF", "A REDUCIR", regex=False)
    
    df["Exceso_Porcentual"] = df["Percentage"] - 100.0
        
    return df

try:
    df_base = cargar_y_limpiar_datos()
except FileNotFoundError:
    st.error("No se encontro 'df_Maestra.csv' en la carpeta 'data/'.")
    st.stop()

if "zona_activa" not in st.session_state:
    st.session_state.zona_activa = "General"


# ==========================================
# VISTA GENERAL
# ==========================================
if st.session_state.zona_activa == "General":

    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">Centro de Alertas Estrategicas</h1>
        <div class="hero-subtitle">
            Monitoreo en tiempo real del estado de inventario por zona geografica.<br>
            Selecciona una region para profundizar en el analisis operativo.
        </div>
        <div class="hero-divider"></div>
    </div>
    """, unsafe_allow_html=True)

    resumen_regiones = df_base.groupby("Region").agg({
        "Percentage":        "mean",
        "Valor_Economico":   "sum",
        "Stock_turnover":    "mean" 
    }).reset_index()

    num_cols = 3
    for i in range(0, len(resumen_regiones), num_cols):
        cols = st.columns(num_cols, gap="medium")
        for j in range(num_cols):
            if i + j < len(resumen_regiones):
                row      = resumen_regiones.iloc[i + j]
                reg      = row["Region"]
                pct      = row["Percentage"]
                rotacion = row["Stock_turnover"] 

                exceso_pct = pct - 100.0

                if exceso_pct >= 25:
                    border_class = "border-critical"
                    estado = "Muy Critico"
                elif exceso_pct > 0:
                    border_class = "border-warning"
                    estado = "Critico"
                else:
                    border_class = "border-healthy"
                    estado = "Saludable"

                delta_class = "delta-positive" if exceso_pct > 0 else "delta-negative"
                sign        = "+" if exceso_pct > 0 else ""

                with cols[j]:
                    st.markdown(f"""
                    <div class="card-wrapper {border_class}">
                        <div class="card-inner">
                            <div class="executive-card">
                                <div class="card-header">
                                    <h3>{reg}</h3>
                                </div>
                                <div class="card-metrics">
                                    <div class="metric-item">
                                        <div class="metric-label">Sobrestock</div>
                                        <div class="metric-value">{pct:.1f}%</div>
                                        <div class="delta-value {delta_class}">{sign}{exceso_pct:.1f}% vs ideal</div>
                                    </div>
                                    <div class="metric-item">
                                        <div class="metric-label">Rotacion Prom.</div>
                                        <div class="metric-value">{rotacion:.2f}x</div>
                                        <div class="action-label" style="color: {'#ef4444' if exceso_pct > 0 else '#10b981'}">{estado}</div>
                                    </div>
                                </div>
                            </div>
                            <div class="card-btn-area"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("Analizar", key=f"nav_{reg}", use_container_width=True):
                        st.session_state.zona_activa = reg
                        st.rerun()


# ==========================================
# VISTA DETALLADA (DRILL-DOWN)
# ==========================================
else:
    zona_sel = st.session_state.zona_activa

    st.markdown(f"""
    <div class="hero-section">
        <h1 class="hero-title">Alertas Operativas: {zona_sel}</h1>
        <div class="hero-subtitle">
            Analisis granular de inventarios, brechas de planeacion y rotacion.<br>
            Vista detallada por categoria y producto.
        </div>
        <div class="hero-divider"></div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Volver al Resumen", type="secondary"):
        st.session_state.zona_activa = "General"
        st.rerun()

    st.write("")

    df_zona = df_base[df_base["Region"] == zona_sel]

    # --- SIDEBAR (FILTROS Y CONTROLES) ---
    with st.sidebar:
        st.markdown("### Filtros de Análisis")
        cat_options   = ["Todas las Categorias"] + sorted(df_zona["Category"].unique().tolist())
        categoria_sel = st.selectbox("Categoria", cat_options)

        df_filtrado = df_zona.copy()
        if categoria_sel != "Todas las Categorias":
            df_filtrado = df_filtrado[df_filtrado["Category"] == categoria_sel]

        sub_options      = ["Todas las Subcategorias"] + sorted(df_filtrado["Subcategory"].unique().tolist())
        subcategoria_sel = st.selectbox("Subcategoria", sub_options)

        if subcategoria_sel != "Todas las Subcategorias":
            df_filtrado = df_filtrado[df_filtrado["Subcategory"] == subcategoria_sel]

        st.divider()
        st.markdown("### Configuración de Tablas")
        top_n = st.slider("Cantidad de productos (Top N):", min_value=1, max_value=50, value=4, step=1)

    # --- KPI CARDS AZULES ("Above the fold") ---
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    
    with col_kpi1:
        capital_riesgo = df_filtrado.loc[df_filtrado["Overstock_critico"] == True, "Valor_Economico"].sum()
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 1px solid #bfdbfe; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.02); height: 100%;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #1d4ed8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">Capital en Riesgo</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #0f172a;">${capital_riesgo:,.2f}</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">Valor inmovilizado en sobrestock crítico</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_kpi2:
        criticos_activos = df_filtrado[df_filtrado["Overstock_critico"] == True].shape[0]
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 1px solid #bfdbfe; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.02); height: 100%;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #1d4ed8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">Alertas Críticas Activas</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #0f172a;">{criticos_activos}</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">Productos urgentes a reducir</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_kpi3:
        max_dias = df_filtrado["Days_inventory"].max() if not df_filtrado.empty else 0
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 1px solid #bfdbfe; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.02); height: 100%;">
            <div style="font-size: 0.85rem; font-weight: 700; color: #1d4ed8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;">Permanencia Máxima</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #0f172a;">{max_dias:.0f} días</div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 4px;">Peor registro de estancamiento</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    eje_agrupacion = "Category" if categoria_sel == "Todas las Categorias" else "Subcategory"
    
    resumen_semaforo = df_filtrado.groupby(eje_agrupacion).agg(
        Stock_Total=("Stock", "sum"),
        Expected_Total=("Units_expected", "sum")
    ).reset_index()
    
    resumen_semaforo["Exceso_Real"] = (resumen_semaforo["Stock_Total"] / resumen_semaforo["Expected_Total"] * 100) - 100.0

    st.markdown(f'<div class="section-title">Nivel de Exceso Actual por {eje_agrupacion}</div>', unsafe_allow_html=True)
    
    cols_sem = st.columns(min(len(resumen_semaforo), 4) if len(resumen_semaforo) > 0 else 1)

    for i, row in enumerate(resumen_semaforo.itertuples()):
        exceso = row.Exceso_Real
        nombre = getattr(row, eje_agrupacion)
        
        if exceso >= 25:
            estado = "Muy Crítico"
            color_hex = "#dc2626"
            bg_hex = "#fef2f2"
        elif exceso > 0:
            estado = "Crítico"
            color_hex = "#f59e0b"
            bg_hex = "#fffbeb"
        else:
            estado = "Saludable"
            color_hex = "#10b981"
            bg_hex = "#f0fdf4"

        signo = "+" if exceso > 0 else ""
        
        with cols_sem[i % 4]:
            st.markdown(f"""
            <div style="background: {bg_hex}; border-top: 4px solid {color_hex}; border-radius: 8px; padding: 16px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <div style="font-size: 0.85rem; font-weight: 600; color: #475569;">{nombre}</div>
                <div style="font-size: 1.5rem; font-weight: 800; color: #1e293b; margin: 4px 0;">{signo}{exceso:.1f}%</div>
                <div style="font-size: 0.75rem; font-weight: 700; color: {color_hex}; text-transform: uppercase;">{estado}</div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")
    
    # --- GRÁFICAS ("Above the fold") ---
    st.markdown('<div class="section-title">Distribución Estructural del Capital Estancado</div>', unsafe_allow_html=True)

    df_tree = df_filtrado[df_filtrado["Valor_Economico"] > 0].copy()

    if not df_tree.empty:
        df_tree["Inventario"] = "Inventario Global"
        
        if categoria_sel == "Todas las Categorias":
            ruta_treemap = ['Inventario', 'Category', 'Subcategory', 'Product_name']
        elif subcategoria_sel == "Todas las Subcategorias":
            ruta_treemap = ['Category', 'Subcategory', 'Product_name']
        else:
            ruta_treemap = ['Subcategory', 'Product_name']

        fig_tree = px.treemap(
            df_tree,
            path=ruta_treemap,
            values='Valor_Economico',
            color='Exceso_Porcentual', 
            color_continuous_scale='RdYlGn_r',
            color_continuous_midpoint=0 
        )
        
        fig_tree.update_traces(
            maxdepth=2, 
            textinfo="label+value",
            texttemplate='<b>%{label}</b><br>$%{value:,.0f}',
            hovertemplate='<b>%{label}</b><br>Capital: $%{value:,.2f}<br>Exceso: %{color:.1f}%'
        )
        
        fig_tree.update_layout(margin=dict(t=20, l=10, r=10, b=10), height=420)
        st.plotly_chart(fig_tree, use_container_width=True)
        
        st.markdown("<div style='text-align: center; color: #64748b; font-size: 0.85rem; margin-top: 8px;'><strong>Tip Interactivo:</strong> Haz clic en los bloques para hacer 'Zoom In' por nivel. La gráfica se adapta automáticamente a tus filtros en la barra lateral.</div>", unsafe_allow_html=True)

    st.write("")
    
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown('<div class="section-title">Brecha Operativa (Stock Real vs Esperado)</div>', unsafe_allow_html=True)
        df_brecha = df_filtrado.groupby(eje_agrupacion)[["Stock", "Units_expected"]].sum().reset_index()
        
        df_melted = df_brecha.melt(
            id_vars=eje_agrupacion, 
            value_vars=["Stock", "Units_expected"], 
            var_name="Tipo", 
            value_name="Unidades"
        )
        
        df_melted["Tipo"] = df_melted["Tipo"].replace({"Stock": "Stock Real (Bodega)", "Units_expected": "Stock Esperado (Planeación)"})
        
        fig_brecha = px.bar(
            df_melted, 
            x=eje_agrupacion, 
            y="Unidades", 
            color="Tipo", 
            barmode="group", 
            color_discrete_map={"Stock Real (Bodega)": "#ef4444", "Stock Esperado (Planeación)": "#3b82f6"}
        )
        fig_brecha.update_layout(
            margin=dict(t=10, l=10, r=10, b=10),
            height=380,
            legend_title_text="",
            xaxis_title=eje_agrupacion,
            yaxis_title="Cantidad de Unidades",
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1)
        )
        st.plotly_chart(fig_brecha, use_container_width=True)
        st.markdown("<div style='text-align: center; color: #64748b; font-size: 0.85rem; margin-top: 8px;'>Comparativa directa entre la cantidad física en bodega y lo proyectado inicialmente.</div>", unsafe_allow_html=True)

    with col_g2:
        st.markdown('<div class="section-title">Exceso de Stock por Periodo</div>', unsafe_allow_html=True)

        df_filtrado["Date"] = pd.to_datetime(df_filtrado["Date"])
        df_tiempo = df_filtrado.groupby("Date").agg(
            Stock=("Stock", "sum"),
            Units_expected=("Units_expected", "sum"),
            Units_sold=("Units_sold", "sum")
        ).reset_index().sort_values("Date")
        df_tiempo["Exceso_Unidades"] = df_tiempo["Stock"] - df_tiempo["Units_expected"]
        df_tiempo["Exceso_Positivo"] = df_tiempo["Exceso_Unidades"].clip(lower=0)

        fig_exceso = go.Figure()

        fig_exceso.add_trace(go.Bar(
            x=df_tiempo["Date"],
            y=df_tiempo["Exceso_Positivo"],
            name="Exceso de Stock",
            marker_color="rgba(239,68,68,0.75)",
            hovertemplate="%{x|%b %Y}<br>Exceso: %{y:,.0f} uds<extra></extra>"
        ))

        fig_exceso.add_trace(go.Scatter(
            x=df_tiempo["Date"],
            y=df_tiempo["Units_sold"],
            name="Unidades Vendidas",
            mode="lines+markers",
            line=dict(color="#10b981", width=2, dash="dot"),
            marker=dict(size=5),
            hovertemplate="%{x|%b %Y}<br>Ventas: %{y:,.0f} uds<extra></extra>"
        ))

        fig_exceso.update_layout(
            barmode="overlay",
            margin=dict(t=10, l=10, r=10, b=10),
            height=380,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#e2e8f0", title="Unidades"),
            xaxis=dict(title=""),
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1)
        )
        st.plotly_chart(fig_exceso, use_container_width=True)
        st.markdown("<div style='text-align: center; color: #64748b; font-size: 0.85rem; margin-top: 8px;'>Unidades en exceso acumuladas respecto al nivel planeado.</div>", unsafe_allow_html=True)

    st.write("")
    
    # --- TABLAS DE DATOS CRUDOS ("Below the fold") ---
    st.markdown('<div class="section-title">Reportes de Datos Crudos</div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["Productos en Umbral Crítico", "Baja Rotación Prolongada", "Más Crítico por Categoría"])

    with tab1:
        df_criticos  = df_filtrado[df_filtrado["Overstock_critico"] == True].sort_values(by="Exceso_Porcentual", ascending=False)
        col_criticos = ["Category", "Subcategory", "Product_name", "Stock", "Units_expected", "Exceso_Porcentual", "Units_sold", "Stock_turnover", "Priority_action"]
        col_criticos = [col for col in col_criticos if col in df_criticos.columns]
        
        st.dataframe(
            df_criticos[col_criticos].head(top_n),
            use_container_width=True, hide_index=True,
            column_config={
                "Category": "Categoria", "Subcategory": "Subcategoria", "Product_name": "Producto",
                "Stock":           st.column_config.NumberColumn("Stock Actual", format="%d"),
                "Units_expected":  st.column_config.NumberColumn("Stock Planeado", format="%d"),
                "Exceso_Porcentual": st.column_config.NumberColumn("Exceso (%)", format="%.1f%%"),
                "Units_sold":      st.column_config.NumberColumn("Ventas", format="%d"),
                "Stock_turnover":  st.column_config.NumberColumn("Rotación", format="%.2fx"),
                "Priority_action": "Acción Recomendada" 
            }
        )

    with tab2:
        df_rotacion  = df_filtrado.sort_values(by="Days_inventory", ascending=False)
        col_rotacion = ["Category", "Subcategory", "Product_name", "Stock", "Days_inventory", "Units_sold", "Stock_turnover"]
        col_rotacion = [col for col in col_rotacion if col in df_rotacion.columns]
        
        st.dataframe(
            df_rotacion[col_rotacion].head(top_n),
            use_container_width=True, hide_index=True,
            column_config={
                "Category": "Categoria", "Subcategory": "Subcategoria", "Product_name": "Producto",
                "Stock":          st.column_config.NumberColumn("Stock Real", format="%d"),
                "Days_inventory": st.column_config.NumberColumn("Dias Estancado", format="%d dias"),
                "Units_sold":     st.column_config.NumberColumn("Ventas", format="%d"),
                "Stock_turnover": st.column_config.NumberColumn("Rotacion", format="%.2fx"),
            }
        )
        
    with tab3:
        if not df_filtrado.empty:
            idx_top = df_filtrado.groupby("Category")["Exceso_Porcentual"].idxmax()
            df_top_cat = df_filtrado.loc[idx_top].sort_values(by="Exceso_Porcentual", ascending=False)
            
            col_top = ["Category", "Product_name", "Stock", "Units_expected", "Exceso_Porcentual", "Days_inventory", "Stock_turnover", "Priority_action"]
            col_top = [col for col in col_top if col in df_top_cat.columns]
            
            st.dataframe(
                df_top_cat[col_top],
                use_container_width=True, hide_index=True,
                column_config={
                    "Category": "Categoria", "Product_name": "Producto Más Crítico",
                    "Stock":          st.column_config.NumberColumn("Stock Real", format="%d"),
                    "Units_expected": st.column_config.NumberColumn("Stock Planeado", format="%d"),
                    "Exceso_Porcentual": st.column_config.NumberColumn("Exceso (%)", format="%.1f%%"),
                    "Days_inventory": st.column_config.NumberColumn("Dias Estancado", format="%d dias"),
                    "Stock_turnover": st.column_config.NumberColumn("Rotacion", format="%.2fx"),
                    "Priority_action": "Acción"
                }
            )
        else:
            st.info("No hay datos suficientes para calcular los más críticos con los filtros actuales.")