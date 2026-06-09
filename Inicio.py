import streamlit as st
from html import escape
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path


# =========================
# Configuración de página
# =========================
st.set_page_config(
    layout="wide",
    page_title="Dashboard Danu",
    page_icon="🚀"
)


# =========================
# CSS externo + override estructural de esta página
# =========================
css_path = Path("styles/main.css")
if css_path.exists():
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.markdown(
    """
    <style>
        :root {
            --rd-page-x: clamp(1rem, 1.9vw, 1.6rem);
            --rd-page-top: clamp(1.4rem, 2vh, 2.2rem);
            --rd-section-gap: 12px;
            --rd-kpi-chart-gap: 12px;
            --rd-fixed-row-gap: 12px;

            --rd-card-radius: clamp(18px, 1.55vw, 24px);

            /* AJUSTE PRINCIPAL: borde más visible */
            --rd-border: 1.5px solid rgba(100, 116, 139, 0.46);
            --rd-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);

            --rd-text: #0f172a;
            --rd-muted: #64748b;
            --rd-soft-bg: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        }

        .block-container {
            max-width: 100% !important;
            padding-top: var(--rd-page-top) !important;
            padding-bottom: clamp(0.8rem, 1.4vh, 1.2rem) !important;
            padding-left: var(--rd-page-x) !important;
            padding-right: var(--rd-page-x) !important;
        }

        h1, h2, h3 {
            margin-top: 0 !important;
        }

        div[data-testid="stVerticalBlock"] {
            gap: var(--rd-fixed-row-gap) !important;
        }

        div[data-testid="stHorizontalBlock"] {
            gap: var(--rd-fixed-row-gap) !important;
        }

        div[data-testid="column"] {
            min-width: 0 !important;
        }

        .rd-main-title {
            display: block;
            overflow: visible !important;
            color: var(--rd-text) !important;
            font-size: 44px !important;
            font-weight: 950 !important;
            letter-spacing: -1.2px !important;
            line-height: 1.16 !important;
            margin: 0 0 20px 0 !important;
            padding: 6px 0 0 0 !important;
            min-height: 58px !important;
            white-space: normal !important;
        }

        div[data-testid="stMarkdownContainer"]:has(.rd-main-title),
        div[data-testid="stMarkdownContainer"]:has(.rd-main-title) * {
            overflow: visible !important;
        }

        .rd-top-card {
            --accent-color: #2563eb;
            position: relative;
            box-sizing: border-box;
            width: 100%;
            min-height: clamp(112px, 12vw, 142px) !important;
            height: 100%;
            overflow: hidden;
            border-radius: var(--rd-card-radius);
            padding: clamp(14px, 1.35vw, 22px) clamp(14px, 1.45vw, 22px) clamp(12px, 1.05vw, 18px);
            background: var(--rd-soft-bg);
            border: var(--rd-border);
            box-shadow: var(--rd-shadow);
            display: flex;
            flex-direction: column;
            justify-content: center;
        }

        .rd-top-card::before {
            content: "";
            position: absolute;
            inset: 0 0 auto 0;
            height: clamp(5px, 0.45vw, 7px);
            background: var(--accent-color);
        }

        .rd-top-card:hover {
            border-color: rgba(71, 85, 105, 0.58) !important;
        }

        .rd-top-title {
            display: block;
            color: var(--rd-text) !important;
            font-size: 15px !important;
            font-weight: 950 !important;
            line-height: 1.12 !important;
            letter-spacing: -0.15px !important;
            margin: 0 0 8px 0 !important;
        }

        .rd-top-value {
            display: flex !important;
            flex-wrap: wrap !important;
            align-items: baseline !important;
            column-gap: 7px !important;
            row-gap: 2px !important;
            color: var(--rd-text) !important;
            font-size: 32px !important;
            font-weight: 950 !important;
            letter-spacing: -1.15px !important;
            line-height: 0.98 !important;
            margin: 0 0 8px 0 !important;
            word-break: keep-all !important;
            overflow-wrap: normal !important;
        }

        .rd-top-number {
            white-space: nowrap !important;
            min-width: 0 !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        .rd-top-unit {
            color: var(--rd-text) !important;
            font-size: 32px !important;
            font-weight: 950 !important;
            letter-spacing: -0.25px !important;
            line-height: 1.05 !important;
            white-space: nowrap !important;
        }

        .rd-top-description {
            color: var(--rd-muted) !important;
            font-size: 12px !important;
            font-weight: 750 !important;
            letter-spacing: 0 !important;
            line-height: 1.22 !important;
            margin: 0 !important;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .rd-chart-anchor {
            display: none !important;
        }

        .rd-kpi-chart-gap,
        .rd-chart-bottom-gap {
            display: block !important;
            clear: both !important;
            width: 100% !important;
            line-height: 0 !important;
            font-size: 0 !important;
            overflow: hidden !important;
            pointer-events: none !important;
        }

        .rd-kpi-chart-gap {
            height: 0 !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        .rd-chart-bottom-gap {
            height: var(--rd-section-gap) !important;
            min-height: 8px !important;
        }

        div[data-testid="stElementContainer"]:has(.rd-kpi-chart-gap),
        div[data-testid="stMarkdownContainer"]:has(.rd-kpi-chart-gap) {
            height: 0 !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: hidden !important;
        }

        div[data-testid="stHorizontalBlock"]:has(.rd-top-card) {
            margin-bottom: 12px !important;
        }

        /* AJUSTE IMPORTANTE:
           aplica el borde visible a la tarjeta de la gráfica */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            box-sizing: border-box !important;
            border-radius: var(--rd-card-radius) !important;
            border: var(--rd-border) !important;
            background: var(--rd-soft-bg) !important;
            box-shadow: var(--rd-shadow) !important;
            padding: clamp(13px, 1.18vw, 18px) clamp(16px, 1.45vw, 22px) !important;
            margin: 0 !important;
            overflow: visible !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: rgba(71, 85, 105, 0.58) !important;
        }

        .rd-chart-header {
            padding: 0 !important;
            margin: 0 0 clamp(8px, 0.8vw, 12px) 0 !important;
        }

        .rd-chart-header h3 {
            color: var(--rd-text) !important;
            font-size: 17px !important;
            font-weight: 950 !important;
            letter-spacing: -0.25px !important;
            line-height: 1.16 !important;
            margin: 0 !important;
        }

        .rd-chart-header p {
            color: var(--rd-muted) !important;
            font-size: 12px !important;
            font-weight: 750 !important;
            line-height: 1.25 !important;
            margin: 8px 0 0 0 !important;
        }

        .rd-bottom-card {
            box-sizing: border-box;
            width: 100%;
            border-radius: var(--rd-card-radius);
            padding: clamp(10px, 0.95vw, 14px) clamp(12px, 1.1vw, 16px);
            background: var(--rd-soft-bg);
            border: var(--rd-border);
            box-shadow: var(--rd-shadow);
            overflow: hidden;
        }

        .rd-bottom-card:hover {
            border-color: rgba(71, 85, 105, 0.58) !important;
        }

        .rd-bottom-grid {
            display: grid;
            grid-template-columns: minmax(220px, 0.72fr) minmax(420px, 1.38fr);
            gap: clamp(8px, 0.82vw, 12px);
            align-items: stretch;
            width: 100%;
        }

        .rd-small-kpi-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: clamp(8px, 0.75vw, 10px);
            width: 100%;
        }

        .rd-small-kpi-wide {
            grid-column: 1 / span 2;
        }

        .rd-small-kpi {
            position: relative;
            cursor: help;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-width: 0;
            min-height: clamp(42px, 3.7vw, 54px);
            border-radius: clamp(12px, 1vw, 15px);
            padding: clamp(6px, 0.55vw, 8px) clamp(8px, 0.75vw, 11px);
            text-align: center;
            background: rgba(255, 255, 255, 0.9);
            border: 1.4px solid rgba(100, 116, 139, 0.38);
            box-shadow: 0 6px 16px rgba(15, 23, 42, 0.035);
            overflow: visible;
        }

        .rd-small-kpi:hover {
            border-color: rgba(71, 85, 105, 0.55) !important;
        }

        .rd-small-kpi-label {
            color: var(--rd-muted);
            font-size: 9px !important;
            font-weight: 950;
            text-transform: uppercase;
            white-space: nowrap;
            line-height: 1.1 !important;
            margin: 0 0 4px 0 !important;
        }

        .rd-small-kpi-value {
            color: var(--rd-text);
            font-size: 18px !important;
            font-weight: 950;
            letter-spacing: -0.6px;
            line-height: 1 !important;
            margin: 0;
            text-align: center;
            overflow-wrap: anywhere;
        }

        .rd-small-kpi-value-wide {
            font-size: 21px !important;
        }

        .rd-ranking {
            width: 100%;
            min-width: 0;
        }

        .rd-ranking-title {
            color: var(--rd-text);
            font-size: 16px !important;
            font-weight: 950;
            line-height: 1.15 !important;
            letter-spacing: -0.25px;
            margin: 0 0 8px 0 !important;
        }

        .rd-ranking-item {
            margin-bottom: clamp(4px, 0.46vw, 7px);
        }

        .rd-ranking-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px !important;
            color: #111827;
            font-size: 12px !important;
            font-weight: 900;
            line-height: 1.1 !important;
            margin-bottom: 3px !important;
        }

        .rd-product-name {
            min-width: 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .rd-ranking-top strong {
            flex-shrink: 0;
            color: #dc2626;
            font-size: 14px !important;
            font-weight: 950;
            white-space: nowrap;
        }

        .rd-bar-track {
            width: 100%;
            height: clamp(5px, 0.44vw, 7px);
            overflow: hidden;
            border-radius: 999px;
            background: #fee2e2;
        }

        .rd-bar-fill {
            height: 100%;
            border-radius: 999px;
            background: #dc2626;
        }

        .rd-footer {
            color: #94a3b8;
            font-size: 11px !important;
            font-weight: 800;
            line-height: 1.15 !important;
            margin: 7px 0 0 0 !important;
        }

        .rd-small-kpi::after {
            content: attr(data-tooltip);
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            width: max-content;
            max-width: min(230px, 80vw);
            z-index: 999;
            opacity: 0;
            pointer-events: none;
            border-radius: 10px;
            padding: 8px 10px;
            text-align: center;
            color: #ffffff;
            background: var(--rd-text);
            box-shadow: 0 10px 25px rgba(15, 23, 42, 0.22);
            font-size: 10px;
            font-weight: 650;
            line-height: 1.3;
            transition: opacity 0.18s ease, transform 0.18s ease;
        }

        .rd-small-kpi::before {
            content: "";
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            z-index: 999;
            opacity: 0;
            border: 6px solid transparent;
            transition: opacity 0.18s ease;
        }

        .rd-tooltip-bottom::after { top: calc(100% + 8px); }
        .rd-tooltip-bottom::before {
            top: calc(100% - 1px);
            border-bottom-color: var(--rd-text);
        }

        .rd-tooltip-top::after { bottom: calc(100% + 8px); }
        .rd-tooltip-top::before {
            bottom: calc(100% - 1px);
            border-top-color: var(--rd-text);
        }

        .rd-small-kpi:hover::after,
        .rd-small-kpi:hover::before { opacity: 1; }

        .rd-small-kpi:hover::after {
            transform: translateX(-50%) translateY(-2px);
        }

        div[data-testid="stPlotlyChart"] {
            margin-top: clamp(-2px, -0.12vw, 0px) !important;
        }

        @media (max-width: 1100px) {
            .rd-bottom-grid {
                grid-template-columns: 1fr;
            }
        }

        @media (max-width: 760px) {
            .block-container {
                padding-left: 0.75rem !important;
                padding-right: 0.75rem !important;
                padding-top: 1rem !important;
            }

            .rd-main-title {
                font-size: 44px !important;
                line-height: 1.16 !important;
                min-height: 58px !important;
                margin-bottom: 20px !important;
                padding-top: 6px !important;
            }

            .rd-top-title { font-size: 15px !important; }
            .rd-top-value { font-size: 39px !important; }
            .rd-top-unit { font-size: 15px !important; }
            .rd-top-description { font-size: 12px !important; }
        }

       /* =====================================================
   TARJETA DE LA GRÁFICA
   El borde real se aplica al stVerticalBlock interno,
   que es el elemento que estás señalando en DevTools.
===================================================== */

/* El wrapper externo ya no dibuja el borde */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.rd-chart-anchor) {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: visible !important;
}

/* ESTE es el elemento que quieres cambiar */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.rd-chart-anchor)
div[data-testid="stVerticalBlock"] {
    box-sizing: border-box !important;
       border: 2px solid rgba(100, 116, 139, 0.55) !important;
    border-radius: var(--rd-card-radius) !important;
    background: var(--rd-soft-bg) !important;
    box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06) !important;
    padding: 15px !important;
    margin: 0 !important;
    overflow: hidden !important;
}

/* Hover opcional */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.rd-chart-anchor)
div[data-testid="stVerticalBlock"]:hover {
    border-color: rgba(71, 85, 105, 0.62) !important;
}
    </style>
    """,
    unsafe_allow_html=True
)


# =========================
# Funciones auxiliares
# =========================
def safe_mean(series):
    value = (
        pd.to_numeric(series, errors="coerce")
        .replace([float("inf"), -float("inf")], pd.NA)
        .dropna()
        .mean()
    )

    if pd.isna(value):
        return 0

    return float(value)


def safe_float(value, default=0):
    if pd.isna(value):
        return default
    return float(value)


# =========================
# Cargar datos
# =========================
@st.cache_data
def cargar_datos():
    ruta = Path("data/df_Maestra.csv")
    df = pd.read_csv(ruta)

    df.columns = df.columns.str.strip()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    df["Overstock_critico"] = (
        df["Overstock_critico"]
        .astype(str)
        .str.lower()
        .map({"true": True, "false": False, "1": True, "0": False})
        .fillna(False)
    )

    df["Exceso_stock"] = (df["Stock"] - df["Units_expected"]).clip(lower=0)

    return df


df_maestra = cargar_datos()


# =========================
# Sidebar - Filtros
# =========================
with st.sidebar:
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

    st.markdown("### Filtros")

    fecha_min = df_maestra["Date"].min().date()
    fecha_max = df_maestra["Date"].max().date()

    rango_fechas = st.date_input(
        "Rango de fechas",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max
    )

    regiones = sorted(df_maestra["Region"].dropna().unique().tolist())
    region = st.selectbox(
        "Región",
        ["Todas"] + regiones
    )

    categorias = sorted(df_maestra["Category"].dropna().unique().tolist())
    categoria = st.selectbox(
        "Categoría",
        ["Todas"] + categorias
    )

    # =========================
    # Subcategoría dependiente de categoría
    # =========================
    df_subcategorias = df_maestra.copy()

    if region != "Todas":
        df_subcategorias = df_subcategorias[
            df_subcategorias["Region"] == region
        ]

    if categoria != "Todas":
        df_subcategorias = df_subcategorias[
            df_subcategorias["Category"] == categoria
        ]

    subcategorias = sorted(
        df_subcategorias["Subcategory"]
        .dropna()
        .unique()
        .tolist()
    )

    subcategoria = st.selectbox(
        "Subcategoría",
        ["Todas"] + subcategorias
    )

    acciones = sorted(df_maestra["Priority_action"].dropna().unique().tolist())
    acciones_seleccionadas = st.multiselect(
        "Acción prioritaria",
        acciones,
        default=acciones
    )


# =========================
# Aplicar filtros
# =========================
df_filtrado = df_maestra.copy()

if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
    fecha_inicio, fecha_fin = rango_fechas

    df_filtrado = df_filtrado[
        (df_filtrado["Date"].dt.date >= fecha_inicio) &
        (df_filtrado["Date"].dt.date <= fecha_fin)
    ]

if region != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Region"] == region]

if categoria != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Category"] == categoria]

if subcategoria != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Subcategory"] == subcategoria]

if acciones_seleccionadas:
    df_filtrado = df_filtrado[
        df_filtrado["Priority_action"].isin(acciones_seleccionadas)
    ]


# =========================
# Cálculos principales
# =========================
ventas_totales = df_filtrado["Sales_amount"].sum()
unidades_vendidas = df_filtrado["Units_sold"].sum()
stock_total = df_filtrado["Stock"].sum()

df_critico = df_filtrado[df_filtrado["Overstock_critico"] == True].copy()

productos_criticos = df_critico["Product_id"].nunique()
unidades_excedentes = df_critico["Exceso_stock"].sum()
stock_critico = df_critico["Stock"].sum()

porcentaje_stock_critico = (
    stock_critico / stock_total * 100
    if stock_total > 0
    else 0
)

dias_promedio_inventario = safe_mean(df_filtrado["Days_inventory"])
dias_promedio_critico = safe_mean(df_critico["Days_inventory"]) if not df_critico.empty else 0

rotacion_promedio = safe_mean(df_filtrado["Stock_turnover"])
rotacion_critica = safe_mean(df_critico["Stock_turnover"]) if not df_critico.empty else 0

progreso_overstock = safe_float(porcentaje_stock_critico)
progreso_dias = min((dias_promedio_inventario / 365) * 100, 100)
progreso_rotacion = min((rotacion_promedio / 1) * 100, 100)


# =========================
# Tarjeta compacta superior
# =========================
def compact_metric_card(title, value, description, badge, icon, accent_color, progress, unit=""):
    title = escape(str(title))
    value = escape(str(value))
    unit = escape(str(unit))
    description = escape(str(description))

    unit_html = f'<span class="rd-top-unit">{unit}</span>' if unit else ""

    return f"""
    <div class="rd-top-card" style="--accent-color: {accent_color};">
        <p class="rd-top-title">{title}</p>
        <p class="rd-top-value"><span class="rd-top-number">{value}</span>{unit_html}</p>
        <p class="rd-top-description">{description}</p>
    </div>
    """


# =========================
# Encabezado
# =========================
st.markdown(
    '<div class="rd-main-title">Panel de Control Principal</div>',
    unsafe_allow_html=True
)


# =========================
# Fila superior: 3 tarjetas
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        compact_metric_card(
            title="Overstock Crítico",
            value=f"{unidades_excedentes:,.0f}",
            unit="unidades",
            description=f"{productos_criticos:,} productos",
            badge="Riesgo alto",
            icon="🚨",
            accent_color="#dc2626",
            progress=progreso_overstock
        ),
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        compact_metric_card(
            title="Días Prom. Inventario",
            value=f"{dias_promedio_inventario:.0f}",
            unit="días",
            description=f"{dias_promedio_critico:.0f} días en productos críticos",
            badge="Inventario lento",
            icon="⏳",
            accent_color="#f59e0b",
            progress=progreso_dias
        ),
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        compact_metric_card(
            title="Rotación Inventario",
            value=f"{rotacion_promedio:.2f}x",
            unit="",
            description=f"{rotacion_critica:.2f}x en productos críticos",
            badge="Baja rotación",
            icon="🔄",
            accent_color="#2563eb",
            progress=progreso_rotacion
        ),
        unsafe_allow_html=True
    )

st.markdown('<div class="rd-kpi-chart-gap" aria-hidden="true">&nbsp;</div>', unsafe_allow_html=True)


# =========================
# Card: Ventas mensuales vs stock total
# =========================
with st.container(border=True):
    st.markdown('<div class="rd-chart-anchor" aria-hidden="true"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="rd-chart-header">
        <h3>Ventas mensuales vs stock total</h3>
        <p>
            Las barras muestran las unidades vendidas por mes y la línea representa el stock disponible.
        </p>
    </div>
    """, unsafe_allow_html=True)

    df_mes = df_filtrado.copy()
    df_mes["Mes"] = df_mes["Date"].dt.to_period("M").dt.to_timestamp()

    ventas_stock_mes = (
        df_mes
        .groupby("Mes", as_index=False)
        .agg({
            "Units_sold": "sum",
            "Stock": "sum",
            "Sales_amount": "sum"
        })
        .sort_values("Mes")
    )

    ventas_stock_mes["Mes_texto"] = ventas_stock_mes["Mes"].dt.strftime("%b %Y")

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=ventas_stock_mes["Mes_texto"],
            y=ventas_stock_mes["Units_sold"],
            name="Unidades vendidas",
            hovertemplate="<b>%{x}</b><br>Unidades vendidas: %{y:,.0f}<extra></extra>"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=ventas_stock_mes["Mes_texto"],
            y=ventas_stock_mes["Stock"],
            name="Stock total",
            yaxis="y2",
            mode="lines+markers",
            hovertemplate="<b>%{x}</b><br>Stock total: %{y:,.0f}<extra></extra>"
        )
    )

    fig.update_layout(
        title="",
        autosize=True,
        height=220,
        margin=dict(l=26, r=26, t=0, b=18),
        font=dict(size=10),
        xaxis=dict(title=None, automargin=True),
        yaxis=dict(title="Vendidas", showgrid=True, automargin=True),
        yaxis2=dict(
            title="Stock",
            overlaying="y",
            side="right",
            showgrid=False,
            automargin=True
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False}
    )

st.markdown('<div class="rd-chart-bottom-gap" aria-hidden="true">&nbsp;</div>', unsafe_allow_html=True)


# =========================
# Datos para panel lateral
# =========================
df_cards = df_filtrado.copy()

if "Exceso_stock" not in df_cards.columns:
    df_cards["Exceso_stock"] = (
        df_cards["Stock"] - df_cards["Units_expected"]
    ).clip(lower=0)

ventas_filtradas_total = df_cards["Sales_amount"].sum()
ventas_generales_total = df_maestra["Sales_amount"].sum()

porcentaje_ventas = (
    ventas_filtradas_total / ventas_generales_total * 100
    if ventas_generales_total > 0
    else 0
)

sell_through_rate = safe_mean(df_cards["Sell_through_pct"])

if sell_through_rate <= 1:
    sell_through_rate = sell_through_rate * 100

ventas_unidades_totales = df_cards["Units_sold"].sum()


# =========================
# Top 5 productos con mayor sobrestock
# =========================
col_producto = "Product_name" if "Product_name" in df_cards.columns else "Product_id"

if col_producto == "Product_name" and "Product_id" in df_cards.columns:
    df_cards["Etiqueta_producto"] = (
        df_cards["Product_name"].astype(str).str.strip()
        + " · ID "
        + df_cards["Product_id"].astype(str)
    )
else:
    df_cards["Etiqueta_producto"] = df_cards[col_producto].astype(str)

top5_sobrestock = (
    df_cards
    .groupby("Etiqueta_producto", as_index=False)["Exceso_stock"]
    .sum()
    .sort_values("Exceso_stock", ascending=False)
    .head(5)
)

max_sobrestock = (
    top5_sobrestock["Exceso_stock"].max()
    if not top5_sobrestock.empty
    else 1
)

top5_items_html = ""

for _, row in top5_sobrestock.iterrows():
    producto_item = escape(str(row["Etiqueta_producto"]))
    exceso = row["Exceso_stock"]
    porcentaje_barra = (exceso / max_sobrestock) * 100 if max_sobrestock > 0 else 0

    top5_items_html += (
        f'<div class="rd-ranking-item">'
        f'<div class="rd-ranking-top">'
        f'<span class="rd-product-name">{producto_item}</span>'
        f'<strong>{exceso:,.0f}</strong>'
        f'</div>'
        f'<div class="rd-bar-track">'
        f'<div class="rd-bar-fill" style="width:{porcentaje_barra:.1f}%;"></div>'
        f'</div>'
        f'</div>'
    )


# =========================
# Panel lateral compacto
# =========================
side_panel_html = (
    f'<div class="rd-bottom-card">'
    f'<div class="rd-bottom-grid">'
    f'<div class="rd-small-kpi-grid">'
    f'<div class="rd-small-kpi rd-tooltip-bottom" data-tooltip="Porcentaje de ventas realizadas respecto al total esperado o disponible en el periodo seleccionado.">'
    f'<p class="rd-small-kpi-label">% ventas</p>'
    f'<p class="rd-small-kpi-value">{porcentaje_ventas:.1f}%</p>'
    f'</div>'
    f'<div class="rd-small-kpi rd-tooltip-bottom" data-tooltip="Porcentaje del inventario disponible que logró venderse. Mientras más alto, mejor movimiento del stock.">'
    f'<p class="rd-small-kpi-label">Sell-through</p>'
    f'<p class="rd-small-kpi-value">{sell_through_rate:.1f}%</p>'
    f'</div>'
    f'<div class="rd-small-kpi rd-small-kpi-wide rd-tooltip-top" data-tooltip="Cantidad total de unidades vendidas según los filtros seleccionados.">'
    f'<p class="rd-small-kpi-label">Unidades vendidas</p>'
    f'<p class="rd-small-kpi-value rd-small-kpi-value-wide">{ventas_unidades_totales:,.0f}</p>'
    f'</div>'
    f'</div>'
    f'<div class="rd-ranking">'
    f'<p class="rd-ranking-title">Top 5 productos con mayor sobrestock</p>'
    f'{top5_items_html}'
    f'<p class="rd-footer">Medido por unidades excedentes de stock.</p>'
    f'</div>'
    f'</div>'
    f'</div>'
)

st.markdown(side_panel_html, unsafe_allow_html=True)