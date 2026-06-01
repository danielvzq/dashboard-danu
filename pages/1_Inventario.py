import streamlit as st
import streamlit.components.v1 as components
from html import escape
import pandas as pd
import numpy as np
from pathlib import Path


# =========================
# Configuración
# =========================
st.set_page_config(
    layout="wide",
    page_title="Inventario",
    page_icon="📦"
)


# =========================
# CSS general
# =========================
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 0.5rem !important;
            padding-left: 1.4rem !important;
            padding-right: 1.4rem !important;
            max-width: 100% !important;
        }

        h1, h2, h3 {
            margin-top: 0 !important;
            margin-bottom: 0.5rem !important;
        }

        div[data-testid="stVerticalBlock"] {
            gap: 0.5rem !important;
        }

        iframe {
            display: block;
        }

        .main-title {
            color: white;
            font-size: 34px;
            font-weight: 950;
            letter-spacing: -1px;
            margin: 0 0 14px 0;
            line-height: 1.1;
        }

        .main-subtitle {
            color: #94a3b8;
            font-size: 15px;
            font-weight: 600;
            margin-top: -6px;
            margin-bottom: 14px;
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
def formato_numero(valor):
    if pd.isna(valor):
        return "0"

    valor = float(valor)

    if abs(valor) >= 1_000_000:
        return f"{valor / 1_000_000:.1f}M"

    if abs(valor) >= 1_000:
        return f"{valor / 1_000:.1f}K"

    return f"{valor:,.0f}"


def formato_pesos(valor):
    if pd.isna(valor):
        return "$0"

    valor = float(valor)

    if abs(valor) >= 1_000_000:
        return f"${valor / 1_000_000:.1f}M"

    if abs(valor) >= 1_000:
        return f"${valor / 1_000:.1f}K"

    return f"${valor:,.0f}"


def safe_div(a, b):
    return a / b if b not in [0, None] and not pd.isna(b) else 0


# =========================
# Cargar datos
# =========================
@st.cache_data
def cargar_datos():
    ruta = Path("data/df_Maestra.csv")
    df = pd.read_csv(ruta)

    df.columns = df.columns.str.strip()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    columnas_numericas = [
        "Units_sold",
        "Stock",
        "Units_expected",
        "Sales_amount",
        "Sell_through_pct",
        "Days_inventory",
        "Stock_turnover"
    ]

    for col in columnas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


df_maestra = cargar_datos()


# =========================
# Sidebar
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
    region = st.selectbox("Región", ["Todas"] + regiones)

    categorias = sorted(df_maestra["Category"].dropna().unique().tolist())
    categoria = st.selectbox("Categoría", ["Todas"] + categorias)

    subcategorias = sorted(df_maestra["Subcategory"].dropna().unique().tolist())
    subcategoria = st.selectbox("Subcategoría", ["Todas"] + subcategorias)


# =========================
# Aplicar filtros
# =========================
df = df_maestra.copy()

if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
    fecha_inicio, fecha_fin = rango_fechas

    df = df[
        (df["Date"].dt.date >= fecha_inicio) &
        (df["Date"].dt.date <= fecha_fin)
    ]

if region != "Todas":
    df = df[df["Region"] == region]

if categoria != "Todas":
    df = df[df["Category"] == categoria]

if subcategoria != "Todas":
    df = df[df["Subcategory"] == subcategoria]


# =========================
# Cálculos de inventario
# =========================
# Sobrestock real: inventario disponible menos unidades vendidas.
# Si quieres mantener tu métrica anterior, cambia Units_sold por Units_expected.
df["Exceso_stock"] = (df["Stock"] - df["Units_sold"]).clip(lower=0)

# Precio unitario estimado
df["Precio_unitario"] = np.where(
    df["Units_sold"] > 0,
    df["Sales_amount"] / df["Units_sold"],
    np.nan
)

precio_global = df["Precio_unitario"].replace([np.inf, -np.inf], np.nan).median()

if "Subcategory" in df.columns:
    df["Precio_unitario"] = df["Precio_unitario"].fillna(
        df.groupby("Subcategory")["Precio_unitario"].transform("median")
    )

if "Category" in df.columns:
    df["Precio_unitario"] = df["Precio_unitario"].fillna(
        df.groupby("Category")["Precio_unitario"].transform("median")
    )

df["Precio_unitario"] = df["Precio_unitario"].fillna(precio_global).fillna(0)

df["Valor_inmovilizado"] = df["Exceso_stock"] * df["Precio_unitario"]

# =========================
# Identificador de producto
# =========================
if "Product_name" in df.columns:
    col_producto = "Product_name"
elif "Product_Name" in df.columns:
    col_producto = "Product_Name"
else:
    col_producto = "Product_id"

if "Product_id" in df.columns and col_producto != "Product_id":
    df["Producto_label"] = (
        df[col_producto].astype(str).str.strip()
        + " · ID "
        + df["Product_id"].astype(str)
    )
else:
    df["Producto_label"] = df[col_producto].astype(str)

# =========================
# Resumen por producto
# =========================
producto_resumen = (
    df
    .groupby("Producto_label", as_index=False)
    .agg(
        unidades_vendidas=("Units_sold", "sum"),
        stock_total=("Stock", "sum"),
        stock_promedio=("Stock", "mean"),
        exceso_stock=("Exceso_stock", "sum"),
        valor_inmovilizado=("Valor_inmovilizado", "sum"),
        ventas_monto=("Sales_amount", "sum")
    )
)

producto_resumen["sell_through_estimado"] = producto_resumen.apply(
    lambda row: safe_div(row["unidades_vendidas"], row["stock_total"]) * 100,
    axis=1
)

producto_resumen = producto_resumen.sort_values(
    "exceso_stock",
    ascending=False
)

total_productos = producto_resumen["Producto_label"].nunique()
total_exceso = producto_resumen["exceso_stock"].sum()
total_valor_inmovilizado = producto_resumen["valor_inmovilizado"].sum()

top5_productos = producto_resumen.head(5).copy()

exceso_top5 = top5_productos["exceso_stock"].sum()
participacion_top5 = safe_div(exceso_top5, total_exceso) * 100

# Stock muerto: productos con stock, pero cero ventas en el periodo
stock_muerto_df = producto_resumen[
    (producto_resumen["unidades_vendidas"] <= 0) &
    (producto_resumen["stock_total"] > 0)
].copy()

# Movimiento mínimo: vendieron algo, pero sell-through menor a 1%
mov_minimo_df = producto_resumen[
    (producto_resumen["unidades_vendidas"] > 0) &
    (producto_resumen["sell_through_estimado"] < 1) &
    (producto_resumen["stock_total"] > 0)
].copy()

stock_muerto_count = stock_muerto_df["Producto_label"].nunique()
mov_minimo_count = mov_minimo_df["Producto_label"].nunique()

valor_stock_muerto = stock_muerto_df["valor_inmovilizado"].sum()

top_stock_muerto = (
    pd.concat([stock_muerto_df, mov_minimo_df])
    .drop_duplicates(subset=["Producto_label"])
    .sort_values("valor_inmovilizado", ascending=False)
    .head(4)
)


# =========================
# HTML Top 5 productos
# =========================
max_exceso = top5_productos["exceso_stock"].max() if not top5_productos.empty else 1

top5_html = ""

for _, row in top5_productos.iterrows():
    nombre = escape(str(row["Producto_label"]))
    exceso = row["exceso_stock"]
    valor = row["valor_inmovilizado"]
    porcentaje_barra = safe_div(exceso, max_exceso) * 100
    porcentaje_total = safe_div(exceso, total_exceso) * 100

    top5_html += f"""
    <div class="product-row">
        <div class="product-top">
            <span class="product-name">{nombre}</span>
            <span class="product-value">{exceso:,.0f} u.</span>
        </div>

        <div class="bar-track">
            <div class="bar-fill" style="width:{porcentaje_barra:.1f}%;"></div>
        </div>

        <div class="product-bottom">
            <span>{porcentaje_total:.1f}% del exceso total</span>
            <span>{formato_pesos(valor)} inmovilizados</span>
        </div>
    </div>
    """


# =========================
# HTML Stock muerto
# =========================
stock_muerto_html = ""

if top_stock_muerto.empty:
    stock_muerto_html = """
    <div class="empty-state">
        No se detectaron productos con stock muerto o movimiento mínimo.
    </div>
    """
else:
    for _, row in top_stock_muerto.iterrows():
        nombre = escape(str(row["Producto_label"]))
        unidades = row["unidades_vendidas"]
        stock = row["stock_total"]
        valor = row["valor_inmovilizado"]

        etiqueta = "Sin ventas" if unidades <= 0 else "Movimiento mínimo"

        stock_muerto_html += f"""
        <div class="dead-row">
            <div>
                <p class="dead-name">{nombre}</p>
                <p class="dead-meta">{etiqueta} · Stock acumulado: {stock:,.0f}</p>
            </div>
            <div class="dead-value">{formato_pesos(valor)}</div>
        </div>
        """


producto_mayor_problema = (
    escape(str(top5_productos.iloc[0]["Producto_label"]))
    if not top5_productos.empty
    else "Sin producto"
)

valor_top5 = top5_productos["valor_inmovilizado"].sum()


# =========================
# Vista HTML completa
# =========================
dashboard_html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{
        margin: 0;
        background: transparent;
        font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}

    .view {{
        height: 670px;
        box-sizing: border-box;
        overflow: hidden;
    }}

    .kpi-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-bottom: 14px;
    }}

    .kpi-card {{
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 24px;
        padding: 18px 20px;
        height: 130px;
        box-sizing: border-box;
        box-shadow: 0 14px 32px rgba(15, 23, 42, 0.10);
        overflow: hidden;
    }}

    .kpi-top {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 13px;
    }}

    .kpi-label {{
        color: #0f172a;
        font-size: 13px;
        font-weight: 950;
        margin: 0;
    }}

    .kpi-icon {{
        width: 34px;
        height: 34px;
        border-radius: 13px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 17px;
        font-weight: 900;
    }}

    .red {{ background: #dc2626; }}
    .orange {{ background: #f59e0b; }}
    .blue {{ background: #2563eb; }}
    .purple {{ background: #7c3aed; }}

    .kpi-value {{
        color: #0f172a;
        font-size: 27px;
        font-weight: 950;
        line-height: 1;
        letter-spacing: -1px;
        margin: 0;
    }}

    .kpi-desc {{
        color: #64748b;
        font-size: 12px;
        font-weight: 700;
        margin: 7px 0 0 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .main-grid {{
        display: grid;
        grid-template-columns: 1.25fr 0.95fr;
        gap: 14px;
        height: 365px;
        margin-bottom: 14px;
    }}

    .panel {{
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 28px;
        padding: 22px 24px;
        box-sizing: border-box;
        box-shadow: 0 14px 32px rgba(15, 23, 42, 0.10);
        overflow: hidden;
    }}

    .panel-title {{
        color: #0f172a;
        font-size: 19px;
        font-weight: 950;
        margin: 0 0 4px 0;
        letter-spacing: -0.3px;
    }}

    .panel-subtitle {{
        color: #64748b;
        font-size: 12px;
        font-weight: 700;
        margin: 0 0 15px 0;
    }}

    .product-row {{
        margin-bottom: 13px;
    }}

    .product-top {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        margin-bottom: 6px;
    }}

    .product-name {{
        color: #111827;
        font-size: 14px;
        font-weight: 900;
        max-width: 78%;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .product-value {{
        color: #dc2626;
        font-size: 14px;
        font-weight: 950;
        white-space: nowrap;
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

    .product-bottom {{
        display: flex;
        justify-content: space-between;
        color: #94a3b8;
        font-size: 11px;
        font-weight: 750;
        margin-top: 5px;
    }}

    .dead-summary {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        margin-bottom: 14px;
    }}

    .dead-mini {{
        background: rgba(255, 255, 255, 0.82);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 18px;
        padding: 14px;
        box-sizing: border-box;
    }}

    .dead-mini-label {{
        color: #64748b;
        font-size: 10px;
        font-weight: 900;
        text-transform: uppercase;
        margin: 0 0 7px 0;
    }}

    .dead-mini-value {{
        color: #0f172a;
        font-size: 24px;
        font-weight: 950;
        margin: 0;
        line-height: 1;
    }}

    .dead-row {{
        display: grid;
        grid-template-columns: 1fr auto;
        gap: 10px;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid rgba(148, 163, 184, 0.20);
    }}

    .dead-name {{
        color: #111827;
        font-size: 13px;
        font-weight: 900;
        margin: 0;
        max-width: 330px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .dead-meta {{
        color: #64748b;
        font-size: 11px;
        font-weight: 700;
        margin: 4px 0 0 0;
    }}

    .dead-value {{
        color: #dc2626;
        font-size: 13px;
        font-weight: 950;
        white-space: nowrap;
    }}

    .empty-state {{
        color: #64748b;
        font-size: 13px;
        font-weight: 700;
        background: rgba(241, 245, 249, 0.9);
        border-radius: 16px;
        padding: 16px;
    }}

    .insight-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 14px;
        height: 145px;
    }}

    .insight {{
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid rgba(148, 163, 184, 0.22);
        border-radius: 24px;
        padding: 18px 20px;
        box-sizing: border-box;
        box-shadow: 0 14px 32px rgba(15, 23, 42, 0.10);
        overflow: hidden;
    }}

    .insight-label {{
        color: #64748b;
        font-size: 11px;
        font-weight: 950;
        text-transform: uppercase;
        margin: 0 0 8px 0;
    }}

    .insight-title {{
        color: #0f172a;
        font-size: 16px;
        font-weight: 950;
        margin: 0 0 6px 0;
        line-height: 1.15;
    }}

    .insight-text {{
        color: #64748b;
        font-size: 12px;
        font-weight: 700;
        line-height: 1.35;
        margin: 0;
    }}
</style>
</head>

<body>
    <div class="view">

        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-top">
                    <p class="kpi-label">Valor inmovilizado</p>
                    <div class="kpi-icon purple">💰</div>
                </div>
                <h2 class="kpi-value">{formato_pesos(total_valor_inmovilizado)}</h2>
                <p class="kpi-desc">Capital estimado detenido en exceso de inventario</p>
            </div>

            <div class="kpi-card">
                <div class="kpi-top">
                    <p class="kpi-label">Unidades excedentes</p>
                    <div class="kpi-icon red">📦</div>
                </div>
                <h2 class="kpi-value">{formato_numero(total_exceso)}</h2>
                <p class="kpi-desc">Inventario excedente acumulado en productos</p>
            </div>

            <div class="kpi-card">
                <div class="kpi-top">
                    <p class="kpi-label">Stock muerto</p>
                    <div class="kpi-icon orange">⚠️</div>
                </div>
                <h2 class="kpi-value">{stock_muerto_count:,} productos</h2>
                <p class="kpi-desc">Con stock disponible y cero ventas en el periodo</p>
            </div>

            <div class="kpi-card">
                <div class="kpi-top">
                    <p class="kpi-label">Concentración Top 5</p>
                    <div class="kpi-icon blue">🎯</div>
                </div>
                <h2 class="kpi-value">{participacion_top5:.1f}%</h2>
                <p class="kpi-desc">Del sobrestock concentrado en solo 5 productos</p>
            </div>
        </div>

        <div class="main-grid">
            <div class="panel">
                <p class="panel-title">Productos que concentran el problema</p>
                <p class="panel-subtitle">Top 5 productos responsables de la mayor parte del sobrestock</p>

                {top5_html}
            </div>

            <div class="panel">
                <p class="panel-title">Stock muerto y movimiento mínimo</p>
                <p class="panel-subtitle">Productos con ventas nulas o sell-through menor a 1%</p>

                <div class="dead-summary">
                    <div class="dead-mini">
                        <p class="dead-mini-label">Sin ventas</p>
                        <h3 class="dead-mini-value">{stock_muerto_count:,}</h3>
                    </div>

                    <div class="dead-mini">
                        <p class="dead-mini-label">Movimiento mínimo</p>
                        <h3 class="dead-mini-value">{mov_minimo_count:,}</h3>
                    </div>
                </div>

                {stock_muerto_html}
            </div>
        </div>

        <div class="insight-grid">
            <div class="insight">
                <p class="insight-label">Punto de partida</p>
                <h3 class="insight-title">{producto_mayor_problema}</h3>
                <p class="insight-text">
                    Es el producto con mayor exceso; debe revisarse antes que el resto del catálogo.
                </p>
            </div>

            <div class="insight">
                <p class="insight-label">Impacto económico</p>
                <h3 class="insight-title">{formato_pesos(valor_top5)} en Top 5</h3>
                <p class="insight-text">
                    El dinero inmovilizado permite priorizar acciones por impacto financiero, no solo por unidades.
                </p>
            </div>

            <div class="insight">
                <p class="insight-label">Acción ejecutiva</p>
                <h3 class="insight-title">Liquidar, redistribuir o pausar compra</h3>
                <p class="insight-text">
                    Los productos con stock muerto deben tratarse como prioridad operativa y comercial.
                </p>
            </div>
        </div>

    </div>
</body>
</html>
"""


# =========================
# Render
# =========================
st.markdown(
    '<h1 class="main-title">Impacto del Inventario</h1>',
    unsafe_allow_html=True
)

st.markdown(
    '<p class="main-subtitle">Vista ejecutiva para identificar productos críticos, stock muerto y dinero inmovilizado.</p>',
    unsafe_allow_html=True
)

components.html(
    dashboard_html,
    height=690,
    scrolling=False
)