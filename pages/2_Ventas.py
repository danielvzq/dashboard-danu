import streamlit as st
import streamlit.components.v1 as components
from html import escape
from pathlib import Path

import pandas as pd
import numpy as np
import plotly.express as px


# =========================
# Configuración de página
# =========================
st.set_page_config(
    page_title="Centro de Ventas",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================
# CSS general - estilo Inicio
# =========================
st.markdown(
    """
    <style>
        :root {
            --rd-card-bg: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            --rd-card-border: 1.7px solid rgba(100, 116, 139, 0.52);
            --rd-card-border-hover: rgba(71, 85, 105, 0.62);
            --rd-card-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);
            --rd-card-radius: 24px;
        }

        .block-container {
            padding-top: 2.2rem !important;
            padding-bottom: 0.8rem !important;
            padding-left: 1.4rem !important;
            padding-right: 1.4rem !important;
            max-width: 100% !important;
        }

        h1, h2, h3 {
            margin-top: 0 !important;
            margin-bottom: 0.6rem !important;
        }

        .main-title {
            color: #0f172a;
            font-size: 30px;
            font-weight: 950;
            letter-spacing: -0.8px;
            margin: 0 0 16px 0;
            line-height: 1.2;
        }

        div[data-testid="stVerticalBlock"] {
            gap: 0.65rem !important;
        }

        div[data-testid="stHorizontalBlock"] {
            gap: 0.8rem !important;
        }

        iframe {
            display: block;
        }

        .chart-card-header {
            padding: 4px 8px 0 8px;
            margin-bottom: 6px;
        }

        .chart-card-header h3 {
            color: #0f172a;
            font-size: 22px;
            font-weight: 900;
            margin: 0;
            letter-spacing: -0.4px;
        }

        .chart-card-header p {
            color: #64748b;
            font-size: 14px;
            font-weight: 600;
            margin: 6px 0 0 0;
        }

        .chart-card-anchor {
            display: none !important;
        }

        /*
           Tarjetas de gráficas.
           El borde visible se aplica al stVerticalBlock interno,
           que es el elemento que Streamlit realmente dibuja dentro
           de st.container(border=True).
        */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.chart-card-anchor) {
            border: none !important;
            box-shadow: none !important;
            background: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
            overflow: visible !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.chart-card-anchor) > div[data-testid="stVerticalBlock"],
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.chart-card-anchor) > div > div[data-testid="stVerticalBlock"] {
            box-sizing: border-box !important;
            border: var(--rd-card-border) !important;
            border-radius: var(--rd-card-radius) !important;
            background: var(--rd-card-bg) !important;
            box-shadow: var(--rd-card-shadow) !important;
            padding: 15px !important;
            margin: 0 !important;
            overflow: hidden !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"]:has(.chart-card-anchor) > div[data-testid="stVerticalBlock"]:hover,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.chart-card-anchor) > div > div[data-testid="stVerticalBlock"]:hover {
            border-color: var(--rd-card-border-hover) !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================
# Cargar CSS personalizado
# =========================
css_path = Path("styles/main.css")

if css_path.exists():
    with open(css_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# =========================
# Funciones auxiliares
# =========================
def safe_sum(series):
    return pd.to_numeric(series, errors="coerce").fillna(0).sum()


def compact_metric_card(title, value, description, accent_color):
    title = escape(str(title))
    value = escape(str(value))
    description = escape(str(description))

    return f"""
<!DOCTYPE html>
<html>
<head>
<style>
    html, body {{
        margin: 0;
        padding: 0;
        background: transparent;
        font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    .metric-card {{
        position: relative;
        overflow: hidden;
        height: 155px;
        box-sizing: border-box;
        border-radius: 24px;
        padding: 26px 20px 18px 20px;
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1.7px solid rgba(100, 116, 139, 0.52);
        box-shadow: 0 10px 26px rgba(15, 23, 42, 0.06);
        transition: border-color 0.18s ease, box-shadow 0.18s ease;
    }}

    .metric-card:hover {{
        border-color: rgba(71, 85, 105, 0.62);
        box-shadow: 0 12px 30px rgba(15, 23, 42, 0.075);
    }}

    .metric-card::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 7px;
        background: var(--accent-color);
    }}

    .metric-title {{
        color: #0f172a;
        font-size: 15px;
        font-weight: 900;
        margin: 0 0 14px 0;
    }}

    .metric-value {{
        color: #0f172a;
        font-size: 28px;
        font-weight: 950;
        letter-spacing: -0.8px;
        line-height: 1;
        margin: 0 0 8px 0;
    }}

    .metric-description {{
        color: #64748b;
        font-size: 13px;
        font-weight: 700;
        line-height: 1.25;
        margin: 0;
    }}
</style>
</head>
<body>
    <div class="metric-card" style="--accent-color: {accent_color};">
        <p class="metric-title">{title}</p>
        <p class="metric-value">{value}</p>
        <p class="metric-description">{description}</p>
    </div>
</body>
</html>
"""


def chart_header(title, description):
    return f"""
    <div class="chart-card-header">
        <h3>{escape(title)}</h3>
        <p>{escape(description)}</p>
    </div>
    """


# =========================
# Carga y preparación de datos
# =========================
@st.cache_data
def cargar_datos():
    df_maestra = pd.read_csv("data/df_Maestra.csv")
    df_maestra.columns = df_maestra.columns.str.strip()
    df_maestra["Date"] = pd.to_datetime(df_maestra["Date"], errors="coerce")

    # ---------------------------------------------------------
    # CORRECCIÓN MATEMÁTICA (Alineada al Notebook)
    # ---------------------------------------------------------
    for col in ["Stock", "Units_sold", "Static_price", "Sales_amount"]:
        if col in df_maestra.columns:
            df_maestra[col] = pd.to_numeric(df_maestra[col], errors="coerce").fillna(0)
            
    if "Stock" in df_maestra.columns and "Units_sold" in df_maestra.columns:
        df_maestra["Excess_stock"] = (df_maestra["Stock"] - df_maestra["Units_sold"]).clip(lower=0)
        df_maestra["Gap_pct"] = (df_maestra["Excess_stock"] / df_maestra["Stock"].replace(0, np.nan)) * 100
        df_maestra["Exceso_Porcentual"] = df_maestra["Gap_pct"].fillna(0)
    
    df_maestra["Sales_amount"] = df_maestra["Sales_amount"].round(0).astype(int)

    for col in ["Region", "Category", "Subcategory"]:
        if col in df_maestra.columns:
            df_maestra[col] = df_maestra[col].astype(str).str.strip().str.title()

    # ---------------------------------------------------------
    # CARGA DE TABLAS ADICIONALES Y ESTANDARIZACIÓN DE COLUMNAS
    # ---------------------------------------------------------
    df_ventas = pd.read_csv("data/ventas_limpio.csv")
    df_clientes = pd.read_csv("data/clientes_limpio.csv")
    df_productos = pd.read_csv("data/productos_limpio.csv")

    for dataframe in [df_ventas, df_clientes, df_productos]:
        dataframe.columns = dataframe.columns.str.strip()

    # Estandarización robusta para evitar KeyErrors con los nombres de los CSVs brutos
    map_ventas = {"date": "Date", "client_id": "Client_id", "product_id": "Product_id", "region": "Region", "units_sold": "Units_sold", "sales_amount": "Sales_amount"}
    df_ventas = df_ventas.rename(columns=lambda x: map_ventas.get(x.lower(), x))

    map_clientes = {"cliente_id": "Client_ID", "ticket_promedio": "Average_Ticket"}
    df_clientes = df_clientes.rename(columns=lambda x: map_clientes.get(x.lower(), x))

    map_prod = {"product_id": "Product_id", "product_name": "Product_name", "category": "Category", "subcategory": "Subcategory", "static_price": "Static_price"}
    df_productos = df_productos.rename(columns=lambda x: map_prod.get(x.lower(), x))

    # Limpieza de fechas
    if "Date" in df_ventas.columns:
        df_ventas["Date"] = pd.to_datetime(df_ventas["Date"], errors="coerce")

    # Segmentación basada en el Ticket Promedio
    if "Average_Ticket" in df_clientes.columns:
        df_clientes["Segmento_Cliente"] = pd.qcut(
            pd.to_numeric(df_clientes["Average_Ticket"], errors="coerce"),
            q=3,
            labels=["Ticket Bajo", "Ticket Medio", "Ticket Alto"],
            duplicates="drop"
        )
        df_clientes["Segmento_Cliente"] = df_clientes["Segmento_Cliente"].astype(str).replace("nan", "Desconocido")

    # Generar tabla unificada (Ventas + Clientes + Productos)
    df_cv = pd.merge(
        df_ventas,
        df_clientes,
        left_on="Client_id",
        right_on="Client_ID",
        how="inner"
    )
    df_cv = pd.merge(df_cv, df_productos, on="Product_id", how="left")

    if "Sales_amount" in df_cv.columns:
        df_cv["Sales_amount"] = (
            pd.to_numeric(df_cv["Sales_amount"], errors="coerce")
            .fillna(0)
            .round(0)
            .astype(int)
        )

    for col in ["Region", "Category", "Subcategory", "Segmento_Cliente"]:
        if col in df_cv.columns:
            df_cv[col] = df_cv[col].astype(str).str.strip().str.title()

    return df_maestra, df_cv


try:
    df_base, df_cv = cargar_datos()
except FileNotFoundError:
    st.error(
        "Error al cargar los archivos CSV. Asegúrate de que 'df_Maestra.csv', "
        "'ventas_limpio.csv', 'clientes_limpio.csv' y 'productos_limpio.csv' estén dentro de la carpeta 'data/'."
    )
    st.stop()


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

    # Asegurar fechas válidas para los filtros
    fechas_validas = df_base["Date"].dropna()
    fecha_min = fechas_validas.min().date() if not fechas_validas.empty else pd.Timestamp("2024-01-01").date()
    fecha_max = fechas_validas.max().date() if not fechas_validas.empty else pd.Timestamp("2025-12-31").date()

    rango_fechas = st.date_input(
        "Rango de fechas",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max
    )

    regiones = sorted(df_base["Region"].dropna().unique().tolist())
    region_sel = st.selectbox("Región", ["Todas"] + regiones)

    categorias = sorted(df_base["Category"].dropna().unique().tolist())
    categoria_sel = st.selectbox("Categoría", ["Todas"] + categorias)

    # Subcategoría dependiente de fecha, región y categoría
    df_subcategorias = df_base.copy()

    if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
        fecha_inicio, fecha_fin = rango_fechas
        mask_fechas = df_subcategorias["Date"].notna()
        df_subcategorias = df_subcategorias[
            mask_fechas &
            (df_subcategorias["Date"].dt.date >= fecha_inicio) &
            (df_subcategorias["Date"].dt.date <= fecha_fin)
        ]

    if region_sel != "Todas":
        df_subcategorias = df_subcategorias[df_subcategorias["Region"] == region_sel]

    if categoria_sel != "Todas":
        df_subcategorias = df_subcategorias[df_subcategorias["Category"] == categoria_sel]

    subcategorias = sorted(df_subcategorias["Subcategory"].dropna().unique().tolist())
    subcategoria_sel = st.selectbox("Subcategoría", ["Todas"] + subcategorias)


# =========================
# Aplicar filtros
# =========================
df_filtrado_maestra = df_base.copy()
df_filtrado_cv = df_cv.copy()

if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
    fecha_inicio, fecha_fin = rango_fechas
    
    # Filtrar Maestra evadiendo NaT
    mask_maestra = df_filtrado_maestra["Date"].notna()
    df_filtrado_maestra = df_filtrado_maestra[
        mask_maestra &
        (df_filtrado_maestra["Date"].dt.date >= fecha_inicio) &
        (df_filtrado_maestra["Date"].dt.date <= fecha_fin)
    ]

    # Filtrar CV evadiendo NaT
    if "Date" in df_filtrado_cv.columns:
        mask_cv = df_filtrado_cv["Date"].notna()
        df_filtrado_cv = df_filtrado_cv[
            mask_cv &
            (df_filtrado_cv["Date"].dt.date >= fecha_inicio) &
            (df_filtrado_cv["Date"].dt.date <= fecha_fin)
        ]

if region_sel != "Todas":
    df_filtrado_maestra = df_filtrado_maestra[df_filtrado_maestra["Region"] == region_sel]
    if "Region" in df_filtrado_cv.columns:
        df_filtrado_cv = df_filtrado_cv[df_filtrado_cv["Region"] == region_sel]

if categoria_sel != "Todas":
    df_filtrado_maestra = df_filtrado_maestra[df_filtrado_maestra["Category"] == categoria_sel]
    if "Category" in df_filtrado_cv.columns:
        df_filtrado_cv = df_filtrado_cv[df_filtrado_cv["Category"] == categoria_sel]

if subcategoria_sel != "Todas":
    df_filtrado_maestra = df_filtrado_maestra[df_filtrado_maestra["Subcategory"] == subcategoria_sel]
    if "Subcategory" in df_filtrado_cv.columns:
        df_filtrado_cv = df_filtrado_cv[df_filtrado_cv["Subcategory"] == subcategoria_sel]


# =========================
# Encabezado
# =========================
st.markdown(
    '<h1 class="main-title">Centro de Ventas y Demanda</h1>',
    unsafe_allow_html=True
)


# =========================
# KPIs superiores
# =========================
revenue_total = safe_sum(df_filtrado_maestra["Sales_amount"])
unidades_vendidas = safe_sum(df_filtrado_maestra["Units_sold"])

if not df_filtrado_maestra.empty and "Product_name" in df_filtrado_maestra.columns:
    top_product = (
        df_filtrado_maestra
        .groupby("Product_name")["Sales_amount"]
        .sum()
        .sort_values(ascending=False)
        .index[0]
    )
else:
    top_product = "N/A"

if not df_filtrado_maestra.empty and "Product_id" in df_filtrado_maestra.columns:
    productos_vendidos = df_filtrado_maestra["Product_id"].nunique()
else:
    productos_vendidos = 0

col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

with col_kpi1:
    components.html(
        compact_metric_card(
            title="Revenue Generado",
            value=f"${revenue_total:,.0f}",
            description="Ingresos totales dentro de la selección",
            accent_color="#16a34a"
        ),
        height=160,
        scrolling=False
    )

with col_kpi2:
    components.html(
        compact_metric_card(
            title="Volumen Movido",
            value=f"{unidades_vendidas:,.0f} uds",
            description="Total de unidades vendidas o despachadas",
            accent_color="#2563eb"
        ),
        height=160,
        scrolling=False
    )

with col_kpi3:
    components.html(
        compact_metric_card(
            title="Producto Estrella",
            value=top_product,
            description=f"Mayor generador de ingresos · {productos_vendidos:,} productos activos",
            accent_color="#7c3aed"
        ),
        height=160,
        scrolling=False
    )


# =========================
# Gráficas
# =========================
plot_config = {"responsive": True, "displayModeBar": False}

tab1, tab2 = st.tabs(["Análisis por Segmento", "Tendencias Anuales"])

with tab1:
    col_c1, col_c2 = st.columns(2)

    with col_c1:
        with st.container(border=True):
            st.markdown('<div class="chart-card-anchor" aria-hidden="true"></div>', unsafe_allow_html=True)
            st.markdown(
                chart_header(
                    "Categorías por perfil de comprador",
                    "Compara los ingresos generados por categoría en cada segmento de cliente."
                ),
                unsafe_allow_html=True
            )

            if not df_filtrado_cv.empty:
                df_perfiles = (
                    df_filtrado_cv
                    .groupby(["Segmento_Cliente", "Category"])["Sales_amount"]
                    .sum()
                    .reset_index()
                )

                fig_bar = px.bar(
                    df_perfiles,
                    x="Segmento_Cliente",
                    y="Sales_amount",
                    color="Category",
                    barmode="group",
                    labels={"Sales_amount": "Ventas ($)", "Segmento_Cliente": "Segmento"},
                    color_discrete_sequence=px.colors.qualitative.Set2
                )

                fig_bar.update_layout(
                    autosize=True,
                    height=310,
                    margin=dict(t=10, l=10, r=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
                    yaxis=dict(tickformat="d", gridcolor="#e2e8f0"),
                    xaxis=dict(title="")
                )

                st.plotly_chart(fig_bar, use_container_width=True, config=plot_config)
            else:
                st.info("Sin datos de clientes para estos filtros.")

    with col_c2:
        with st.container(border=True):
            st.markdown('<div class="chart-card-anchor" aria-hidden="true"></div>', unsafe_allow_html=True)
            st.markdown(
                chart_header(
                    "Concentración geográfica por segmento",
                    "Muestra qué regiones concentran más ventas según el perfil de comprador."
                ),
                unsafe_allow_html=True
            )

            if not df_filtrado_cv.empty:
                df_geo = (
                    df_filtrado_cv
                    .groupby(["Region", "Segmento_Cliente"])["Sales_amount"]
                    .sum()
                    .reset_index()
                )

                orden_regiones = (
                    df_geo.groupby("Region")["Sales_amount"]
                    .sum()
                    .sort_values(ascending=True)
                    .index
                )

                colores_segmento = {
                    "Ticket Bajo": "#3b82f6",
                    "Ticket Medio": "#10b981",
                    "Ticket Alto": "#f59e0b",
                    "Desconocido": "#94a3b8"
                }

                fig_geo = px.bar(
                    df_geo,
                    x="Sales_amount",
                    y="Region",
                    color="Segmento_Cliente",
                    orientation="h",
                    barmode="stack",
                    labels={"Sales_amount": "Ventas ($)", "Region": "", "Segmento_Cliente": "Segmento"},
                    color_discrete_map=colores_segmento
                )

                fig_geo.update_layout(
                    autosize=True,
                    height=310,
                    margin=dict(t=10, l=10, r=10, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
                    yaxis=dict(categoryorder="array", categoryarray=orden_regiones),
                    xaxis=dict(tickformat="d", gridcolor="#e2e8f0")
                )

                st.plotly_chart(fig_geo, use_container_width=True, config=plot_config)
            else:
                st.info("Sin datos geográficos para graficar.")

with tab2:
    with st.container(border=True):
        st.markdown('<div class="chart-card-anchor" aria-hidden="true"></div>', unsafe_allow_html=True)
        st.markdown(
            chart_header(
                "Evolución anual de subcategorías",
                "Visualiza la tendencia mensual de ingresos por subcategoría."
            ),
            unsafe_allow_html=True
        )

        if not df_filtrado_maestra.empty:
            df_tendencia = (
                df_filtrado_maestra
                .set_index("Date")
                .groupby([pd.Grouper(freq="ME"), "Subcategory"])["Sales_amount"]
                .sum()
                .reset_index()
            )

            fig_line = px.line(
                df_tendencia,
                x="Date",
                y="Sales_amount",
                color="Subcategory",
                markers=True,
                labels={"Date": "Mes", "Sales_amount": "Ingresos mensuales ($)"}
            )

            fig_line.update_traces(hovertemplate="<b>%{data.name}</b><br>Ventas: $%{y:,.0f}<extra></extra>")
            fig_line.update_layout(
                autosize=True,
                height=310,
                margin=dict(t=10, l=10, r=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(gridcolor="#e2e8f0", tickformat="d"),
                xaxis=dict(gridcolor="#e2e8f0", title="", tickformat="%b %Y"),
                hovermode="closest"
            )

            st.plotly_chart(fig_line, use_container_width=True, config=plot_config)
        else:
            st.info("Sin datos para trazar la tendencia temporal.")