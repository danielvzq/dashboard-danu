# pages/4_Pronosticos.py
# ══════════════════════════════════════════════════════════════════════
# DANUStore — Pronósticos de Demanda
# ══════════════════════════════════════════════════════════════════════

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
    build_product_region_table,
    build_transfer_df,
    make_node_trace,
    make_route_trace,
    GEO_LAYOUT,
)

# ══════════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Pronósticos — DANUStore", layout="wide")

css_path = Path("styles/main.css")
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# TARJETA DE MÉTRICA
# ══════════════════════════════════════════════════════════════════════
def metric_card(title, value, description, badge, icon, accent, progress):
    title=escape(str(title)); value=escape(str(value)); description=escape(str(description))
    badge=escape(str(badge)); icon=escape(str(icon)); progress=max(0.0,min(float(progress),100.0))
    return f"""<!DOCTYPE html><html><head><style>
    body{{margin:0;font-family:Inter,system-ui,sans-serif;background:transparent;}}
    .card{{background:linear-gradient(135deg,#ffffff 0%,#f8fafc 100%);
        border:1px solid rgba(148,163,184,.22);border-radius:26px;padding:26px;height:200px;
        box-sizing:border-box;box-shadow:0 18px 40px rgba(15,23,42,.10);position:relative;overflow:hidden;}}
    .card::before{{content:"";position:absolute;top:-40px;right:-40px;width:130px;height:130px;
        background:{accent};opacity:.09;border-radius:999px;}}
    .top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;}}
    .ttl{{color:#0f172a;font-size:14px;font-weight:900;margin:0;line-height:1.35;max-width:78%;}}
    .ico{{min-width:34px;height:34px;border-radius:11px;background:{accent};color:white;
        display:flex;align-items:center;justify-content:center;font-size:16px;
        box-shadow:0 8px 18px rgba(15,23,42,.16);font-weight:900;}}
    .val{{color:#0f172a;font-size:22px;font-weight:950;letter-spacing:-.8px;line-height:1;
        margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
    .desc{{color:#64748b;font-size:11.5px;font-weight:600;margin:7px 0 0 0;line-height:1.45;}}
    .foot{{display:flex;align-items:center;gap:9px;margin-top:13px;}}
    .badge{{background:rgba(15,23,42,.06);color:#334155;font-size:11px;font-weight:800;
        padding:4px 9px;border-radius:999px;white-space:nowrap;}}
    .track{{flex:1;height:6px;background:#e5e7eb;border-radius:999px;overflow:hidden;}}
    .fill{{height:100%;width:{progress:.1f}%;background:{accent};border-radius:999px;}}
    </style></head><body>
    <div class="card">
      <div class="top"><p class="ttl">{title}</p><div class="ico">{icon}</div></div>
      <h1 class="val">{value}</h1><p class="desc">{description}</p>
      <div class="foot"><span class="badge">{badge}</span>
        <div class="track"><div class="fill"></div></div>
      </div>
    </div></body></html>"""

def dual_region_card(title, best_name, best_val, worst_name, worst_val, horizon):
    title=escape(str(title)); best_name=escape(str(best_name)); best_val=escape(str(best_val))
    worst_name=escape(str(worst_name)); worst_val=escape(str(worst_val))
    return f"""<!DOCTYPE html><html><head><style>
    body{{margin:0;font-family:Inter,system-ui,sans-serif;background:transparent;}}
    .card{{background:linear-gradient(135deg,#ffffff 0%,#f8fafc 100%);
        border:1px solid rgba(148,163,184,.22);border-radius:26px;padding:22px 26px;
        height:200px;box-sizing:border-box;box-shadow:0 18px 40px rgba(15,23,42,.10);
        position:relative;overflow:hidden;}}
    .card::before{{content:"";position:absolute;top:-40px;right:-40px;width:130px;height:130px;
        background:#7c3aed;opacity:.07;border-radius:999px;}}
    .ttl{{color:#0f172a;font-size:14px;font-weight:900;margin:0 0 14px 0;}}
    .row{{display:flex;align-items:center;gap:10px;margin-bottom:10px;}}
    .dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0;}}
    .lbl{{color:#64748b;font-size:11px;font-weight:700;min-width:44px;}}
    .nm{{color:#0f172a;font-size:13px;font-weight:800;flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
    .val{{color:#0f172a;font-size:13px;font-weight:900;white-space:nowrap;}}
    .note{{color:#94a3b8;font-size:10.5px;margin-top:10px;}}
    </style></head><body>
    <div class="card">
      <p class="ttl">{title}</p>
      <div class="row"><div class="dot" style="background:#16a34a"></div>
        <span class="lbl">Mayor</span><span class="nm">{best_name}</span><span class="val">{best_val}</span></div>
      <div class="row"><div class="dot" style="background:#dc2626"></div>
        <span class="lbl">Menor</span><span class="nm">{worst_name}</span><span class="val">{worst_val}</span></div>
      <p class="note">Sin filtros · Prophet · {horizon} meses · Dataset completo</p>
    </div></body></html>"""

# ══════════════════════════════════════════════════════════════════════
# COLORES Y UMBRALES
# ══════════════════════════════════════════════════════════════════════
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

# ══════════════════════════════════════════════════════════════════════
# LOLLIPOP CHART — mejor para valores similares que barras horizontales
# ══════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════
# ACCURACY DEL MODELO
# ══════════════════════════════════════════════════════════════════════
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

# ══════════════════════════════════════════════════════════════════════
# DATOS
# ══════════════════════════════════════════════════════════════════════
df_maestra     = load_data()
MODEL_ACCURACY = compute_model_accuracy()

# ══════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        '<div class="sidebar-header"><div class="sidebar-icon">📦</div>'
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

# ══════════════════════════════════════════════════════════════════════
# FILTROS
# ══════════════════════════════════════════════════════════════════════
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

df_prod_kpi = apply_date(df_maestra.copy())
if region_sel  != "Todas": df_prod_kpi = df_prod_kpi[df_prod_kpi["Region"]      == region_sel]
if cat_sel     != "Todas": df_prod_kpi = df_prod_kpi[df_prod_kpi["Category"]    == cat_sel]
if subcat_sel  != "Todas": df_prod_kpi = df_prod_kpi[df_prod_kpi["Subcategory"] == subcat_sel]

if df_filtrado.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

# ── region_prophet: la región seleccionada, o la primera si "Todas" ──
region_prophet = region_sel if region_sel != "Todas" else df_maestra["Region"].mode()[0]

# ── subcat_prophet: SOLO se usa cuando hay subcategoría seleccionada.
#    Si subcat_sel == "Todas", la serie temporal muestra todas las subcats
#    agregadas, sin forzar ninguna como default.
subcat_prophet = subcat_sel if subcat_sel != "Todas" else None

region_label = REG_LABEL.get(region_sel, region_sel) if region_sel != "Todas" else "Todas las regiones"
ref15, ref25 = period_thresholds(horizon)

# ══════════════════════════════════════════════════════════════════════
# PROPHET — FUENTE ÚNICA DE VERDAD
# ══════════════════════════════════════════════════════════════════════

with st.spinner("Calculando pronósticos..."):
    forecast_df  = build_forecast_summary(df_base_kpi, region_prophet, horizon)
    region_fc_df = build_region_forecast(horizon)

if forecast_df.empty:
    st.warning("No hay datos suficientes para generar pronósticos con los filtros actuales.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────
kpi_total_units  = (forecast_df["Forecast_avg"] * horizon).sum()
kpi_hist_units   = (forecast_df["Hist_avg"]     * horizon).sum()
kpi_growth_total = ((kpi_total_units-kpi_hist_units)/kpi_hist_units*100) if kpi_hist_units>0 else 0.0

fc_sorted  = forecast_df.sort_values("Growth_pct", ascending=False)
best_row   = fc_sorted.iloc[0];  best_name  = best_row["Subcategory"];  best_pct  = best_row["Growth_pct"]
worst_row  = fc_sorted.iloc[-1]; worst_name = worst_row["Subcategory"]; worst_pct = worst_row["Growth_pct"]
best_badge,  best_accent  = growth_label(best_pct,  horizon)
worst_badge, worst_accent = growth_label(worst_pct, horizon)

best_region  = region_fc_df.iloc[0]
worst_region = region_fc_df.iloc[-1]

# ══════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════
st.title(f"Pronósticos de Demanda — {region_label}")
ctx_parts = []
if cat_sel     != "Todas": ctx_parts.append(f"Categoría: **{cat_sel}**")
if subcat_sel  != "Todas": ctx_parts.append(f"Subcategoría: **{subcat_sel}**")
if product_sel != "Todas": ctx_parts.append(f"Producto: **{product_sel}**")
ctx_parts.append(f"Horizonte: **{horizon} meses**")
st.markdown(" · ".join(ctx_parts))
st.divider()

# ══════════════════════════════════════════════════════════════════════
# KPIs
# ══════════════════════════════════════════════════════════════════════
c1, c2, c3, c4 = st.columns(4)

with c1:
    t1_badge, t1_accent = growth_label(kpi_growth_total, horizon)
    sign_t = "+" if kpi_growth_total >= 0 else ""
    components.html(metric_card(
        f"Unidades estimadas · {horizon} meses", f"{kpi_total_units:,.0f} u",
        f"Histórico periodo: {kpi_hist_units:,.0f} u · Variación: {sign_t}{kpi_growth_total:.1f}%",
        t1_badge, "→", t1_accent,
        min(abs(kpi_growth_total/ref25*100) if ref25>0 else 70, 100),
    ), height=220)

with c2:
    components.html(metric_card(
        f"Mejor subcategoria · {horizon} meses", best_name,
        f"+{best_pct:.1f}% según Prophet · {annualize(best_pct,horizon):+.1f}% anualizado",
        best_badge, "+", best_accent,
        min(abs(best_pct/ref25*100) if ref25>0 else 0, 100),
    ), height=220)

with c3:
    sign3 = "+" if worst_pct >= 0 else ""
    components.html(metric_card(
        f"Menor alza · {horizon} meses", worst_name,
        f"{sign3}{worst_pct:.1f}% según Prophet · {annualize(worst_pct,horizon):+.1f}% anualizado",
        worst_badge, "!", worst_accent,
        min(abs(worst_pct/ref25*100) if ref25>0 else 0, 100),
    ), height=220)

with c4:
    components.html(dual_region_card(
        f"Regiones · {horizon} meses (sin filtros)",
        best_region["Region_label"],  f"{best_region['Forecast_total']:,.0f} u",
        worst_region["Region_label"], f"{worst_region['Forecast_total']:,.0f} u",
        horizon,
    ), height=220)

st.divider()

# ══════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════
tab_pred, tab_redist = st.tabs(["Predicción de demanda", "Redistribución de inventario"])

# ══════════════════════════════════════════════════════════════════════
# TAB 1 — PREDICCIÓN DE DEMANDA
# ══════════════════════════════════════════════════════════════════════
with tab_pred:

    # ── Serie temporal ────────────────────────────────────────────────
    # Si hay subcategoría o producto seleccionado → Prophet específico
    # Si no hay filtro → Prophet sobre el total de la región (todas las subcats)
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
        chart_title    = f"Demanda proyectada — {product_sel}"

    elif subcat_prophet is not None:
        # Subcategoría seleccionada explícitamente
        hist_df, fc_df = fit_prophet("Subcategory", subcat_prophet, region_prophet, horizon)
        chart_title    = f"Demanda proyectada — {subcat_prophet}"

    else:
        # Sin filtro: Prophet sobre el TOTAL de la región (todas las subcats agregadas)
        @st.cache_data(show_spinner=False)
        def fit_prophet_region_total(region, periods):
            df  = load_data()
            sub = (df[df["Region"]==region]
                   .groupby("YearMonth").agg(y=("Units_sold","sum")).reset_index())
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

        hist_df, fc_df = fit_prophet_region_total(region_prophet, horizon)
        chart_title    = f"Demanda proyectada — {region_label} (todas las categorías)"

    if hist_df is not None:
        future_fc = fc_df[fc_df["ds"] > hist_df["ds"].max()]
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=pd.concat([future_fc["ds"], future_fc["ds"][::-1]]),
            y=pd.concat([future_fc["yhat_upper"], future_fc["yhat_lower"][::-1]]),
            fill="toself", fillcolor="rgba(37,99,235,.08)",
            line=dict(color="rgba(0,0,0,0)"), hoverinfo="skip", name="Intervalo de confianza",
        ))
        fig.add_trace(go.Scatter(
            x=hist_df["ds"], y=hist_df["y"], mode="lines+markers", name="Histórico",
            line=dict(color="#2563eb", width=3), marker=dict(size=6, color="#2563eb"),
            hovertemplate="<b>%{x|%b %Y}</b><br>Ventas: %{y:,.0f} u<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=future_fc["ds"], y=future_fc["yhat"],
            mode="lines+markers", name=f"Forecast Prophet ({horizon} meses)",
            line=dict(color="#16a34a", width=3, dash="dot"),
            marker=dict(size=9, symbol="diamond", color="#16a34a"),
            hovertemplate="<b>%{x|%b %Y}</b><br>Forecast: %{y:,.0f} u<extra></extra>",
        ))
        fig.update_layout(
            title=dict(text=chart_title, font=dict(size=18, color="#0f172a")),
            height=460, hovermode="x unified",
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            font=dict(color="#0f172a", family="Inter, system-ui, sans-serif"),
            margin=dict(l=40, r=40, t=70, b=40),
            xaxis=dict(title="Período", showgrid=True,
                       gridcolor="rgba(148,163,184,.20)", linecolor="rgba(148,163,184,.30)"),
            yaxis=dict(title="Unidades", showgrid=True,
                       gridcolor="rgba(148,163,184,.20)", linecolor="rgba(148,163,184,.30)"),
            legend=dict(orientation="h", y=1.08, x=0),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("La banda azul muestra el intervalo de confianza. La línea punteada verde es la demanda proyectada por Prophet.")
    else:
        nivel = "producto" if product_sel != "Todas" else "subcategoría/región"
        st.info(f"No hay suficientes datos históricos para este {nivel} (mínimo 6 meses).")

    st.divider()

    # ── Gráfica barras Prophet + Accuracy ─────────────────────────────
    col_bar, col_acc = st.columns([3, 1], gap="large")

    with col_bar:
        st.markdown(f"### Crecimiento por subcategoria · {region_label}")
        st.caption("Crecimiento calculado por Prophet: demanda proyectada vs promedio histórico.")
        fc_bar = forecast_df.sort_values("Growth_pct", ascending=False)
        colors_bar = [bar_color(v, horizon) for v in fc_bar["Growth_pct"]]
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=fc_bar["Growth_pct"], y=fc_bar["Subcategory"],
            orientation="h",
            text=[f"{v:+.1f}%" for v in fc_bar["Growth_pct"]],
            textposition="outside",
            marker=dict(color=colors_bar, opacity=0.88),
            customdata=np.stack([fc_bar["Forecast_avg"]*horizon, fc_bar["Hist_avg"]*horizon], axis=-1),
            hovertemplate=(
                "<b>%{y}</b><br>Crecimiento Prophet: %{x:+.1f}%<br>"
                "Forecast total: %{customdata[0]:,.0f} u<br>"
                "Histórico total: %{customdata[1]:,.0f} u<extra></extra>"
            ),
        ))
        fig_bar.add_vline(x=ref15, line=dict(color="#f59e0b", width=1.5, dash="dot"),
            annotation_text=f"15% anual ({ref15:.1f}% en {horizon}m)",
            annotation_position="top", annotation_font=dict(color="#b45309", size=10))
        fig_bar.add_vline(x=ref25, line=dict(color="#16a34a", width=1.5, dash="dot"),
            annotation_text=f"25% anual ({ref25:.1f}% en {horizon}m)",
            annotation_position="top", annotation_font=dict(color="#15803d", size=10))
        fig_bar.update_layout(
            height=440, plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            font=dict(color="#0f172a", family="Inter, system-ui, sans-serif"),
            margin=dict(l=10, r=100, t=20, b=40),
            yaxis=dict(autorange="reversed", tickfont=dict(size=13)),
            xaxis=dict(title=f"Crecimiento Prophet en {horizon} meses (%)",
                       showgrid=True, gridcolor="rgba(148,163,184,.20)",
                       zeroline=True, zerolinecolor="rgba(148,163,184,.40)", zerolinewidth=1.5),
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        st.caption(
            f"Verde: >= {ref25:.1f}% en {horizon}m (óptimo >25% anual)  ·  "
            f"Azul: >= {ref15:.1f}% (saludable 15-25% anual)  ·  "
            f"Rojo: < {ref15:.1f}% (por debajo del 15% anual)"
        )

    with col_acc:
        st.markdown("### Confianza del modelo")
        st.markdown("<br>", unsafe_allow_html=True)
        acc_color = "#16a34a" if MODEL_ACCURACY>=85 else "#f59e0b" if MODEL_ACCURACY>=75 else "#dc2626"
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=MODEL_ACCURACY,
            number=dict(suffix="%", font=dict(size=34, color="#0f172a", family="Inter, system-ui, sans-serif")),
            gauge=dict(
                axis=dict(range=[0,100], tickwidth=1, tickcolor="#cbd5e1",
                          tickfont=dict(size=10, color="#64748b")),
                bar=dict(color=acc_color, thickness=0.55),
                bgcolor="#f8fafc", borderwidth=0,
                steps=[dict(range=[0,75],color="#fee2e2"),
                       dict(range=[75,85],color="#fef3c7"),
                       dict(range=[85,100],color="#dcfce7")],
                threshold=dict(line=dict(color="#0f172a",width=2), thickness=0.75, value=MODEL_ACCURACY),
            ),
            title=dict(
                text=("Accuracy general<br>"
                      "<span style='font-size:11px;color:#64748b'>Walk-forward · datos históricos</span>"),
                font=dict(size=13, color="#0f172a", family="Inter, system-ui, sans-serif"),
            ),
        ))
        fig_gauge.update_layout(height=300, paper_bgcolor="#ffffff",
            margin=dict(l=20,r=20,t=60,b=10), font=dict(family="Inter, system-ui, sans-serif"))
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.markdown(
            f"""<div style="background:#f8fafc;border:1px solid rgba(148,163,184,.22);
                border-radius:16px;padding:14px;margin-top:4px;">
                <p style="margin:0;font-size:12px;font-weight:700;color:#0f172a;">Metodología</p>
                <p style="margin:6px 0 0 0;font-size:11px;color:#64748b;line-height:1.55;">
                Walk-forward mensual. Predice cada mes usando solo datos anteriores.
                MAPE: <b>{100-MODEL_ACCURACY:.1f}%</b><br><br>
                Valor fijo para todo el modelo.
                </p></div>""",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Estacionalidad / Comparación por región — con toggle ──────────
    st.markdown("### Análisis estacional")

    # Toggle para cambiar entre estacionalidad mensual y comparación de regiones
    vista_opcion = st.radio(
        "",
        ["Estacionalidad mensual de ventas", "Comparación de regiones por forecast"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if vista_opcion == "Estacionalidad mensual de ventas":
        st.caption("Promedio histórico de ventas por mes del año. Útil para anticipar picos y planear reabastecimiento.")

        df_seas = df_base_kpi.copy()
        df_seas["Month"] = df_seas["Date"].dt.month
        month_names = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                       7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}
        seasonality = df_seas.groupby("Month")["Units_sold"].mean().reset_index()
        seasonality["Month_name"] = seasonality["Month"].map(month_names)
        seasonality = seasonality.sort_values("Month")
        global_avg  = seasonality["Units_sold"].mean()
        seas_colors = ["#16a34a" if v>=global_avg*1.05 else "#dc2626" if v<=global_avg*0.95 else "#2563eb"
                       for v in seasonality["Units_sold"]]

        fig_seas = go.Figure()
        fig_seas.add_hline(y=global_avg, line=dict(color="#94a3b8", width=1.5, dash="dot"),
            annotation_text="Promedio", annotation_position="right",
            annotation_font=dict(color="#64748b", size=11))
        fig_seas.add_trace(go.Bar(
            x=seasonality["Month_name"], y=seasonality["Units_sold"],
            marker=dict(color=seas_colors, opacity=0.88),
            text=[f"{v:,.0f}" for v in seasonality["Units_sold"]],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Promedio histórico: %{y:,.0f} u<extra></extra>",
        ))
        fig_seas.update_layout(
            height=380, plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            font=dict(color="#0f172a", family="Inter, system-ui, sans-serif"),
            margin=dict(l=10, r=40, t=20, b=40),
            xaxis=dict(title="Mes", showgrid=False),
            yaxis=dict(title="Ventas promedio (u)", showgrid=True, gridcolor="rgba(148,163,184,.20)"),
        )
        st.plotly_chart(fig_seas, use_container_width=True)
        st.caption(
            "Verde: >5% sobre el promedio  ·  Rojo: >5% bajo el promedio  ·  "
            "Azul: dentro del rango  ·  Datos históricos reales, no Prophet."
        )

    else:
        # Comparación de regiones: forecast total por región para 3 y 6 meses
        st.caption(f"Demanda total proyectada por Prophet para cada región. Sin filtros, dataset completo.")

        with st.spinner("Cargando comparación de regiones..."):
            fc3 = build_region_forecast(3)
            fc6 = build_region_forecast(6)

        fc3 = fc3.rename(columns={"Forecast_total":"fc3", "Growth_pct":"gp3"})
        fc6 = fc6.rename(columns={"Forecast_total":"fc6", "Growth_pct":"gp6"})
        region_compare = fc3[["Region_label","Hist_avg","fc3","gp3"]].merge(
            fc6[["Region_label","fc6","gp6"]], on="Region_label"
        ).sort_values("fc6", ascending=True)

        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            name="Forecast 3 meses",
            y=region_compare["Region_label"],
            x=region_compare["fc3"],
            orientation="h",
            marker=dict(color="#2563eb", opacity=0.80),
            hovertemplate="<b>%{y}</b><br>3 meses: %{x:,.0f} u<extra></extra>",
        ))
        fig_comp.add_trace(go.Bar(
            name="Forecast 6 meses",
            y=region_compare["Region_label"],
            x=region_compare["fc6"],
            orientation="h",
            marker=dict(color="#16a34a", opacity=0.80),
            hovertemplate="<b>%{y}</b><br>6 meses: %{x:,.0f} u<extra></extra>",
        ))
        fig_comp.update_layout(
            barmode="group",
            height=420, plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            font=dict(color="#0f172a", family="Inter, system-ui, sans-serif"),
            margin=dict(l=10, r=40, t=20, b=40),
            legend=dict(orientation="h", y=1.06, x=0),
            yaxis=dict(tickfont=dict(size=12)),
            xaxis=dict(title="Unidades proyectadas", showgrid=True,
                       gridcolor="rgba(148,163,184,.20)"),
        )
        st.plotly_chart(fig_comp, use_container_width=True)

        # Tabla resumen
        tabla = region_compare.copy()
        tabla.columns = ["Región","Promedio hist. mensual","Forecast 3m","Crec. 3m (%)","Forecast 6m","Crec. 6m (%)"]
        tabla["Promedio hist. mensual"] = tabla["Promedio hist. mensual"].map("{:,.0f}".format)
        tabla["Forecast 3m"]            = tabla["Forecast 3m"].map("{:,.0f}".format)
        tabla["Forecast 6m"]            = tabla["Forecast 6m"].map("{:,.0f}".format)
        tabla["Crec. 3m (%)"]           = tabla["Crec. 3m (%)"].map("{:+.1f}%".format)
        tabla["Crec. 6m (%)"]           = tabla["Crec. 6m (%)"].map("{:+.1f}%".format)
        st.dataframe(tabla.sort_values("Forecast 6m", ascending=False), use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════
# TAB 2 — REDISTRIBUCIÓN DE INVENTARIO
# ══════════════════════════════════════════════════════════════════════
with tab_redist:

    st.markdown("### Plan de redistribución de inventario")
    st.markdown(
        "El sistema detecta regiones con exceso de stock respecto a la demanda "
        f"proyectada a {horizon} meses (Prophet) y sugiere transferencias hacia "
        "las regiones con mayor demanda esperada."
    )

    with st.spinner("Calculando pronósticos por región..."):
        subcat_region_forecast = build_subcat_region_forecast(df_maestra, horizon)

    prod_region = build_product_region_table(df_maestra, subcat_region_forecast)
    transfer_df = build_transfer_df(prod_region, horizon)

    frames, slider_steps = [], []
    for i, row in transfer_df.iterrows():
        frames.append(go.Frame(
            data=[make_route_trace(row, horizon),
                  make_node_trace(highlight_origen=row["Origen"], highlight_destino=row["Destino"])],
            name=str(i),
        ))
        slider_steps.append(dict(
            args=[[str(i)], dict(frame=dict(duration=700, redraw=True), mode="immediate")],
            label=f"{REG_LABEL.get(row['Origen'],'?')} → {REG_LABEL.get(row['Destino'],'?')}",
            method="animate",
        ))

    first_row = transfer_df.iloc[0]
    fig_map   = go.Figure(
        data=[make_route_trace(first_row, horizon),
              make_node_trace(highlight_origen=first_row["Origen"], highlight_destino=first_row["Destino"])],
        frames=frames,
        layout=go.Layout(
            height=640,
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color="#0f172a", family="Inter, system-ui, sans-serif"),
            margin=dict(l=0, r=0, t=60, b=0), geo=GEO_LAYOUT,
            title=dict(
                text=(f"Flujo de redistribución — Prophet {horizon} meses   "
                      "Rojo: envía  ·  Verde: recibe  ·  Azul: sin movimiento"),
                font=dict(size=14, color="#0f172a"),
            ),
            updatemenus=[dict(
                type="buttons", showactive=False,
                x=0.5, xanchor="center", y=-0.04, yanchor="top",
                bgcolor="#f1f5f9", bordercolor="rgba(148,163,184,.4)",
                font=dict(color="#0f172a"),
                buttons=[
                    dict(label="Play", method="animate",
                         args=[None, dict(frame=dict(duration=1400, redraw=True),
                                          fromcurrent=True, transition=dict(duration=200))]),
                    dict(label="Pausa", method="animate",
                         args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")]),
                ],
            )],
            sliders=[dict(
                active=0,
                currentvalue=dict(prefix="Transferencia: ", font=dict(color="#64748b", size=13)),
                pad=dict(t=50, b=10),
                bgcolor="#f8fafc", bordercolor="rgba(148,163,184,.3)",
                font=dict(color="#334155", size=11),
                steps=slider_steps,
            )],
        ),
    )
    st.plotly_chart(fig_map, use_container_width=True)
    st.caption(
        f"Presiona Play para recorrer las transferencias sugeridas (Prophet {horizon} meses). "
        "Pasa el cursor sobre cada ruta para ver el detalle del producto."
    )

    st.markdown("### Plan detallado de transferencias")
    transfer_show = transfer_df[[
        "Producto","Categoría","Subcategoría","Origen","Destino",
        "Unidades_sugeridas","Exceso_origen","Forecast_destino",
        "Sell_through_origen","Sell_through_destino","Distancia_km",
    ]].copy()
    transfer_show["Origen"]  = transfer_show["Origen"].map(REG_LABEL)
    transfer_show["Destino"] = transfer_show["Destino"].map(REG_LABEL)
    transfer_show.columns = [
        "Producto","Categoría","Subcategoría","Origen","Destino",
        "Unidades sugeridas","Exceso origen (u)",
        f"Forecast destino ({horizon} meses)",
        "Sell-through origen (%)","Sell-through destino (%)","Distancia (km)",
    ]
    st.dataframe(transfer_show, use_container_width=True, hide_index=True)