# src/redistribucion.py

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from datetime import date
from dateutil.relativedelta import relativedelta

# CONSTANTES GEOGRÁFICAS

REGION_COORDS: dict[str, dict] = {
    "bajío":                               {"lat": 20.88, "lon": -101.07, "city": "León"},
    "ciudad de méxico":                    {"lat": 19.43, "lon": -99.13,  "city": "CDMX"},
    "zona metropolitana de monterrey":     {"lat": 25.67, "lon": -100.31, "city": "Monterrey"},
    "zona metropolitana de guadalajara":   {"lat": 20.66, "lon": -103.35, "city": "Guadalajara"},
    "noroeste":                            {"lat": 29.09, "lon": -110.96, "city": "Hermosillo"},
    "sureste":                             {"lat": 20.97, "lon": -89.62,  "city": "Mérida"},
    "sur":                                 {"lat": 17.07, "lon": -96.72,  "city": "Oaxaca"},
}

REG_LABEL: dict[str, str] = {
    "bajío":                               "Bajío",
    "ciudad de méxico":                    "CDMX",
    "zona metropolitana de monterrey":     "ZM Monterrey",
    "zona metropolitana de guadalajara":   "ZM Guadalajara",
    "noroeste":                            "Noroeste",
    "sureste":                             "Sureste",
    "sur":                                 "Sur",
}

GEO_LAYOUT = dict(
    scope="world",
    projection_type="natural earth",
    showland=True,    landcolor="#e8f0e9",
    showocean=True,   oceancolor="#cce4f7",
    showlakes=True,   lakecolor="#cce4f7",
    showcountries=True,
    countrycolor="#94a3b8",
    subunitcolor="rgba(148,163,184,.30)",
    coastlinecolor="#94a3b8",
    showrivers=True,  rivercolor="#cce4f7",
    bgcolor="rgba(248,250,252,1)",
    lonaxis=dict(range=[-118.5, -86.5]),
    lataxis=dict(range=[14.0,   33.5]),
)

# UTILIDADES

def haversine(lat1, lon1, lat2, lon2) -> int:
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return int(2 * R * np.arcsin(np.sqrt(a)))


def get_forecast_dates(df_master: pd.DataFrame, horizon: int) -> list[date]:
    """
    Devuelve las fechas reales del forecast: los N meses SIGUIENTES
    al último mes histórico en el dataset.
    """
    last_month = df_master["YearMonth"].max().to_timestamp().date()
    dates = []
    for i in range(1, horizon + 1):
        d = last_month + relativedelta(months=i)
        dates.append(date(d.year, d.month, 1))
    return dates


def _ensure_overstock_cols(df: pd.DataFrame) -> pd.DataFrame:

    df = df.copy()

    # ── Excess_stock ──────────────────────────────────────────────────
    if "Excess_stock" not in df.columns:
        if "Sobrestock crítico por MES" in df.columns:
            df["Excess_stock"] = (
                pd.to_numeric(df["Sobrestock crítico por MES"], errors="coerce")
                .clip(lower=0)
                .fillna(0)
            )
        else:
            # Fallback: diferencia simple vs demanda planeada
            _demand = "Units_expected" if "Units_expected" in df.columns else "Units_sold"
            df["Excess_stock"] = (df["Stock"] - df[_demand]).clip(lower=0)

    # ── Excedente acumulado ───────────────────────────────────────────
    if "Excedente" not in df.columns:
        df["Excedente"] = pd.to_numeric(
            df.get("Excedente", 0), errors="coerce"
        ).fillna(0)
    else:
        df["Excedente"] = pd.to_numeric(df["Excedente"], errors="coerce").fillna(0)

    # ── Gap_pct ───────────────────────────────────────────────────────
    if "Gap_pct" not in df.columns:
        df["Gap_pct"] = (
            df["Excess_stock"] / df["Stock"].replace(0, np.nan)
        ) * 100

    return df

# PASO 1 — CLASIFICAR REGIONES: ORIGEN / DESTINO / EQUILIBRIO

def build_redist_base(
    df_master: pd.DataFrame,
    subcat_region_forecast: dict[tuple[str, str], float],
    horizon: int = 3,
) -> pd.DataFrame:

    df = _ensure_overstock_cols(df_master)

    region_sub = (
        df.groupby(["Region", "Category", "Subcategory"])
        .agg(
            Avg_stock     = ("Stock",         "mean"),
            # Exceso real: promedio de Sobrestock MES (con buffer de ventas)
            Avg_excess    = ("Excess_stock",  "mean"),
            # Presión acumulada: promedio de Excedente positivo
            # (refleja meses donde el sobrestock creció, no solo el nivel absoluto)
            Avg_excedente = ("Excedente",     lambda x: x.clip(lower=0).mean()),
            Avg_sold      = ("Units_sold",    "mean"),
            Gap_pct       = ("Gap_pct",       "mean"),
            Sell_through  = ("Sell_through_pct", "mean"),
        )
        .reset_index()
    )

    # Forecast por par (subcat, región): suma total del horizonte → ÷ horizon = mensual
    fc_rows = [
        {"Subcategory": k[0], "Region": k[1], "Forecast_total": v}
        for k, v in subcat_region_forecast.items()
    ]
    fc_df  = pd.DataFrame(fc_rows)
    redist = region_sub.merge(fc_df, on=["Subcategory", "Region"], how="left")
    redist["Forecast_total"] = redist["Forecast_total"].fillna(0)
    redist["Forecast_avg"]   = redist["Forecast_total"] / max(horizon, 1)

    # Score_origen: usa Gap_pct real (68-96%) → discrimina mejor entre regiones
    redist["Score_origen"] = (
        redist["Gap_pct"] / redist["Forecast_avg"].replace(0, np.nan)
    ).fillna(0)

    # Score_destino: alta demanda relativa al exceso propio
    redist["Score_destino"] = (
        redist["Forecast_avg"] / redist["Avg_excess"].replace(0, np.nan)
    ).fillna(0)

    p75_o = redist["Score_origen"].quantile(0.75)
    p75_d = redist["Score_destino"].quantile(0.75)
    max_o = redist["Score_origen"].max() or 1
    max_d = redist["Score_destino"].max() or 1

    def rol(row):
        es_o = row["Score_origen"]  >= p75_o
        es_d = row["Score_destino"] >= p75_d
        if es_o and es_d:
            return "ORIGEN" if (row["Score_origen"] / max_o) > (row["Score_destino"] / max_d) else "DESTINO"
        if es_o:
            return "ORIGEN"
        if es_d:
            return "DESTINO"
        return "Equilibrio"

    redist["Rol"] = redist.apply(rol, axis=1)
    return redist

# PASO 2 — FORECAST MENSUAL DETALLADO

@st.cache_data(show_spinner=False)
def build_monthly_forecast(horizon: int) -> pd.DataFrame:
    """
    Extrae los yhat individuales mes a mes de Prophet (no el promedio).
    Necesario para distribuir oleadas proporcionalmente a la demanda.
    """
    from src.forecast_engine import load_data, fit_prophet
    df   = load_data()
    rows = []
    for reg in df["Region"].dropna().unique():
        for sc in df["Subcategory"].dropna().unique():
            hist_df, fc_df = fit_prophet("Subcategory", sc, reg, horizon)
            if hist_df is None:
                continue
            max_ds = hist_df["ds"].max()
            futuro = fc_df[fc_df["ds"] > max_ds].reset_index(drop=True)
            for i, frow in futuro.iterrows():
                rows.append({
                    "Region":      reg,
                    "Subcategory": sc,
                    "Mes_num":     i + 1,
                    "Mes_label":   frow["ds"].strftime("%b %Y"),
                    "Fecha_mes":   frow["ds"].date(),
                    "yhat":        max(float(frow["yhat"]), 0),
                })
    return pd.DataFrame(rows)

# PASO 3 — PLAN DE OLEADAS A NIVEL PRODUCTO

def build_wave_plan(
    df_master:   pd.DataFrame,
    redist_base: pd.DataFrame,
    fc_monthly:  pd.DataFrame,
    horizon:     int = 3,
) -> tuple[pd.DataFrame, pd.DataFrame]:

    df = _ensure_overstock_cols(df_master)

    # Fechas reales del forecast (días 1 y 15 de cada mes pronosticado)
    forecast_dates = get_forecast_dates(df, horizon)
    oleada_dates   = []
    for fd in forecast_dates:
        oleada_dates.append(fd)
        oleada_dates.append(date(fd.year, fd.month, 15))

    # ── Producto más débil: último mes disponible ─────────────────────
    last_month = df["YearMonth"].max()
    df_last    = df[df["YearMonth"] == last_month]

    prod_region_last = (
        df_last
        .groupby(["Product_id", "Product_name", "Category", "Subcategory", "Region"])
        .agg(
            last_stock        = ("Stock",        "sum"),
            last_excess       = ("Excess_stock", "sum"),   # Sobrestock MES
            last_excedente    = ("Excedente",    "sum"),   # Excedente acumulado
            last_sold         = ("Units_sold",   "sum"),
            gap_pct           = ("Gap_pct",      "mean"),
            sell_through      = ("Sell_through_pct", "mean"),
        )
        .reset_index()
    )

    # Producto más débil = mayor Gap_pct en la región origen
    weakest = (
        prod_region_last
        .sort_values("gap_pct", ascending=False)
        .groupby(["Subcategory", "Region"])
        .first()
        .reset_index()
    )

    # ── Pares ORIGEN → DESTINO 
    origenes = redist_base[redist_base["Rol"] == "ORIGEN"][
        ["Region", "Category", "Subcategory", "Avg_excess", "Avg_excedente", "Gap_pct"]
    ].copy()
    destinos = redist_base[redist_base["Rol"] == "DESTINO"][
        ["Region", "Category", "Subcategory", "Forecast_avg"]
    ].copy()

    pares = origenes.merge(
        destinos, on=["Category", "Subcategory"],
        suffixes=("_origen", "_destino")
    )
    pares = pares[pares["Region_origen"] != pares["Region_destino"]].copy()

    # Añadir el producto más débil del origen
    pares = pares.merge(
        weakest[[
            "Subcategory", "Region",
            "Product_id", "Product_name",
            "last_excess", "last_excedente",
            "gap_pct", "sell_through"
        ]].rename(columns={
            "Region":          "Region_origen",
            "last_excess":     "Excess_producto",      # Sobrestock MES del último mes
            "last_excedente":  "Excedente_producto",   # Excedente acumulado del último mes
            "gap_pct":         "Gap_producto",
            "sell_through":    "Sell_through_origen",
        }),
        on=["Subcategory", "Region_origen"],
        how="left",
    )

    # ── Total a transferir 
    pares["Forecast_total_h"]  = pares["Forecast_avg"] * horizon
    pares["Total_transferir"]  = pares.apply(
        lambda r: max(int(min(
            max(r.get("Excedente_producto", 0), 0) * 0.80,    # presión acumulada
            r.get("Excess_producto", r["Avg_excess"]) * 0.80,  # techo sobrestock MES
            r["Forecast_total_h"] * 0.60,                      # cap demanda destino
        )), 0),
        axis=1,
    )
    pares = pares[pares["Total_transferir"] > 0].reset_index(drop=True)

    pares["Distancia_km"] = pares.apply(
        lambda r: haversine(
            REGION_COORDS[r["Region_origen"]]["lat"],
            REGION_COORDS[r["Region_origen"]]["lon"],
            REGION_COORDS[r["Region_destino"]]["lat"],
            REGION_COORDS[r["Region_destino"]]["lon"],
        ), axis=1
    )

    #  Generar oleadas 
    plan_rows = []
    for _, par in pares.iterrows():
        subcat  = par["Subcategory"]
        reg_dst = par["Region_destino"]
        reg_src = par["Region_origen"]

        fc_dst = (
            fc_monthly[
                (fc_monthly["Region"]      == reg_dst) &
                (fc_monthly["Subcategory"] == subcat)
            ]
            .sort_values("Mes_num")
            .reset_index(drop=True)
        )

        if fc_dst.empty or fc_dst["yhat"].sum() == 0:
            yhats  = [par["Forecast_avg"]] * horizon
            labels = [fd.strftime("%b %Y") for fd in forecast_dates]
        else:
            yhats  = fc_dst["yhat"].tolist()[:horizon]
            labels = fc_dst["Mes_label"].tolist()[:horizon]

        while len(yhats) < horizon:
            yhats.append(yhats[-1] if yhats else 0)
            labels.append(f"Mes {len(yhats)}")

        total_yhat   = sum(yhats) if sum(yhats) > 0 else 1
        oleada_units = []
        oleada_num   = 0

        for m_idx, (yhat_m, label_m) in enumerate(zip(yhats, labels)):
            peso_mes     = yhat_m / total_yhat
            unidades_mes = par["Total_transferir"] * peso_mes

            for bisemana in range(2):
                oleada_num += 1
                fecha_real  = oleada_dates[m_idx * 2 + bisemana]
                u           = round(unidades_mes / 2)
                oleada_units.append(u)

                plan_rows.append({
                    "Product_id":           par.get("Product_id", ""),
                    "Producto":             par.get("Product_name", "—"),
                    "Subcategoría":         subcat,
                    "Categoría":            par["Category"],
                    "Origen":               reg_src,
                    "Destino":              reg_dst,
                    "Origen_label":         REG_LABEL.get(reg_src, reg_src),
                    "Destino_label":        REG_LABEL.get(reg_dst, reg_dst),
                    "Oleada":               oleada_num,
                    "Fecha_envío":          fecha_real.strftime("%d %b %Y"),
                    "Mes_num":              m_idx + 1,
                    "Mes_pronóstico":       label_m,
                    "Demanda_destino_mes":  round(yhat_m),
                    "Unidades_oleada":      u,
                    "Total_transferencia":  par["Total_transferir"],
                    # ── Campos enriquecidos con nuevas variables ──────
                    "Sobrestock_origen_u":  round(par.get("Excess_producto", par["Avg_excess"])),
                    "Excedente_origen_u":   round(max(par.get("Excedente_producto", 0), 0)),
                    "Gap_origen_pct":       round(par.get("Gap_producto", par["Gap_pct"]), 1),
                    "Sell_through_origen":  round(par.get("Sell_through_origen", 0), 1),
                    "Distancia_km":         par["Distancia_km"],
                })

        # Ajuste de redondeo en la última oleada
        diff = par["Total_transferir"] - sum(oleada_units)
        if diff != 0 and plan_rows:
            plan_rows[-1]["Unidades_oleada"] += diff

    plan_df = (
        pd.DataFrame(plan_rows)
        .sort_values(["Subcategoría", "Origen", "Destino", "Oleada"])
        .reset_index(drop=True)
    )

    return pares, plan_df

# TRAZAS DEL MAPA — un frame por oleada (6 frames fijos)

def build_animation_frames(
    plan_df: pd.DataFrame,
    horizon: int,
) -> tuple:
    """
    Un frame por fila de plan_df, ordenado por Mes → Oleada → mayor total.
    Mapa inicia LIMPIO (sin líneas).
    """
    ordered = (
        plan_df
        .sort_values(
            ["Mes_num", "Oleada", "Total_transferencia"],
            ascending=[True, True, False]
        )
        .reset_index(drop=True)
    )

    frames, slider_steps = [], []
    max_u_all = ordered["Unidades_oleada"].max() or 1

    for i, row in ordered.iterrows():
        o_coords = REGION_COORDS[row["Origen"]]
        d_coords = REGION_COORDS[row["Destino"]]

        node_trace = _make_nodes({row["Origen"]}, {row["Destino"]})

        width = 3 + 5 * (row["Unidades_oleada"] / max_u_all)
        route_trace = go.Scattergeo(
            lat=[o_coords["lat"], d_coords["lat"]],
            lon=[o_coords["lon"], d_coords["lon"]],
            mode="lines",
            line=dict(width=width, color="#16a34a"),
            opacity=0.85,
            hoverinfo="skip",
            showlegend=False,
        )

        orig_label = REG_LABEL.get(row["Origen"], row["Origen"])
        dest_label = REG_LABEL.get(row["Destino"], row["Destino"])

        # Anotación enriquecida: muestra Sobrestock y Excedente del origen
        annotation = dict(
            x=0.02, y=0.98,
            xref="paper", yref="paper",
            xanchor="left", yanchor="top",
            text=(
                f"<b>{row['Producto']}</b><br>"
                f"{orig_label} → {dest_label}<br>"
                f"<b>{row['Fecha_envío']}</b>  ·  {row['Mes_pronóstico']}<br>"
                f"Esta oleada: <b>{int(row['Unidades_oleada']):,} u</b><br>"
                f"Total transferencia: {int(row['Total_transferencia']):,} u<br>"
                f"Demanda destino: {int(row['Demanda_destino_mes']):,} u/mes<br>"
                f"Sobrestock origen: {int(row.get('Sobrestock_origen_u', 0)):,} u<br>"
                f"Excedente acumulado: {int(row.get('Excedente_origen_u', 0)):,} u<br>"
                f"Gap origen: {row.get('Gap_origen_pct', 0):.1f}% del stock<br>"
                f"Distancia: {int(row['Distancia_km']):,} km"
            ),
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor="rgba(148,163,184,0.6)",
            borderwidth=1.5,
            borderpad=10,
            font=dict(size=11, color="#0f172a",
                      family="Inter, system-ui, sans-serif"),
            showarrow=False,
            align="left",
        )

        n_total = len(ordered)
        frames.append(go.Frame(
            data=[node_trace, route_trace],
            name=str(i),
            layout=go.Layout(
                title_text=(
                    f"Transferencia {i + 1} de {n_total}  ·  "
                    f"Mes {int(row['Mes_num'])}  ·  "
                    f"Oleada {int(row['Oleada'])} de 6  ·  "
                    f"{row['Fecha_envío']}"
                ),
                annotations=[annotation],
            ),
        ))

        slider_steps.append(dict(
            args=[
                [str(i)],
                dict(frame=dict(duration=1800, redraw=True), mode="immediate"),
            ],
            label=row["Fecha_envío"],
            method="animate",
        ))

    # Estado inicial: mapa limpio, sin líneas
    init_nodes = _make_nodes(set(), set())
    init_route = go.Scattergeo(
        lat=[None], lon=[None], mode="lines",
        line=dict(width=0, color="rgba(0,0,0,0)"),
        hoverinfo="skip", showlegend=False,
    )
    init_annotation = dict(
        x=0.02, y=0.98,
        xref="paper", yref="paper",
        xanchor="left", yanchor="top",
        text=(
            f"<b>Plan de {len(ordered)} transferencias</b><br>"
            f"Presiona ▶ Play para iniciar<br>"
            f"Período: {ordered['Fecha_envío'].iloc[0]} – "
            f"{ordered['Fecha_envío'].iloc[-1]}"
        ),
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor="rgba(148,163,184,0.6)",
        borderwidth=1.5, borderpad=10,
        font=dict(size=11, color="#0f172a",
                  family="Inter, system-ui, sans-serif"),
        showarrow=False, align="left",
    )

    return frames, slider_steps, init_nodes, [init_route], init_annotation, len(ordered)

# NODOS DEL MAPA

def _make_nodes(active_origins: set, active_dests: set) -> go.Scattergeo:
    regions = list(REGION_COORDS.keys())
    colors, sizes = [], []
    for r in regions:
        if r in active_origins:
            colors.append("#ef4444"); sizes.append(22)
        elif r in active_dests:
            colors.append("#22c55e"); sizes.append(22)
        else:
            colors.append("#3b82f6"); sizes.append(14)
    return go.Scattergeo(
        lat=[REGION_COORDS[r]["lat"] for r in regions],
        lon=[REGION_COORDS[r]["lon"] for r in regions],
        mode="markers+text",
        marker=dict(size=sizes, color=colors,
                    line=dict(width=2, color="white")),
        text=[REGION_COORDS[r]["city"] for r in regions],
        textposition="top center",
        textfont=dict(size=11, color="#0f172a"),
        hovertext=[REG_LABEL.get(r, r) for r in regions],
        hoverinfo="text",
        showlegend=False,
    )