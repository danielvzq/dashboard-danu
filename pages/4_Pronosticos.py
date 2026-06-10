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
    _make_nodes,
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
# CSS general responsivo
# =========================
st.markdown(
    """
    <style>
        :root {
            --rd-card-bg: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            --rd-card-border: 1.7px solid rgba(100, 116, 139, 0.52);
            --rd-card-border-hover: rgba(71, 85, 105, 0.62);
            --rd-card-radius: clamp(18px, 1.55vw, 24px);
            --rd-inner-border: 1.4px solid rgba(100, 116, 139, 0.38);
            --rd-card-shadow: 0 8px 24px rgba(15, 23, 42, 0.035);
            --rd-inner-shadow: 0 6px 16px rgba(15, 23, 42, 0.035);
            --rd-gap: clamp(8px, 0.82vw, 12px);
        }

        .block-container {
            /* Más aire superior para que el header fijo de Streamlit no corte el título */
            padding-top: clamp(2.15rem, 3.2vh, 3.2rem) !important;
            padding-bottom: clamp(0.8rem, 1.4vh, 1.2rem) !important;
            padding-left: clamp(1rem, 1.9vw, 1.6rem) !important;
            padding-right: clamp(1rem, 1.9vw, 1.6rem) !important;
            max-width: 100% !important;
        }

        h1, h2, h3, h4 {
            margin-top: 0 !important;
        }

        .main-title {
            color: #0f172a;
            font-size: clamp(2rem, 3.35vw, 3.25rem);
            font-weight: 950;
            letter-spacing: clamp(-1.4px, -0.12vw, -0.7px);
            margin: 0 0 clamp(0.55rem, 0.9vw, 0.85rem) 0;
            line-height: 1.18;
            padding-top: 0.08em;
            overflow: visible;
        }

        .forecast-context {
            color: #64748b;
            font-size: clamp(11px, 0.9vw, 13px);
            font-weight: 800;
            margin: 0 0 clamp(0.7rem, 1.1vw, 1rem) 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        div[data-testid="stVerticalBlock"] {
            gap: clamp(0.5rem, 0.8vw, 0.75rem) !important;
        }

        div[data-testid="stHorizontalBlock"] {
            gap: clamp(0.55rem, 0.85vw, 0.8rem) !important;
        }

        div[data-testid="stMarkdownContainer"]:has(.main-title),
        div[data-testid="stMarkdownContainer"]:has(.forecast-context) {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }

        div[data-testid="stTabs"] {
            margin-top: 0 !important;
        }

        button[data-baseweb="tab"] {
            padding-top: 7px !important;
            padding-bottom: 7px !important;
            border-radius: 999px !important;
            font-weight: 850 !important;
        }

        button[kind="secondary"] {
            border-radius: 999px !important;
            font-weight: 850 !important;
        }

        iframe {
            display: block;
            width: 100% !important;
            max-width: 100% !important;
        }

        .chart-card-header {
            padding: 0;
            margin-bottom: clamp(9px, 0.85vw, 13px);
        }

        .chart-card-header h3 {
            color: #0f172a;
            font-size: clamp(16px, 1.25vw, 21px);
            font-weight: 950;
            margin: 0;
            letter-spacing: -0.25px;
            line-height: 1.22;
        }

        .chart-card-header p {
            color: #64748b;
            font-size: clamp(11px, 0.88vw, 13px);
            font-weight: 800;
            margin: clamp(4px, 0.45vw, 7px) 0 0 0;
            line-height: 1.25;
        }

        .section-title-spacer {
            height: clamp(4px, 0.45vw, 7px);
            min-height: 4px;
        }

        .redist-map-spacer {
            height: clamp(24px, 1.75vw, 32px);
            min-height: 24px;
        }

        /* Streamlit agrega demasiado aire en los divider; aquí lo compactamos. */
        hr {
            margin: clamp(1rem, 1.35vw, 1.45rem) 0 !important;
        }

        div[data-testid="stPlotlyChart"] iframe,
        div[data-testid="stPlotlyChart"] > div {
            overflow: visible !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stPlotlyChart"],
        div[data-testid="stDataFrame"] {
            border-radius: var(--rd-card-radius) !important;
            border: var(--rd-card-border) !important;
            background: var(--rd-card-bg) !important;
            box-shadow: var(--rd-card-shadow) !important;
            overflow: hidden !important;
        }

        [data-testid="stVerticalBlockBorderWrapper"] {
            padding: clamp(0.5rem, 0.85vw, 0.8rem) !important;
        }

        div[data-testid="stPlotlyChart"] {
            padding: clamp(0.45rem, 0.7vw, 0.65rem) clamp(0.55rem, 0.85vw, 0.8rem) clamp(0.55rem, 0.85vw, 0.8rem) !important;
        }

        div[data-testid="stPlotlyChart"] > div {
            width: 100% !important;
        }

        div[data-testid="stMetric"] {
            border-radius: clamp(14px, 1.2vw, 18px) !important;
            border: var(--rd-inner-border) !important;
            background: rgba(255, 255, 255, 0.9) !important;
            box-shadow: var(--rd-inner-shadow) !important;
            padding: clamp(0.55rem, 0.8vw, 0.75rem) clamp(0.65rem, 0.95vw, 0.85rem) !important;
        }

        div[data-testid="stDataFrame"] {
            background: #ffffff !important;
        }

        div[data-testid="stPlotlyChart"]:hover,
        div[data-testid="stDataFrame"]:hover,
        [data-testid="stVerticalBlockBorderWrapper"]:hover,
        div[data-testid="stMetric"]:hover {
            border-color: var(--rd-card-border-hover) !important;
        }

        [data-testid="stExpander"],
        [data-testid="stPopover"] {
            font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        div[data-testid="stPopover"] button {
            min-width: 105px !important;
            height: 38px !important;
            white-space: nowrap !important;
            border-radius: 999px !important;
            font-weight: 800 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 0 clamp(12px, 1vw, 16px) !important;
        }

        div[data-testid="stRadio"] label {
            font-weight: 800 !important;
        }

        @media (max-width: 1180px) {
            .block-container {
                padding-left: clamp(0.85rem, 1.6vw, 1.2rem) !important;
                padding-right: clamp(0.85rem, 1.6vw, 1.2rem) !important;
            }

            .chart-card-header h3 {
                font-size: clamp(13px, 1.65vw, 17px);
            }

            .chart-card-header p {
                font-size: clamp(9.5px, 1.15vw, 12px);
            }

            div[data-testid="stPlotlyChart"] {
                padding: 0.55rem 0.65rem !important;
            }
        }

        @media (max-width: 820px) {
            .block-container {
                padding-left: 0.75rem !important;
                padding-right: 0.75rem !important;
                padding-top: 1.35rem !important;
            }

            .main-title {
                font-size: clamp(1.7rem, 8vw, 2.35rem);
                margin-bottom: 0.55rem;
            }

            .forecast-context {
                font-size: clamp(9.5px, 2.4vw, 12px);
                white-space: normal;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
            }

            div[data-testid="stVerticalBlock"] {
                gap: 0.45rem !important;
            }

            div[data-testid="stHorizontalBlock"] {
                gap: 0.45rem !important;
            }

            [data-testid="stVerticalBlockBorderWrapper"],
            div[data-testid="stPlotlyChart"],
            div[data-testid="stDataFrame"] {
                border-radius: 14px !important;
            }

            div[data-testid="stPlotlyChart"] {
                padding: 0.45rem 0.5rem !important;
            }

            .chart-card-header h3 {
                font-size: clamp(11px, 2.4vw, 14px);
            }

            .chart-card-header p {
                font-size: clamp(8px, 1.85vw, 10px);
                margin-top: 5px;
            }

            button[data-baseweb="tab"] {
                padding-left: 10px !important;
                padding-right: 10px !important;
                font-size: 12px !important;
            }
        }

        @media (max-width: 520px) {
            .block-container {
                padding-left: 0.55rem !important;
                padding-right: 0.55rem !important;
            }

            .main-title {
                font-size: clamp(1.45rem, 8.5vw, 2rem);
            }

            .forecast-context {
                font-size: clamp(8.2px, 2.8vw, 10px);
            }

            div[data-testid="stPlotlyChart"] {
                padding: 0.35rem 0.35rem !important;
            }

            button[data-baseweb="tab"] {
                padding-left: 8px !important;
                padding-right: 8px !important;
                font-size: 11px !important;
            }
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
# Refuerzo de estilo de esta vista
# =========================
st.markdown(
    """
    <style>
        [data-testid="stVerticalBlockBorderWrapper"],
        div[data-testid="stPlotlyChart"],
        div[data-testid="stDataFrame"] {
            border: 1.7px solid rgba(100, 116, 139, 0.52) !important;
            border-radius: clamp(18px, 1.55vw, 24px) !important;
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%) !important;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.035) !important;
            overflow: hidden !important;
        }

        div[data-testid="stMetric"] {
            border: 1.4px solid rgba(100, 116, 139, 0.38) !important;
            border-radius: clamp(14px, 1.2vw, 18px) !important;
        }

        div[data-testid="stPlotlyChart"]:hover,
        div[data-testid="stDataFrame"]:hover,
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: rgba(71, 85, 105, 0.62) !important;
        }

        @media (max-width: 820px) {
            [data-testid="stVerticalBlockBorderWrapper"],
            div[data-testid="stPlotlyChart"],
            div[data-testid="stDataFrame"] {
                border-radius: 14px !important;
            }
        }
    </style>
    """,
    unsafe_allow_html=True
)


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
<html lang="es">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<style>
    html, body {{
        width: 100%;
        height: 100%;
        margin: 0;
        padding: 0;
        background: transparent;
        font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        overflow: hidden;
    }}

    * {{
        box-sizing: border-box;
    }}

    :root {{
        --rd-card-bg: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        --rd-card-border: 1.7px solid rgba(100, 116, 139, 0.52);
        --rd-card-border-hover: rgba(71, 85, 105, 0.62);
        --rd-card-radius: clamp(18px, 1.55vw, 24px);
        --rd-inner-border: 1.4px solid rgba(100, 116, 139, 0.38);
        --rd-card-shadow: 0 8px 24px rgba(15, 23, 42, 0.035);
    }}

    .metric-card {{
        position: relative;
        overflow: hidden;
        height: 100%;
        min-height: 128px;
        width: 100%;
        border-radius: var(--rd-card-radius);
        padding: clamp(15px, 1.05vw, 19px) clamp(17px, 1.25vw, 23px) clamp(13px, 0.95vw, 17px);
        background: var(--rd-card-bg);
        border: var(--rd-card-border);
        box-shadow: var(--rd-card-shadow);
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}

    .metric-card::before {{
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: clamp(5px, 0.45vw, 7px);
        background: var(--accent-color);
    }}

    .metric-card:hover {{
        border-color: var(--rd-card-border-hover);
    }}

    .metric-title {{
        color: #0f172a;
        font-size: clamp(16px, 1.18vw, 20px);
        font-weight: 950;
        margin: 0 0 clamp(5px, 0.55vw, 8px) 0;
        line-height: 1.1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .metric-value {{
        color: #0f172a;
        font-size: clamp(34px, 2.65vw, 46px);
        font-weight: 950;
        line-height: 1;
        letter-spacing: clamp(-1px, -0.08vw, -0.6px);
        margin: 0 0 clamp(5px, 0.45vw, 8px) 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .metric-description {{
        color: #64748b;
        font-size: clamp(13px, 0.95vw, 16px);
        font-weight: 750;
        line-height: 1.24;
        margin: 0;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }}

    .metric-footer {{
        display: flex;
        align-items: center;
        gap: clamp(7px, 0.65vw, 9px);
        margin-top: clamp(7px, 0.6vw, 10px);
        min-width: 0;
    }}

    .metric-badge {{
        color: #334155;
        background: rgba(255, 255, 255, 0.9);
        border: var(--rd-inner-border);
        border-radius: 999px;
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.035);
        padding: clamp(3px, 0.35vw, 5px) clamp(7px, 0.7vw, 10px);
        font-size: clamp(10.5px, 0.78vw, 13px);
        font-weight: 950;
        white-space: nowrap;
    }}

    .metric-track {{
        flex: 1;
        min-width: 38px;
        height: clamp(6px, 0.48vw, 8px);
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

    @media (max-width: 820px) {{
        html, body {{
            overflow: visible;
        }}

        .metric-card {{
            min-height: 122px;
            height: 100%;
            border-radius: 14px;
            padding: 13px 10px 10px;
        }}

        .metric-card::before {{
            height: 4px;
        }}

        .metric-title {{
            font-size: clamp(11px, 2.2vw, 14px);
            margin-bottom: 5px;
        }}

        .metric-value {{
            font-size: clamp(21px, 4.2vw, 28px);
            white-space: normal;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }}

        .metric-description {{
            font-size: clamp(9.5px, 1.85vw, 12px);
            line-height: 1.18;
        }}

        .metric-badge {{
            font-size: clamp(8.5px, 1.6vw, 10.5px);
            padding: 3px 7px;
        }}
    }}

    @media (max-width: 520px) {{
        .metric-card {{
            min-height: 112px;
            height: 100%;
            padding: 11px 7px 8px;
            border-radius: 13px;
        }}

        .metric-title {{
            font-size: clamp(9px, 2.1vw, 11px);
            margin-bottom: 4px;
        }}

        .metric-value {{
            font-size: clamp(17px, 3.8vw, 22px);
            margin-bottom: 4px;
        }}

        .metric-description {{
            font-size: clamp(8px, 1.75vw, 9.5px);
        }}

        .metric-footer {{
            gap: 5px;
            margin-top: 6px;
        }}

        .metric-badge {{
            font-size: clamp(7px, 1.6vw, 8.5px);
            padding: 2px 5px;
        }}

        .metric-track {{
            min-width: 24px;
        }}
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
        height: clamp(82px, 6.8vw, 94px);
        min-height: 82px;
        box-sizing: border-box;
        border-radius: clamp(14px, 1.2vw, 18px);
        padding: clamp(9px, 0.88vw, 12px) clamp(12px, 1.05vw, 16px);
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1.7px solid rgba(100, 116, 139, 0.52);
        box-shadow: 0 6px 16px rgba(15, 23, 42, 0.035);
        display: flex;
        flex-direction: column;
        justify-content: center;
        overflow: hidden;
    ">
        <p style="
            margin: 0 0 clamp(4px, 0.42vw, 6px) 0;
            font-size: clamp(10.5px, 0.78vw, 13px);
            font-weight: 950;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: .25px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            line-height: 1.1;
        ">{label}</p>
        <p style="
            margin: 0;
            font-size: clamp(19px, 1.78vw, 27px);
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
    label = escape(str(label))
    subtitle = escape(str(subtitle))

    col_t, col_p = st.columns([6.5, 1.7])

    with col_t:
        st.markdown(
            f"""
            <div class="chart-card-header">
                <h3>{label}</h3>
                <p>{subtitle}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_p:
        if popover_body:
            st.markdown(
                "<div style='height:clamp(2px,0.35vw,4px);'></div>",
                unsafe_allow_html=True
            )

            with st.popover(popover_title if popover_title else "Ver", use_container_width=True):
                st.markdown(popover_body)

    st.markdown("<div class='section-title-spacer'></div>", unsafe_allow_html=True)

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
    from prophet import Prophet as _Prophet

    df      = load_data()
    months  = sorted(df["YearMonth"].unique())
    errors  = []

    top_region = df["Region"].value_counts().idxmax()
    df_r = df[df["Region"] == top_region]

    subcats = [
        sc for sc in df_r["Subcategory"].dropna().unique()
        if df_r[df_r["Subcategory"] == sc]["YearMonth"].nunique() >= 8
    ]

    for i in range(6, min(len(months), 6 + 6)):
        train_m = months[:i]
        test_m  = months[i]

        for sc in subcats:
            sub_train = (
                df_r[(df_r["Subcategory"] == sc) & (df_r["YearMonth"].isin(train_m))]
                .groupby("YearMonth")
                .agg(y=("Units_sold", "sum"))
                .reset_index()
            )
            sub_test = (
                df_r[(df_r["Subcategory"] == sc) & (df_r["YearMonth"] == test_m)]
                ["Units_sold"].sum()
            )

            if len(sub_train) < 6 or sub_test == 0:
                continue

            sub_train["ds"] = sub_train["YearMonth"].dt.to_timestamp()
            sub_train = sub_train[["ds", "y"]]

            try:
                m = _Prophet(
                    changepoint_prior_scale=0.05,
                    seasonality_mode="additive",
                    uncertainty_samples=0,
                    yearly_seasonality=False,
                    weekly_seasonality=False,
                    daily_seasonality=False,
                )
                if len(sub_train) >= 12:
                    m.add_seasonality(name="semestral", period=182.5, fourier_order=3)

                m.fit(sub_train)
                future = m.make_future_dataframe(periods=1, freq="MS")
                fc     = m.predict(future)
                yhat   = max(float(fc["yhat"].iloc[-1]), 0)

                ape = abs(sub_test - yhat) / sub_test * 100
                errors.append(ape)
            except Exception:
                continue

    return round(100 - float(np.mean(errors)), 1) if errors else 0.0

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
kpi_growth_total = ((kpi_total_units - kpi_hist_units) / kpi_hist_units * 100) if kpi_hist_units > 0 else 0.0

if not forecast_df.empty and forecast_df["Hist_avg"].sum() > 0:
    kpi_growth_ponderado = (
        (forecast_df["Growth_pct"] * forecast_df["Hist_avg"]).sum()
        / forecast_df["Hist_avg"].sum()
    )
else:
    kpi_growth_ponderado = kpi_growth_total

fc_sorted  = forecast_df.sort_values("Growth_pct", ascending=False)
best_row   = fc_sorted.iloc[0];  best_name  = best_row["Subcategory"];  best_pct  = best_row["Growth_pct"]
worst_row  = fc_sorted.iloc[-1]; worst_name = worst_row["Subcategory"]; worst_pct = worst_row["Growth_pct"]
best_badge,  best_accent  = growth_label(best_pct,  horizon)
worst_badge, worst_accent = growth_label(worst_pct, horizon)

# =========================
# Encabezado compacto
# =========================
ctx_parts = []
if cat_sel     != "Todas": ctx_parts.append(f"Cat: {cat_sel}")
if subcat_sel  != "Todas": ctx_parts.append(f"Sub: {subcat_sel}")
if product_sel != "Todas": ctx_parts.append(f"Prod: {product_sel}")
ctx_parts.append(f"{horizon} meses")
ctx_str = "  ·  ".join(ctx_parts)

st.markdown(
    f'<h1 class="main-title">Panel de Pronósticos</h1>'
    f'<p class="forecast-context">{escape(str(region_label))}  ·  {escape(str(ctx_str))}</p>',
    unsafe_allow_html=True
)


# 3 TABS
tab_resumen, tab_analisis, tab_redist = st.tabs([
    "Resumen",
    "Análisis",
    "Redistribución",
])

with tab_resumen:

    c1, c2, c3 = st.columns(3)

    with c1:
        t1_badge, t1_accent = growth_label(kpi_growth_total, horizon)
        sign_t  = "+" if kpi_growth_total  >= 0 else ""
        sign_wp = "+" if kpi_growth_ponderado >= 0 else ""
        components.html(metric_card(
            f"Unidades estimadas · {horizon} meses", f"{kpi_total_units:,.0f} uds",
            f"Histórico: {kpi_hist_units:,.0f} uds · Total: {sign_t}{kpi_growth_total:.1f}% · Ponderado: {sign_wp}{kpi_growth_ponderado:.1f}%",
            t1_badge, "→", t1_accent,
            min(abs(kpi_growth_total/ref25*100) if ref25>0 else 70, 100),
        ), height=148, scrolling=False)

    with c2:
        components.html(metric_card(
            f"Mejor subcategoria · {horizon} meses", best_name,
            f"+{best_pct:.1f}% según Prophet · {annualize(best_pct,horizon):+.1f}% anualizado",
            best_badge, "+", best_accent,
            min(abs(best_pct/ref25*100) if ref25>0 else 0, 100),
        ), height=148, scrolling=False)

    with c3:
        sign3 = "+" if worst_pct >= 0 else ""
        components.html(metric_card(
            f"Menor alza · {horizon} meses", worst_name,
            f"{sign3}{worst_pct:.1f}% según Prophet · {annualize(worst_pct,horizon):+.1f}% anualizado",
            worst_badge, "!", worst_accent,
            min(abs(worst_pct/ref25*100) if ref25>0 else 0, 100),
        ), height=148, scrolling=False)

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
                "Forecast total: %{customdata[0]:,.0f} uds<br>"
                "Histórico total: %{customdata[1]:,.0f} uds<extra></extra>"
            ),
        ))

        fig_bar.add_vline(x=ref15, line=dict(color="#f59e0b", width=2.5, dash="dot"))
        fig_bar.add_vline(x=ref25, line=dict(color="#0138FF", width=2.5, dash="dot"))

        fig_bar.add_annotation(
            x=ref15, y=1.15, xref="x", yref="paper",
            text=f"15% anual ({ref15:.1f}% en {horizon}m)",
            showarrow=False, font=dict(color="#b45309", size=10),
            bgcolor="rgba(255,255,255,0.95)", bordercolor="rgba(245,158,11,0.30)",
            borderwidth=2, borderpad=4, xanchor="center", yanchor="bottom", xshift=-28
        )

        fig_bar.add_annotation(
            x=ref25, y=1.05, xref="x", yref="paper",
            text=f"25% anual ({ref25:.1f}% en {horizon}m)",
            showarrow=False, font=dict(color="#0B3CEE", size=10),
            bgcolor="rgba(255,255,255,0.95)", bordercolor="rgba(37,99,235,0.30)",
            borderwidth=2, borderpad=4, xanchor="center", yanchor="bottom", xshift=28
        )

        x_min = min(0, fc_bar["Growth_pct"].min(), ref15, ref25)
        x_max = max(fc_bar["Growth_pct"].max(), ref15, ref25)
        padding = (x_max - x_min) * 0.18 if x_max != x_min else 1

        fig_bar.update_layout(
            height=340,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#0f172a", family="Inter, system-ui, sans-serif", size=12),
            margin=dict(l=18, r=122, t=64, b=64),
            yaxis=dict(autorange="reversed", tickfont=dict(size=13), automargin=True),
            xaxis=dict(
                title=dict(text=f"Crecimiento Prophet en {horizon} meses (%)", font=dict(size=14), standoff=14),
                showgrid=True, gridcolor="rgba(0,0,0,0.18)",
                zeroline=True, zerolinecolor="rgba(0,0,0,0.35)", zerolinewidth=2,
                tickfont=dict(size=12),
                automargin=True,
                range=[x_min, x_max + padding]
            ),
        )

        st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False, "responsive": True})

with col_acc:

    st.markdown(
        "<div style='height: 100px;'></div>",
        unsafe_allow_html=True,
    )

    acc_color = (
        "#16a34a" if MODEL_ACCURACY >= 85
        else "#f59e0b" if MODEL_ACCURACY >= 75
        else "#dc2626"
    )

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=MODEL_ACCURACY,
        domain={"x": [0.05, 0.85], "y": [0.15, 0.95]},
        number=dict(suffix="%", font=dict(size=38, color="#0f172a", family="Inter, system-ui, sans-serif")),
        gauge=dict(
            shape="angular",
            axis=dict(range=[0, 100], tickwidth=1, tickcolor="#cbd5e1", tickfont=dict(size=9, color="#64748b")),
            bar=dict(color=acc_color, thickness=0.45),
            bgcolor="#f8fafc",
            borderwidth=0,
            steps=[
                dict(range=[0, 75],   color="#fee2e2"),
                dict(range=[75, 85],  color="#fef3c7"),
                dict(range=[85, 100], color="#dcfce7")
            ],
            threshold=dict(line=dict(color="#0f172a", width=2), thickness=0.75, value=MODEL_ACCURACY),
        ),
    ))

    fig_gauge.update_layout(
        height=340,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=30, b=30),
        font=dict(family="Inter, system-ui, sans-serif", color="#0f172a"),
        annotations=[dict(
            text=(
                "Confiabilidad<br>"
                "<span style='font-size:11px;color:#64748b'>"
                "Walk-forward · histórico</span>"
            ),
            x=0.2, y=1.0, xref="paper", yref="paper",
            showarrow=False, align="center",
            font=dict(size=15, color="#0f172a", family="Inter, system-ui, sans-serif")
        )]
    )

    st.plotly_chart(fig_gauge, use_container_width=True, config={"displayModeBar": False, "responsive": True})

# ─────────────────────────────────────────────────────────────────────
# TAB 2 — ANÁLISIS
# ─────────────────────────────────────────────────────────────────────
with tab_analisis:

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
            if len(sub) >= 12:
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
            if len(sub_base) >= 12:
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
                     f"Forecast: {int(future_fc['yhat'].mean()):,} uds/mes  ·  "
                     f"Var: {sign_d}{delta:,.0f} uds/mes",
            popover_title="",
            popover_body=(
                "**Línea azul** — ventas históricas reales por mes  \n\n"
                "**Línea verde punteada** — demanda proyectada por Prophet  \n\n"
                "**Banda azul** — intervalo de confianza  \n\n"
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
            line=dict(color="#2563eb", width=3), marker=dict(size=6, color="#2563eb"),
            hovertemplate="<b>%{x|%b %Y}</b><br>%{y:,.0f} uds<extra></extra>",
        ))
        fig_dem.add_trace(go.Scatter(
            x=future_fc["ds"], y=future_fc["yhat"],
            mode="lines+markers", name=f"Forecast ({horizon}m)",
            line=dict(color="#16a34a", width=2.5, dash="dot"),
            marker=dict(size=6, symbol="diamond", color="#16a34a"),
            hovertemplate="<b>%{x|%b %Y}</b><br>%{y:,.0f} uds<extra></extra>",
        ))
        fig_dem.update_layout(
            height=270, hovermode="x unified",
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#0f172a", family="Inter, system-ui, sans-serif", size=13),
            margin=dict(l=52, r=24, t=8, b=50),
            xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.18)", tickfont=dict(size=12), automargin=True),
            yaxis=dict(title=dict(text="uds", font=dict(size=14), standoff=10), showgrid=True, gridcolor="rgba(0,0,0,0.18)", tickfont=dict(size=12), automargin=True),
            legend=dict(orientation="h", y=1.13, x=0, font=dict(size=12)),
        )
        st.plotly_chart(fig_dem, use_container_width=True, config={"displayModeBar": False, "responsive": True})
    else:
        st.info("Sin datos suficientes (mínimo 6 meses).")

    month_names = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                   7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}

    seas_m = df_filtrado.groupby("YearMonth")["Units_sold"].sum().reset_index()
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
                "Promedio de ventas por mes del año.  \n\n"
                "**Verde** — mes >5% sobre el promedio  \n\n"
                "**Rojo** — mes >5% bajo el promedio  \n\n"
                "**Azul** — mes dentro del rango promedio"
            ),
        )
        fig_seas = go.Figure()
        fig_seas.add_hline(y=global_avg, line=dict(color="#94a3b8",width=2,dash="dot"),
            annotation_text="Prom.", annotation_position="right",
            annotation_font=dict(color="#64748b",size=8))
        fig_seas.add_trace(go.Bar(
            x=seasonality["Month_name"], y=seasonality["Units_sold"],
            marker=dict(color=seas_colors, opacity=0.88),
            hovertemplate="<b>%{x}</b><br>%{y:,.0f} uds<extra></extra>",
        ))
        fig_seas.update_layout(
            height=245, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#0f172a", family="Inter, system-ui, sans-serif", size=13),
            margin=dict(l=46, r=22, t=8, b=46),
            xaxis=dict(showgrid=False, tickfont=dict(size=12), automargin=True),
            yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.18)",
                       tickfont=dict(size=12), tickformat=",.0f", automargin=True),
        )
        st.plotly_chart(fig_seas, use_container_width=True, config={"displayModeBar": False, "responsive": True})

    with col_reg:
        section_title(
            "Forecast por región",
            subtitle="Prophet · sin filtros · 3m vs 6m",
            popover_title="",
            popover_body=(
                "Demanda total proyectada por Prophet para cada región.  \n\n"
                "**Azul** — forecast a 3 meses  \n\n"
                "**Verde** — forecast a 6 meses"
            ),
        )
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            name="3m", y=region_compare["Region_label"], x=region_compare["fc3"],
            orientation="h", marker=dict(color="#2563eb", opacity=0.80),
            hovertemplate="<b>%{y}</b><br>3m: %{x:,.0f} uds<extra></extra>",
        ))
        fig_comp.add_trace(go.Bar(
            name="6m", y=region_compare["Region_label"], x=region_compare["fc6"],
            orientation="h", marker=dict(color="#16a34a", opacity=0.80),
            hovertemplate="<b>%{y}</b><br>6m: %{x:,.0f} uds<extra></extra>",
        ))
        fig_comp.update_layout(
            barmode="group", height=245,
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#0f172a", family="Inter, system-ui, sans-serif", size=13),
            margin=dict(l=78, r=18, t=8, b=46),
            legend=dict(orientation="h", y=1.14, x=0, font=dict(size=12)),
            yaxis=dict(tickfont=dict(size=12), automargin=True),
            xaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.18)",
                       tickfont=dict(size=12), tickformat=",.0f", automargin=True),
        )
        st.plotly_chart(fig_comp, use_container_width=True, config={"displayModeBar": False, "responsive": True})


# ─────────────────────────────────────────────────────────────────────
# TAB 3 — REDISTRIBUCIÓN
# ─────────────────────────────────────────────────────────────────────
with tab_redist:

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

    with st.spinner("Calculando..."):
        subcat_region_forecast = build_subcat_region_forecast(df_maestra, horizon)
        fc_monthly             = build_monthly_forecast(horizon)

    df_work = df_maestra.copy()
    if "Excess_stock" not in df_work.columns:
        _demand_col = "Units_expected" if "Units_expected" in df_work.columns else "Units_sold"
        df_work["Excess_stock"] = (df_work["Stock"] - df_work[_demand_col]).clip(lower=0)

    redist_base_df    = build_redist_base(df_work, subcat_region_forecast, horizon)
    pares_df, plan_df = build_wave_plan(df_work, redist_base_df, fc_monthly, horizon)

    if plan_df.empty:
        st.info("No se encontraron transferencias.")
        st.stop()

    oleadas       = sorted(plan_df["Oleada"].unique())
    primera_fecha = plan_df["Fecha_envío"].iloc[0]
    ultima_fecha  = plan_df[plan_df["Oleada"]==oleadas[-1]]["Fecha_envío"].iloc[0]

    km1, km2, km3, km4 = st.columns(4)
    with km1:
        st.markdown(_mini_kpi("Productos", str(plan_df["Producto"].nunique())), unsafe_allow_html=True)
    with km2:
        st.markdown(_mini_kpi("Unidades totales", f"{plan_df['Unidades_oleada'].sum():,} uds"), unsafe_allow_html=True)
    with km3:
        st.markdown(_mini_kpi("Pares origen→destino", str(len(pares_df))), unsafe_allow_html=True)
    with km4:
        st.markdown(_mini_kpi("Período", f"{primera_fecha} – {ultima_fecha}"), unsafe_allow_html=True)

    st.markdown("<div class='redist-map-spacer'></div>", unsafe_allow_html=True)

    if vista_redist == "Mapa":
        frames, slider_steps, init_nodes, init_routes, init_annotation, n_frames = \
            build_animation_frames(plan_df, horizon)

        fig_map = go.Figure(
            data=[init_nodes] + init_routes,
            frames=frames,
            layout=go.Layout(
                height=510,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#0f172a", family="Inter, system-ui, sans-serif", size=12),
                margin=dict(l=0, r=0, t=36, b=24),
                geo=GEO_LAYOUT,
                annotations=[init_annotation],
                title=dict(
                    text=f"Plan de {n_frames} transferencias  ·  ▶ Play para iniciar",
                    font=dict(size=12, color="#64748b"),
                    x=0.5, xanchor="center",
                ),
                updatemenus=[dict(
                    type="buttons", showactive=False, direction="left",
                    x=0.5, xanchor="center", y=-0.035, yanchor="top",
                    bgcolor="#f1f5f9", bordercolor="rgba(148,163,184,.4)",
                    font=dict(color="#0f172a", size=12),
                    pad=dict(r=8, t=8),
                    buttons=[
                        dict(label="▶  Play", method="animate",
                             args=[None, dict(frame=dict(duration=2000, redraw=True),
                                              fromcurrent=True,
                                              transition=dict(duration=400, easing="cubic-in-out"))]),
                        dict(label="⏸  Pausa", method="animate",
                             args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")]),
                    ],
                )],
                sliders=[dict(
                    active=0,
                    currentvalue=dict(prefix="", visible=True, font=dict(size=11, color="#64748b")),
                    pad=dict(t=44, b=8, l=20, r=20),
                    len=0.92, x=0.04,
                    bgcolor="#f8fafc", bordercolor="rgba(148,163,184,.3)",
                    borderwidth=2, font=dict(color="#334155", size=10),
                    steps=slider_steps, tickcolor="rgba(148,163,184,.4)",
                )],
            ),
        )
        st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False, "responsive": True})

    else:
        base_oleadas = (
            plan_df
            .groupby(["Producto", "Subcategoría", "Origen_label", "Destino_label", "Oleada"])
            ["Unidades_oleada"].sum()
            .reset_index()
        )

        oleadas_presentes = sorted(base_oleadas["Oleada"].unique())
        pivot = base_oleadas.pivot_table(
            index=["Producto", "Subcategoría", "Origen_label", "Destino_label"],
            columns="Oleada",
            values="Unidades_oleada",
            aggfunc="sum",
            fill_value=0,
        ).reset_index()
        pivot.columns.name = None
        pivot = pivot.rename(columns={
            "Origen_label":  "Origen",
            "Destino_label": "Destino",
            **{o: f"Oleada {o}" for o in oleadas_presentes},
        })

        col_olas = [f"Oleada {o}" for o in oleadas_presentes]
        pivot["Total oleadas"] = pivot[col_olas].sum(axis=1)
        pivot = pivot.sort_values("Total oleadas", ascending=False)

        dist_map = (
            plan_df
            .groupby(["Producto", "Subcategoría", "Origen_label", "Destino_label"])
            ["Distancia_km"].first()
            .reset_index()
            .rename(columns={"Origen_label": "Origen", "Destino_label": "Destino"})
        )
        resumen = pivot.merge(dist_map, on=["Producto", "Subcategoría", "Origen", "Destino"], how="left")
        resumen = resumen.rename(columns={"Distancia_km": "Dist. (km)"})
        cols_finales = ["Producto", "Subcategoría", "Origen", "Destino","Total oleadas", "Dist. (km)"] + col_olas 
        resumen = resumen[cols_finales]

        u_ola = (
            plan_df
            .groupby(["Oleada", "Mes_num", "Fecha_envío"])["Unidades_oleada"]
            .sum()
            .reset_index()
            .sort_values("Oleada")
        )

        PALETA_MESES = {1:"#3b82f6",2:"#22c55e",3:"#f59e0b",4:"#a855f7",5:"#ef4444",6:"#eab308"}
        mes_labels = (
            plan_df[["Mes_num","Mes_pronóstico"]]
            .drop_duplicates("Mes_num")
            .sort_values("Mes_num")
            .set_index("Mes_num")["Mes_pronóstico"]
            .to_dict()
        )

        PANEL_H = 340
        col_tabla, col_chart = st.columns([1, 1], gap="large")

        with col_tabla:
            st.markdown(
                "<h4 style='margin:0 0 8px 0; font-size:1rem; color:#1e3a5f;'>"
                "Resumen de transferencias por producto"
                "</h4>",
                unsafe_allow_html=True,
            )
            st.dataframe(resumen, use_container_width=True, hide_index=True, height=PANEL_H)

        with col_chart:
            st.markdown(
                "<h4 style='margin:0 0 8px 0; font-size:1rem; color:#1e3a5f;'>"
                "Unidades por oleada"
                "</h4>",
                unsafe_allow_html=True,
            )

            fig_prog = go.Figure()
            fig_prog.add_trace(go.Bar(
                x=[f"Oleada {int(r.Oleada)}<br>{r.Fecha_envío}" for _, r in u_ola.iterrows()],
                y=u_ola["Unidades_oleada"],
                marker=dict(color=[PALETA_MESES.get(int(m), "#94a3b8") for m in u_ola["Mes_num"]], opacity=0.88),
                text=[f"{int(u):,} uds" for u in u_ola["Unidades_oleada"]],
                textposition="outside",
                textfont=dict(size=9),
                hovertemplate="<b>%{x}</b><br>%{y:,} unidades<extra></extra>",
            ))
            fig_prog.update_layout(
                height=PANEL_H,
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#0f172a", family="Inter, system-ui, sans-serif", size=12),
                margin=dict(l=44, r=16, t=14, b=78),
                xaxis=dict(showgrid=False, tickfont=dict(size=10), automargin=True),
                yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.18)", tickfont=dict(size=11), automargin=True),
                showlegend=False,
            )
            st.plotly_chart(fig_prog, use_container_width=True, config={"displayModeBar": False, "responsive": True})

            emojis = ["🔵","🟢","🟠","🟣","🔴","🟡"]
            caption_parts = [
                f"{emojis[m-1]} {mes_labels.get(m, f'Mes {m}')}"
                for m in sorted(mes_labels.keys())
            ]
            st.caption("  ·  ".join(caption_parts))