# pages/4_Pronosticos.py
# DANUStore — Pronósticos de Demanda

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import streamlit.components.v1 as components

import pandas as pd
import numpy as np
import plotly.graph_objects as go

from pathlib import Path
from html import escape

from src.forecast_engine import (
    load_data,
    fit_prophet,
    build_forecast_summary,
    build_subcat_region_forecast,
    build_region_forecast,
)
from src.redistribucion import (
    REGION_COORDS,
    REG_LABEL,
    GEO_LAYOUT,
    build_redist_base,
    build_monthly_forecast,
    build_wave_plan,
    build_animation_frames,
)

# =========================
# Configuración de página
# =========================
st.set_page_config(
    layout="wide",
    page_title="Pronósticos — DANUStore",
    page_icon="🚀"
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

        h1, h2, h3, h4 {
            margin-top: 0 !important;
            margin-bottom: 0.6rem !important;
        }

        

        .main-title {
            color: white;
            font-size: 30px;
            font-weight: 950;
            letter-spacing: -0.8px;
            margin: 0 0 6px 0;
            line-height: 1.2;
        }

        .forecast-context {
            color: rgba(255, 255, 255, 0.78);
            font-size: 13px;
            font-weight: 700;
            margin: 0 0 16px 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
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
            line-height: 1.35;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 24px !important;
            border: 1px solid rgba(148, 163, 184, 0.22) !important;
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%) !important;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.035) !important;
            padding: 0.4rem 0.6rem !important;
        }

        div[data-testid="stPlotlyChart"] {
            border-radius: 24px !important;
            border: 1px solid rgba(148, 163, 184, 0.22) !important;
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%) !important;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.035) !important;
            padding: 0.45rem 0.65rem !important;
        }

        div[data-testid="stMetric"] {
            border-radius: 18px !important;
            border: 1px solid rgba(148, 163, 184, 0.22) !important;
            background: rgba(255, 255, 255, 0.88) !important;
            padding: 0.65rem 0.75rem !important;
        }

        div[data-testid="stDataFrame"] {
            border-radius: 20px !important;
            overflow: hidden !important;
            border: 1px solid rgba(148, 163, 184, 0.22) !important;
            background: #ffffff !important;
        }

        button[kind="secondary"], button[data-baseweb="tab"] {
            border-radius: 999px !important;
            font-weight: 800 !important;
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
# Tarjeta compacta superior
# =========================
def metric_card(title, value, description, badge, icon, accent, progress):
    title = escape(str(title))
    value = escape(str(value))
    description = escape(str(description))
    badge = escape(str(badge))
    icon = escape(str(icon))

    try:
        progress = max(0, min(float(progress), 100))
    except Exception:
        progress = 0

    return f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{
        margin: 0;
        background: transparent;
        font-family: Inter, system-ui, sans-serif;
    }}

    .metric-card {{
        position: relative;
        overflow: hidden;
        height: 155px;
        box-sizing: border-box;
        border-radius: 24px;
        padding: 26px 20px 18px 20px;
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid rgba(148, 163, 184, 0.28);
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
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .metric-value {{
        color: #0f172a;
        font-size: clamp(20px, 2.1vw, 28px);
        font-weight: 950;
        line-height: 1.05;
        margin: 0 0 8px 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .metric-description {{
        color: #64748b;
        font-size: 13px;
        font-weight: 700;
        line-height: 1.3;
        margin: 0;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }}

    .metric-footer {{
        display: flex;
        align-items: center;
        gap: 8px;
        margin-top: 10px;
    }}

    .metric-badge {{
        color: #334155;
        background: rgba(15, 23, 42, 0.06);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 999px;
        padding: 4px 9px;
        font-size: 10px;
        font-weight: 850;
        white-space: nowrap;
    }}

    .metric-track {{
        flex: 1;
        height: 6px;
        border-radius: 999px;
        background: #e5e7eb;
        overflow: hidden;
    }}

    .metric-fill {{
        width: {progress:.1f}%;
        height: 100%;
        border-radius: 999px;
        background: var(--accent-color);
    }}
</style>
</head>

<body>
    <div class="metric-card" style="--accent-color: {accent};">
        <p class="metric-title">{title}</p>
        <p class="metric-value">{value}</p>
        <p class="metric-description">{description}</p>
        <div class="metric-footer">
            <span class="metric-badge">{icon} {badge}</span>
            <div class="metric-track"><div class="metric-fill"></div></div>
        </div>
    </div>
</body>
</html>
"""


dot = lambda color: (
    f'<span style="display:inline-block;width:11px;height:11px;border-radius:50%;'
    f'background:{color};margin-right:5px;vertical-align:middle;"></span>'
)

def _mini_kpi(label, value):
    label = escape(str(label))
    value = escape(str(value))

    return f"""
    <div style="
        height: 74px;
        box-sizing: border-box;
        border-radius: 18px;
        padding: 12px 14px;
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid rgba(148, 163, 184, 0.28);
        display: flex;
        flex-direction: column;
        justify-content: center;
    ">
        <p style="
            margin: 0 0 6px 0;
            font-size: 10px;
            font-weight: 850;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: .25px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        ">{label}</p>
        <p style="
            margin: 0;
            font-size: 20px;
            font-weight: 950;
            color: #0f172a;
            letter-spacing: -0.6px;
            line-height: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        ">{value}</p>
    </div>
    """


def section_title(label, subtitle="", popover_title="Ver", popover_body=""):
    """Renders a prominent section title with an optional info popover beside it."""

    # CSS para evitar que el botón del popover se parta en varias líneas
    st.markdown(
        """
        <style>
        div[data-testid="stPopover"] button {
            min-width: 105px !important;
            height: 38px !important;
            white-space: nowrap !important;
            border-radius: 999px !important;
            font-weight: 700 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 0 16px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Columna del botón más ancha para evitar que "Ver" se corte
    col_t, col_p = st.columns([6.5, 1.7])

    with col_t:
        st.markdown(
            f"""
            <div class="chart-card-header" style="padding:0;margin-bottom:8px;">
                <h3 style="
                    color:#0f172a;
                    font-size:20px;
                    font-weight:900;
                    margin:0;
                    letter-spacing:-0.4px;
                    line-height:1.15;
                ">
                    {label}
                </h3>
                <p style="
                    color:#64748b;
                    font-size:13px;
                    font-weight:700;
                    margin:8px 0 0 0;
                    line-height:1.25;
                ">
                    {subtitle}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_p:
        if popover_body:
            st.markdown(
                "<div style='height:4px;'></div>",
                unsafe_allow_html=True
            )

            with st.popover(popover_title if popover_title else "Ver", use_container_width=True):
                st.markdown(popover_body)

# COLORES Y UMBRALES
def period_thresholds(h):
    return ((1.15)**(h/12)-1)*100, ((1.25)**(h/12)-1)*100

def bar_color(pct, h):
    r15, r25 = period_thresholds(h)
    if pct >= r25: return "#16a34a"
    if pct >= r15: return "#2563eb"
    return "#dc2626"

def growth_label(pct, h):
    r15, r25 = period_thresholds(h)
    if pct >= r25: return "Crecimiento optimo",    "#16a34a"
    if pct >= r15: return "Crecimiento saludable", "#2563eb"
    if pct >= 0:   return "Crecimiento moderado",  "#f59e0b"
    return "En descenso", "#dc2626"

def annualize(pct, h):
    return ((1+pct/100)**(12/max(h,1))-1)*100

# ACCURACY DEL MODELO
@st.cache_data(show_spinner=False)
def compute_model_accuracy() -> float:
    df     = load_data()
    months = sorted(df["YearMonth"].unique())
    errors = []
    for i in range(6, len(months)):
        train_m = months[:i]; test_m = months[i]
        train_data = df[df["YearMonth"].isin(train_m)]
        test_data  = df[df["YearMonth"] == test_m]
        last3      = train_m[-3:]
        pred   = train_data[train_data["YearMonth"].isin(last3)].groupby("Subcategory")["Units_sold"].mean()
        actual = test_data.groupby("Subcategory")["Units_sold"].mean()
        common = pred.index.intersection(actual.index)
        if len(common) > 0:
            mape_i = (np.abs(actual[common]-pred[common])/actual[common].replace(0,np.nan)).mean()*100
            errors.append(mape_i)
    return round(100-float(np.mean(errors)),1) if errors else 0.0

# DATOS
df_maestra     = load_data()
MODEL_ACCURACY = compute_model_accuracy()

# SIDEBAR
with st.sidebar:
    st.markdown(
        '<div class="sidebar-header"><div class="sidebar-icon">🚀</div>'
        '<div><p class="sidebar-title">RocketData</p>'
        '<p class="sidebar-subtitle">Inventory Dashboard</p></div></div>',
        unsafe_allow_html=True,
    )
    st.page_link("Inicio.py",              label="Inicio")
    st.page_link("pages/1_Inventario.py",  label="Inventario")
    st.page_link("pages/2_Ventas.py",      label="Ventas")
    st.page_link("pages/3_Alertas.py",     label="Alertas")
    st.page_link("pages/4_Pronosticos.py", label="Pronósticos")

    st.divider()
    st.markdown("### Filtros")

    fecha_min    = df_maestra["Date"].min().date()
    fecha_max    = df_maestra["Date"].max().date()
    rango_fechas = st.date_input("Rango de fechas",
        value=(fecha_min, fecha_max), min_value=fecha_min, max_value=fecha_max)

    regiones   = sorted(df_maestra["Region"].dropna().unique().tolist())
    region_sel = st.selectbox("Región", ["Todas"] + regiones)

    categorias = sorted(df_maestra["Category"].dropna().unique().tolist())
    cat_sel    = st.selectbox("Categoría", ["Todas"] + categorias)

    if cat_sel == "Todas":
        subcategorias = sorted(df_maestra["Subcategory"].dropna().unique().tolist())
    else:
        subcategorias = sorted(
            df_maestra.loc[df_maestra["Category"]==cat_sel,"Subcategory"]
            .dropna().unique().tolist())
    subcat_sel = st.selectbox("Subcategoría", ["Todas"] + subcategorias)

    if subcat_sel != "Todas":
        productos = sorted(df_maestra.loc[df_maestra["Subcategory"]==subcat_sel,"Product_name"].dropna().unique().tolist())
    elif cat_sel != "Todas":
        productos = sorted(df_maestra.loc[df_maestra["Category"]==cat_sel,"Product_name"].dropna().unique().tolist())
    else:
        productos = sorted(df_maestra["Product_name"].dropna().unique().tolist())
    product_sel = st.selectbox("Producto", ["Todas"] + productos)

    st.divider()
    horizon = st.radio("Horizonte forecast", [3, 6], horizontal=True,
                       format_func=lambda x: f"{x} meses")

# FILTROS
def apply_date(df):
    if isinstance(rango_fechas, tuple) and len(rango_fechas)==2:
        fi, ff = rango_fechas
        return df[(df["Date"].dt.date>=fi)&(df["Date"].dt.date<=ff)]
    return df

df_filtrado = apply_date(df_maestra.copy())
if region_sel  != "Todas": df_filtrado = df_filtrado[df_filtrado["Region"]       == region_sel]
if cat_sel     != "Todas": df_filtrado = df_filtrado[df_filtrado["Category"]     == cat_sel]
if subcat_sel  != "Todas": df_filtrado = df_filtrado[df_filtrado["Subcategory"]  == subcat_sel]
if product_sel != "Todas": df_filtrado = df_filtrado[df_filtrado["Product_name"] == product_sel]

df_base_kpi = apply_date(df_maestra.copy())
if region_sel != "Todas": df_base_kpi = df_base_kpi[df_base_kpi["Region"]   == region_sel]
if cat_sel    != "Todas": df_base_kpi = df_base_kpi[df_base_kpi["Category"] == cat_sel]

if df_filtrado.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

region_prophet = region_sel if region_sel != "Todas" else df_maestra["Region"].mode()[0]
subcat_prophet = subcat_sel if subcat_sel != "Todas" else None
region_label   = REG_LABEL.get(region_sel, region_sel) if region_sel != "Todas" else "Todas las regiones"
ref15, ref25   = period_thresholds(horizon)

# PROPHET — FUENTE ÚNICA DE VERDAD
with st.spinner("Calculando pronósticos..."):
    forecast_df  = build_forecast_summary(df_base_kpi, region_prophet, horizon)
    region_fc_df = build_region_forecast(horizon)

if forecast_df.empty:
    st.warning("No hay datos suficientes para los filtros actuales.")
    st.stop()

# KPIs globales
kpi_total_units  = (forecast_df["Forecast_avg"] * horizon).sum()
kpi_hist_units   = (forecast_df["Hist_avg"]     * horizon).sum()
kpi_growth_total = ((kpi_total_units-kpi_hist_units)/kpi_hist_units*100) if kpi_hist_units>0 else 0.0

fc_sorted  = forecast_df.sort_values("Growth_pct", ascending=False)
best_row   = fc_sorted.iloc[0];  best_name  = best_row["Subcategory"];  best_pct  = best_row["Growth_pct"]
worst_row  = fc_sorted.iloc[-1]; worst_name = worst_row["Subcategory"]; worst_pct = worst_row["Growth_pct"]
best_badge,  best_accent  = growth_label(best_pct,  horizon)
worst_badge, worst_accent = growth_label(worst_pct, horizon)

# =========================
# Encabezado
# =========================
ctx_parts = []
if cat_sel     != "Todas": ctx_parts.append(f"Cat: {cat_sel}")
if subcat_sel  != "Todas": ctx_parts.append(f"Sub: {subcat_sel}")
if product_sel != "Todas": ctx_parts.append(f"Prod: {product_sel}")
ctx_parts.append(f"{horizon} meses")
ctx_str = "  ·  ".join(ctx_parts)

st.markdown(
    '<h1 class="main-title">Panel de Pronósticos</h1>',
    unsafe_allow_html=True
)

st.markdown(
    f'<p class="forecast-context">{escape(str(region_label))}  ·  {escape(str(ctx_str))}</p>',
    unsafe_allow_html=True
)


# 5 TABS
tab_resumen, tab_analisis, tab_redist = st.tabs([
    "Resumen",
    "Análisis",
    "Redistribución",
])

with tab_resumen:

    c1, c2, c3 = st.columns(3)

    with c1:
        t1_badge, t1_accent = growth_label(kpi_growth_total, horizon)
        sign_t = "+" if kpi_growth_total >= 0 else ""
        components.html(metric_card(
            f"Unidades estimadas · {horizon} meses", f"{kpi_total_units:,.0f} u",
            f"Histórico: {kpi_hist_units:,.0f} u · Variación: {sign_t}{kpi_growth_total:.1f}%",
            t1_badge, "→", t1_accent,
            min(abs(kpi_growth_total/ref25*100) if ref25>0 else 70, 100),
        ), height=160, scrolling=False)

    with c2:
        components.html(metric_card(
            f"Mejor subcategoria · {horizon} meses", best_name,
            f"+{best_pct:.1f}% según Prophet · {annualize(best_pct,horizon):+.1f}% anualizado",
            best_badge, "+", best_accent,
            min(abs(best_pct/ref25*100) if ref25>0 else 0, 100),
        ), height=160, scrolling=False)

    with c3:
        sign3 = "+" if worst_pct >= 0 else ""
        components.html(metric_card(
            f"Menor alza · {horizon} meses", worst_name,
            f"{sign3}{worst_pct:.1f}% según Prophet · {annualize(worst_pct,horizon):+.1f}% anualizado",
            worst_badge, "!", worst_accent,
            min(abs(worst_pct/ref25*100) if ref25>0 else 0, 100),
        ), height=160, scrolling=False)

    st.divider()

    col_bar, col_acc = st.columns([3, 1], gap="large")

    with col_bar:
        section_title(
            "Crecimiento por subcategoría",
            subtitle=f"{region_label} · Prophet · {horizon} meses",
        )

        fc_bar = forecast_df.sort_values("Growth_pct", ascending=False)
        colors_bar = [bar_color(v, horizon) for v in fc_bar["Growth_pct"]]

        fig_bar = go.Figure()

        fig_bar.add_trace(go.Bar(
            x=fc_bar["Growth_pct"],
            y=fc_bar["Subcategory"],
            orientation="h",
            text=[f"{v:+.1f}%" for v in fc_bar["Growth_pct"]],
            textposition="outside",
            cliponaxis=False,
            marker=dict(color=colors_bar, opacity=0.88),
            customdata=np.stack(
                [
                    fc_bar["Forecast_avg"] * horizon,
                    fc_bar["Hist_avg"] * horizon
                ],
                axis=-1
            ),
            hovertemplate=(
                "<b>%{y}</b><br>Crecimiento: %{x:+.1f}%<br>"
                "Forecast total: %{customdata[0]:,.0f} u<br>"
                "Histórico total: %{customdata[1]:,.0f} u<extra></extra>"
            ),
        ))

        # Líneas guía sin texto automático para evitar que se encimen
        fig_bar.add_vline(
            x=ref15,
            line=dict(color="#f59e0b", width=1.5, dash="dot")
        )

        fig_bar.add_vline(
            x=ref25,
            line=dict(color="#16a34a", width=1.5, dash="dot")
        )

        # Etiqueta de 15% anual, arriba y ligeramente a la izquierda
        fig_bar.add_annotation(
            x=ref15,
            y=1.15,
            xref="x",
            yref="paper",
            text=f"15% anual ({ref15:.1f}% en {horizon}m)",
            showarrow=False,
            font=dict(color="#b45309", size=10),
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="rgba(245,158,11,0.30)",
            borderwidth=1,
            borderpad=4,
            xanchor="center",
            yanchor="bottom",
            xshift=-28
        )

        # Etiqueta de 25% anual, más abajo y ligeramente a la derecha
        fig_bar.add_annotation(
            x=ref25,
            y=1.05,
            xref="x",
            yref="paper",
            text=f"25% anual ({ref25:.1f}% en {horizon}m)",
            showarrow=False,
            font=dict(color="#15803d", size=10),
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="rgba(22,163,74,0.30)",
            borderwidth=1,
            borderpad=4,
            xanchor="center",
            yanchor="bottom",
            xshift=28
        )

        # Rango dinámico para que no se corten textos fuera de las barras
        x_min = min(0, fc_bar["Growth_pct"].min(), ref15, ref25)
        x_max = max(fc_bar["Growth_pct"].max(), ref15, ref25)

        padding = (x_max - x_min) * 0.18 if x_max != x_min else 1

        fig_bar.update_layout(
            height=300,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(
                color="#0f172a",
                family="Inter, system-ui, sans-serif"
            ),
            margin=dict(l=10, r=120, t=70, b=30),
            yaxis=dict(
                autorange="reversed",
                tickfont=dict(size=12),
                automargin=True
            ),
            xaxis=dict(
                title=f"Crecimiento Prophet en {horizon} meses (%)",
                showgrid=True,
                gridcolor="rgba(148,163,184,.20)",
                zeroline=True,
                zerolinecolor="rgba(148,163,184,.40)",
                zerolinewidth=1.5,
                range=[x_min, x_max + padding]
            ),
        )

        st.plotly_chart(
            fig_bar,
            use_container_width=True,
            config={"displayModeBar": False}
        )


    with col_acc:
        section_title(
            "Confiabilidad",
            subtitle="Walk-forward · histórico",
        )

        acc_color = (
            "#16a34a" if MODEL_ACCURACY >= 85
            else "#f59e0b" if MODEL_ACCURACY >= 75
            else "#dc2626"
        )

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=MODEL_ACCURACY,
            domain={
    "x": [0.08, 0.92],
    "y": [0.06, 0.68]
},
            number=dict(
                suffix="%",
                font=dict(
                    size=34,
                    color="#0f172a",
                    family="Inter, system-ui, sans-serif"
                )
            ),
            gauge=dict(
                shape="angular",
                axis=dict(
                    range=[0, 100],
                    tickwidth=1,
                    tickcolor="#cbd5e1",
                    tickfont=dict(size=10, color="#64748b")
                ),
                bar=dict(
                    color=acc_color,
                    thickness=0.50
                ),
                bgcolor="#f8fafc",
                borderwidth=0,
                steps=[
                    dict(range=[0, 75], color="#fee2e2"),
                    dict(range=[75, 85], color="#fef3c7"),
                    dict(range=[85, 100], color="#dcfce7")
                ],
                threshold=dict(
                    line=dict(color="#0f172a", width=2),
                    thickness=0.75,
                    value=MODEL_ACCURACY
                ),
            ),
        ))

        fig_gauge.update_layout(
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10),
            font=dict(
                family="Inter, system-ui, sans-serif",
                color="#0f172a"
            ),
            annotations=[
                dict(
                    text=(
                        "Accuracy general<br>"
                        "<span style='font-size:12px;color:#64748b'>"
                        "Walk-forward · datos históricos</span>"
                    ),
                    x=0.5,
                    y=0.96,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                    align="center",
                    font=dict(
                        size=15,
                        color="#0f172a",
                        family="Inter, system-ui, sans-serif"
                    )
                )
            ]
        )

        st.plotly_chart(
            fig_gauge,
            use_container_width=True,
            config={"displayModeBar": False}
        )


# ─────────────────────────────────────────────────────────────────────
# TAB 2 — DEMANDA
# Serie temporal Prophet
# ─────────────────────────────────────────────────────────────────────
with tab_analisis:

    # ── Serie temporal (compacta arriba) ─────────────────────────────
    if product_sel != "Todas":
        @st.cache_data(show_spinner=False)
        def fit_prophet_product(product_name, region, periods):
            df   = load_data()
            mask = (df["Product_name"]==product_name) & (df["Region"]==region)
            sub  = df[mask].groupby("YearMonth").agg(y=("Units_sold","sum")).reset_index()
            if len(sub) < 6: return None, None
            sub["ds"] = sub["YearMonth"].dt.to_timestamp()
            sub = sub[["ds","y"]]
            from prophet import Prophet as _P
            m = _P(changepoint_prior_scale=0.05, seasonality_mode="additive",
                   uncertainty_samples=300, yearly_seasonality=False,
                   weekly_seasonality=False, daily_seasonality=False)
            m.add_seasonality(name="semestral", period=182.5, fourier_order=3)
            m.fit(sub); future = m.make_future_dataframe(periods=periods, freq="MS")
            return sub, m.predict(future)
        hist_df, fc_df = fit_prophet_product(product_sel, region_prophet, horizon)
        chart_label = product_sel

    elif subcat_prophet is not None:
        hist_df, fc_df = fit_prophet("Subcategory", subcat_prophet, region_prophet, horizon)
        chart_label = subcat_prophet

    else:
        sub_base = (
            df_base_kpi.groupby("YearMonth").agg(y=("Units_sold","sum")).reset_index()
        )
        if len(sub_base) >= 6:
            sub_base["ds"] = sub_base["YearMonth"].dt.to_timestamp()
            sub_base = sub_base[["ds","y"]]
            from prophet import Prophet as _P
            _m = _P(changepoint_prior_scale=0.05, seasonality_mode="additive",
                    uncertainty_samples=300, yearly_seasonality=False,
                    weekly_seasonality=False, daily_seasonality=False)
            _m.add_seasonality(name="semestral", period=182.5, fourier_order=3)
            _m.fit(sub_base)
            _future = _m.make_future_dataframe(periods=horizon, freq="MS")
            hist_df = sub_base; fc_df = _m.predict(_future)
        else:
            hist_df, fc_df = None, None
        cat_label   = cat_sel if cat_sel != "Todas" else "Todas las categorías"
        chart_label = cat_label

    if hist_df is not None:
        future_fc = fc_df[fc_df["ds"] > hist_df["ds"].max()]
        delta     = future_fc["yhat"].mean() - hist_df["y"].mean()
        sign_d    = "+" if delta >= 0 else ""

        section_title(
            "Demanda proyectada",
            subtitle=f"{chart_label}  ·  {region_label}  ·  {horizon} meses  ·  "
                     f"Forecast: {int(future_fc['yhat'].mean()):,} u/mes  ·  "
                     f"Var: {sign_d}{delta:,.0f} u/mes",
            popover_title="",
            popover_body=(
                "**Línea azul** — ventas históricas reales por mes  \n\n"
                "**Línea verde punteada** — demanda proyectada por Prophet  \n\n"
                "**Banda azul** — intervalo de confianza (rango posible de la predicción)  \n\n"
                "Los valores de la gráfica corresponden a la serie seleccionada: "
                "subcategoría, producto individual o región total."
            ),
        )

        fig_dem = go.Figure()
        fig_dem.add_trace(go.Scatter(
            x=pd.concat([future_fc["ds"], future_fc["ds"][::-1]]),
            y=pd.concat([future_fc["yhat_upper"], future_fc["yhat_lower"][::-1]]),
            fill="toself", fillcolor="rgba(37,99,235,.08)",
            line=dict(color="rgba(0,0,0,0)"), hoverinfo="skip", name="IC",
        ))
        fig_dem.add_trace(go.Scatter(
            x=hist_df["ds"], y=hist_df["y"], mode="lines+markers", name="Histórico",
            line=dict(color="#2563eb", width=2), marker=dict(size=4, color="#2563eb"),
            hovertemplate="<b>%{x|%b %Y}</b><br>%{y:,.0f} u<extra></extra>",
        ))
        fig_dem.add_trace(go.Scatter(
            x=future_fc["ds"], y=future_fc["yhat"],
            mode="lines+markers", name=f"Forecast ({horizon}m)",
            line=dict(color="#16a34a", width=2, dash="dot"),
            marker=dict(size=6, symbol="diamond", color="#16a34a"),
            hovertemplate="<b>%{x|%b %Y}</b><br>%{y:,.0f} u<extra></extra>",
        ))
        fig_dem.update_layout(
            height=260, hovermode="x unified",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#0f172a", family="Inter, system-ui, sans-serif"),
            margin=dict(l=40, r=20, t=5, b=25),
            xaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,.20)",
                       tickfont=dict(size=9)),
            yaxis=dict(title="u", showgrid=True, gridcolor="rgba(148,163,184,.20)",
                       tickfont=dict(size=9)),
            legend=dict(orientation="h", y=1.15, x=0, font=dict(size=9)),
        )
        st.plotly_chart(fig_dem, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Sin datos suficientes (mínimo 6 meses).")

    # ── Fila inferior: Estacionalidad (izq) + Comparación regiones (der) ──
    month_names = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                   7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}

    # Estacionalidad: suma por YearMonth → promedio por mes (coherente con serie)
    seas_m = df_base_kpi.groupby("YearMonth")["Units_sold"].sum().reset_index()
    seas_m["Month"] = seas_m["YearMonth"].dt.month
    seasonality = seas_m.groupby("Month")["Units_sold"].mean().reset_index()
    seasonality["Month_name"] = seasonality["Month"].map(month_names)
    seasonality = seasonality.sort_values("Month")
    global_avg  = seasonality["Units_sold"].mean()
    seas_colors = [
        "#16a34a" if v >= global_avg*1.05
        else "#dc2626" if v <= global_avg*0.95
        else "#2563eb"
        for v in seasonality["Units_sold"]
    ]
    peak_m = seasonality.loc[seasonality["Units_sold"].idxmax(), "Month_name"]
    variab = (seasonality["Units_sold"].max()-seasonality["Units_sold"].min())/global_avg*100

    # Comparación regiones
    with st.spinner(""):
        fc3 = build_region_forecast(3)
        fc6 = build_region_forecast(6)
    fc3 = fc3.rename(columns={"Forecast_total":"fc3","Growth_pct":"gp3"})
    fc6 = fc6.rename(columns={"Forecast_total":"fc6","Growth_pct":"gp6"})
    region_compare = fc3[["Region_label","fc3","gp3"]].merge(
        fc6[["Region_label","fc6","gp6"]], on="Region_label"
    ).sort_values("fc6", ascending=True)

    col_seas, col_reg = st.columns([1, 1], gap="large")

    with col_seas:
        section_title(
            "Estacionalidad mensual",
            subtitle=f"Pico: {peak_m}  ·  Variabilidad: {variab:.0f}%",
            popover_title="",
            popover_body=(
                "Promedio de ventas por mes del año, usando la misma escala que la serie temporal.  \n\n"
                "**Verde** — mes >5% sobre el promedio (pico de demanda)  \n\n"
                "**Rojo** — mes >5% bajo el promedio (valle de demanda)  \n\n"
                "**Azul** — mes dentro del rango promedio  \n\n"
                "Útil para planear reabastecimiento y campañas con anticipación."
            ),
        )
        fig_seas = go.Figure()
        fig_seas.add_hline(y=global_avg, line=dict(color="#94a3b8",width=1,dash="dot"),
            annotation_text="Prom.", annotation_position="right",
            annotation_font=dict(color="#64748b",size=8))
        fig_seas.add_trace(go.Bar(
            x=seasonality["Month_name"], y=seasonality["Units_sold"],
            marker=dict(color=seas_colors, opacity=0.88),
            hovertemplate="<b>%{x}</b><br>%{y:,.0f} u<extra></extra>",
        ))
        fig_seas.update_layout(
            height=250, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#0f172a", family="Inter, system-ui, sans-serif"),
            margin=dict(l=10, r=20, t=5, b=25),
            xaxis=dict(showgrid=False, tickfont=dict(size=9)),
            yaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,.20)",
                       tickfont=dict(size=9), tickformat=",.0f"),
        )
        st.plotly_chart(fig_seas, use_container_width=True, config={"displayModeBar": False})

    with col_reg:
        section_title(
            "Forecast por región",
            subtitle="Prophet · sin filtros · 3m vs 6m",
            popover_title="",
            popover_body=(
                "Demanda total proyectada por Prophet para cada región. "
                "No se ve afectada por ningún filtro — siempre muestra el dataset completo.  \n\n"
                "**Azul** — forecast a 3 meses  \n\n"
                "**Verde** — forecast a 6 meses  \n\n"
                "Ordenadas de menor a mayor demanda proyectada a 6 meses."
            ),
        )
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            name="3m", y=region_compare["Region_label"], x=region_compare["fc3"],
            orientation="h", marker=dict(color="#2563eb", opacity=0.80),
            hovertemplate="<b>%{y}</b><br>3m: %{x:,.0f} u<extra></extra>",
        ))
        fig_comp.add_trace(go.Bar(
            name="6m", y=region_compare["Region_label"], x=region_compare["fc6"],
            orientation="h", marker=dict(color="#16a34a", opacity=0.80),
            hovertemplate="<b>%{y}</b><br>6m: %{x:,.0f} u<extra></extra>",
        ))
        fig_comp.update_layout(
            barmode="group", height=250,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#0f172a", family="Inter, system-ui, sans-serif"),
            margin=dict(l=10, r=10, t=5, b=25),
            legend=dict(orientation="h", y=1.15, x=0, font=dict(size=9)),
            yaxis=dict(tickfont=dict(size=9)),
            xaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,.20)",
                       tickfont=dict(size=9), tickformat=",.0f"),
        )
        st.plotly_chart(fig_comp, use_container_width=True, config={"displayModeBar": False})

with tab_redist:

    # ── Header con popovers y toggle interno ──────────────────────────
    col_th, col_p1, col_toggle = st.columns([3, 1, 2])
    with col_th:
        st.markdown(
            """
            <div class="chart-card-header">
                <h3>Redistribución de inventario</h3>
                <p>Plan de transferencia basado en demanda proyectada y exceso de stock.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col_p1:
        with st.popover("¿Cómo funciona?", use_container_width=True):
            st.markdown(
                f"Detecta el **producto más débil** por subcategoría y región y lo "
                f"redistribuye hacia donde hay mayor demanda proyectada a **{horizon} meses**. "
                f"Transferencias en **6 oleadas bisemanales** proporcionales a la demanda del destino."
            )
            st.markdown("---")
            st.markdown(
                f"{dot('#ef4444')} **Rojo** — Envía stock  \n"
                f"{dot('#22c55e')} **Verde** — Recibe stock  \n"
                f"{dot('#3b82f6')} **Azul** — Sin movimiento  \n"
                "**Grosor** — proporcional a unidades en tránsito",
                unsafe_allow_html=True,
            )
    with col_toggle:
        vista_redist = st.radio(
            "", ["Mapa", "Plan de envíos"],
            horizontal=True, label_visibility="collapsed",
        )

    # ── Calcular (siempre, para ambas vistas) ────────────────────────
    with st.spinner("Calculando..."):
        subcat_region_forecast = build_subcat_region_forecast(df_maestra, horizon)
        fc_monthly             = build_monthly_forecast(horizon)

    df_work = df_maestra.copy()
    if "Excess_stock" not in df_work.columns:
        df_work["Excess_stock"] = (df_work["Stock"] - df_work["Units_sold"]).clip(lower=0)

    redist_base_df    = build_redist_base(df_work, subcat_region_forecast, horizon)
    pares_df, plan_df = build_wave_plan(df_work, redist_base_df, fc_monthly, horizon)

    if plan_df.empty:
        st.info("No se encontraron transferencias.")
        st.stop()

    oleadas       = sorted(plan_df["Oleada"].unique())
    primera_fecha = plan_df["Fecha_envío"].iloc[0]
    ultima_fecha  = plan_df[plan_df["Oleada"]==oleadas[-1]]["Fecha_envío"].iloc[0]

    # ── 4 KPIs mini ──────────────────────────────────────────────────
    km1, km2, km3, km4 = st.columns(4)
    with km1:
        st.markdown(_mini_kpi("Productos", str(plan_df["Producto"].nunique())),
                    unsafe_allow_html=True)
    with km2:
        st.markdown(_mini_kpi("Unidades totales", f"{plan_df['Unidades_oleada'].sum():,} u"),
                    unsafe_allow_html=True)
    with km3:
        st.markdown(_mini_kpi("Pares origen→destino", str(len(pares_df))),
                    unsafe_allow_html=True)
    with km4:
        st.markdown(_mini_kpi("Período", f"{primera_fecha} – {ultima_fecha}"),
                    unsafe_allow_html=True)

    st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)

    # ── VISTA A: MAPA ANIMADO ─────────────────────────────────────────
    if vista_redist == "Mapa":
        frames, slider_steps, init_nodes, init_routes, init_annotation, n_frames = \
            build_animation_frames(plan_df, horizon)

        fig_map = go.Figure(
            data=[init_nodes] + init_routes,
            frames=frames,
            layout=go.Layout(
                height=490,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#0f172a", family="Inter, system-ui, sans-serif"),
                margin=dict(l=0, r=0, t=55, b=0),
                geo=GEO_LAYOUT,
                annotations=[init_annotation],
                title=dict(
                    text=f"Plan de {n_frames} transferencias  ·  ▶ Play para iniciar",
                    font=dict(size=12, color="#0f172a"),
                ),
                updatemenus=[dict(
                    type="buttons", showactive=False, direction="left",
                    x=0.5, xanchor="center", y=-0.05, yanchor="top",
                    bgcolor="#f1f5f9", bordercolor="rgba(148,163,184,.4)",
                    font=dict(color="#0f172a", size=12),
                    pad=dict(r=8, t=8),
                    buttons=[
                        dict(label="▶  Play", method="animate",
                             args=[None, dict(frame=dict(duration=2000, redraw=True),
                                              fromcurrent=True,
                                              transition=dict(duration=400,
                                                              easing="cubic-in-out"))]),
                        dict(label="⏸  Pausa", method="animate",
                             args=[[None], dict(frame=dict(duration=0, redraw=False),
                                                mode="immediate")]),
                    ],
                )],
                sliders=[dict(
                    active=0,
                    currentvalue=dict(prefix="", visible=True,
                                      font=dict(size=11, color="#64748b")),
                    pad=dict(t=45, b=8, l=20, r=20),
                    len=0.92, x=0.04,
                    bgcolor="#f8fafc", bordercolor="rgba(148,163,184,.3)",
                    borderwidth=1, font=dict(color="#334155", size=10),
                    steps=slider_steps, tickcolor="rgba(148,163,184,.4)",
                )],
            ),
        )
        st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False})

    # ── VISTA B: PLAN DE ENVÍOS ───────────────────────────────────────
    else:
        col_ctrl, col_check = st.columns([3, 1])
        with col_ctrl:
            oleada_sel = st.select_slider(
                "Oleada",
                options=list(range(1, len(oleadas)+1)),
                value=1,
                format_func=lambda x: (
                    f"Oleada {x}  ·  "
                    f"{plan_df[plan_df['Oleada']==x]['Fecha_envío'].iloc[0]}"
                ),
            )
        with col_check:
            mostrar_todo = st.checkbox("Ver todo", value=False)

        tabla_filtrada = plan_df if mostrar_todo else plan_df[plan_df["Oleada"]==oleada_sel]

        # Métricas de oleada
        if not mostrar_todo:
            m1, m2, m3, m4 = st.columns(4)
            with m1: st.metric("Transferencias", f"{len(tabla_filtrada)}")
            with m2: st.metric("Unidades", f"{tabla_filtrada['Unidades_oleada'].sum():,} u")
            with m3: st.metric("Rutas", str(tabla_filtrada[["Origen","Destino"]].drop_duplicates().__len__()))
            with m4: st.metric("Dist. prom.", f"{tabla_filtrada['Distancia_km'].mean():,.0f} km")

        tabla_show = tabla_filtrada[[
            "Producto","Subcategoría","Origen_label","Destino_label",
            "Oleada","Fecha_envío","Unidades_oleada","Total_transferencia",
            "Demanda_destino_mes","Exceso_origen_u","Gap_origen_pct","Distancia_km",
        ]].copy()
        tabla_show.columns = [
            "Producto","Subcategoría","Origen","Destino",
            "Oleada","Fecha","Unidades","Total",
            "Demanda destino (u)","Exceso origen (u)","Gap (%)","Dist (km)",
        ]
        st.dataframe(tabla_show, use_container_width=True, hide_index=True, height=155)

        # Resumen + barras lado a lado
        col_res, col_prog = st.columns([3, 2], gap="large")
        with col_res:
            resumen = (
                plan_df
                .groupby(["Producto","Subcategoría","Origen_label","Destino_label"])
                .agg(Total_u=("Unidades_oleada","sum"), N=("Oleada","count"),
                     Primer=("Fecha_envío","first"), Ultimo=("Fecha_envío","last"),
                     Exceso=("Exceso_origen_u","first"), Gap=("Gap_origen_pct","first"),
                     Dist=("Distancia_km","first"))
                .reset_index().sort_values("Total_u", ascending=False)
            )
            resumen.columns = ["Producto","Subcategoría","Origen","Destino",
                                "Total u","Oleadas","Primer envío","Último envío",
                                "Exceso (u)","Gap (%)","Dist (km)"]
            st.dataframe(resumen, use_container_width=True, hide_index=True, height=155)

        with col_prog:
            u_ola = (plan_df.groupby(["Oleada","Mes_num","Fecha_envío"])["Unidades_oleada"]
                     .sum().reset_index().sort_values("Oleada"))
            colores_mes = {1:"#3b82f6", 2:"#22c55e", 3:"#f59e0b"}
            fig_prog = go.Figure()
            fig_prog.add_trace(go.Bar(
                x=[f"Ol.{int(r.Oleada)}<br>{r.Fecha_envío}" for _, r in u_ola.iterrows()],
                y=u_ola["Unidades_oleada"],
                marker=dict(color=[colores_mes.get(int(m),"#94a3b8")
                                   for m in u_ola["Mes_num"]], opacity=0.88),
                text=[f"{int(u):,}" for u in u_ola["Unidades_oleada"]],
                textposition="outside", textfont=dict(size=9),
                hovertemplate="<b>%{x}</b><br>%{y:,} u<extra></extra>",
            ))
            fig_prog.update_layout(
                height=175, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#0f172a", family="Inter, system-ui, sans-serif"),
                margin=dict(l=10, r=10, t=15, b=50),
                xaxis=dict(showgrid=False, tickfont=dict(size=8)),
                yaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,.20)",
                           tickfont=dict(size=8)),
                showlegend=False,
            )
            st.plotly_chart(fig_prog, use_container_width=True, config={"displayModeBar": False})
            st.caption("Azul = Enero  ·  Verde = Febrero  ·  Naranja = Marzo")