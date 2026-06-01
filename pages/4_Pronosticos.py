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

# CONFIG
st.set_page_config(page_title="Pronósticos — DANUStore", layout="wide")

css_path = Path("styles/main.css")
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# TARJETA DE MÉTRICA
def metric_card(title, value, description, badge, icon, accent, progress):
    title=escape(str(title)); value=escape(str(value)); description=escape(str(description))
    badge=escape(str(badge)); icon=escape(str(icon)); progress=max(0.0,min(float(progress),100.0))
    return f"""<!DOCTYPE html><html><head><style>
    body{{margin:0;font-family:Inter,system-ui,sans-serif;background:transparent;}}
    .card{{background:linear-gradient(135deg,#ffffff 0%,#f8fafc 100%);
        border:1px solid rgba(148,163,184,.22);border-radius:20px;padding:16px 20px;height:140px;
        box-sizing:border-box;box-shadow:0 18px 40px rgba(15,23,42,.10);position:relative;overflow:hidden;}}
    .card::before{{content:"";position:absolute;top:-40px;right:-40px;width:130px;height:130px;
        background:{accent};opacity:.09;border-radius:999px;}}
    .top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;}}
    .ttl{{color:#0f172a;font-size:12px;font-weight:900;margin:0;line-height:1.3;max-width:78%;}}
    .ico{{min-width:34px;height:34px;border-radius:11px;background:{accent};color:white;
        display:flex;align-items:center;justify-content:center;font-size:16px;
        box-shadow:0 8px 18px rgba(15,23,42,.16);font-weight:900;}}
    .val{{color:#0f172a;font-size:18px;font-weight:950;letter-spacing:-.5px;line-height:1;
        margin:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
    .desc{{color:#64748b;font-size:10px;font-weight:600;margin:4px 0 0 0;line-height:1.3;}}
    .foot{{display:flex;align-items:center;gap:6px;margin-top:8px;}}
    .badge{{background:rgba(15,23,42,.06);color:#334155;font-size:10px;font-weight:800;
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

dot = lambda color: (
    f'<span style="display:inline-block;width:11px;height:11px;border-radius:50%;'
    f'background:{color};margin-right:5px;vertical-align:middle;"></span>'
)

def _mini_kpi(label, value):
    return (
        f'<div style="background:#f8fafc;border:1px solid rgba(148,163,184,.22);'
        f'border-radius:12px;padding:10px 14px;">'
        f'<p style="margin:0;font-size:10px;font-weight:700;color:#64748b;">{label}</p>'
        f'<p style="margin:2px 0 0 0;font-size:15px;font-weight:900;color:#0f172a;'
        f'letter-spacing:-0.5px;">{value}</p></div>'
    )

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

# HEADER
st.markdown("""<style>
h4, h3, h2, h1 { color: #0f172a !important; }
</style>""", unsafe_allow_html=True)
ctx_parts = []
if cat_sel     != "Todas": ctx_parts.append(f"Cat: {cat_sel}")
if subcat_sel  != "Todas": ctx_parts.append(f"Sub: {subcat_sel}")
if product_sel != "Todas": ctx_parts.append(f"Prod: {product_sel}")
ctx_parts.append(f"{horizon} meses")
ctx_str = "  ·  ".join(ctx_parts)
st.markdown(
    f"<p style='color:#0f172a;font-size:12px;font-weight:700;margin:0;"
    f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>"
    f"Pronósticos — {region_label}"
    f"<span style='color:#94a3b8;font-weight:400;font-size:11px;margin-left:10px;'>{ctx_str}</span>"
    f"</p>",
    unsafe_allow_html=True,
)

# 4 TABS
tab_resumen, tab_analisis, tab_redist, tab_plan = st.tabs([
    "Resumen",
    "Análisis",
    "Redistribución",
    "Plan de envíos",
])

# TAB 1 — RESUMEN

with tab_resumen:

    st.markdown(
        f"<p style='color:#64748b;font-size:12px;font-weight:600;margin:0 0 12px 0;'>"
        f"Horizonte: {horizon} meses  ·  {region_label}</p>",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        t1_badge, t1_accent = growth_label(kpi_growth_total, horizon)
        sign_t = "+" if kpi_growth_total >= 0 else ""
        components.html(metric_card(
            f"Unidades estimadas · {horizon} meses", f"{kpi_total_units:,.0f} u",
            f"Histórico: {kpi_hist_units:,.0f} u · Variación: {sign_t}{kpi_growth_total:.1f}%",
            t1_badge, "→", t1_accent,
            min(abs(kpi_growth_total/ref25*100) if ref25>0 else 70, 100),
        ), height=150)
    with c2:
        components.html(metric_card(
            f"Mejor subcategoria · {horizon} meses", best_name,
            f"+{best_pct:.1f}% según Prophet · {annualize(best_pct,horizon):+.1f}% anualizado",
            best_badge, "+", best_accent,
            min(abs(best_pct/ref25*100) if ref25>0 else 0, 100),
        ), height=150)
    with c3:
        sign3 = "+" if worst_pct >= 0 else ""
        components.html(metric_card(
            f"Menor alza · {horizon} meses", worst_name,
            f"{sign3}{worst_pct:.1f}% según Prophet · {annualize(worst_pct,horizon):+.1f}% anualizado",
            worst_badge, "!", worst_accent,
            min(abs(worst_pct/ref25*100) if ref25>0 else 0, 100),
        ), height=150)

    st.markdown("<br>", unsafe_allow_html=True)

    col_bar, col_acc = st.columns([3, 1], gap="large")

    with col_bar:
        st.markdown(
            f"<p style='color:#0f172a;font-size:14px;font-weight:800;margin:0 0 4px 0;'>"
            f"Crecimiento por subcategoría</p>"
            f"<p style='color:#64748b;font-size:11px;font-weight:500;margin:0 0 12px 0;'>"
            f"{region_label}  ·  Pronóstico Prophet a {horizon} meses</p>",
            unsafe_allow_html=True,
        )
        fc_bar     = forecast_df.sort_values("Growth_pct", ascending=False)
        colors_bar = [bar_color(v, horizon) for v in fc_bar["Growth_pct"]]
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=fc_bar["Growth_pct"], y=fc_bar["Subcategory"],
            orientation="h",
            text=[f"{v:+.1f}%" for v in fc_bar["Growth_pct"]],
            textposition="outside",
            marker=dict(color=colors_bar, opacity=0.88),
            customdata=np.stack([fc_bar["Forecast_avg"]*horizon,
                                 fc_bar["Hist_avg"]*horizon], axis=-1),
            hovertemplate=(
                "<b>%{y}</b><br>Crecimiento: %{x:+.1f}%<br>"
                "Forecast total: %{customdata[0]:,.0f} u<br>"
                "Histórico total: %{customdata[1]:,.0f} u<extra></extra>"
            ),
        ))
        fig_bar.add_vline(x=ref15, line=dict(color="#f59e0b", width=1.5, dash="dot"),
            annotation_text=f"15% anual ({ref15:.1f}%·{horizon}m)",
            annotation_position="top", annotation_font=dict(color="#b45309", size=10))
        fig_bar.add_vline(x=ref25, line=dict(color="#16a34a", width=1.5, dash="dot"),
            annotation_text=f"25% anual ({ref25:.1f}%·{horizon}m)",
            annotation_position="top", annotation_font=dict(color="#15803d", size=10))
        fig_bar.update_layout(
            height=320, plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            font=dict(color="#0f172a", family="Inter, system-ui, sans-serif"),
            margin=dict(l=10, r=110, t=10, b=30),
            yaxis=dict(autorange="reversed", tickfont=dict(size=12)),
            xaxis=dict(title=f"Crecimiento en {horizon} meses (%)",
                       showgrid=True, gridcolor="rgba(148,163,184,.20)",
                       zeroline=True, zerolinecolor="rgba(148,163,184,.40)", zerolinewidth=1.5),
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        st.caption(
            "🟢 Crecimiento óptimo (≥25% anual)  ·  🔵 Crecimiento saludable (≥15% anual)  ·  🔴 Crecimiento moderado/descenso"
        )

    with col_acc:
        st.markdown(
            "<p style='color:#0f172a;font-size:14px;font-weight:800;margin:0 0 4px 0;'>"
            "Confianza del modelo</p>"
            "<p style='color:#64748b;font-size:11px;font-weight:500;margin:0 0 12px 0;'>"
            "Walk-forward · datos históricos</p>",
            unsafe_allow_html=True,
        )
        acc_color = "#16a34a" if MODEL_ACCURACY>=85 else "#f59e0b" if MODEL_ACCURACY>=75 else "#dc2626"
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=MODEL_ACCURACY,
            number=dict(suffix="%", font=dict(size=34, color="#0f172a",
                        family="Inter, system-ui, sans-serif")),
            gauge=dict(
                axis=dict(range=[0,100], tickwidth=1, tickcolor="#cbd5e1",
                          tickfont=dict(size=10, color="#64748b")),
                bar=dict(color=acc_color, thickness=0.55),
                bgcolor="#f8fafc", borderwidth=0,
                steps=[dict(range=[0,75],  color="#fee2e2"),
                       dict(range=[75,85], color="#fef3c7"),
                       dict(range=[85,100],color="#dcfce7")],
                threshold=dict(line=dict(color="#0f172a", width=2),
                               thickness=0.75, value=MODEL_ACCURACY),
            ),
        ))
        fig_gauge.update_layout(
            height=240, paper_bgcolor="#ffffff",
            margin=dict(l=20,r=20,t=20,b=10),
            font=dict(family="Inter, system-ui, sans-serif"),
        )
        st.plotly_chart(fig_gauge, use_container_width=True)
        acc_label = "Excelente" if MODEL_ACCURACY>=85 else "Aceptable" if MODEL_ACCURACY>=75 else "Bajo"
        st.markdown(
            f"<p style='text-align:center;color:{acc_color};font-size:12px;"
            f"font-weight:800;margin:0;'>{acc_label} — {MODEL_ACCURACY:.1f}%</p>",
            unsafe_allow_html=True,
        )



# TAB 2 — ANÁLISIS

with tab_analisis:

    # ── SECCIÓN: DEMANDA PROYECTADA ───────────────────────────────────────────

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
            m.fit(sub)
            future = m.make_future_dataframe(periods=periods, freq="MS")
            return sub, m.predict(future)

        hist_df, fc_df = fit_prophet_product(product_sel, region_prophet, horizon)
        chart_title    = product_sel
        chart_subtitle = f"Producto  ·  {region_label}  ·  {horizon} meses"

    elif subcat_prophet is not None:
        hist_df, fc_df = fit_prophet("Subcategory", subcat_prophet, region_prophet, horizon)
        chart_title    = subcat_prophet
        chart_subtitle = f"Subcategoría  ·  {region_label}  ·  {horizon} meses"

    else:
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
            m.fit(sub)
            future = m.make_future_dataframe(periods=periods, freq="MS")
            return sub, m.predict(future)

        hist_df, fc_df = fit_prophet_region_total(region_prophet, horizon)
        chart_title    = "Todas las categorías"
        chart_subtitle = f"{region_label}  ·  {horizon} meses"

    # ── Fila superior: título demanda + 3 KPIs inline ────────────────────────
    if hist_df is not None:
        future_fc = fc_df[fc_df["ds"] > hist_df["ds"].max()]
        delta  = future_fc["yhat"].mean() - hist_df["y"].mean()
        sign_d = "+" if delta >= 0 else ""
        kpi_badges = (
            f"<span style='background:#f1f5f9;border:1px solid rgba(148,163,184,.25);"
            f"border-radius:8px;padding:3px 10px;font-size:10px;font-weight:700;"
            f"color:#334155;margin-right:6px;white-space:nowrap;'>"
            f"Último: {int(hist_df['y'].iloc[-1]):,} u</span>"
            f"<span style='background:#f1f5f9;border:1px solid rgba(148,163,184,.25);"
            f"border-radius:8px;padding:3px 10px;font-size:10px;font-weight:700;"
            f"color:#334155;margin-right:6px;white-space:nowrap;'>"
            f"Forecast: {int(future_fc['yhat'].mean()):,} u/mes</span>"
            f"<span style='background:#f1f5f9;border:1px solid rgba(148,163,184,.25);"
            f"border-radius:8px;padding:3px 10px;font-size:10px;font-weight:700;"
            f"color:#334155;white-space:nowrap;'>"
            f"Variación: {sign_d}{delta:,.0f} u/mes</span>"
        )
        st.markdown(
            f"<p style='color:#0f172a;font-size:13px;font-weight:800;margin:0 0 4px 0;'>"
            f"Demanda proyectada"
            f"<span style='color:#94a3b8;font-weight:400;font-size:11px;margin-left:8px;'>"
            f"{chart_title}  ·  {chart_subtitle}</span></p>"
            f"<div style='margin-bottom:6px;'>{kpi_badges}</div>",
            unsafe_allow_html=True,
        )

        fig_dem = go.Figure()
        fig_dem.add_trace(go.Scatter(
            x=pd.concat([future_fc["ds"], future_fc["ds"][::-1]]),
            y=pd.concat([future_fc["yhat_upper"], future_fc["yhat_lower"][::-1]]),
            fill="toself", fillcolor="rgba(37,99,235,.08)",
            line=dict(color="rgba(0,0,0,0)"), hoverinfo="skip",
            name="Intervalo de confianza",
        ))
        fig_dem.add_trace(go.Scatter(
            x=hist_df["ds"], y=hist_df["y"],
            mode="lines+markers", name="Histórico",
            line=dict(color="#2563eb", width=2),
            marker=dict(size=4, color="#2563eb"),
            hovertemplate="<b>%{x|%b %Y}</b><br>Ventas: %{y:,.0f} u<extra></extra>",
        ))
        fig_dem.add_trace(go.Scatter(
            x=future_fc["ds"], y=future_fc["yhat"],
            mode="lines+markers",
            name=f"Forecast ({horizon}m)",
            line=dict(color="#16a34a", width=2, dash="dot"),
            marker=dict(size=7, symbol="diamond", color="#16a34a"),
            hovertemplate="<b>%{x|%b %Y}</b><br>Forecast: %{y:,.0f} u<extra></extra>",
        ))
        fig_dem.update_layout(
            height=210, hovermode="x unified",
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            font=dict(color="#0f172a", family="Inter, system-ui, sans-serif"),
            margin=dict(l=40, r=20, t=5, b=25),
            xaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,.20)",
                       linecolor="rgba(148,163,184,.30)", tickfont=dict(size=10)),
            yaxis=dict(title="u", showgrid=True, gridcolor="rgba(148,163,184,.20)",
                       linecolor="rgba(148,163,184,.30)", tickfont=dict(size=10)),
            legend=dict(orientation="h", y=1.12, x=0, font=dict(size=10)),
        )
        st.plotly_chart(fig_dem, use_container_width=True)
    else:
        nivel = "producto" if product_sel != "Todas" else "subcategoría/región"
        st.info(f"No hay suficientes datos históricos para este {nivel} (mínimo 6 meses).")

    # ── Fila inferior: Estacionalidad (izq) + Comparación de regiones (der) ──

    # Datos de estacionalidad
    df_seas = df_base_kpi.copy()
    df_seas["Month"] = df_seas["Date"].dt.month
    month_names = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",
                   7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}
    seasonality = df_seas.groupby("Month")["Units_sold"].mean().reset_index()
    seasonality["Month_name"] = seasonality["Month"].map(month_names)
    seasonality = seasonality.sort_values("Month")
    global_avg  = seasonality["Units_sold"].mean()
    seas_colors = [
        "#16a34a" if v >= global_avg*1.05
        else "#dc2626" if v <= global_avg*0.95
        else "#2563eb"
        for v in seasonality["Units_sold"]
    ]
    peak_month   = seasonality.loc[seasonality["Units_sold"].idxmax(), "Month_name"]
    variabilidad = (seasonality["Units_sold"].max() - seasonality["Units_sold"].min()) / global_avg * 100

    # Datos de comparación de regiones
    with st.spinner("Calculando..."):
        fc3 = build_region_forecast(3)
        fc6 = build_region_forecast(6)
    fc3 = fc3.rename(columns={"Forecast_total":"fc3","Growth_pct":"gp3"})
    fc6 = fc6.rename(columns={"Forecast_total":"fc6","Growth_pct":"gp6"})
    region_compare = fc3[["Region_label","Hist_avg","fc3","gp3"]].merge(
        fc6[["Region_label","fc6","gp6"]], on="Region_label"
    ).sort_values("fc6", ascending=True)

    col_seas, col_reg = st.columns([1, 1], gap="large")

    with col_seas:
        st.markdown(
            f"<p style='color:#0f172a;font-size:12px;font-weight:800;margin:0 0 1px 0;'>"
            f"Estacionalidad mensual"
            f"<span style='color:#94a3b8;font-weight:400;font-size:10px;margin-left:6px;'>"
            f"Pico: {peak_month}  ·  Variabilidad: {variabilidad:.1f}%</span></p>",
            unsafe_allow_html=True,
        )
        fig_seas = go.Figure()
        fig_seas.add_hline(y=global_avg,
            line=dict(color="#94a3b8", width=1, dash="dot"),
            annotation_text="Prom.", annotation_position="right",
            annotation_font=dict(color="#64748b", size=9))
        fig_seas.add_trace(go.Bar(
            x=seasonality["Month_name"], y=seasonality["Units_sold"],
            marker=dict(color=seas_colors, opacity=0.88),
            hovertemplate="<b>%{x}</b><br>%{y:,.0f} u<extra></extra>",
        ))
        fig_seas.update_layout(
            height=200, plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            font=dict(color="#0f172a", family="Inter, system-ui, sans-serif"),
            margin=dict(l=10, r=30, t=8, b=25),
            xaxis=dict(showgrid=False, tickfont=dict(size=10)),
            yaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,.20)",
                       tickfont=dict(size=9)),
        )
        st.plotly_chart(fig_seas, use_container_width=True)

    with col_reg:
        st.markdown(
            "<p style='color:#0f172a;font-size:12px;font-weight:800;margin:0 0 1px 0;'>"
            "Comparación de regiones"
            "<span style='color:#94a3b8;font-weight:400;font-size:10px;margin-left:6px;'>"
            "Forecast Prophet · dataset completo</span></p>",
            unsafe_allow_html=True,
        )
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Bar(
            name="3 m", y=region_compare["Region_label"], x=region_compare["fc3"],
            orientation="h", marker=dict(color="#2563eb", opacity=0.80),
            hovertemplate="<b>%{y}</b><br>3 meses: %{x:,.0f} u<extra></extra>",
        ))
        fig_comp.add_trace(go.Bar(
            name="6 m", y=region_compare["Region_label"], x=region_compare["fc6"],
            orientation="h", marker=dict(color="#16a34a", opacity=0.80),
            hovertemplate="<b>%{y}</b><br>6 meses: %{x:,.0f} u<extra></extra>",
        ))
        fig_comp.update_layout(
            barmode="group",
            height=200, plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            font=dict(color="#0f172a", family="Inter, system-ui, sans-serif"),
            margin=dict(l=10, r=10, t=8, b=25),
            legend=dict(orientation="h", y=1.12, x=0, font=dict(size=10)),
            yaxis=dict(tickfont=dict(size=10)),
            xaxis=dict(showgrid=True, gridcolor="rgba(148,163,184,.20)",
                       tickfont=dict(size=9)),
        )
        st.plotly_chart(fig_comp, use_container_width=True)


# TAB 4 — REDISTRIBUCIÓN
# Mapa animado + KPIs + leyenda

with tab_redist:

    col_title_r, col_pop1, col_pop2 = st.columns([4, 1, 1])
    with col_title_r:
        st.markdown("### Plan de redistribución de inventario")
    with col_pop1:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.popover("¿Cómo funciona?", use_container_width=False):
            st.markdown(
                f"Detecta el **producto más débil** por subcategoría y región y lo "
                f"redistribuye hacia las regiones con mayor demanda proyectada a "
                f"**{horizon} meses**. Las transferencias se ejecutan en **6 oleadas "
                f"bisemanales** proporcionales a la demanda mensual del destino."
            )
    with col_pop2:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.popover("Ver leyenda", use_container_width=False):
            st.markdown(
                f"{dot('#ef4444')} **Rojo** — Envía stock  \n"
                f"{dot('#22c55e')} **Verde** — Recibe stock  \n"
                f"{dot('#3b82f6')} **Azul** — Sin movimiento  \n"
                "**Grosor de línea** — proporcional a las unidades en tránsito",
                unsafe_allow_html=True,
            )

    with st.spinner("Calculando plan de redistribución..."):
        subcat_region_forecast = build_subcat_region_forecast(df_maestra, horizon)
        fc_monthly             = build_monthly_forecast(horizon)

    df_work = df_maestra.copy()
    if "Excess_stock" not in df_work.columns:
        df_work["Excess_stock"] = (df_work["Stock"] - df_work["Units_sold"]).clip(lower=0)

    redist_base_df    = build_redist_base(df_work, subcat_region_forecast, horizon)
    pares_df, plan_df = build_wave_plan(df_work, redist_base_df, fc_monthly, horizon)

    if plan_df.empty:
        st.info("No se encontraron transferencias con los datos actuales.")
        st.stop()

    frames, slider_steps, init_nodes, init_routes, init_annotation, n_frames = \
        build_animation_frames(plan_df, horizon)

    oleadas       = sorted(plan_df["Oleada"].unique())
    primera_fecha = plan_df["Fecha_envío"].iloc[0]
    ultima_fecha  = plan_df[plan_df["Oleada"]==oleadas[-1]]["Fecha_envío"].iloc[0]

    km1, km2, km3, km4 = st.columns(4)
    with km1:
        st.markdown(_mini_kpi("Productos a redistribuir",
                              str(plan_df["Producto"].nunique())),
                    unsafe_allow_html=True)
    with km2:
        st.markdown(_mini_kpi("Unidades totales",
                              f"{plan_df['Unidades_oleada'].sum():,} u"),
                    unsafe_allow_html=True)
    with km3:
        st.markdown(_mini_kpi("Pares origen → destino",
                              str(len(pares_df))),
                    unsafe_allow_html=True)
    with km4:
        st.markdown(_mini_kpi("Período",
                              f"{primera_fecha} – {ultima_fecha}"),
                    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    fig_map = go.Figure(
        data=[init_nodes] + init_routes,
        frames=frames,
        layout=go.Layout(
            height=460,
            paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
            font=dict(color="#0f172a", family="Inter, system-ui, sans-serif"),
            margin=dict(l=0, r=0, t=65, b=0),
            geo=GEO_LAYOUT,
            annotations=[init_annotation],
            title=dict(
                text=f"Plan de {n_frames} transferencias  ·  Presiona ▶ Play para iniciar",
                font=dict(size=13, color="#0f172a"),
            ),
            updatemenus=[dict(
                type="buttons", showactive=False, direction="left",
                x=0.5, xanchor="center", y=-0.06, yanchor="top",
                bgcolor="#f1f5f9", bordercolor="rgba(148,163,184,.4)",
                font=dict(color="#0f172a", size=13),
                pad=dict(r=10, t=10),
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
                                  font=dict(size=12, color="#64748b")),
                pad=dict(t=50, b=10, l=20, r=20),
                len=0.92, x=0.04,
                bgcolor="#f8fafc", bordercolor="rgba(148,163,184,.3)",
                borderwidth=1, font=dict(color="#334155", size=10),
                steps=slider_steps, tickcolor="rgba(148,163,184,.4)",
            )],
        ),
    )
    st.plotly_chart(fig_map, use_container_width=True)

    dot = lambda color: (
        f'<span style="display:inline-block;width:11px;height:11px;border-radius:50%;'
        f'background:{color};margin-right:5px;vertical-align:middle;"></span>'
    )



# TAB 5 — PLAN DE ENVÍOS
# Tabla de transferencias + resumen ejecutivo + barras de oleadas

with tab_plan:

    st.markdown("**Plan detallado de transferencias**")

    col_ctrl, col_check = st.columns([3, 1])
    with col_ctrl:
        oleada_sel = st.select_slider(
            "Seleccionar oleada",
            options=list(range(1, len(oleadas) + 1)),
            value=1,
            format_func=lambda x: (
                f"Oleada {x}  ·  "
                f"{plan_df[plan_df['Oleada']==x]['Fecha_envío'].iloc[0]}"
            ),
        )
    with col_check:
        mostrar_todo = st.checkbox("Ver plan completo", value=False)

    tabla_filtrada = plan_df if mostrar_todo else plan_df[plan_df["Oleada"] == oleada_sel]

    if not mostrar_todo:
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Transferencias", f"{len(tabla_filtrada)}")
        with m2:
            st.metric("Unidades en tránsito",
                      f"{tabla_filtrada['Unidades_oleada'].sum():,} u")
        with m3:
            st.metric("Rutas activas",
                      str(tabla_filtrada[["Origen","Destino"]].drop_duplicates().__len__()))
        with m4:
            avg_d = tabla_filtrada["Distancia_km"].mean() \
                    if "Distancia_km" in tabla_filtrada else 0
            st.metric("Distancia promedio", f"{avg_d:,.0f} km")

    tabla_show = tabla_filtrada[[
        "Producto","Subcategoría","Categoría",
        "Origen_label","Destino_label",
        "Oleada","Fecha_envío",
        "Unidades_oleada","Total_transferencia",
        "Demanda_destino_mes",
        "Exceso_origen_u","Gap_origen_pct",
        "Sell_through_origen","Distancia_km",
    ]].copy()
    tabla_show.columns = [
        "Producto","Subcategoría","Categoría",
        "Origen","Destino",
        "Oleada","Fecha de envío",
        "Unidades (oleada)","Total transferencia",
        "Demanda destino ese mes (u)",
        "Exceso origen (u)","Gap origen (%)",
        "Sell-through origen (%)","Distancia (km)",
    ]

    st.dataframe(tabla_show, use_container_width=True,
                 hide_index=True, height=160)

    col_res, col_prog = st.columns([3, 2], gap="large")

    with col_res:
        st.markdown("**Resumen ejecutivo**")
        resumen = (
            plan_df
            .groupby(["Producto","Subcategoría","Origen_label","Destino_label"])
            .agg(
                Total_u      = ("Unidades_oleada",  "sum"),
                Oleadas      = ("Oleada",            "count"),
                Primer_envío = ("Fecha_envío",       "first"),
                Último_envío = ("Fecha_envío",       "last"),
                Exceso_u     = ("Exceso_origen_u",   "first"),
                Gap_pct      = ("Gap_origen_pct",    "first"),
                Dist_km      = ("Distancia_km",      "first"),
            )
            .reset_index()
            .sort_values("Total_u", ascending=False)
        )
        resumen.columns = [
            "Producto","Subcategoría","Origen","Destino",
            "Total u","Oleadas","Primer envío","Último envío",
            "Exceso origen (u)","Gap (%)","Dist (km)"
        ]
        st.dataframe(resumen, use_container_width=True,
                     hide_index=True, height=160)

    with col_prog:
        st.markdown("**Unidades por oleada**")
        u_por_oleada = (
            plan_df.groupby(["Oleada","Mes_num","Fecha_envío"])["Unidades_oleada"]
            .sum().reset_index().sort_values("Oleada")
        )
        colores_mes = {1:"#3b82f6", 2:"#22c55e", 3:"#f59e0b"}
        fig_prog = go.Figure()
        fig_prog.add_trace(go.Bar(
            x=[f"Ol.{int(r['Oleada'])}<br>{r['Fecha_envío']}"
               for _, r in u_por_oleada.iterrows()],
            y=u_por_oleada["Unidades_oleada"],
            marker=dict(
                color=[colores_mes.get(int(m), "#94a3b8")
                       for m in u_por_oleada["Mes_num"]],
                opacity=0.88,
            ),
            text=[f"{int(u):,}" for u in u_por_oleada["Unidades_oleada"]],
            textposition="outside",
            textfont=dict(size=10),
            hovertemplate="<b>%{x}</b><br>%{y:,} u<extra></extra>",
        ))
        fig_prog.update_layout(
            height=180,
            plot_bgcolor="#ffffff", paper_bgcolor="#ffffff",
            font=dict(color="#0f172a", family="Inter, system-ui, sans-serif"),
            margin=dict(l=10, r=10, t=20, b=60),
            xaxis=dict(showgrid=False, tickfont=dict(size=9)),
            yaxis=dict(title="Unidades", showgrid=True,
                       gridcolor="rgba(148,163,184,.20)"),
            showlegend=False,
        )
        st.plotly_chart(fig_prog, use_container_width=True)