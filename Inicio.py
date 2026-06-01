import streamlit as st
import streamlit.components.v1 as components
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
    page_icon="📦"
)


# =========================
# CSS general compacto
# =========================
st.markdown(
    """
    <style>
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
            color: white;
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
            <div class="sidebar-icon">📦</div>
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

    subcategorias = sorted(df_maestra["Subcategory"].dropna().unique().tolist())
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
def compact_metric_card(title, value, description, badge, icon, accent_color, progress):
    title = escape(str(title))
    value = escape(str(value))
    description = escape(str(description))
    badge = escape(str(badge))
    icon = escape(str(icon))

    progress = max(0, min(safe_float(progress), 100))

    return f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{
        margin: 0;
        font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: transparent;
    }}

    .metric-card {{
        height: 132px;
        box-sizing: border-box;
        border-radius: 20px;
        padding: 14px 16px;
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid rgba(148, 163, 184, 0.22);
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
        overflow: hidden;
    }}

    .metric-top {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }}

    .metric-title {{
        color: #0f172a;
        font-size: 13px;
        font-weight: 900;
        margin: 0;
    }}

    .metric-icon {{
        width: 30px;
        height: 30px;
        border-radius: 11px;
        background: {accent_color};
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 15px;
    }}

    .metric-value {{
        color: #0f172a;
        font-size: 23px;
        font-weight: 950;
        letter-spacing: -1px;
        line-height: 1;
        margin: 0;
    }}

    .metric-description {{
        color: #64748b;
        font-size: 11px;
        font-weight: 650;
        margin: 5px 0 8px 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .metric-footer {{
        display: flex;
        align-items: center;
        gap: 8px;
    }}

    .metric-badge {{
        background: rgba(15, 23, 42, 0.06);
        color: #334155;
        font-size: 10px;
        font-weight: 800;
        padding: 4px 8px;
        border-radius: 999px;
        white-space: nowrap;
    }}

    .metric-track {{
        flex: 1;
        height: 6px;
        background: #e5e7eb;
        border-radius: 999px;
        overflow: hidden;
    }}

    .metric-fill {{
        height: 100%;
        width: {progress:.1f}%;
        background: {accent_color};
        border-radius: 999px;
    }}
</style>
</head>

<body>
    <div class="metric-card">
        <div class="metric-top">
            <p class="metric-title">{title}</p>
            <div class="metric-icon">{icon}</div>
        </div>

        <h1 class="metric-value">{value}</h1>
        <p class="metric-description">{description}</p>

        <div class="metric-footer">
            <span class="metric-badge">{badge}</span>
            <div class="metric-track">
                <div class="metric-fill"></div>
            </div>
        </div>
    </div>
</body>
</html>
"""


# =========================
# Encabezado
# =========================
st.markdown(
    '<h1 class="main-title">Panel de Control Principal</h1>',
    unsafe_allow_html=True
)


# =========================
# Fila superior: 3 tarjetas
# =========================
col1, col2, col3 = st.columns(3)

with col1:
    components.html(
        compact_metric_card(
            title="Overstock Crítico",
            value=f"{productos_criticos:,} productos",
            description=f"{unidades_excedentes:,.0f} unidades excedentes",
            badge="Riesgo alto",
            icon="🚨",
            accent_color="#dc2626",
            progress=progreso_overstock
        ),
        height=145,
        scrolling=False
    )

with col2:
    components.html(
        compact_metric_card(
            title="Días Prom. Inventario",
            value=f"{dias_promedio_inventario:.0f} días",
            description=f"{dias_promedio_critico:.0f} días en productos críticos",
            badge="Inventario lento",
            icon="⏳",
            accent_color="#f59e0b",
            progress=progreso_dias
        ),
        height=145,
        scrolling=False
    )

with col3:
    components.html(
        compact_metric_card(
            title="Rotación Inventario",
            value=f"{rotacion_promedio:.2f}x",
            description=f"{rotacion_critica:.2f}x en productos críticos",
            badge="Baja rotación",
            icon="🔄",
            accent_color="#2563eb",
            progress=progreso_rotacion
        ),
        height=145,
        scrolling=False
    )


# =========================
# Datos para gráfica
# =========================
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
    height=310,
    margin=dict(l=35, r=35, t=10, b=35),
    xaxis=dict(title=None),
    yaxis=dict(title="Vendidas", showgrid=True),
    yaxis2=dict(
        title="Stock",
        overlaying="y",
        side="right",
        showgrid=False
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.03,
        xanchor="right",
        x=1
    ),
    hovermode="x unified"
)


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

    top5_items_html += f"""
    <div class="ranking-item">
        <div class="ranking-top">
            <span class="product-name">{producto_item}</span>
            <strong>{exceso:,.0f}</strong>
        </div>
        <div class="bar-track">
            <div class="bar-fill" style="width:{porcentaje_barra:.1f}%;"></div>
        </div>
    </div>
    """

# =========================
# Panel lateral compacto
# =========================
side_panel_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{
        margin: 0;
        font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: transparent;
    }}

    .side-card {{
        height: 250px;
        box-sizing: border-box;
        border-radius: 24px;
        padding: 20px 22px;
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid rgba(148, 163, 184, 0.22);
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
        overflow: hidden;
    }}

    .title {{
        color: #0f172a;
        font-size: 18px;
        font-weight: 950;
        margin: 0 0 14px 0;
    }}

    .content-grid {{
        display: grid;
        grid-template-columns: 0.95fr 1.4fr;
        gap: 22px;
        align-items: start;
    }}

    .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 14px;
    width: 100%;
}}

.kpi-wide {{
    grid-column: 1 / span 2;
}}

.kpi {{
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.85);
    border: 1px solid rgba(148, 163, 184, 0.22);
    padding: 14px 12px;
    min-height: 74px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}}

.kpi-label {{
    color: #64748b;
    font-size: 10px;
    font-weight: 850;
    text-transform: uppercase;
    margin: 0 0 8px 0;
    white-space: nowrap;
}}

.kpi-value {{
    color: #0f172a;
    font-size: 24px;
    font-weight: 950;
    letter-spacing: -0.8px;
    line-height: 1;
    margin: 0;
}}

.kpi-value-wide {{
    font-size: 28px;
}}

    .section-title {{
        color: #0f172a;
        font-size: 14px;
        font-weight: 900;
        margin: 0 0 10px 0;
    }}

    .ranking-item {{
        margin-bottom: 8px;
    }}

    .ranking-top {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
        color: #111827;
        font-size: 12px;
        font-weight: 800;
    }}

    .ranking-top strong {{
        color: #dc2626;
        font-size: 12px;
    }}

    .bar-track {{
        width: 100%;
        height: 7px;
        background: #fee2e2;
        border-radius: 999px;
        overflow: hidden;
    }}

    .bar-fill {{
        height: 100%;
        background: linear-gradient(90deg, #ef4444, #991b1b);
        border-radius: 999px;
    }}

    .footer {{
        color: #94a3b8;
        font-size: 10px;
        font-weight: 650;
        margin-top: 6px;
    }}
</style>
</head>

<body>
    <div class="side-card">

        <div class="content-grid">
            <div class="kpi-grid">
    <div class="kpi">
        <p class="kpi-label">% ventas</p>
        <p class="kpi-value">{porcentaje_ventas:.1f}%</p>
    </div>

    <div class="kpi">
        <p class="kpi-label">Sell-through</p>
        <p class="kpi-value">{sell_through_rate:.1f}%</p>
    </div>

    <div class="kpi kpi-wide">
        <p class="kpi-label">Ventas</p>
        <p class="kpi-value kpi-value-wide">{ventas_unidades_totales:,.0f}</p>
    </div>
</div>

            <div>
                <p class="section-title">Top 5 productos con mayor sobrestock</p>

                {top5_items_html}

                <p class="footer">
                    Medido por unidades excedentes de stock.
                </p>
            </div>
        </div>
    </div>
</body>
</html>
"""


st.plotly_chart(
    fig,
    use_container_width=True,
    config={"displayModeBar": False}
)

components.html(
    side_panel_html,
    height=270,
    scrolling=False
)