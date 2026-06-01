import streamlit as st
import streamlit_shadcn_ui as ui
import streamlit.components.v1 as components
from html import escape 
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# =========================
# Configuración de página
# =========================
st.set_page_config(
    layout="wide"
)

# =========================
# Cargar CSS personalizado
# =========================
css_path = Path("styles/main.css")

if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

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

sell_through_promedio = df_filtrado["Sell_through_pct"].mean()

dias_promedio_inventario = df_filtrado["Days_inventory"].replace([float("inf"), -float("inf")], pd.NA).dropna().mean()

dias_promedio_critico = (
    df_critico["Days_inventory"].replace([float("inf"), -float("inf")], pd.NA).dropna().mean()
    if not df_critico.empty
    else 0
)

accion_prioritaria = (
    df_critico["Priority_action"].mode()[0]
    if not df_critico.empty
    else "Sin acción crítica"
)

rotacion_promedio = df_filtrado["Stock_turnover"].replace(
    [float("inf"), -float("inf")], pd.NA
).dropna().mean()

rotacion_critica = (
    df_critico["Stock_turnover"].replace(
        [float("inf"), -float("inf")], pd.NA
    ).dropna().mean()
    if not df_critico.empty
    else 0
)

# =========================
# Encabezado
# =========================
st.title("Panel de Control Principal")

# =========================
# Tarjetas superiores modernas
# =========================

def modern_metric_card(title, value, description, badge, icon, accent_color, progress):
    title = escape(str(title))
    value = escape(str(value))
    description = escape(str(description))
    badge = escape(str(badge))
    icon = escape(str(icon))

    progress = max(0, min(progress, 100))

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
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 26px;
        padding: 28px;
        height: 190px;
        box-sizing: border-box;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.10);
        position: relative;
        overflow: hidden;
    }}

    .metric-card::before {{
        content: "";
        position: absolute;
        top: -40px;
        right: -40px;
        width: 120px;
        height: 120px;
        opacity: 0.10;
        border-radius: 999px;
    }}

    .metric-top {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 18px;
    }}

    .metric-title {{
        color: #0f172a;
        font-size: 17px;
        font-weight: 900;
        margin: 0;
    }}

    .metric-icon {{
        width: 38px;
        height: 38px;
        border-radius: 14px;
        background: {accent_color};
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 19px;
        box-shadow: 0 10px 22px rgba(15, 23, 42, 0.18);
    }}

    .metric-value {{
        color: #0f172a;
        font-size: 28px;
        font-weight: 950;
        letter-spacing: -1.6px;
        line-height: 1;
        margin: 0;
    }}

    .metric-description {{
        color: #64748b;
        font-size: 14px;
        font-weight: 650;
        margin: 10px 0 0 0;
    }}

    .metric-footer {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: 18px;
    }}

    .metric-badge {{
        background: rgba(15, 23, 42, 0.06);
        color: #334155;
        font-size: 12px;
        font-weight: 800;
        padding: 6px 10px;
        border-radius: 999px;
        white-space: nowrap;
    }}

    .metric-track {{
        flex: 1;
        height: 8px;
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

progreso_overstock = porcentaje_stock_critico
progreso_dias = min((dias_promedio_inventario / 365) * 100, 100)
progreso_rotacion = min((rotacion_promedio / 1) * 100, 100)

col1, col2, col3 = st.columns(3)

with col1:
    components.html(
        modern_metric_card(
            title="Overstock Crítico",
            value=f"{productos_criticos:,} productos",
            description=f"{unidades_excedentes:,.0f} unidades excedentes",
            badge="Riesgo alto",
            icon="🚨",
            accent_color="#dc2626",
            progress=progreso_overstock
        ),
        height=210,
        scrolling=False
    )

with col2:
    components.html(
        modern_metric_card(
            title="Días Prom. Inventario",
            value=f"{dias_promedio_inventario:.0f} días",
            description=f"{dias_promedio_critico:.0f} días en productos críticos",
            badge="Inventario lento",
            icon="⏳",
            accent_color="#f59e0b",
            progress=progreso_dias
        ),
        height=245,
        scrolling=False
    )

with col3:
    components.html(
        modern_metric_card(
            title="Rotación Inventario",
            value=f"{rotacion_promedio:.2f}x",
            description=f"{rotacion_critica:.2f}x en productos críticos",
            badge="Baja rotación",
            icon="🔄",
            accent_color="#2563eb",
            progress=progreso_rotacion
        ),
        height=245,
        scrolling=False
    )

# =========================
# Ventas vs Stock
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
        yaxis="y",
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
    title="Unidades vendidas vs stock por mes",
    xaxis=dict(
        title="Mes"
    ),
    yaxis=dict(
        title="Unidades vendidas",
        showgrid=True
    ),
    yaxis2=dict(
        title="Stock total",
        overlaying="y",
        side="right",
        showgrid=False
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    ),
    height=500,
    margin=dict(l=40, r=40, t=80, b=40),
    hovermode="x unified"
)

# =========================
# Tarjetas modernas debajo de la gráfica
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

sell_through_rate = (
    df_cards["Sell_through_pct"]
    .replace([float("inf"), -float("inf")], pd.NA)
    .dropna()
    .mean()
)

if pd.isna(sell_through_rate):
    sell_through_rate = 0

if sell_through_rate <= 1:
    sell_through_rate = sell_through_rate * 100

ventas_unidades_totales = df_cards["Units_sold"].sum()
ventas_monto_totales = df_cards["Sales_amount"].sum()
registros_ventas = df_cards.shape[0]

top5_sobrestock = ( #Cambiar a subcategoría
    df_cards
    .groupby("Category", as_index=False)["Exceso_stock"]
    .sum()
    .sort_values("Exceso_stock", ascending=False)
    .head(5)
)

max_sobrestock = top5_sobrestock["Exceso_stock"].max() if not top5_sobrestock.empty else 1

top5_items_html = ""

for _, row in top5_sobrestock.iterrows():
    categoria_item = escape(str(row["Category"]))
    exceso = row["Exceso_stock"]
    porcentaje_barra = (exceso / max_sobrestock) * 100 if max_sobrestock > 0 else 0

    top5_items_html += f"""
    <div class="ranking-item">
        <div class="ranking-top">
            <span class="ranking-name">{categoria_item}</span>
            <span class="ranking-value">{exceso:,.0f}</span>
        </div>
        <div class="bar-track">
            <div class="bar-fill" style="width:{porcentaje_barra:.1f}%;"></div>
        </div>
    </div>
    """


resumen_ventas_card_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{
        margin: 0;
        font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: transparent;
    }}

        .sales-card {{
        min-height: 390px;
        height: auto;
        box-sizing: border-box;
        border-radius: 28px;
        padding: 30px;
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid rgba(148, 163, 184, 0.22);
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.10);
        overflow: hidden;
        position: relative;
    }}

    .sales-card::before {{
        content: "";
        position: absolute;
        top: -70px;
        right: -70px;
        width: 190px;
        height: 190px;
        opacity: 0.10;
        border-radius: 999px;
    }}

    .header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 22px;
        position: relative;
        z-index: 2;
    }}

    .title {{
        color: #0f172a;
        font-size: 20px;
        font-weight: 950;
        margin: 0;
    }}

    .badge {{
        background: #ecfdf5;
        color: #047857;
        padding: 8px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 850;
        white-space: nowrap;
    }}

    .main-grid {{
        display: grid;
        grid-template-columns: 1.15fr 1fr;
        gap: 24px;
        align-items: stretch;
        position: relative;
        z-index: 2;
    }}

    .main-metric {{
        background: rgba(255, 255, 255, 0.76);
        border: 1px solid rgba(148, 163, 184, 0.20);
        border-radius: 24px;
        padding: 24px;
        min-height: 230px;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }}

    .metric-label {{
        color: #64748b;
        font-size: 13px;
        font-weight: 800;
        margin: 0 0 12px 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    .metric-value-big {{
        color: #0f172a;
        font-size: 56px;
        font-weight: 950;
        letter-spacing: -2.5px;
        line-height: 1;
        margin: 0;
    }}

    .metric-description {{
        color: #64748b;
        font-size: 14px;
        font-weight: 650;
        line-height: 1.45;
        margin: 14px 0 0 0;
    }}

    .progress-track {{
        width: 100%;
        height: 11px;
        background: #e5e7eb;
        border-radius: 999px;
        margin-top: 20px;
        overflow: hidden;
    }}

    .progress-fill {{
        height: 100%;
        width: {min(porcentaje_ventas, 100):.1f}%;
        background: linear-gradient(90deg, #22c55e, #15803d);
        border-radius: 999px;
    }}

    .side-metrics {{
        display: grid;
        grid-template-rows: repeat(2, minmax(0, 1fr));
        gap: 18px;
        height: 100%;
    }}

    .mini-card {{
        background: rgba(255, 255, 255, 0.78);
        border: 1px solid rgba(148, 163, 184, 0.20);
        border-radius: 22px;
        padding: 20px 24px;
        box-sizing: border-box;
        min-height: 106px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}

    .mini-top {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
    }}

    .mini-label {{
        color: #64748b;
        font-size: 12px;
        font-weight: 850;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 0.45px;
    }}

    .mini-icon {{
        width: 32px;
        height: 32px;
        border-radius: 12px;
        display: flex;
        justify-content: center;
        align-items: center;
        color: white;
        font-size: 16px;
        font-weight: 900;
    }}

    .green {{
        background: #16a34a;
    }}

    .blue {{
        background: #2563eb;
    }}

    .mini-value {{
        color: #0f172a;
        font-size: 30px;
        font-weight: 950;
        line-height: 1;
        letter-spacing: -1px;
        margin: 0;
    }}

    .mini-description {{
        color: #64748b;
        font-size: 13px;
        font-weight: 650;
        margin: 8px 0 0 0;
        line-height: 1.35;
    }}

    .footer {{
        color: #94a3b8;
        font-size: 12px;
        font-weight: 650;
        margin-top: 14px;
    }}
</style>
</head>

<body>
    <div class="sales-card">
        <div class="header">
            <p class="title">Resumen de ventas</p>
            <span class="badge">Filtros actuales</span>
        </div>

        <div class="main-grid">
            <div class="main-metric">
                <p class="metric-label">% de ventas</p>
                <h1 class="metric-value-big">{porcentaje_ventas:.1f}%</h1>
                <p class="metric-description">
                    ${ventas_filtradas_total:,.2f} de ${ventas_generales_total:,.2f} en ventas totales.
                </p>

                <div class="progress-track">
                    <div class="progress-fill"></div>
                </div>

                <p class="footer">
                    Participación de las ventas filtradas sobre el total general.
                </p>
            </div>

            <div class="side-metrics">
                <div class="mini-card">
                    <div class="mini-top">
                        <p class="mini-label">Sell-through rate</p>
                        <div class="mini-icon green">↗</div>
                    </div>
                    <h2 class="mini-value">{sell_through_rate:.1f}%</h2>
                    <p class="mini-description">
                        Inventario vendido promedio.
                    </p>
                </div>

                <div class="mini-card">
                    <div class="mini-top">
                        <p class="mini-label">Ventas totales</p>
                        <div class="mini-icon blue">🛒</div>
                    </div>
                    <h2 class="mini-value">{ventas_unidades_totales:,.0f}</h2>
                    <p class="mini-description">
                        Unidades vendidas · {registros_ventas:,} registros.
                    </p>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""


top5_card_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{
        margin: 0;
        font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: transparent;
    }}

    .card {{
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 28px;
        padding: 34px;
        height: 330px;
        box-sizing: border-box;
        box-shadow: 0 18px 40px rgba(15, 23, 42, 0.10);
        overflow: hidden;
    }}

    .title {{
        color: #0f172a;
        font-size: 20px;
        font-weight: 900;
        margin: 0 0 26px 0;
    }}

    .ranking-item {{
        margin-bottom: 18px;
    }}

    .ranking-top {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }}

    .ranking-name {{
        color: #111827;
        font-size: 15px;
        font-weight: 850;
    }}

    .ranking-value {{
        color: #dc2626;
        font-size: 15px;
        font-weight: 900;
    }}

    .bar-track {{
        width: 100%;
        height: 8px;
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
        font-size: 13px;
        font-weight: 600;
        margin-top: 20px;
    }}
</style>
</head>

<body>
    <div class="card">
        <p class="title">Top 5 categorías con mayor sobrestock</p>

        {top5_items_html}

        <p class="footer">
            Medido por unidades excedentes de stock.
        </p>
    </div>
</body>
</html>
"""

st.markdown("<br>", unsafe_allow_html=True)

# Tarjeta de Top 5 
components.html(top5_card_html, height=360, scrolling=False)

# =========================
# Pestañas
# =========================
st.markdown("### Detalles Operativos")

st.plotly_chart(fig, use_container_width=True)

# Tarjeta principal en una fila completa
components.html(resumen_ventas_card_html, height=430, scrolling=False)

if pd.isna(sell_through_rate):
    sell_through_rate = 0

# Por si tu columna viene en formato decimal, ejemplo: 0.35 en vez de 35
if sell_through_rate <= 1:
    sell_through_rate = sell_through_rate * 100

ventas_unidades_totales = df_cards["Units_sold"].sum()
ventas_monto_totales = df_cards["Sales_amount"].sum()
registros_ventas = df_cards.shape[0]

