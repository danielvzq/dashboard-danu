# pages/4_Pronosticos.py
# ══════════════════════════════════════════════════════════════════
# Vista de Pronósticos — DANUStore  · Dark theme · Rediseño visual
# ══════════════════════════════════════════════════════════════════

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import streamlit_shadcn_ui as ui
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from prophet import Prophet

st.set_page_config(
    page_title="Pronósticos — DANUStore",
    page_icon="📈",
    layout="wide",
)

with open("styles/main.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── CSS adicional para dark cards y tablas ────────────────────────
st.markdown("""
<style>
/* Fondo general de la página */
.stApp { background-color: #0f0f0f; }
section[data-testid="stSidebar"] { background-color: #161616; }
section[data-testid="stSidebar"] * { color: #e5e5e5 !important; }

/* Títulos y textos */
h1, h2, h3, h4, .stMarkdown p, label, .stCaption { color: #f0f0f0 !important; }

/* Tabs */
.stTabs [role="tab"] { color: #aaa !important; }
.stTabs [role="tab"][aria-selected="true"] { color: #fff !important; border-bottom-color: #6366f1 !important; }

/* Dataframe */
.stDataFrame { border-radius: 12px; overflow: hidden; }
iframe { border-radius: 12px !important; }

/* Dividers */
hr { border-color: #2a2a2a !important; }

/* Spinner */
.stSpinner > div { border-top-color: #6366f1 !important; }

/* Metric cards override */
[data-testid="stMetricValue"] { color: #fff !important; }
</style>
""", unsafe_allow_html=True)

# ── Paleta de colores para dark theme ────────────────────────────
# Gráficas
C_CYAN     = "#22d3ee"   # histórico
C_VIOLET   = "#a78bfa"   # pronóstico
C_EMERALD  = "#34d399"   # positivo / alza
C_ROSE     = "#fb7185"   # negativo / baja
C_AMBER    = "#fbbf24"   # neutro / estable
C_SLATE    = "#94a3b8"   # textos secundarios
C_FONDO    = "#161616"   # fondo de gráficas
C_GRID     = "#2a2a2a"   # grillas
C_PAPER    = "#0f0f0f"   # fondo papel

# Mapa
C_ORIGEN   = "#f87171"   # rojo
C_DESTINO  = "#4ade80"   # verde
C_EQUILIBRIO = "#fb923c" # naranja


# ══════════════════════════════════════════════════════════════════
# DATOS Y MODELOS
# ══════════════════════════════════════════════════════════════════
@st.cache_data
def load_data():
    df = pd.read_csv("data/df_Maestra.csv", parse_dates=["Date"])
    df["YearMonth"]    = df["Date"].dt.to_period("M")
    df["Excess_stock"] = (df["Stock"] - df["Units_sold"]).clip(lower=0)
    df["Gap_units"]    = df["Stock"] - df["Units_sold"]
    df["Gap_pct"]      = df["Gap_units"] / df["Stock"].replace(0, np.nan) * 100
    return df


@st.cache_data
def fit_prophet(group_col, group_val, region, periods):
    df = load_data()
    mask = (df["Region"] == region) & (df[group_col] == group_val)
    sub  = (
        df[mask]
        .groupby("YearMonth")
        .agg(y=("Units_sold", "sum"))
        .reset_index()
    )
    sub["ds"] = sub["YearMonth"].dt.to_timestamp()
    sub = sub[["ds", "y"]]
    m = Prophet(
        changepoint_prior_scale=0.05,
        seasonality_mode="additive",
        uncertainty_samples=300,
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
    )
    m.add_seasonality(name="semestral", period=182.5, fourier_order=3)
    m.fit(sub)
    future   = m.make_future_dataframe(periods=periods, freq="MS")
    forecast = m.predict(future)
    return sub, forecast


REGION_COORDS = {
    "bajío":                             {"lat": 20.88, "lon": -101.07, "city": "León"},
    "ciudad de méxico":                  {"lat": 19.43, "lon": -99.13,  "city": "CDMX"},
    "zona metropolitana de monterrey":   {"lat": 25.67, "lon": -100.31, "city": "Monterrey"},
    "zona metropolitana de guadalajara": {"lat": 20.66, "lon": -103.35, "city": "Guadalajara"},
    "noroeste":                          {"lat": 29.09, "lon": -110.96, "city": "Hermosillo"},
    "sureste":                           {"lat": 20.97, "lon": -89.62,  "city": "Mérida"},
    "sur":                               {"lat": 17.07, "lon": -96.72,  "city": "Oaxaca"},
}

REG_LABEL = {
    "bajío": "Bajío",
    "ciudad de méxico": "CDMX",
    "zona metropolitana de monterrey": "ZM Monterrey",
    "zona metropolitana de guadalajara": "ZM Guadalajara",
    "noroeste": "Noroeste",
    "sureste": "Sureste",
    "sur": "Sur",
}


def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2-lat1)/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin((lon2-lon1)/2)**2
    return int(2 * R * np.arcsin(np.sqrt(a)))


df_base = load_data()


# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## Filtros")
    st.divider()

    region_sel = st.selectbox(
        "Región",
        options=sorted(df_base["Region"].unique()),
        format_func=lambda x: REG_LABEL.get(x, x.title()),
    )
    cat_sel = st.selectbox(
        "Categoría",
        options=["Todas"] + sorted(df_base["Category"].unique()),
    )
    subcats_opts = (
        sorted(df_base[df_base["Category"] == cat_sel]["Subcategory"].unique())
        if cat_sel != "Todas"
        else sorted(df_base["Subcategory"].unique())
    )
    subcat_sel = st.selectbox("Subcategoría", options=subcats_opts)
    prods_opts = ["Toda la subcategoría"] + sorted(
        df_base[
            (df_base["Region"] == region_sel) &
            (df_base["Subcategory"] == subcat_sel)
        ]["Product_name"].unique()
    )
    product_sel = st.selectbox("Producto", options=prods_opts)
    st.divider()
    horizon = st.radio(
        "Horizonte",
        options=[3, 6],
        format_func=lambda x: f"{x} meses",
        horizontal=True,
    )
    st.divider()
    st.caption("DANUStore · Inteligencia Predictiva")


# ══════════════════════════════════════════════════════════════════
# ENCABEZADO
# ══════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style='margin-bottom:4px'>
  <span style='font-size:28px;font-weight:700;color:#f0f0f0'>Pronósticos de Inventario</span>
</div>
<div style='color:{C_SLATE};font-size:14px;margin-bottom:24px'>
  Región: <b style='color:#e2e8f0'>{REG_LABEL.get(region_sel, region_sel.title())}</b>
  &nbsp;·&nbsp; Subcategoría: <b style='color:#e2e8f0'>{subcat_sel}</b>
  &nbsp;·&nbsp; Horizonte: <b style='color:#e2e8f0'>{horizon} meses</b>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# KPIs
# ══════════════════════════════════════════════════════════════════
@st.cache_data
def calcular_kpis_tendencia(region, subcat, horizon):
    df_k    = load_data()
    subcats = sorted(df_k["Subcategory"].unique())
    rows    = []
    for sc in subcats:
        try:
            hist, fc = fit_prophet("Subcategory", sc, region, horizon)
            fut = fc[fc["ds"] > hist["ds"].max()]
            if fut.empty or hist.empty:
                continue
            hist_rec = hist.tail(3)["y"].mean()
            fc_prom  = fut["yhat"].mean()
            cambio   = (fc_prom - hist_rec) / hist_rec * 100 if hist_rec > 0 else 0
            tendencia = "↑ Alza" if cambio >= 2 else ("↓ Baja" if cambio <= -2 else "→ Estable")
            rows.append({
                "Subcategoría":   sc,
                "Histórico (u)":  round(hist_rec, 0),
                "Pronóstico (u)": round(fc_prom, 0),
                "Cambio %":       round(cambio, 1),
                "Tendencia":      tendencia,
            })
        except Exception:
            pass
    return pd.DataFrame(rows)


def kpi_card(title, value, subtitle, color="#6366f1", icon=""):
    return f"""
    <div style='
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #2a2a4a;
        border-left: 4px solid {color};
        border-radius: 12px;
        padding: 20px 22px;
        height: 110px;
        display: flex; flex-direction: column; justify-content: space-between;
    '>
      <div style='font-size:12px;color:{C_SLATE};text-transform:uppercase;letter-spacing:0.08em;font-weight:600'>{title}</div>
      <div style='font-size:26px;font-weight:800;color:#f8fafc;line-height:1.1'>{icon} {value}</div>
      <div style='font-size:12px;color:{color};font-weight:500'>{subtitle}</div>
    </div>"""


with st.spinner("Calculando tendencias…"):
    kpi_df = calcular_kpis_tendencia(region_sel, subcat_sel, horizon)

k1, k2, k3, k4 = st.columns(4)

if not kpi_df.empty:
    row_sel = kpi_df[kpi_df["Subcategoría"] == subcat_sel]
    with k1:
        if not row_sel.empty:
            r = row_sel.iloc[0]
            color = C_EMERALD if r["Cambio %"] >= 2 else (C_ROSE if r["Cambio %"] <= -2 else C_AMBER)
            st.markdown(kpi_card(
                subcat_sel[:24],
                f"{int(r['Pronóstico (u)']):,} u",
                f"{r['Cambio %']:+.1f}% vs histórico",
                color=color, icon=r["Tendencia"].split()[0],
            ), unsafe_allow_html=True)
        else:
            st.markdown(kpi_card("Subcategoría", "—", "Sin datos"), unsafe_allow_html=True)

    alzas = kpi_df[kpi_df["Cambio %"] >= 2].sort_values("Cambio %", ascending=False)
    with k2:
        if not alzas.empty:
            t = alzas.iloc[0]
            st.markdown(kpi_card(
                "Mayor alza",
                f"+{t['Cambio %']:.1f}%",
                f"{t['Subcategoría']}  ·  {int(t['Pronóstico (u)']):,} u",
                color=C_EMERALD, icon="↑",
            ), unsafe_allow_html=True)
        else:
            st.markdown(kpi_card("Mayor alza", "—", "Sin alzas detectadas", color=C_SLATE), unsafe_allow_html=True)

    bajas = kpi_df[kpi_df["Cambio %"] <= -2].sort_values("Cambio %")
    with k3:
        if not bajas.empty:
            b = bajas.iloc[0]
            st.markdown(kpi_card(
                "Mayor baja",
                f"{b['Cambio %']:.1f}%",
                f"{b['Subcategoría']}  ·  {int(b['Pronóstico (u)']):,} u",
                color=C_ROSE, icon="↓",
            ), unsafe_allow_html=True)
        else:
            st.markdown(kpi_card("Mayor baja", "—", "Demanda estable", color=C_SLATE), unsafe_allow_html=True)

    n_a = int((kpi_df["Cambio %"] >= 2).sum())
    n_b = int((kpi_df["Cambio %"] <= -2).sum())
    n_e = len(kpi_df) - n_a - n_b
    with k4:
        st.markdown(kpi_card(
            "Resumen tendencias",
            f"↑{n_a} · ↓{n_b} · →{n_e}",
            f"{len(kpi_df)} subcategorías · {REG_LABEL.get(region_sel,'')}",
            color=C_VIOLET, icon="",
        ), unsafe_allow_html=True)
else:
    for col in [k1, k2, k3, k4]:
        with col:
            st.markdown(kpi_card("—", "Sin datos", "Ajusta los filtros", color=C_SLATE), unsafe_allow_html=True)

st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PESTAÑAS
# ══════════════════════════════════════════════════════════════════
tab_pred, tab_redist = st.tabs(["  Predicción de demanda  ", "  Redistribución  "])


# ──────────────────────────────────────────────────────────────────
# PESTAÑA 1 — Predicción de demanda
# ──────────────────────────────────────────────────────────────────
with tab_pred:
    use_product = product_sel != "Toda la subcategoría"
    group_col   = "Product_name" if use_product else "Subcategory"
    group_val   = product_sel   if use_product else subcat_sel
    label_pred  = f"{group_val}  ·  {REG_LABEL.get(region_sel, region_sel.title())}"

    with st.spinner("Entrenando modelo Prophet…"):
        hist_df, fc_df = fit_prophet(group_col, group_val, region_sel, horizon)

    fut_mask = fc_df["ds"] > hist_df["ds"].max()
    hist_fc  = fc_df[~fut_mask]
    fut_fc   = fc_df[fut_mask]
    corte    = hist_df["ds"].max()

    # ── Gráfica principal — dark ──────────────────────────────────
    fig = go.Figure()

    # Banda IC 95% — violeta translúcida
    fig.add_trace(go.Scatter(
        x=pd.concat([fut_fc["ds"], fut_fc["ds"][::-1]]),
        y=pd.concat([fut_fc["yhat_upper"], fut_fc["yhat_lower"][::-1]]),
        fill="toself",
        fillcolor="rgba(167,139,250,0.12)",
        line=dict(color="rgba(0,0,0,0)"),
        name="IC 95%",
        hoverinfo="skip",
    ))

    # Área bajo histórico — cyan translúcido
    fig.add_trace(go.Scatter(
        x=hist_df["ds"], y=hist_df["y"],
        mode="lines",
        line=dict(color=C_CYAN, width=0),
        fill="tozeroy",
        fillcolor="rgba(34,211,238,0.06)",
        showlegend=False,
        hoverinfo="skip",
    ))

    # Línea histórica — cyan
    fig.add_trace(go.Scatter(
        x=hist_df["ds"], y=hist_df["y"],
        mode="lines+markers",
        name="Histórico",
        line=dict(color=C_CYAN, width=2.5),
        marker=dict(size=6, color=C_CYAN, line=dict(width=2, color=C_FONDO)),
        hovertemplate="<b>%{x|%b %Y}</b><br>Ventas: <b>%{y:,.0f} u</b><extra>Histórico</extra>",
    ))

    # Ajuste modelo — cyan punteado
    fig.add_trace(go.Scatter(
        x=hist_fc["ds"], y=hist_fc["yhat"],
        mode="lines",
        name="Ajuste modelo",
        line=dict(color=C_CYAN, width=1.2, dash="dot"),
        opacity=0.35,
        hoverinfo="skip",
    ))

    # Pronóstico — violeta
    fig.add_trace(go.Scatter(
        x=fut_fc["ds"], y=fut_fc["yhat"],
        mode="lines+markers",
        name=f"Pronóstico +{horizon}m",
        line=dict(color=C_VIOLET, width=2.5),
        marker=dict(size=9, symbol="diamond", color=C_VIOLET,
                    line=dict(width=2, color=C_FONDO)),
        hovertemplate="<b>%{x|%b %Y}</b><br>Pronóstico: <b>%{y:,.0f} u</b><extra>Pronóstico</extra>",
    ))

    # Línea de corte
    fig.add_shape(
        type="line", x0=corte, x1=corte, y0=0, y1=1,
        xref="x", yref="paper",
        line=dict(dash="dot", color=C_SLATE, width=1.5),
    )
    fig.add_annotation(
        x=corte, y=0.97, xref="x", yref="paper",
        text="  Hoy", showarrow=False, xanchor="left",
        font=dict(color=C_SLATE, size=11),
    )

    fig.update_layout(
        title=dict(
            text=f"<b style='color:#f8fafc'>Demanda pronosticada</b>"
                 f"<span style='color:{C_SLATE};font-size:14px'>  {label_pred}</span>",
            font=dict(size=18, color="#f8fafc"),
        ),
        xaxis_title="Mes",
        yaxis_title="Unidades vendidas",
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            bgcolor="rgba(22,22,22,0.8)", bordercolor="#2a2a2a", borderwidth=1,
            font=dict(color="#e2e8f0", size=12),
        ),
        height=440,
        plot_bgcolor=C_FONDO,
        paper_bgcolor=C_PAPER,
        xaxis=dict(
            showgrid=True, gridcolor=C_GRID, gridwidth=1,
            showline=False, tickfont=dict(size=11, color=C_SLATE),
            title_font=dict(color=C_SLATE),
        ),
        yaxis=dict(
            showgrid=True, gridcolor=C_GRID, gridwidth=1,
            showline=False, tickfont=dict(size=11, color=C_SLATE),
            title_font=dict(color=C_SLATE),
            rangemode="tozero",
        ),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#1e1e2e", bordercolor="#6366f1",
                        font=dict(color="white", size=13)),
        margin=dict(t=70, b=50, l=60, r=30),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Sub-tabs ──────────────────────────────────────────────────
    t_vals, t_comp = st.tabs(["  Valores del pronóstico  ", "  Tendencias por subcategoría  "])

    with t_vals:
        tbl = fut_fc[["ds","yhat","yhat_lower","yhat_upper"]].copy()
        tbl.columns = ["Mes","Pronóstico","IC Inferior","IC Superior"]
        tbl["Mes"] = tbl["Mes"].dt.strftime("%b %Y")
        tbl[["Pronóstico","IC Inferior","IC Superior"]] = (
            tbl[["Pronóstico","IC Inferior","IC Superior"]].round(0).astype(int)
        )
        st.dataframe(
            tbl.style
               .format({"Pronóstico": "{:,}", "IC Inferior": "{:,}", "IC Superior": "{:,}"})
               .set_properties(**{"text-align": "right"})
               .set_table_styles([
                   {"selector": "th", "props": [("background-color","#1a1a2e"),("color","#a78bfa"),("font-weight","600")]},
                   {"selector": "td", "props": [("background-color","#0f0f1a"),("color","#e2e8f0")]},
               ]),
            use_container_width=True, hide_index=True,
        )

    with t_comp:
        st.markdown(f"<p style='color:{C_SLATE};font-size:13px'>Cambio % entre el promedio histórico reciente y el pronóstico por subcategoría.</p>",
                    unsafe_allow_html=True)

        if not kpi_df.empty:
            tbl_tend = (
                kpi_df[["Subcategoría","Histórico (u)","Pronóstico (u)","Cambio %","Tendencia"]]
                .copy().sort_values("Cambio %", ascending=False).reset_index(drop=True)
            )
            tbl_tend["Histórico (u)"]  = tbl_tend["Histórico (u)"].astype(int)
            tbl_tend["Pronóstico (u)"] = tbl_tend["Pronóstico (u)"].astype(int)

            def color_row(val):
                if isinstance(val, float):
                    if val >= 2:   return f"color: {C_EMERALD}; font-weight:600"
                    if val <= -2:  return f"color: {C_ROSE};    font-weight:600"
                    return f"color: {C_AMBER}"
                return ""

            # Use `apply` instead of `applymap` for broader pandas compatibility
            def _color_col(s):
                return [color_row(v) for v in s]

            st.dataframe(
                tbl_tend.style
                    .apply(_color_col, subset=["Cambio %"])
                    .format({"Histórico (u)": "{:,}", "Pronóstico (u)": "{:,}", "Cambio %": "{:+.1f}%"})
                    .set_table_styles([
                        {"selector": "th", "props": [("background-color","#1a1a2e"),("color","#a78bfa"),("font-weight","600")]},
                        {"selector": "td", "props": [("background-color","#0f0f1a"),("color","#e2e8f0")]},
                    ]),
                use_container_width=True, hide_index=True,
            )

            # Gráfica de barras horizontales — dark
            bar_df  = kpi_df.sort_values("Cambio %", ascending=True).reset_index(drop=True)
            colores = [
                C_EMERALD if v >= 2 else (C_ROSE if v <= -2 else C_AMBER)
                for v in bar_df["Cambio %"]
            ]

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=bar_df["Cambio %"],
                y=bar_df["Subcategoría"],
                orientation="h",
                marker=dict(
                    color=colores,
                    opacity=0.85,
                    line=dict(color="rgba(0,0,0,0.2)", width=0.5),
                ),
                text=[f"{v:+.1f}%" for v in bar_df["Cambio %"]],
                textposition="outside",
                textfont=dict(size=12, color="#e2e8f0"),
                hovertemplate="<b>%{y}</b><br>Cambio: %{x:+.1f}%<extra></extra>",
            ))
            fig_bar.add_vline(x=0, line_dash="solid", line_color="#3f3f5c", line_width=1.5)
            fig_bar.add_vrect(
                x0=-2, x1=2,
                fillcolor="rgba(148,163,184,0.04)",
                line_width=0,
                annotation_text="zona estable",
                annotation_position="top left",
                annotation_font=dict(size=10, color=C_SLATE),
            )
            fig_bar.update_layout(
                title=dict(
                    text=f"<b style='color:#f8fafc'>Tendencia de demanda</b>"
                         f"<span style='color:{C_SLATE};font-size:13px'>  {REG_LABEL.get(region_sel,'')} · próximos {horizon} meses</span>",
                    font=dict(size=17, color="#f8fafc"),
                ),
                xaxis_title="Cambio % vs histórico reciente",
                height=420,
                plot_bgcolor=C_FONDO,
                paper_bgcolor=C_PAPER,
                xaxis=dict(
                    showgrid=True, gridcolor=C_GRID, zeroline=False,
                    ticksuffix="%", tickfont=dict(size=11, color=C_SLATE),
                    title_font=dict(color=C_SLATE),
                ),
                yaxis=dict(tickfont=dict(size=12, color="#e2e8f0")),
                hoverlabel=dict(bgcolor="#1e1e2e", bordercolor="#6366f1",
                                font=dict(color="white", size=13)),
                margin=dict(l=20, r=90, t=60, b=50),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            c1, c2, c3 = st.columns(3)
            c1.markdown(f"<span style='color:{C_EMERALD};font-size:18px'>■</span> <span style='color:#e2e8f0'>**Alza** ≥ +2%</span>", unsafe_allow_html=True)
            c2.markdown(f"<span style='color:{C_ROSE};font-size:18px'>■</span> <span style='color:#e2e8f0'>**Baja** ≤ −2%</span>", unsafe_allow_html=True)
            c3.markdown(f"<span style='color:{C_AMBER};font-size:18px'>■</span> <span style='color:#e2e8f0'>**Estable** entre −2% y +2%</span>", unsafe_allow_html=True)
        else:
            st.info("No hay datos suficientes para calcular tendencias en esta región.")


# ──────────────────────────────────────────────────────────────────
# PESTAÑA 2 — Redistribución
# ──────────────────────────────────────────────────────────────────
with tab_redist:

    @st.cache_data
    def calcular_redistribucion():
        df_r = load_data()
        base = (
            df_r.groupby(["Region","Subcategory"])
            .agg(
                Avg_excess=("Excess_stock","mean"),
                Gap_pct=("Gap_pct","mean"),
                Sell_through=("Sell_through_pct","mean"),
            )
            .reset_index()
        )
        rows = []
        for reg in df_r["Region"].unique():
            for sc in df_r["Subcategory"].unique():
                try:
                    h, fc = fit_prophet("Subcategory", sc, reg, 3)
                    fc_avg = fc[fc["ds"] > h["ds"].max()]["yhat"].mean()
                    rows.append({"Region": reg, "Subcategory": sc, "Forecast_avg": fc_avg})
                except Exception:
                    pass
        fc_df2 = pd.DataFrame(rows)
        base   = base.merge(fc_df2, on=["Region","Subcategory"], how="left")
        # Restaurar lógica por cuantiles (más robusta) pero añadir fallback para filas no clasificadas
        base["Forecast_avg"] = base["Forecast_avg"].replace(0, np.nan)
        base["Avg_excess"]   = base["Avg_excess"].replace(0, np.nan)

        # Fórmulas originales
        base["Score_origen"]  = base["Gap_pct"] * (1 / base["Forecast_avg"].replace(0, np.nan))
        base["Score_destino"] = base["Forecast_avg"] / base["Avg_excess"].replace(0, np.nan)

        # Umbrales por cuantiles
        p75_o = base["Score_origen"].quantile(0.75)
        p75_d = base["Score_destino"].quantile(0.75)

        base["Rol"] = "Equilibrio"
        base.loc[base["Score_origen"] >= p75_o, "Rol"] = "ORIGEN"
        base.loc[base["Score_destino"] >= p75_d, "Rol"] = "DESTINO"

        # Fallback: para las filas que quedaron en 'Equilibrio', asignar ORIGEN o DESTINO según el mayor score disponible
        mask_eq = base["Rol"] == "Equilibrio"
        base.loc[mask_eq, "Rol"] = np.where(
            base.loc[mask_eq, "Score_origen"].fillna(-np.inf) >= base.loc[mask_eq, "Score_destino"].fillna(-np.inf),
            "ORIGEN",
            "DESTINO",
        )

        # Reemplazar cualquier NaN final por DESTINO para seguridad
        base["Rol"] = base["Rol"].fillna("DESTINO")
        return base

    with st.spinner("Calculando redistribución…"):
        redist_df = calcular_redistribucion()

    reg_rol = (
        redist_df.groupby("Region")["Rol"]
        .apply(lambda x: x.value_counts().idxmax())
        .reset_index()
        .rename(columns={"Rol": "Rol_predominante"})
    )
    reg_rol["lat"]  = reg_rol["Region"].map(lambda r: REGION_COORDS.get(r,{}).get("lat",0))
    reg_rol["lon"]  = reg_rol["Region"].map(lambda r: REGION_COORDS.get(r,{}).get("lon",0))
    reg_rol["city"] = reg_rol["Region"].map(lambda r: REGION_COORDS.get(r,{}).get("city",""))

    COLOR_ROL  = {"ORIGEN": C_ORIGEN,    "DESTINO": C_DESTINO,    "Equilibrio": C_EQUILIBRIO}
    HALO_ROL   = {"ORIGEN": "rgba(248,113,113,0.18)", "DESTINO": "rgba(74,222,128,0.18)", "Equilibrio": "rgba(251,146,60,0.18)"}

    fig_map = go.Figure()

    # Líneas de transferencia
    origenes = reg_rol[reg_rol["Rol_predominante"] == "ORIGEN"]
    destinos  = reg_rol[reg_rol["Rol_predominante"] == "DESTINO"]
    for _, orig in origenes.iterrows():
        for _, dest in destinos.iterrows():
            dist = haversine(orig["lat"], orig["lon"], dest["lat"], dest["lon"])
            fig_map.add_trace(go.Scattergeo(
                lat=[orig["lat"], dest["lat"]],
                lon=[orig["lon"], dest["lon"]],
                mode="lines",
                line=dict(width=1.8, color="rgba(167,139,250,0.35)"),
                hovertemplate=(
                    f"<b>{orig['city']} → {dest['city']}</b><br>"
                    f"Distancia: ~{dist:,} km<extra></extra>"
                ),
                showlegend=False,
            ))

    # Halos
    for _, row in reg_rol.iterrows():
        fig_map.add_trace(go.Scattergeo(
            lat=[row["lat"]], lon=[row["lon"]],
            mode="markers",
            marker=dict(size=42, color=HALO_ROL[row["Rol_predominante"]], line=dict(width=0)),
            showlegend=False, hoverinfo="skip",
        ))

    # Marcadores
    for _, row in reg_rol.iterrows():
        fig_map.add_trace(go.Scattergeo(
            lat=[row["lat"]], lon=[row["lon"]],
            mode="markers+text",
            marker=dict(
                size=18,
                color=COLOR_ROL[row["Rol_predominante"]],
                opacity=1,
                line=dict(width=2.5, color="#0f0f0f"),
            ),
            text=[f"  {row['city']}"],
            textposition="middle right",
            textfont=dict(size=12, color="#f0f0f0", family="Arial Black"),
            hovertemplate=(
                f"<b>{row['Region'].title()}</b><br>"
                f"Rol: <b>{row['Rol_predominante']}</b><extra></extra>"
            ),
            showlegend=False,
        ))

    fig_map.update_layout(
        geo=dict(
            scope="north america",
            resolution=50,
            center=dict(lat=23.6, lon=-102.5),
            projection_scale=4.8,
            showland=True,       landcolor="#1a1a2e",
            showocean=True,      oceancolor="#0d1b2a",
            showlakes=True,      lakecolor="#0d1b2a",
            showrivers=True,     rivercolor="#1e3a5f",
            showcoastlines=True, coastlinecolor="#2d3561", coastlinewidth=1,
            showcountries=True,  countrycolor="#2d3561",  countrywidth=1,
            showsubunits=True,   subunitcolor="#252550",  subunitwidth=0.5,
            bgcolor="#0f0f0f",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=-0.06,
            xanchor="center", x=0.5,
            bgcolor="rgba(15,15,30,0.9)",
            bordercolor="#2a2a4a", borderwidth=1,
            font=dict(size=12, color="#e2e8f0"),
        ),
        title=dict(
            text="<b style='color:#f8fafc'>Mapa de redistribución de inventario</b>",
            font=dict(size=17, color="#f8fafc"),
            x=0.01,
        ),
        height=520,
        margin=dict(l=0, r=0, t=55, b=15),
        paper_bgcolor="#0f0f0f",
        hoverlabel=dict(bgcolor="#1e1e2e", bordercolor="#6366f1",
                        font=dict(color="white", size=13)),
    )
    fig_map_layout = fig_map  # keep reference; we'll add plan lines before plotting

    # ── Plan de transferencias ────────────────────────────────────
    st.markdown("<h3 style='color:#f0f0f0'>Plan de transferencias sugerido</h3>", unsafe_allow_html=True)

    plan = (
        redist_df[redist_df["Rol"] == "ORIGEN"][["Region","Subcategory","Avg_excess"]]
        .merge(
            redist_df[redist_df["Rol"] == "DESTINO"][["Region","Subcategory","Forecast_avg"]],
            on="Subcategory", suffixes=("_origen","_destino"),
        )
    )
    plan["Unidades"]   = (plan["Avg_excess"] * 0.30).round(0).astype(int)
    plan["Dist (km)"]  = plan.apply(lambda r: haversine(
        REGION_COORDS.get(r["Region_origen"],{}).get("lat",0),
        REGION_COORDS.get(r["Region_origen"],{}).get("lon",0),
        REGION_COORDS.get(r["Region_destino"],{}).get("lat",0),
        REGION_COORDS.get(r["Region_destino"],{}).get("lon",0),
    ), axis=1)
    plan["Origen"]     = plan["Region_origen"].map(lambda x: REG_LABEL.get(x, x.title()))
    plan["Destino"]    = plan["Region_destino"].map(lambda x: REG_LABEL.get(x, x.title()))
    plan["Exceso (u)"] = plan["Avg_excess"].round(0).astype(int)
    plan["Demanda"]    = plan["Forecast_avg"].round(0).astype(int)

    plan_show = (
        plan[["Subcategory","Origen","Destino","Exceso (u)","Demanda","Unidades","Dist (km)"]]
        .rename(columns={"Subcategory":"Subcategoría"})
        .sort_values("Unidades", ascending=False)
        .reset_index(drop=True)
    )
    # Añadir líneas del plan de transferencias al mapa (una por fila del plan)
    for _, r in plan.iterrows():
        lat_o = REGION_COORDS.get(r["Region_origen"], {}).get("lat")
        lon_o = REGION_COORDS.get(r["Region_origen"], {}).get("lon")
        lat_d = REGION_COORDS.get(r["Region_destino"], {}).get("lat")
        lon_d = REGION_COORDS.get(r["Region_destino"], {}).get("lon")
        if lat_o is None or lat_d is None:
            continue
        fig_map.add_trace(go.Scattergeo(
            lat=[lat_o, lat_d], lon=[lon_o, lon_d],
            mode="lines",
            line=dict(width=2.2, color="rgba(167,139,250,0.45)"),
            hovertemplate=(
                f"<b>{r['Subcategory']}</b><br>Origen: {REG_LABEL.get(r['Region_origen'], r['Region_origen'])}<br>"
                f"Destino: {REG_LABEL.get(r['Region_destino'], r['Region_destino'])}<br>Unidades: {int(r['Unidades']):,}<extra></extra>"
            ),
            showlegend=False,
        ))

    # Finalmente, pintar el mapa una sola vez (con todas las conexiones)
    st.plotly_chart(fig_map, use_container_width=True)

    # ── Leyenda visual (solo una) ──────────────────────────────────
    # Mostrar solo dos leyendas: ORIGEN y DESTINO (el usuario pidió eliminar 'Equilibrio')
    lc1, lc2 = st.columns(2)
    lc1.markdown(
        f"<div style='text-align:center;padding:10px;background:rgba(248,113,113,0.1);border:1px solid {C_ORIGEN};border-radius:8px;color:{C_ORIGEN};font-weight:600'>🔴 ORIGEN — Enviar stock</div>",
        unsafe_allow_html=True,
    )
    lc2.markdown(
        f"<div style='text-align:center;padding:10px;background:rgba(74,222,128,0.1);border:1px solid {C_DESTINO};border-radius:8px;color:{C_DESTINO};font-weight:600'>🟢 DESTINO — Recibir stock</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)

    st.dataframe(
        plan_show.style
            .format({"Exceso (u)": "{:,}", "Demanda": "{:,}", "Unidades": "{:,}", "Dist (km)": "{:,}"})
            .bar(subset=["Unidades"], color="rgba(167,139,250,0.3)")
            .set_table_styles([
                {"selector": "th", "props": [("background-color","#1a1a2e"),("color","#a78bfa"),("font-weight","600"),("font-size","13px")]},
                {"selector": "td", "props": [("background-color","#0f0f1a"),("color","#e2e8f0"),("font-size","13px")]},
            ]),
        use_container_width=True, hide_index=True,
    )