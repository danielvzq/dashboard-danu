# pages/3_Alertas.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from html import escape
from urllib.parse import quote


# =========================
# Configuración de página
# =========================
st.set_page_config(
    page_title="Centro de Alertas",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================
# CSS general estilo Inicio + hover original de Alertas
# =========================
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.2rem !important;
            padding-bottom: 0.8rem !important;
            padding-left: 1.4rem !important;
            padding-right: 1.4rem !important;
            max-width: 100% !important;
        }

        h1, h2, h3 {
            margin-top: 0 !important;
            margin-bottom: 0.5rem !important;
        }

        div[data-testid="stVerticalBlock"] {
            gap: 0.65rem !important;
        }

        div[data-testid="stHorizontalBlock"] {
            gap: 0.85rem !important;
        }

        iframe {
            display: block;
        }

        /* =========================
           Sidebar armonizado
        ========================= */
        .sidebar-header {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 4px 18px 4px;
        }

        .sidebar-icon {
            width: 42px;
            height: 42px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            box-shadow: 0 10px 22px rgba(37, 99, 235, 0.22);
            font-size: 21px;
        }

        .sidebar-title {
            color: #0f172a;
            font-size: 17px;
            font-weight: 950;
            margin: 0;
            line-height: 1.05;
        }

        .sidebar-subtitle {
            color: #64748b;
            font-size: 12px;
            font-weight: 700;
            margin: 3px 0 0 0;
        }

        /* =========================
           Cards base estilo Inicio
        ========================= */
        .soft-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 24px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.035);
            overflow: hidden;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 24px !important;
            border: 1px solid rgba(148, 163, 184, 0.22) !important;
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%) !important;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.035) !important;
            padding: 0.4rem 0.65rem !important;
        }

        .chart-card-header {
            padding: 6px 8px 0 8px;
            margin-bottom: 4px;
        }

        .chart-card-header h3 {
            color: #0f172a !important;
            font-size: 20px !important;
            font-weight: 950 !important;
            margin: 0 !important;
            letter-spacing: -0.4px;
        }

        .chart-card-header p {
            color: #64748b;
            font-size: 13px;
            font-weight: 650;
            margin: 4px 0 0 0;
        }

        .section-title {
            color: #0f172a !important;
            font-size: 18px !important;
            font-weight: 950 !important;
            margin: 0 0 12px 0 !important;
            letter-spacing: -0.35px;
        }

        .section-subtitle {
            color: #64748b;
            font-size: 13px;
            font-weight: 650;
            margin: -6px 0 12px 0;
        }

        /* =========================
           KPIs superiores detalle
        ========================= */
        .metric-card {
            position: relative;
            overflow: hidden;
            min-height: 142px;
            box-sizing: border-box;
            border-radius: 24px;
            padding: 28px 22px 18px 22px;
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid rgba(148, 163, 184, 0.28);
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.035);
        }

        .metric-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 7px;
            background: var(--accent-color);
        }

        .metric-title {
            color: #0f172a;
            font-size: 14px;
            font-weight: 900;
            margin: 0 0 12px 0;
        }

        .metric-value-main {
            color: #0f172a;
            font-size: 27px;
            font-weight: 950;
            line-height: 1.05;
            margin: 0 0 8px 0;
            letter-spacing: -0.8px;
        }

        .metric-description {
            color: #64748b;
            font-size: 12px;
            font-weight: 700;
            margin: 0;
            line-height: 1.25;
        }

        /* =========================
           Tarjetas regionales con hover original
           Se mantienen colores: verde / naranja / rojo
        ========================= */
        .card-wrapper {
            border-radius: 24px;
            padding: 2px;
            margin-bottom: 0.7rem;
            background: rgba(148, 163, 184, 0.25);
            transition: background 0.35s ease, box-shadow 0.35s ease, transform 0.35s ease;
            min-height: 190px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.035);
        }

        .card-wrapper:hover {
            transform: translateY(-5px);
        }

        .card-wrapper.border-healthy:hover {
            background: #10b981;
            box-shadow: 0 16px 28px rgba(16, 185, 129, 0.30);
        }

        .card-wrapper.border-warning:hover {
            background: #f59e0b;
            box-shadow: 0 16px 28px rgba(245, 158, 11, 0.30);
        }

        .card-wrapper.border-critical:hover {
            background: #ef4444;
            box-shadow: 0 16px 28px rgba(239, 68, 68, 0.30);
        }

        .card-inner {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border-radius: 22px;
            overflow: hidden;
            transition: background 0.35s ease;
            height: 100%;
            min-height: 190px;
            display: flex;
            flex-direction: column;
        }

        .card-wrapper:hover .card-inner {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        }

        .executive-card {
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            height: 100%;
            justify-content: space-between;
        }

        .card-header {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            padding: 8px 12px;
            border-radius: 16px;
            position: relative;
            overflow: hidden;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .card-header::before {
            content: "";
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.28), transparent);
            animation: shimmer 2.4s infinite;
        }

        @keyframes shimmer {
            0% { left: -100%; }
            100% { left: 100%; }
        }

        .card-header h3 {
            font-size: 0.92rem !important;
            font-weight: 850 !important;
            color: #ffffff !important;
            margin: 0 !important;
            text-align: center;
            position: relative;
            z-index: 1;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            line-height: 1.1;
        }

        .card-metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }

        .metric-item {
            background: rgba(255, 255, 255, 0.85);
            padding: 10px 12px;
            border-radius: 16px;
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-left: 4px solid #2563eb;
            transition: transform 0.3s ease, background 0.3s ease;
        }

        .card-wrapper:hover .metric-item {
            background: rgba(248, 250, 252, 0.96);
            transform: translateX(3px);
        }

        .metric-label {
            font-size: 0.68rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 800;
            margin-bottom: 3px;
        }

        .metric-value {
            font-size: 1.25rem;
            font-weight: 950;
            color: #0f172a;
            line-height: 1.05;
        }

        .delta-value {
            font-size: 0.76rem;
            font-weight: 750;
            margin-top: 3px;
        }

        .delta-positive { color: #ef4444; }
        .delta-negative { color: #10b981; }

        .action-label {
            font-size: 0.68rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 3px;
        }

        .card-btn-area {
            padding: 0 14px 14px 14px;
        }

        /* Botones */
        [data-testid="stButton"] button {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
            border: none !important;
            border-radius: 14px !important;
            font-weight: 800 !important;
            width: 100% !important;
            padding: 8px 14px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 5px 14px rgba(37, 99, 235, 0.22) !important;
            color: white !important;
            font-size: 0.9rem !important;
        }

        [data-testid="stButton"] button:hover {
            background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
            box-shadow: 0 8px 18px rgba(37, 99, 235, 0.34) !important;
            transform: translateY(-1px) !important;
        }

        [data-testid="stButton"] button p,
        [data-testid="stButton"] button span {
            color: white !important;
            margin: 0 !important;
        }

        /* Semáforo detalle */
        .traffic-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid rgba(148, 163, 184, 0.22);
            border-radius: 22px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.035);
            margin-bottom: 14px;
            position: relative;
            overflow: hidden;
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }

        .traffic-card::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 6px;
            background: var(--status-color);
        }

        .traffic-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
        }

        .traffic-name {
            font-size: 0.85rem;
            font-weight: 800;
            color: #475569;
            margin: 4px 0 8px 0;
        }

        .traffic-value {
            font-size: 1.45rem;
            font-weight: 950;
            color: #0f172a;
            margin: 0 0 6px 0;
            letter-spacing: -0.5px;
        }

        .traffic-status {
            font-size: 0.72rem;
            font-weight: 900;
            text-transform: uppercase;
            color: var(--status-color);
        }
    
        /* =========================
           Botón integrado en tarjetas de región
        ========================= */
        .card-wrapper {
            min-height: 250px !important;
            border-radius: 24px !important;
        }

        .card-inner {
            min-height: 250px !important;
            border-radius: 22px !important;
        }

        .executive-card {
            padding: 16px 16px 10px 16px !important;
            height: auto !important;
            flex: 1 1 auto;
        }

        .card-btn-area {
            padding: 0 16px 16px 16px !important;
        }

        .analyze-link {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            min-height: 42px;
            box-sizing: border-box;
            border-radius: 14px;
            text-decoration: none !important;
            font-size: 0.92rem;
            font-weight: 850;
            color: #0f172a !important;
            background: #ffffff;
            border: 1px solid rgba(148, 163, 184, 0.40);
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.055);
            transition: all 0.25s ease;
        }

        .analyze-link:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 24px rgba(15, 23, 42, 0.12);
        }

        .card-wrapper.border-healthy:hover .analyze-link {
            color: #047857 !important;
            background: #ecfdf5;
            border-color: #10b981;
            box-shadow: 0 12px 24px rgba(16, 185, 129, 0.20);
        }

        .card-wrapper.border-warning:hover .analyze-link {
            color: #b45309 !important;
            background: #fffbeb;
            border-color: #f59e0b;
            box-shadow: 0 12px 24px rgba(245, 158, 11, 0.20);
        }

        .card-wrapper.border-critical:hover .analyze-link {
            color: #b91c1c !important;
            background: #fef2f2;
            border-color: #ef4444;
            box-shadow: 0 12px 24px rgba(239, 68, 68, 0.20);
        }
</style>
    """,
    unsafe_allow_html=True
)


# =========================
# Cargar CSS externo si existe
# =========================
css_path = Path("styles/main.css")
if css_path.exists():
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# =========================
# Funciones auxiliares
# =========================
def formato_pesos(valor):
    try:
        return f"${float(valor):,.0f}"
    except Exception:
        return "$0"


def compact_metric_card(title, value, description, accent_color):
    return f"""
    <div class="metric-card" style="--accent-color: {accent_color};">
        <p class="metric-title">{escape(str(title))}</p>
        <p class="metric-value-main">{escape(str(value))}</p>
        <p class="metric-description">{escape(str(description))}</p>
    </div>
    """


def render_chart_header(title, subtitle):
    st.markdown(
        f"""
        <div class="chart-card-header">
            <h3>{escape(str(title))}</h3>
            <p>{escape(str(subtitle))}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_sidebar_base():
    st.markdown(
        """
        <div class="sidebar-header">
            <div class="sidebar-icon">🚀</div>
            <div>
                <p class="sidebar-title">RocketData</p>
                <p class="sidebar-subtitle">Inventory Dashboard</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.page_link("Inicio.py", label="Inicio")
    st.page_link("pages/1_Inventario.py", label="Inventario")
    st.page_link("pages/2_Ventas.py", label="Ventas")
    st.page_link("pages/3_Alertas.py", label="Alertas")
    st.page_link("pages/4_Pronosticos.py", label="Pronósticos")
    st.divider()


# =========================
# Datos
# =========================
@st.cache_data
def cargar_y_limpiar_datos():
    df = pd.read_csv("data/df_Maestra.csv")

    df.columns = df.columns.str.strip()

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    df["Region"] = df["Region"].astype(str).str.strip().str.title()
    df["Category"] = df["Category"].astype(str).str.strip().str.title()
    df["Subcategory"] = df["Subcategory"].astype(str).str.strip().str.title()
    df["Product_name"] = df["Product_name"].astype(str).str.strip()

    df["Overstock_critico"] = (
        df["Overstock_critico"]
        .astype(str)
        .str.lower()
        .map({"true": True, "false": False, "1": True, "0": False})
        .fillna(False)
    )

    for col in ["Stock", "Static_price", "Percentage", "Units_expected", "Units_sold", "Stock_turnover", "Days_inventory"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["Valor_Economico"] = df["Stock"] * df["Static_price"]

    if "Priority_action" in df.columns:
        df["Priority_action"] = (
            df["Priority_action"]
            .astype(str)
            .str.replace("OFF", "A REDUCIR", regex=False)
        )

    df["Exceso_Porcentual"] = df["Percentage"] - 100.0

    return df


try:
    df_base = cargar_y_limpiar_datos()
except FileNotFoundError:
    st.error("No se encontró 'df_Maestra.csv' en la carpeta 'data/'.")
    st.stop()


if "zona_activa" not in st.session_state:
    st.session_state.zona_activa = "General"

# Permite abrir el detalle desde un botón HTML integrado a la tarjeta
zona_query = st.query_params.get("zona")
if zona_query:
    st.session_state.zona_activa = str(zona_query)


# =========================
# Sidebar base
# =========================
with st.sidebar:
    render_sidebar_base()


# ==========================================
# Vista general
# ==========================================
if st.session_state.zona_activa == "General":

    st.markdown(
        """
        <div class="page-hero">
            <h1>Centro de Alertas Estratégicas</h1>
            <p>Monitorea regiones con sobrestock, baja rotación y capital inmovilizado.</p>
            <div class="hero-divider"></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    resumen_regiones = (
        df_base
        .groupby("Region", as_index=False)
        .agg({
            "Percentage": "mean",
            "Valor_Economico": "sum",
            "Stock_turnover": "mean"
        })
    )

    st.markdown('<div class="section-title">Resumen ejecutivo por región</div>', unsafe_allow_html=True)

    num_cols = 4
    for i in range(0, len(resumen_regiones), num_cols):
        cols = st.columns(num_cols, gap="small")

        for j in range(num_cols):
            if i + j >= len(resumen_regiones):
                continue

            row = resumen_regiones.iloc[i + j]
            reg = row["Region"]
            pct = row["Percentage"]
            rotacion = row["Stock_turnover"]
            exceso_pct = pct - 100.0

            if exceso_pct >= 25:
                border_class = "border-critical"
                estado = "Muy Crítico"
            elif exceso_pct > 0:
                border_class = "border-warning"
                estado = "Crítico"
            else:
                border_class = "border-healthy"
                estado = "Saludable"

            delta_class = "delta-positive" if exceso_pct > 0 else "delta-negative"
            sign = "+" if exceso_pct > 0 else ""
            action_color = "#ef4444" if exceso_pct > 0 else "#10b981"
            reg_url = quote(str(reg), safe="")

            with cols[j]:
                st.markdown(
                    f"""
                    <div class="card-wrapper {border_class}">
                        <div class="card-inner">
                            <div class="executive-card">
                                <div class="card-header">
                                    <h3>{escape(str(reg))}</h3>
                                </div>
                                <div class="card-metrics">
                                    <div class="metric-item">
                                        <div class="metric-label">Sobrestock</div>
                                        <div class="metric-value">{pct:.1f}%</div>
                                        <div class="delta-value {delta_class}">{sign}{exceso_pct:.1f}% vs ideal</div>
                                    </div>
                                    <div class="metric-item">
                                        <div class="metric-label">Rotación Prom.</div>
                                        <div class="metric-value">{rotacion:.2f}x</div>
                                        <div class="action-label" style="color: {action_color};">{estado}</div>
                                    </div>
                                </div>
                            </div>
                            <div class="card-btn-area">
                                <a class="analyze-link" href="?zona={reg_url}" target="_self">
                                    Analizar región
                                </a>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )


# ==========================================
# Vista detallada
# ==========================================
else:
    zona_sel = st.session_state.zona_activa

    st.markdown(
        f"""
        <div class="page-hero">
            <h1>Alertas Operativas: {escape(str(zona_sel))}</h1>
            <p>Detalle de exceso, capital estancado y productos críticos por categoría.</p>
            <div class="hero-divider"></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_back, col_space = st.columns([1, 5])
    with col_back:
        if st.button("Volver al resumen", type="secondary", use_container_width=True):
            st.query_params.clear()
            st.session_state.zona_activa = "General"
            st.rerun()

    df_zona = df_base[df_base["Region"] == zona_sel].copy()

    # --- Sidebar filtros detalle ---
    with st.sidebar:
        st.markdown("### Filtros")

        cat_options = ["Todas"] + sorted(df_zona["Category"].dropna().unique().tolist())
        categoria_sel = st.selectbox("Categoría", cat_options)

        df_filtrado = df_zona.copy()
        if categoria_sel != "Todas":
            df_filtrado = df_filtrado[df_filtrado["Category"] == categoria_sel]

        sub_options = ["Todas"] + sorted(df_filtrado["Subcategory"].dropna().unique().tolist())
        subcategoria_sel = st.selectbox("Subcategoría", sub_options)

        if subcategoria_sel != "Todas":
            df_filtrado = df_filtrado[df_filtrado["Subcategory"] == subcategoria_sel]

        st.divider()
        st.markdown("### Configuración de tablas")
        top_n = st.slider("Cantidad de productos (Top N)", min_value=1, max_value=50, value=4, step=1)

    eje_agrupacion = "Category" if categoria_sel == "Todas" else "Subcategory"
    plot_config = {"responsive": True, "displayModeBar": False}

    tab_tarjetas, tab_mapa, tab_graficas, tab_tablas = st.tabs([
        "Niveles de Exceso",
        "Mapa Estructural",
        "Comparativas y Tendencias",
        "Reportes Detallados"
    ])

    # --- Pestaña 1 ---
    with tab_tarjetas:
        capital_riesgo = df_filtrado.loc[df_filtrado["Overstock_critico"] == True, "Valor_Economico"].sum()
        criticos_activos = df_filtrado[df_filtrado["Overstock_critico"] == True].shape[0]
        max_dias = df_filtrado["Days_inventory"].max() if not df_filtrado.empty else 0

        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

        with col_kpi1:
            st.markdown(
                compact_metric_card(
                    "Capital en Riesgo",
                    formato_pesos(capital_riesgo),
                    "Valor inmovilizado en sobrestock crítico",
                    "#dc2626"
                ),
                unsafe_allow_html=True
            )

        with col_kpi2:
            st.markdown(
                compact_metric_card(
                    "Alertas Críticas Activas",
                    f"{criticos_activos:,}",
                    "Productos urgentes a reducir",
                    "#f59e0b"
                ),
                unsafe_allow_html=True
            )

        with col_kpi3:
            st.markdown(
                compact_metric_card(
                    "Permanencia Máxima",
                    f"{max_dias:.0f} días",
                    "Peor registro de estancamiento",
                    "#2563eb"
                ),
                unsafe_allow_html=True
            )

        st.write("")

        resumen_semaforo = (
            df_filtrado
            .groupby(eje_agrupacion, as_index=False)
            .agg(
                Stock_Total=("Stock", "sum"),
                Expected_Total=("Units_expected", "sum")
            )
        )

        resumen_semaforo["Exceso_Real"] = (
            resumen_semaforo["Stock_Total"] / resumen_semaforo["Expected_Total"].replace(0, pd.NA) * 100
        ).fillna(0) - 100.0

        st.markdown(f'<div class="section-title">Nivel de Exceso Actual por {eje_agrupacion}</div>', unsafe_allow_html=True)

        if resumen_semaforo.empty:
            st.info("No hay datos suficientes para mostrar el semáforo con los filtros actuales.")
        else:
            cols_sem = st.columns(min(len(resumen_semaforo), 4) if len(resumen_semaforo) > 0 else 1)

            for i, row in enumerate(resumen_semaforo.itertuples()):
                exceso = row.Exceso_Real
                nombre = getattr(row, eje_agrupacion)

                if exceso >= 25:
                    estado = "Muy Crítico"
                    color_hex = "#dc2626"
                elif exceso > 0:
                    estado = "Crítico"
                    color_hex = "#f59e0b"
                else:
                    estado = "Saludable"
                    color_hex = "#10b981"

                signo = "+" if exceso > 0 else ""

                with cols_sem[i % len(cols_sem)]:
                    st.markdown(
                        f"""
                        <div class="traffic-card" style="--status-color: {color_hex};">
                            <div class="traffic-name">{escape(str(nombre))}</div>
                            <div class="traffic-value">{signo}{exceso:.1f}%</div>
                            <div class="traffic-status">{estado}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    # --- Pestaña 2 ---
    with tab_mapa:
        with st.container(border=True):
            render_chart_header(
                "Distribución estructural del capital estancado",
                "El tamaño representa valor económico y el color muestra el nivel de exceso porcentual."
            )

            df_tree = df_filtrado[df_filtrado["Valor_Economico"] > 0].copy()

            if not df_tree.empty:
                df_tree["Inventario"] = "Inventario Global"

                if categoria_sel == "Todas":
                    ruta_treemap = ["Inventario", "Category", "Subcategory", "Product_name"]
                elif subcategoria_sel == "Todas":
                    ruta_treemap = ["Category", "Subcategory", "Product_name"]
                else:
                    ruta_treemap = ["Subcategory", "Product_name"]

                fig_tree = px.treemap(
                    df_tree,
                    path=ruta_treemap,
                    values="Valor_Economico",
                    color="Exceso_Porcentual",
                    color_continuous_scale="RdYlGn_r",
                    color_continuous_midpoint=0
                )

                fig_tree.update_traces(
                    maxdepth=2,
                    textinfo="label+value",
                    texttemplate="<b>%{label}</b><br>$%{value:,.0f}",
                    hovertemplate="<b>%{label}</b><br>Capital: $%{value:,.0f}<br>Exceso: %{color:.0f}%<extra></extra>"
                )

                fig_tree.update_layout(
                    autosize=True,
                    margin=dict(t=10, l=10, r=10, b=10),
                    height=360,
                    paper_bgcolor="rgba(0,0,0,0)"
                )

                st.plotly_chart(fig_tree, use_container_width=True, config=plot_config)
                st.caption("Tip: Haz clic en los bloques para hacer zoom por nivel.")
            else:
                st.info("No hay datos suficientes de capital estancado para generar esta visualización.")

    # --- Pestaña 3 ---
    with tab_graficas:
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            with st.container(border=True):
                render_chart_header(
                    "Brecha operativa",
                    "Compara stock real contra stock esperado para detectar excedentes estructurales."
                )

                df_brecha = df_filtrado.groupby(eje_agrupacion, as_index=False)[["Stock", "Units_expected"]].sum()

                if not df_brecha.empty:
                    df_melted = df_brecha.melt(
                        id_vars=eje_agrupacion,
                        value_vars=["Stock", "Units_expected"],
                        var_name="Tipo",
                        value_name="Unidades"
                    )

                    df_melted["Tipo"] = df_melted["Tipo"].replace({
                        "Stock": "Stock Real",
                        "Units_expected": "Stock Esperado"
                    })

                    fig_brecha = px.bar(
                        df_melted,
                        x=eje_agrupacion,
                        y="Unidades",
                        color="Tipo",
                        barmode="group",
                        color_discrete_map={"Stock Real": "#ef4444", "Stock Esperado": "#3b82f6"}
                    )

                    fig_brecha.update_layout(
                        autosize=True,
                        margin=dict(t=10, l=10, r=10, b=10),
                        height=350,
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        legend_title_text="",
                        xaxis_title="",
                        yaxis_title="Unidades",
                        legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=1),
                        yaxis=dict(tickformat="d", gridcolor="#e2e8f0")
                    )

                    st.plotly_chart(fig_brecha, use_container_width=True, config=plot_config)
                else:
                    st.info("Sin datos para graficar la brecha operativa.")

        with col_g2:
            with st.container(border=True):
                render_chart_header(
                    "Exceso de stock por periodo",
                    "Muestra excedente positivo contra unidades vendidas a través del tiempo."
                )

                if "Date" in df_filtrado.columns:
                    df_filtrado["Date"] = pd.to_datetime(df_filtrado["Date"], errors="coerce")

                    df_tiempo = (
                        df_filtrado
                        .dropna(subset=["Date"])
                        .groupby("Date", as_index=False)
                        .agg(
                            Stock=("Stock", "sum"),
                            Units_expected=("Units_expected", "sum"),
                            Units_sold=("Units_sold", "sum")
                        )
                        .sort_values("Date")
                    )
                else:
                    df_tiempo = pd.DataFrame()

                if not df_tiempo.empty:
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
                        autosize=True,
                        barmode="overlay",
                        margin=dict(t=10, l=10, r=10, b=10),
                        height=350,
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        yaxis=dict(gridcolor="#e2e8f0", title="Unidades", tickformat="d"),
                        xaxis=dict(title=""),
                        legend=dict(orientation="h", yanchor="bottom", y=1.04, xanchor="right", x=1),
                        hovermode="x unified"
                    )

                    st.plotly_chart(fig_exceso, use_container_width=True, config=plot_config)
                else:
                    st.info("Sin registros históricos para trazar la tendencia temporal del exceso.")

    # --- Pestaña 4 ---
    with tab_tablas:
        with st.container(border=True):
            render_chart_header(
                "Reportes de datos crudos",
                "Consulta los productos críticos, baja rotación y máximos excesos por categoría."
            )

            sub_tab1, sub_tab2, sub_tab3 = st.tabs([
                "Productos en Umbral Crítico",
                "Baja Rotación Prolongada",
                "Más Crítico por Categoría"
            ])

            with sub_tab1:
                df_criticos = (
                    df_filtrado[df_filtrado["Overstock_critico"] == True]
                    .sort_values(by="Exceso_Porcentual", ascending=False)
                )
                col_criticos = [
                    "Category", "Subcategory", "Product_name", "Stock", "Units_expected",
                    "Exceso_Porcentual", "Units_sold", "Stock_turnover", "Priority_action"
                ]
                col_criticos = [col for col in col_criticos if col in df_criticos.columns]

                st.dataframe(
                    df_criticos[col_criticos].head(top_n),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Category": "Categoría",
                        "Subcategory": "Subcategoría",
                        "Product_name": "Producto",
                        "Stock": st.column_config.NumberColumn("Stock Actual", format="%d"),
                        "Units_expected": st.column_config.NumberColumn("Stock Planeado", format="%d"),
                        "Exceso_Porcentual": st.column_config.NumberColumn("Exceso (%)", format="%.1f%%"),
                        "Units_sold": st.column_config.NumberColumn("Ventas", format="%d"),
                        "Stock_turnover": st.column_config.NumberColumn("Rotación", format="%.2fx"),
                        "Priority_action": "Acción Recomendada"
                    }
                )

            with sub_tab2:
                df_rotacion = df_filtrado.sort_values(by="Days_inventory", ascending=False)
                col_rotacion = ["Category", "Subcategory", "Product_name", "Stock", "Days_inventory", "Units_sold", "Stock_turnover"]
                col_rotacion = [col for col in col_rotacion if col in df_rotacion.columns]

                st.dataframe(
                    df_rotacion[col_rotacion].head(top_n),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Category": "Categoría",
                        "Subcategory": "Subcategoría",
                        "Product_name": "Producto",
                        "Stock": st.column_config.NumberColumn("Stock Real", format="%d"),
                        "Days_inventory": st.column_config.NumberColumn("Días Estancado", format="%d días"),
                        "Units_sold": st.column_config.NumberColumn("Ventas", format="%d"),
                        "Stock_turnover": st.column_config.NumberColumn("Rotación", format="%.2fx")
                    }
                )

            with sub_tab3:
                if not df_filtrado.empty:
                    idx_top = df_filtrado.groupby("Category")["Exceso_Porcentual"].idxmax()
                    df_top_cat = df_filtrado.loc[idx_top].sort_values(by="Exceso_Porcentual", ascending=False)

                    col_top = [
                        "Category", "Product_name", "Stock", "Units_expected",
                        "Exceso_Porcentual", "Days_inventory", "Stock_turnover", "Priority_action"
                    ]
                    col_top = [col for col in col_top if col in df_top_cat.columns]

                    st.dataframe(
                        df_top_cat[col_top],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Category": "Categoría",
                            "Product_name": "Producto Más Crítico",
                            "Stock": st.column_config.NumberColumn("Stock Real", format="%d"),
                            "Units_expected": st.column_config.NumberColumn("Stock Planeado", format="%d"),
                            "Exceso_Porcentual": st.column_config.NumberColumn("Exceso (%)", format="%.1f%%"),
                            "Days_inventory": st.column_config.NumberColumn("Días Estancado", format="%d días"),
                            "Stock_turnover": st.column_config.NumberColumn("Rotación", format="%.2fx"),
                            "Priority_action": "Acción"
                        }
                    )
                else:
                    st.info("No hay datos suficientes para calcular los más críticos con los filtros actuales.")
