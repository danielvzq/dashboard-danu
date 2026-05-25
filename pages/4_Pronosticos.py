# pages/4_Pronosticos.py
# ══════════════════════════════════════════════════════════════════
# Vista de Pronósticos — DANUStore
# Mismo sidebar y estilo visual que Inicio.py
# ══════════════════════════════════════════════════════════════════

import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from prophet import Prophet
from pathlib import Path
from html import escape

# ── Configuración ──────────────────────────────────────────────────
st.set_page_config(
    page_title="Pronósticos — DANUStore",
    page_icon="📈",
    layout="wide",
)

css_path = Path("styles/main.css")
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# HELPERS — mismos estilos de card que Inicio.py
# ══════════════════════════════════════════════════════════════════
def modern_metric_card(title, value, description, badge, icon, accent_color, progress):
    title       = escape(str(title))
    value       = escape(str(value))
    description = escape(str(description))
    badge       = escape(str(badge))
    icon        = escape(str(icon))
    progress    = max(0, min(progress, 100))
    return f"""<!DOCTYPE html><html><head><style>
    body{{margin:0;font-family:Inter,system-ui,sans-serif;background:transparent}}
    .metric-card{{background:linear-gradient(135deg,#ffffff 0%,#f8fafc 100%);
        border:1px solid rgba(148,163,184,.22);border-radius:26px;padding:28px;
        height:190px;box-sizing:border-box;
        box-shadow:0 18px 40px rgba(15,23,42,.10);position:relative;overflow:hidden}}
    .metric-card::before{{content:"";position:absolute;top:-40px;right:-40px;
        width:120px;height:120px;background:{accent_color};opacity:.10;border-radius:999px}}
    .metric-top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}}
    .metric-title{{color:#0f172a;font-size:17px;font-weight:900;margin:0}}
    .metric-icon{{width:38px;height:38px;border-radius:14px;background:{accent_color};color:white;
        display:flex;align-items:center;justify-content:center;font-size:19px;
        box-shadow:0 10px 22px rgba(15,23,42,.18)}}
    .metric-value{{color:#0f172a;font-size:28px;font-weight:950;letter-spacing:-1.6px;line-height:1;margin:0}}
    .metric-description{{color:#64748b;font-size:14px;font-weight:650;margin:10px 0 0 0}}
    .metric-footer{{display:flex;align-items:center;gap:10px;margin-top:18px}}
    .metric-badge{{background:rgba(15,23,42,.06);color:#334155;font-size:12px;font-weight:800;
        padding:6px 10px;border-radius:999px;white-space:nowrap}}
    .metric-track{{flex:1;height:8px;background:#e5e7eb;border-radius:999px;overflow:hidden}}
    .metric-fill{{height:100%;width:{progress:.1f}%;background:{accent_color};border-radius:999px}}
    </style></head><body>
    <div class="metric-card">
        <div class="metric-top">
            <p class="metric-title">{title}</p>
            <div class="metric-icon">{icon}</div>
        </div>
        <h1 class="metric-value">{value}</h1>
        <p class="metric-description">{description}</p>
        <div class="metric-footer">
            <span class="metric-badge">{badge}</span>
            <div class="metric-track"><div class="metric-fill"></div></div>
        </div>
    </div></body></html>"""


def top5_card_html(rows_html):
    return f"""<!DOCTYPE html><html><head><style>
    body{{margin:0;font-family:Inter,system-ui,sans-serif;background:transparent}}
    .card{{background:linear-gradient(135deg,#ffffff 0%,#f8fafc 100%);
        border:1px solid rgba(148,163,184,.22);border-radius:28px;padding:28px;
        box-sizing:border-box;box-shadow:0 18px 40px rgba(15,23,42,.10);overflow:hidden}}
    .title{{color:#0f172a;font-size:18px;font-weight:900;margin:0 0 20px 0}}
    .item{{margin-bottom:14px}}
    .item-top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}}
    .item-name{{color:#111827;font-size:14px;font-weight:800}}
    .item-sub{{color:#6366f1;font-size:12px;font-weight:700}}
    .item-val{{color:#dc2626;font-size:14px;font-weight:900}}
    .bar-track{{width:100%;height:7px;background:#fee2e2;border-radius:999px;overflow:hidden}}
    .bar-fill{{height:100%;background:linear-gradient(90deg,#ef4444,#991b1b);border-radius:999px}}
    .footer{{color:#94a3b8;font-size:12px;font-weight:600;margin-top:16px}}
    </style></head><body>
    <div class="card">
        <p class="title">Top 5 — Mayor sobrestock</p>
        {rows_html}
        <p class="footer">Medido por exceso promedio mensual de unidades.</p>
    </div></body></html>"""


# ══════════════════════════════════════════════════════════════════
# DATOS Y MODELOS
# ══════════════════════════════════════════════════════════════════
@st.cache_data
def load_data():
    df = pd.read_csv("data/df_Maestra.csv", parse_dates=["Date"])
    df.columns = df.columns.str.strip()
    df["YearMonth"]    = df["Date"].dt.to_period("M")
    df["Excess_stock"] = (df["Stock"] - df["Units_sold"]).clip(lower=0)
    df["Gap_units"]    = df["Stock"] - df["Units_sold"]
    df["Gap_pct"]      = df["Gap_units"] / df["Stock"].replace(0, np.nan) * 100
    df["Overstock_critico"] = (
        df["Overstock_critico"].astype(str).str.lower()
        .map({"true": True, "false": False, "1": True, "0": False})
        .fillna(False)
    )
    return df


@st.cache_data
def fit_prophet(group_col, group_val, region, periods):
    df = load_data()
    mask = (df["Region"] == region) & (df[group_col] == group_val)
    sub  = (
        df[mask].groupby("YearMonth")
        .agg(y=("Units_sold","sum")).reset_index()
    )
    sub["ds"] = sub["YearMonth"].dt.to_timestamp()
    sub = sub[["ds","y"]]
    m = Prophet(
        changepoint_prior_scale=0.05, seasonality_mode="additive",
        uncertainty_samples=300, yearly_seasonality=False,
        weekly_seasonality=False, daily_seasonality=False,
    )
    m.add_seasonality(name="semestral", period=182.5, fourier_order=3)
    m.fit(sub)
    future = m.make_future_dataframe(periods=periods, freq="MS")
    return sub, m.predict(future)


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
    "bajío": "Bajío", "ciudad de méxico": "CDMX",
    "zona metropolitana de monterrey": "ZM Monterrey",
    "zona metropolitana de guadalajara": "ZM Guadalajara",
    "noroeste": "Noroeste", "sureste": "Sureste", "sur": "Sur",
}

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2-lat1)/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin((lon2-lon1)/2)**2
    return int(2 * R * np.arcsin(np.sqrt(a)))


df_maestra = load_data()


# ══════════════════════════════════════════════════════════════════
# SIDEBAR — idéntico a Inicio.py
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    # Header igual que Inicio.py
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
        unsafe_allow_html=True,
    )

    st.page_link("Inicio.py",               label="Inicio")
    st.page_link("pages/1_Inventario.py",   label="Inventario")
    st.page_link("pages/2_Ventas.py",       label="Ventas")
    st.page_link("pages/3_Alertas.py",      label="Alertas")
    st.page_link("pages/4_Pronosticos.py",  label="Pronósticos")

    st.divider()
    st.markdown("### Filtros")

    fecha_min = df_maestra["Date"].min().date()
    fecha_max = df_maestra["Date"].max().date()
    rango_fechas = st.date_input(
        "Rango de fechas",
        value=(fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max,
    )

    regiones = sorted(df_maestra["Region"].dropna().unique().tolist())
    region_sel = st.selectbox("Región", ["Todas"] + regiones)

    categorias = sorted(df_maestra["Category"].dropna().unique().tolist())
    cat_sel = st.selectbox("Categoría", ["Todas"] + categorias)

    subcategorias = sorted(df_maestra["Subcategory"].dropna().unique().tolist())
    subcat_sel = st.selectbox("Subcategoría", ["Todas"] + subcategorias)

    acciones = sorted(df_maestra["Priority_action"].dropna().unique().tolist())
    acciones_sel = st.multiselect("Acción prioritaria", acciones, default=acciones)

    st.divider()
    st.markdown("### Pronóstico")

    product_sel = st.selectbox(
        "Producto",
        options=(
            ["Toda la subcategoría"] + sorted(
                df_maestra[
                    (df_maestra["Region"] == region_sel) &
                    (df_maestra["Subcategory"] == subcat_sel)
                ]["Product_name"].unique()
            )
            if (region_sel != "Todas" and subcat_sel != "Todas")
            else ["Toda la subcategoría"]
        ),
    )
    horizon = st.radio(
        "Horizonte de predicción",
        options=[3, 6],
        format_func=lambda x: f"{x} meses",
        horizontal=True,
    )


# ── Aplicar filtros ────────────────────────────────────────────────
df_filtrado = df_maestra.copy()

if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
    fi, ff = rango_fechas
    df_filtrado = df_filtrado[
        (df_filtrado["Date"].dt.date >= fi) &
        (df_filtrado["Date"].dt.date <= ff)
    ]
if region_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Region"] == region_sel]
if cat_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Category"] == cat_sel]
if subcat_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["Subcategory"] == subcat_sel]
if acciones_sel:
    df_filtrado = df_filtrado[df_filtrado["Priority_action"].isin(acciones_sel)]

region_prophet = region_sel if region_sel != "Todas" else df_maestra["Region"].mode()[0]
subcat_prophet = subcat_sel if subcat_sel != "Todas" else df_maestra["Subcategory"].mode()[0]


# ══════════════════════════════════════════════════════════════════
# ENCABEZADO
# ══════════════════════════════════════════════════════════════════
st.title("📈 Pronósticos de Inventario")
reg_label_activo = REG_LABEL.get(region_sel, region_sel.title()) if region_sel != "Todas" else "Todas las regiones"
st.markdown(
    f"Región: **{reg_label_activo}** &nbsp;·&nbsp; "
    f"Subcategoría: **{subcat_sel}** &nbsp;·&nbsp; "
    f"Horizonte: **{horizon} meses**"
)


# ══════════════════════════════════════════════════════════════════
# KPI CARDS — mismo estilo HTML que Inicio.py
# ══════════════════════════════════════════════════════════════════
stock_total      = df_filtrado["Stock"].sum()
df_critico       = df_filtrado[df_filtrado["Overstock_critico"] == True].copy()
productos_crit   = df_critico["Product_id"].nunique() if not df_critico.empty else 0
unidades_exc     = df_critico["Excess_stock"].sum()   if not df_critico.empty else 0
pct_critico      = (df_critico["Stock"].sum() / stock_total * 100) if stock_total > 0 else 0
dias_prom        = df_filtrado["Days_inventory"].replace([np.inf,-np.inf], np.nan).dropna().mean()
dias_prom        = dias_prom if not np.isnan(dias_prom) else 0
rotacion         = df_filtrado["Stock_turnover"].replace([np.inf,-np.inf], np.nan).dropna().mean()
rotacion         = rotacion if not np.isnan(rotacion) else 0

c1, c2, c3 = st.columns(3)
with c1:
    components.html(modern_metric_card(
        "Overstock Crítico", f"{productos_crit:,} productos",
        f"{unidades_exc:,.0f} unidades excedentes",
        "Riesgo alto", "🚨", "#dc2626", pct_critico,
    ), height=210, scrolling=False)
with c2:
    components.html(modern_metric_card(
        "Días Prom. Inventario", f"{dias_prom:.0f} días",
        "Promedio de rotación del inventario filtrado",
        "Inventario lento", "⏳", "#f59e0b",
        min((dias_prom / 365) * 100, 100),
    ), height=210, scrolling=False)
with c3:
    components.html(modern_metric_card(
        "Rotación Inventario", f"{rotacion:.2f}x",
        "Stock turnover promedio del período filtrado",
        "Baja rotación", "🔄", "#2563eb",
        min(rotacion * 100, 100),
    ), height=210, scrolling=False)


# ══════════════════════════════════════════════════════════════════
# PESTAÑAS
# ══════════════════════════════════════════════════════════════════
st.markdown("### Análisis Predictivo")
tab_pred, tab_stock, tab_redist = st.tabs([
    "📊 Predicción de demanda",
    "🚨 Sobrestock crítico",
    "🗺️ Redistribución",
])


# ──────────────────────────────────────────────────────────────────
# PESTAÑA 1 — Predicción de demanda
# ──────────────────────────────────────────────────────────────────
with tab_pred:
    use_product = product_sel != "Toda la subcategoría"
    group_col   = "Product_name" if use_product else "Subcategory"
    group_val   = product_sel   if use_product else subcat_prophet
    label_pred  = f"{group_val}  ·  {REG_LABEL.get(region_prophet, region_prophet.title())}"

    with st.spinner("Entrenando modelo Prophet…"):
        hist_df, fc_df = fit_prophet(group_col, group_val, region_prophet, horizon)

    fut_mask = fc_df["ds"] > hist_df["ds"].max()
    hist_fc  = fc_df[~fut_mask]
    fut_fc   = fc_df[fut_mask]
    corte    = hist_df["ds"].max().strftime("%Y-%m-%d")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pd.concat([fut_fc["ds"], fut_fc["ds"][::-1]]),
        y=pd.concat([fut_fc["yhat_upper"], fut_fc["yhat_lower"][::-1]]),
        fill="toself", fillcolor="rgba(99,102,241,0.10)",
        line=dict(color="rgba(0,0,0,0)"), name="IC 95%", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=hist_df["ds"], y=hist_df["y"], mode="lines+markers",
        name="Histórico", line=dict(color="#2563eb", width=2.5),
        marker=dict(size=6, color="#2563eb"),
        hovertemplate="<b>%{x|%b %Y}</b><br>Ventas: <b>%{y:,.0f} u</b><extra>Histórico</extra>",
    ))
    fig.add_trace(go.Scatter(
        x=hist_fc["ds"], y=hist_fc["yhat"], mode="lines",
        line=dict(color="#2563eb", width=1.2, dash="dot"),
        opacity=0.4, showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=fut_fc["ds"], y=fut_fc["yhat"], mode="lines+markers",
        name=f"Pronóstico +{horizon}m", line=dict(color="#dc2626", width=2.5),
        marker=dict(size=9, symbol="diamond", color="#dc2626"),
        hovertemplate="<b>%{x|%b %Y}</b><br>Pronóstico: <b>%{y:,.0f} u</b><extra>Pronóstico</extra>",
    ))
    fig.add_shape(
        type="line", x0=corte, x1=corte, y0=0, y1=1,
        xref="x", yref="paper",
        line=dict(dash="dot", color="#94a3b8", width=1.5),
    )
    fig.add_annotation(
        x=corte, y=0.97, xref="x", yref="paper",
        text="  Hoy", showarrow=False, xanchor="left",
        font=dict(color="#94a3b8", size=11),
    )
    fig.update_layout(
        title=f"Demanda pronosticada — {label_pred}",
        xaxis_title="Mes", yaxis_title="Unidades vendidas",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=440, plot_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9", rangemode="tozero"),
        hovermode="x unified",
        margin=dict(t=70, b=50, l=60, r=30),
    )
    st.plotly_chart(fig, use_container_width=True)

    t_vals, t_comp = st.tabs(["  Valores del pronóstico  ", "  Comparativa de subcategorías  "])

    with t_vals:
        tbl = fut_fc[["ds","yhat","yhat_lower","yhat_upper"]].copy()
        tbl.columns = ["Mes","Pronóstico","IC Inferior","IC Superior"]
        tbl["Mes"] = tbl["Mes"].dt.strftime("%b %Y")
        tbl[["Pronóstico","IC Inferior","IC Superior"]] = (
            tbl[["Pronóstico","IC Inferior","IC Superior"]].round(0).astype(int)
        )
        st.dataframe(tbl, use_container_width=True, hide_index=True)

    with t_comp:
        with st.spinner("Calculando comparativa…"):
            comp_rows = []
            for sc in sorted(df_maestra["Subcategory"].unique()):
                try:
                    h, fc = fit_prophet("Subcategory", sc, region_prophet, horizon)
                    avg   = h["y"].mean()
                    for _, r in fc[fc["ds"] > h["ds"].max()].iterrows():
                        comp_rows.append({
                            "Subcategoría": sc,
                            "Mes"         : r["ds"].strftime("%b %Y"),
                            "Pronóstico"  : int(round(r["yhat"])),
                            "Cambio %"    : round((r["yhat"] - avg) / avg * 100, 1),
                        })
                except Exception:
                    pass
        comp_df = pd.DataFrame(comp_rows)
        if not comp_df.empty:
            pivot = comp_df.pivot_table(
                index="Subcategoría", columns="Mes",
                values="Pronóstico", aggfunc="first"
            )
            st.dataframe(pivot, use_container_width=True)

            primer_mes = comp_df["Mes"].unique()[0]
            bar_df = comp_df[comp_df["Mes"]==primer_mes].sort_values("Pronóstico", ascending=True)
            colores = ["#16a34a" if v >= 2 else "#dc2626" if v <= -2 else "#f59e0b"
                       for v in bar_df["Cambio %"]]
            fig_bar = go.Figure(go.Bar(
                x=bar_df["Pronóstico"], y=bar_df["Subcategoría"], orientation="h",
                marker=dict(color=colores, opacity=0.85),
                text=[f"{v:,} u  ({c:+.1f}%)" for v, c in
                      zip(bar_df["Pronóstico"], bar_df["Cambio %"])],
                textposition="outside",
            ))
            fig_bar.update_layout(
                title=f"{REG_LABEL.get(region_prophet,'')} — {primer_mes}",
                xaxis_title="Unidades pronosticadas", height=380,
                plot_bgcolor="white",
                xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
                margin=dict(l=110, r=130),
            )
            st.plotly_chart(fig_bar, use_container_width=True)


# ──────────────────────────────────────────────────────────────────
# PESTAÑA 2 — Sobrestock crítico
# ──────────────────────────────────────────────────────────────────
with tab_stock:
    prod_over = (
        df_filtrado.groupby(["Category","Subcategory","Product_name"])
        .agg(
            Avg_excess       = ("Excess_stock",     "mean"),
            Avg_gap_pct      = ("Gap_pct",          "mean"),
            Avg_days_inv     = ("Days_inventory",   "mean"),
            Avg_sell_through = ("Sell_through_pct", "mean"),
            Total_sold       = ("Units_sold",       "sum"),
        )
        .reset_index()
        .sort_values("Avg_excess", ascending=False)
        .reset_index(drop=True)
    )

    # ── Top 5 con el mismo estilo de card de Inicio.py ────────────
    if not prod_over.empty:
        top5     = prod_over.head(5)
        max_exc  = top5["Avg_excess"].max() or 1
        rows_html = ""
        for _, r in top5.iterrows():
            pct_bar = (r["Avg_excess"] / max_exc) * 100
            name    = escape(r["Product_name"].replace(r["Subcategory"],"").strip())
            subcat  = escape(r["Subcategory"])
            val     = f"{int(r['Avg_excess']):,} u"
            rows_html += f"""
            <div class="item">
                <div class="item-top">
                    <div>
                        <span class="item-name">{name}</span>
                        <span class="item-sub"> &nbsp;{subcat}</span>
                    </div>
                    <span class="item-val">{val}</span>
                </div>
                <div class="bar-track">
                    <div class="bar-fill" style="width:{pct_bar:.1f}%"></div>
                </div>
            </div>"""
        components.html(top5_card_html(rows_html), height=360, scrolling=False)
    else:
        st.info("No hay datos con los filtros seleccionados.")

    st.markdown("#### Ranking completo de productos")
    busqueda = st.text_input("🔎 Buscar producto", placeholder="ej. Sneakers, Boots…")
    df_show  = prod_over.copy()
    if busqueda:
        df_show = df_show[df_show["Product_name"].str.contains(busqueda, case=False)]

    df_disp = df_show.copy()
    df_disp["Avg_excess"]       = df_disp["Avg_excess"].round(0).astype(int)
    df_disp["Avg_gap_pct"]      = df_disp["Avg_gap_pct"].round(1)
    df_disp["Avg_days_inv"]     = df_disp["Avg_days_inv"].round(0).astype(int)
    df_disp["Avg_sell_through"] = df_disp["Avg_sell_through"].round(1)
    df_disp.columns = ["Categoría","Subcategoría","Producto",
                        "Exceso (u)","Gap %","Días inv","Sell-through %","Total vendido"]
    st.dataframe(df_disp, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("#### Sobrestock por región × subcategoría")
    gap_pivot = (
        df_filtrado.groupby(["Region","Subcategory"])
        .agg(Gap_pct=("Gap_pct","mean"),
             Excess_stock=("Excess_stock","mean"),
             Days_inventory=("Days_inventory","mean"))
        .reset_index()
    )
    s1, s2, s3 = st.tabs(["% Sobrestock", "Exceso (u)", "Días inventario"])
    for tab_s, col_s, cmap_s in [
        (s1, "Gap_pct", "YlOrRd"),
        (s2, "Excess_stock", "YlOrRd"),
        (s3, "Days_inventory", "RdYlGn_r"),
    ]:
        with tab_s:
            if gap_pivot.empty or gap_pivot["Region"].nunique() < 2:
                st.info("Selecciona 'Todas' en Región para ver la tabla comparativa.")
            else:
                pv = gap_pivot.pivot(index="Subcategory", columns="Region", values=col_s).round(1)
                pv.columns = [REG_LABEL.get(c, c) for c in pv.columns]
                st.dataframe(pv.style.background_gradient(cmap=cmap_s, axis=None),
                             use_container_width=True)


# ──────────────────────────────────────────────────────────────────
# PESTAÑA 3 — Redistribución
# ──────────────────────────────────────────────────────────────────
with tab_redist:
    st.caption("🔴 ORIGEN = enviar stock  ·  🟢 DESTINO = recibir stock")

    @st.cache_data
    def calcular_redistribucion():
        df_r = load_data()
        base = (
            df_r.groupby(["Region","Subcategory"])
            .agg(Avg_excess=("Excess_stock","mean"),
                 Gap_pct=("Gap_pct","mean"),
                 Sell_through=("Sell_through_pct","mean"))
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
        base["Score_origen"]  = base["Gap_pct"] * (1 / base["Forecast_avg"].replace(0, np.nan))
        base["Score_destino"] = base["Forecast_avg"] / base["Avg_excess"].replace(0, np.nan)
        p75_o = base["Score_origen"].quantile(0.75)
        p75_d = base["Score_destino"].quantile(0.75)
        base["Rol"] = "Equilibrio"
        base.loc[base["Score_origen"]  >= p75_o, "Rol"] = "ORIGEN"
        base.loc[base["Score_destino"] >= p75_d, "Rol"] = "DESTINO"
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
    COLOR_ROL = {"ORIGEN": "#dc2626", "DESTINO": "#16a34a", "Equilibrio": "#f59e0b"}

    fig_map = go.Figure()
    origenes = reg_rol[reg_rol["Rol_predominante"] == "ORIGEN"]
    destinos  = reg_rol[reg_rol["Rol_predominante"] == "DESTINO"]
    for _, orig in origenes.iterrows():
        for _, dest in destinos.iterrows():
            dist = haversine(orig["lat"], orig["lon"], dest["lat"], dest["lon"])
            fig_map.add_trace(go.Scattergeo(
                lat=[orig["lat"], dest["lat"]], lon=[orig["lon"], dest["lon"]],
                mode="lines", line=dict(width=1.8, color="rgba(99,102,241,0.35)"),
                hovertemplate=f"<b>{orig['city']} → {dest['city']}</b><br>~{dist:,} km<extra></extra>",
                showlegend=False,
            ))
    for _, row in reg_rol.iterrows():
        fig_map.add_trace(go.Scattergeo(
            lat=[row["lat"]], lon=[row["lon"]],
            mode="markers+text",
            marker=dict(size=20, color=COLOR_ROL[row["Rol_predominante"]],
                        opacity=0.9, line=dict(width=2, color="white")),
            text=[f"  {row['city']}"], textposition="middle right",
            textfont=dict(size=11, color="#0f172a", family="Arial Black"),
            hovertemplate=(
                f"<b>{row['Region'].title()}</b><br>"
                f"Rol: <b>{row['Rol_predominante']}</b><extra></extra>"
            ),
            showlegend=False,
        ))
    fig_map.update_layout(
        geo=dict(
            scope="north america", resolution=50,
            center=dict(lat=23.6, lon=-102.5), projection_scale=4.8,
            showland=True,       landcolor="#f8fafc",
            showocean=True,      oceancolor="#dbeafe",
            showlakes=True,      lakecolor="#dbeafe",
            showcoastlines=True, coastlinecolor="#cbd5e1",
            showcountries=True,  countrycolor="#cbd5e1",
            showsubunits=True,   subunitcolor="#e2e8f0",
            bgcolor="#ffffff",
        ),
        height=480, margin=dict(l=0, r=0, t=40, b=0),
        title=dict(text="<b>Mapa de redistribución de inventario</b>",
                   font=dict(size=17, color="#0f172a"), x=0.01),
        paper_bgcolor="#ffffff",
    )
    st.plotly_chart(fig_map, use_container_width=True)

    lc1, lc2 = st.columns(2)
    lc1.markdown(
        "<div style='text-align:center;padding:10px;background:#fee2e2;"
        "border:1px solid #dc2626;border-radius:8px;color:#dc2626;font-weight:600'>"
        "🔴 ORIGEN — Enviar stock</div>", unsafe_allow_html=True)
    lc2.markdown(
        "<div style='text-align:center;padding:10px;background:#dcfce7;"
        "border:1px solid #16a34a;border-radius:8px;color:#16a34a;font-weight:600'>"
        "🟢 DESTINO — Recibir stock</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)

    plan = (
        redist_df[redist_df["Rol"]=="ORIGEN"][["Region","Subcategory","Avg_excess"]]
        .merge(redist_df[redist_df["Rol"]=="DESTINO"][["Region","Subcategory","Forecast_avg"]],
               on="Subcategory", suffixes=("_origen","_destino"))
    )
    plan["Unidades"]    = (plan["Avg_excess"] * 0.30).round(0).astype(int)
    plan["Dist (km)"]   = plan.apply(lambda r: haversine(
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
        .sort_values("Unidades", ascending=False).reset_index(drop=True)
    )
    st.markdown("#### Plan de transferencias sugerido")
    st.dataframe(plan_show, use_container_width=True, hide_index=True)