# pages/4_Pronosticos.py
# ══════════════════════════════════════════════════════════════════════
# DANUStore — Pronósticos Inteligentes
# Forecasting • Redistribución • Planeación Predictiva
# ══════════════════════════════════════════════════════════════════════

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import streamlit.components.v1 as components

import pandas as pd
import numpy as np

import plotly.graph_objects as go
import plotly.express as px

from prophet import Prophet

from pathlib import Path
from html import escape
import textwrap

# ══════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Pronósticos — DANUStore",
    page_icon="📈",
    layout="wide",
)

css_path = Path("styles/main.css")

if css_path.exists():
    with open(css_path) as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )

# ══════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════
def modern_metric_card(
    title,
    value,
    description,
    badge,
    icon,
    accent_color,
    progress
):

    title       = escape(str(title))
    value       = escape(str(value))
    description = escape(str(description))
    badge       = escape(str(badge))
    icon        = escape(str(icon))

    progress = max(0, min(progress, 100))

    return f"""
    <!DOCTYPE html>
    <html>
    <head>

    <style>

    body {{
        margin:0;
        font-family:Inter,system-ui,sans-serif;
        background:transparent;
    }}

    .metric-card {{

        background:
            linear-gradient(
                135deg,
                rgba(15,23,42,.98),
                rgba(30,41,59,.96)
            );

        border:1px solid rgba(148,163,184,.12);

        border-radius:28px;

        padding:28px;

        height:210px;

        box-sizing:border-box;

        overflow:hidden;

        position:relative;

        box-shadow:
            0 15px 40px rgba(0,0,0,.35);

    }}

    .metric-card::before {{

        content:"";

        position:absolute;

        top:-50px;
        right:-50px;

        width:140px;
        height:140px;

        background:{accent_color};

        opacity:.10;

        border-radius:999px;
    }}

    .metric-top {{

        display:flex;

        justify-content:space-between;

        align-items:center;

        margin-bottom:18px;
    }}

    .metric-title {{

        color:#cbd5e1;

        font-size:15px;

        font-weight:800;

        margin:0;
    }}

    .metric-icon {{

        width:44px;
        height:44px;

        border-radius:14px;

        background:{accent_color};

        display:flex;

        align-items:center;

        justify-content:center;

        font-size:20px;

        color:white;
    }}

    .metric-value {{

        color:white;

        font-size:34px;

        font-weight:950;

        letter-spacing:-1px;

        margin:0;
    }}

    .metric-description {{

        color:#94a3b8;

        font-size:14px;

        line-height:1.5;

        margin-top:10px;
    }}

    .metric-footer {{

        display:flex;

        align-items:center;

        gap:12px;

        margin-top:18px;
    }}

    .metric-badge {{

        background:rgba(255,255,255,.06);

        padding:6px 12px;

        border-radius:999px;

        color:#e2e8f0;

        font-size:12px;

        font-weight:700;
    }}

    .metric-track {{

        flex:1;

        height:8px;

        background:rgba(255,255,255,.08);

        border-radius:999px;

        overflow:hidden;
    }}

    .metric-fill {{

        width:{progress:.1f}%;

        height:100%;

        background:{accent_color};

        border-radius:999px;
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

# ══════════════════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════════════════
@st.cache_data
def load_data():

    df = pd.read_csv(
        "data/df_Maestra.csv",
        parse_dates=["Date"]
    )

    df.columns = df.columns.str.strip()

    df["YearMonth"] = df["Date"].dt.to_period("M")

    df["Excess_stock"] = (
        df["Stock"] - df["Units_sold"]
    ).clip(lower=0)

    df["Gap_units"] = (
        df["Stock"] - df["Units_sold"]
    )

    df["Gap_pct"] = (
        df["Gap_units"] /
        df["Stock"].replace(0, np.nan)
    ) * 100

    return df

df_maestra = load_data()

# ══════════════════════════════════════════════════════════════════════
# FORECAST CACHE
# ══════════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def fit_prophet(
    group_col,
    group_val,
    region,
    periods
):

    df = load_data()

    mask = (
        (df["Region"] == region)
        &
        (df[group_col] == group_val)
    )

    sub = (
        df[mask]
        .groupby("YearMonth")
        .agg(y=("Units_sold", "sum"))
        .reset_index()
    )

    if len(sub) < 6:
        return None, None

    sub["ds"] = sub["YearMonth"].dt.to_timestamp()

    sub = sub[["ds", "y"]]

    model = Prophet(
        changepoint_prior_scale=0.08,
        seasonality_mode="additive",
        uncertainty_samples=200,
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
    )

    model.add_seasonality(
        name="semiannual",
        period=182.5,
        fourier_order=4
    )

    model.fit(sub)

    future = model.make_future_dataframe(
        periods=periods,
        freq="MS"
    )

    fc = model.predict(future)

    return sub, fc

# ══════════════════════════════════════════════════════════════════════
# REGIONES
# ══════════════════════════════════════════════════════════════════════
REGION_COORDS = {

    "bajío": {
        "lat": 20.88,
        "lon": -101.07,
        "city": "León"
    },

    "ciudad de méxico": {
        "lat": 19.43,
        "lon": -99.13,
        "city": "CDMX"
    },

    "zona metropolitana de monterrey": {
        "lat": 25.67,
        "lon": -100.31,
        "city": "Monterrey"
    },

    "zona metropolitana de guadalajara": {
        "lat": 20.66,
        "lon": -103.35,
        "city": "Guadalajara"
    },

    "noroeste": {
        "lat": 29.09,
        "lon": -110.96,
        "city": "Hermosillo"
    },

    "sureste": {
        "lat": 20.97,
        "lon": -89.62,
        "city": "Mérida"
    },

    "sur": {
        "lat": 17.07,
        "lon": -96.72,
        "city": "Oaxaca"
    },
}

REG_LABEL = {

    "bajío": "Bajío",

    "ciudad de méxico": "CDMX",

    "zona metropolitana de monterrey":
        "ZM Monterrey",

    "zona metropolitana de guadalajara":
        "ZM Guadalajara",

    "noroeste": "Noroeste",

    "sureste": "Sureste",

    "sur": "Sur",
}

def haversine(lat1, lon1, lat2, lon2):

    R = 6371

    lat1, lon1, lat2, lon2 = map(
        np.radians,
        [lat1, lon1, lat2, lon2]
    )

    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        +
        np.cos(lat1)
        * np.cos(lat2)
        * np.sin((lon2 - lon1) / 2) ** 2
    )

    return int(
        2 * R * np.arcsin(np.sqrt(a))
    )

# ══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:

    sidebar_html = (
        '<div class="sidebar-header">'
        '<div class="sidebar-icon">📦</div>'
        '<div>'
        '<p class="sidebar-title">RocketData</p>'
        '<p class="sidebar-subtitle">Inventory Dashboard</p>'
        '</div>'
        '</div>'
    )

    st.markdown(sidebar_html, unsafe_allow_html=True)

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

    regiones = sorted(
        df_maestra["Region"]
        .dropna()
        .unique()
        .tolist()
    )

    region_sel = st.selectbox(
        "Región",
        ["Todas"] + regiones
    )

    categorias = sorted(
        df_maestra["Category"]
        .dropna()
        .unique()
        .tolist()
    )

    cat_sel = st.selectbox(
        "Categoría",
        ["Todas"] + categorias
    )

    # Subcategorías dependientes de la categoría seleccionada
    if cat_sel == "Todas":
        subcategorias = sorted(
            df_maestra["Subcategory"]
            .dropna()
            .unique()
            .tolist()
        )
    else:
        subcategorias = sorted(
            df_maestra.loc[
                df_maestra["Category"] == cat_sel,
                "Subcategory"
            ]
            .dropna()
            .unique()
            .tolist()
        )

    subcat_sel = st.selectbox(
        "Subcategoría",
        ["Todas"] + subcategorias
    )

    # Selector de producto dependiente de subcategoría (o categoría si no hay subcat)
    if subcat_sel != "Todas":
        productos = sorted(
            df_maestra.loc[
                df_maestra["Subcategory"] == subcat_sel,
                "Product_name"
            ]
            .dropna()
            .unique()
            .tolist()
        )
    elif cat_sel != "Todas":
        productos = sorted(
            df_maestra.loc[
                df_maestra["Category"] == cat_sel,
                "Product_name"
            ]
            .dropna()
            .unique()
            .tolist()
        )
    else:
        productos = sorted(
            df_maestra["Product_name"]
            .dropna()
            .unique()
            .tolist()
        )

    product_sel = st.selectbox(
        "Producto",
        ["Todas"] + productos
    )

    st.divider()

    horizon = st.radio(
        "Horizonte forecast",
        [3, 6],
        horizontal=True,
        format_func=lambda x: f"{x} meses"
    )

# ══════════════════════════════════════════════════════════════════════
# FILTROS
# ══════════════════════════════════════════════════════════════════════
df_filtrado = df_maestra.copy()

if isinstance(rango_fechas, tuple):

    fi, ff = rango_fechas

    df_filtrado = df_filtrado[
        (df_filtrado["Date"].dt.date >= fi)
        &
        (df_filtrado["Date"].dt.date <= ff)
    ]

if region_sel != "Todas":
    df_filtrado = df_filtrado[
        df_filtrado["Region"] == region_sel
    ]

if cat_sel != "Todas":
    df_filtrado = df_filtrado[
        df_filtrado["Category"] == cat_sel
    ]

if subcat_sel != "Todas":
    df_filtrado = df_filtrado[
        df_filtrado["Subcategory"] == subcat_sel
    ]

if 'product_sel' in globals() and product_sel != "Todas":
    df_filtrado = df_filtrado[
        df_filtrado["Product_name"] == product_sel
    ]

region_prophet = (
    region_sel
    if region_sel != "Todas"
    else df_maestra["Region"].mode()[0]
)

subcat_prophet = (
    subcat_sel
    if subcat_sel != "Todas"
    else df_maestra["Subcategory"].mode()[0]
)

# ══════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════
st.title("📈 Pronósticos Inteligentes")

st.markdown(f"""
Región:
**{REG_LABEL.get(region_prophet, region_prophet.title())}**
&nbsp; · &nbsp;
Horizonte:
**{horizon} meses**
""")

# ══════════════════════════════════════════════════════════════════════
# KPIs FORECAST
# ══════════════════════════════════════════════════════════════════════
forecast_rows = []

with st.spinner("Calculando modelos predictivos..."):

    for sc in sorted(df_filtrado["Subcategory"].dropna().unique()):

        hist, fc = fit_prophet(
            "Subcategory",
            sc,
            region_prophet,
            horizon
        )

        if hist is None:
            continue

        futuro = fc[
            fc["ds"] > hist["ds"].max()
        ]

        hist_avg = hist["y"].mean()
        future_avg = futuro["yhat"].mean()

        growth = (
            (
                (future_avg - hist_avg)
                /
                hist_avg
            ) * 100
            if hist_avg > 0
            else 0
        )

        forecast_rows.append({

            "Subcategory": sc,

            "Hist_avg": hist_avg,

            "Forecast_avg": future_avg,

            "Growth_pct": growth
        })

forecast_df = pd.DataFrame(forecast_rows)

future_total = forecast_df["Forecast_avg"].sum()

growth_positive = (
    forecast_df["Growth_pct"] > 0
).sum()

growth_negative = (
    forecast_df["Growth_pct"] < -5
).sum()

top_growth = forecast_df.sort_values(
    "Growth_pct",
    ascending=False
).iloc[0]

c1, c2, c3, c4 = st.columns(4)

with c1:
    components.html(
        modern_metric_card(
            "Demanda futura",
            f"{future_total:,.0f} u",
            "Volumen estimado total para el horizonte seleccionado.",
            "Forecast agregado",
            "📦",
            "#2563eb",
            85
        ),
        height=220
    )

with c2:
    components.html(
        modern_metric_card(
            "Subcategorías en expansión",
            f"{growth_positive}",
            "Subcategorías con tendencia positiva esperada.",
            "Crecimiento forecast",
            "📈",
            "#16a34a",
            (growth_positive / max(len(forecast_df),1))*100
        ),
        height=220
    )

with c3:
    components.html(
        modern_metric_card(
            "Riesgo desaceleración",
            f"{growth_negative}",
            "Subcategorías con caída importante proyectada.",
            "Forecast negativo",
            "⚠️",
            "#dc2626",
            (growth_negative / max(len(forecast_df),1))*100
        ),
        height=220
    )

with c4:
    components.html(
        modern_metric_card(
            "Mayor aceleración",
            f"{top_growth['Growth_pct']:+.1f}%",
            f"{top_growth['Subcategory']} lidera el crecimiento.",
            "Top performer",
            "🚀",
            "#7c3aed",
            min(abs(top_growth["Growth_pct"]),100)
        ),
        height=220
    )

# ══════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════
tab_pred, tab_redist = st.tabs([
    "📊 Predicción de demanda",
    "🗺️ Redistribución inteligente"
])

# ══════════════════════════════════════════════════════════════════════
# TAB PREDICCION
# ══════════════════════════════════════════════════════════════════════
with tab_pred:

    hist_df, fc_df = fit_prophet(
        "Subcategory",
        subcat_prophet,
        region_prophet,
        horizon
    )

    if hist_df is not None:

        future_mask = (
            fc_df["ds"] > hist_df["ds"].max()
        )

        future_fc = fc_df[future_mask]

        fig = go.Figure()

        fig.add_trace(go.Scatter(

            x=pd.concat([
                future_fc["ds"],
                future_fc["ds"][::-1]
            ]),

            y=pd.concat([
                future_fc["yhat_upper"],
                future_fc["yhat_lower"][::-1]
            ]),

            fill="toself",

            fillcolor="rgba(59,130,246,.12)",

            line=dict(color="rgba(0,0,0,0)"),

            hoverinfo="skip",

            name="Intervalo confianza"
        ))

        fig.add_trace(go.Scatter(

            x=hist_df["ds"],

            y=hist_df["y"],

            mode="lines+markers",

            name="Histórico",

            line=dict(
                color="#60a5fa",
                width=4
            ),

            marker=dict(size=7),

            hovertemplate=
                "<b>%{x|%b %Y}</b><br>"
                "Ventas: %{y:,.0f} u"
                "<extra></extra>"
        ))

        fig.add_trace(go.Scatter(

            x=future_fc["ds"],

            y=future_fc["yhat"],

            mode="lines+markers",

            name="Forecast",

            line=dict(
                color="#22c55e",
                width=5
            ),

            marker=dict(
                size=10,
                symbol="diamond"
            ),

            hovertemplate=
                "<b>%{x|%b %Y}</b><br>"
                "Forecast: %{y:,.0f} u"
                "<extra></extra>"
        ))

        fig.update_layout(

            title=
                f"Demanda esperada — "
                f"{subcat_prophet}",

            height=600,

            hovermode="x unified",

            plot_bgcolor="rgba(0,0,0,0)",

            paper_bgcolor="rgba(0,0,0,0)",

            font=dict(color="#e2e8f0"),

            margin=dict(
                l=40,
                r=40,
                t=70,
                b=40
            ),

            xaxis=dict(
                title="Tiempo",
                showgrid=True,
                gridcolor="rgba(148,163,184,.10)"
            ),

            yaxis=dict(
                title="Unidades",
                showgrid=True,
                gridcolor="rgba(148,163,184,.10)"
            ),

            legend=dict(
                orientation="h",
                y=1.06
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.caption(
            "La banda azul representa el intervalo "
            "de confianza del modelo predictivo."
        )

    st.markdown("## 📈 Crecimiento esperado")

    top_growth_df = forecast_df.sort_values(
        "Growth_pct",
        ascending=False
    ).head(12)

    fig_bar = go.Figure()

    fig_bar.add_trace(go.Bar(

        x=top_growth_df["Growth_pct"],

        y=top_growth_df["Subcategory"],

        orientation="h",

        text=[
            f"{v:+.1f}%"
            for v in top_growth_df["Growth_pct"]
        ],

        textposition="outside",

        marker=dict(
            color=top_growth_df["Growth_pct"],
            colorscale="Viridis"
        )
    ))

    fig_bar.update_layout(

        height=560,

        title=
            "Subcategorías con mayor "
            "crecimiento proyectado",

        plot_bgcolor="rgba(0,0,0,0)",

        paper_bgcolor="rgba(0,0,0,0)",

        font=dict(color="#e2e8f0"),

        yaxis=dict(
            autorange="reversed"
        ),

        xaxis=dict(
            title="% crecimiento esperado",
            showgrid=True,
            gridcolor="rgba(148,163,184,.12)"
        )
    )

    st.plotly_chart(
        fig_bar,
        use_container_width=True
    )

# ══════════════════════════════════════════════════════════════════════
# TAB REDISTRIBUCION
# ══════════════════════════════════════════════════════════════════════
with tab_redist:

    st.markdown(
        "## 🗺️ Redistribución inteligente"
    )

    transfer_rows = []

    subcats_all = (
        df_maestra["Subcategory"]
        .dropna()
        .unique()
    )

    for sc in subcats_all:

        sub_df = df_maestra[
            df_maestra["Subcategory"] == sc
        ].copy()

        resumen = (
            sub_df.groupby(["Region", "Category"])
            .agg(
                Excess_stock=("Excess_stock", "mean"),
                Units_sold=("Units_sold", "mean"),
                Stock=("Stock", "mean"),
                Sell_through=("Sell_through_pct", "mean")
            )
            .reset_index()
        )

        resumen["Origen_score"] = (
            resumen["Excess_stock"] *
            (100 - resumen["Sell_through"])
        )

        resumen["Destino_score"] = (
            resumen["Units_sold"] *
            resumen["Sell_through"]
        )

        origenes = resumen.sort_values(
            "Origen_score",
            ascending=False
        ).head(3)

        destinos = resumen.sort_values(
            "Destino_score",
            ascending=False
        ).head(3)

        for _, o in origenes.iterrows():

            for _, d in destinos.iterrows():

                if o["Region"] == d["Region"]:
                    continue

                exceso = o["Excess_stock"]

                demanda = d["Units_sold"]

                unidades = int(
                    max(
                        min(
                            exceso * 0.75,
                            demanda * 0.55
                        ),
                        0
                    )
                )

                if unidades <= 0:
                    continue

                dist = haversine(
                    REGION_COORDS[o["Region"]]["lat"],
                    REGION_COORDS[o["Region"]]["lon"],
                    REGION_COORDS[d["Region"]]["lat"],
                    REGION_COORDS[d["Region"]]["lon"]
                )

                transfer_rows.append({

                    "Origen": o["Region"],

                    "Destino": d["Region"],

                    "Subcategory": sc,

                    "Category": o["Category"],

                    "Unidades": unidades,

                    "Distancia": dist,

                    "Exceso_origen": round(exceso, 0),

                    "Demanda_destino": round(demanda, 0),

                    "Sell_through_destino":
                        round(d["Sell_through"], 1)
                })

    transfer_df = (
        pd.DataFrame(transfer_rows)
        .sort_values(
            "Unidades",
            ascending=False
        )
        .drop_duplicates(
            subset=[
                "Origen",
                "Destino",
                "Subcategory"
            ]
        )
    )

    # ══════════════════════════════════════════════════════════════
    # MAPA
    # ══════════════════════════════════════════════════════════════
    fig_map = go.Figure()

    for _, row in transfer_df.iterrows():

        o = REGION_COORDS[row["Origen"]]
        d = REGION_COORDS[row["Destino"]]

        fig_map.add_trace(go.Scattergeo(

            lat=[o["lat"], d["lat"]],

            lon=[o["lon"], d["lon"]],

            mode="lines",

            line=dict(
                width=2.5,
                color="rgba(99,102,241,.42)"
            ),

            hovertemplate=
                f"<b>{REG_LABEL.get(row['Origen'])}"
                f" → "
                f"{REG_LABEL.get(row['Destino'])}</b><br><br>"

                f"Categoría: "
                f"<b>{row['Category']}</b><br>"

                f"Subcategoría: "
                f"<b>{row['Subcategory']}</b><br>"

                f"Cantidad: "
                f"<b>{row['Unidades']:,} u</b><br>"

                f"Distancia: "
                f"<b>{row['Distancia']:,} km</b><br>"

                f"Exceso origen: "
                f"<b>{row['Exceso_origen']:,} u</b><br>"

                f"Demanda destino: "
                f"<b>{row['Demanda_destino']:,} u</b>"

                "<extra></extra>",

            showlegend=False
        ))

    for region, data in REGION_COORDS.items():

        fig_map.add_trace(go.Scattergeo(

            lat=[data["lat"]],

            lon=[data["lon"]],

            mode="markers+text",

            marker=dict(
                size=18,
                color="#2563eb",
                line=dict(
                    width=2,
                    color="white"
                )
            ),

            text=[data["city"]],

            textposition="top center",

            hovertemplate=
                f"<b>{REG_LABEL.get(region)}</b>"
                "<extra></extra>",

            showlegend=False
        ))

    fig_map.update_layout(

        height=680,

        paper_bgcolor="rgba(0,0,0,0)",

        plot_bgcolor="rgba(0,0,0,0)",

        font=dict(color="#e2e8f0"),

        margin=dict(
            l=0,
            r=0,
            t=60,
            b=0
        ),

        geo=dict(

            scope="north america",

            projection_scale=4.8,

            center=dict(
                lat=23.6,
                lon=-102.5
            ),

            showland=True,

            landcolor="#0f172a",

            showocean=True,

            oceancolor="#020617",

            showlakes=True,

            lakecolor="#020617",

            showcountries=True,

            countrycolor="rgba(255,255,255,.12)",

            subunitcolor="rgba(255,255,255,.08)",

            coastlinecolor="rgba(255,255,255,.08)",

            bgcolor="rgba(0,0,0,0)"
        )
    )

    st.plotly_chart(
        fig_map,
        use_container_width=True
    )

    st.caption(
        "Las conexiones representan transferencias "
        "óptimas sugeridas según demanda, "
        "sell-through y exceso de inventario."
    )

    # ══════════════════════════════════════════════════════════════
    # TABLA
    # ══════════════════════════════════════════════════════════════
    st.markdown(
        "## 📦 Plan sugerido de transferencias"
    )

    transfer_show = transfer_df.copy()

    transfer_show["Origen"] = (
        transfer_show["Origen"]
        .map(REG_LABEL)
    )

    transfer_show["Destino"] = (
        transfer_show["Destino"]
        .map(REG_LABEL)
    )

    transfer_show.columns = [

        "Origen",

        "Destino",

        "Subcategoría",

        "Categoría",

        "Cantidad sugerida",

        "Distancia (km)",

        "Exceso origen",

        "Demanda destino",

        "Sell-through destino"
    ]

    st.dataframe(
        transfer_show,
        use_container_width=True,
        hide_index=True
    )