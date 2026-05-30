# utils/redistribucion.py
# ══════════════════════════════════════════════════════════════════════
# DANUStore — Lógica de Redistribución de Inventario
# Surplus · Transferencias · Trazas del mapa animado
# ══════════════════════════════════════════════════════════════════════
#
# Separado de la UI para que 4_Pronosticos.py solo llame funciones
# y se enfoque en renderizar.
#
# Importar así:
#   from utils.redistribucion import (
#       REGION_COORDS, REG_LABEL, haversine,
#       build_product_region_table,
#       build_transfer_df,
#       make_node_trace,
#       make_route_trace,
#   )
# ══════════════════════════════════════════════════════════════════════

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# ══════════════════════════════════════════════════════════════════════
# CONSTANTES GEOGRÁFICAS
# ══════════════════════════════════════════════════════════════════════

REGION_COORDS: dict[str, dict] = {
    "bajío": {
        "lat": 20.88, "lon": -101.07, "city": "León"
    },
    "ciudad de méxico": {
        "lat": 19.43, "lon": -99.13, "city": "CDMX"
    },
    "zona metropolitana de monterrey": {
        "lat": 25.67, "lon": -100.31, "city": "Monterrey"
    },
    "zona metropolitana de guadalajara": {
        "lat": 20.66, "lon": -103.35, "city": "Guadalajara"
    },
    "noroeste": {
        "lat": 29.09, "lon": -110.96, "city": "Hermosillo"
    },
    "sureste": {
        "lat": 20.97, "lon": -89.62, "city": "Mérida"
    },
    "sur": {
        "lat": 17.07, "lon": -96.72, "city": "Oaxaca"
    },
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


# ══════════════════════════════════════════════════════════════════════
# UTILIDADES GEOGRÁFICAS
# ══════════════════════════════════════════════════════════════════════

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """Distancia en km entre dos coordenadas (fórmula haversine)."""
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    )
    return int(2 * R * np.arcsin(np.sqrt(a)))


# ══════════════════════════════════════════════════════════════════════
# PASO 2 — TABLA PRODUCTO × REGIÓN CON FORECAST
# ══════════════════════════════════════════════════════════════════════

def build_product_region_table(
    df_master: pd.DataFrame,
    subcat_region_forecast: dict[tuple[str, str], float],
) -> pd.DataFrame:
    """
    Construye una tabla a nivel Producto × Región con:
      - ventas y stock históricos promedio
      - share de ventas dentro de su subcategoría+región
      - demanda pronosticada para el horizonte (via forecast)
      - surplus = stock − forecast  (exceso sobre lo que se venderá)

    Parámetros
    ----------
    df_master               : DataFrame completo de df_Maestra
    subcat_region_forecast  : dict {(subcat, region): demanda_total}

    Retorna
    -------
    DataFrame con columnas:
        Product_id, Product_name, Category, Subcategory, Region,
        avg_sales, avg_stock, avg_sell_through, share,
        subcat_forecast, product_forecast, surplus
    """
    prod_region = (
        df_master
        .groupby(
            ["Product_id", "Product_name",
             "Category", "Subcategory", "Region"]
        )
        .agg(
            avg_sales=("Units_sold", "mean"),
            avg_stock=("Stock", "mean"),
            avg_sell_through=("Sell_through_pct", "mean"),
        )
        .reset_index()
    )

    # Share de cada producto dentro de su subcategoría+región
    subcat_totals = (
        prod_region
        .groupby(["Subcategory", "Region"])["avg_sales"]
        .sum()
        .reset_index()
        .rename(columns={"avg_sales": "subcat_total"})
    )
    prod_region = prod_region.merge(
        subcat_totals, on=["Subcategory", "Region"]
    )
    prod_region["share"] = (
        prod_region["avg_sales"]
        / prod_region["subcat_total"].replace(0, np.nan)
    ).fillna(0)

    # Forecast del producto = share × forecast de su subcategoría+región
    prod_region["subcat_forecast"] = prod_region.apply(
        lambda r: subcat_region_forecast.get(
            (r["Subcategory"], r["Region"]), 0.0
        ),
        axis=1,
    )
    prod_region["product_forecast"] = (
        prod_region["share"] * prod_region["subcat_forecast"]
    )

    # Surplus = stock actual − demanda pronosticada
    prod_region["surplus"] = (
        prod_region["avg_stock"] - prod_region["product_forecast"]
    ).clip(lower=0)

    return prod_region


# ══════════════════════════════════════════════════════════════════════
# PASO 3 — GENERACIÓN DE TRANSFERENCIAS
# ══════════════════════════════════════════════════════════════════════

def build_transfer_df(
    prod_region: pd.DataFrame,
    horizon: int,
    surplus_threshold: float = 50.0,
    origen_pct: float = 0.50,
    destino_pct: float = 0.30,
    min_units: int = 5,
) -> pd.DataFrame:
    """
    Genera el plan de transferencias sugeridas.

    Lógica
    ------
    • Origen  : cualquier región donde surplus > surplus_threshold
    • Destino : TODAS las demás regiones, ordenadas por mayor forecast
                (mayor demanda pronosticada = mejor lugar para recibir)
                Sin restricciones adicionales → todas las regiones
                pueden mandar Y recibir.
    • Cantidad: min(surplus × origen_pct, forecast_destino × destino_pct)

    Parámetros
    ----------
    prod_region        : salida de build_product_region_table()
    horizon            : meses del horizonte (para el tooltip)
    surplus_threshold  : mínimo de exceso para ser origen (default 50 u)
    origen_pct         : fracción del surplus que se puede enviar (0.50)
    destino_pct        : fracción del forecast destino a cubrir (0.30)
    min_units          : transferencia mínima en unidades (5)

    Retorna
    -------
    DataFrame ordenado por Unidades_sugeridas desc, sin duplicados
    (Product_id, Origen, Destino).
    """
    rows = []

    for pid in prod_region["Product_id"].unique():

        p = prod_region[prod_region["Product_id"] == pid].copy()

        origins = p[p["surplus"] > surplus_threshold].sort_values(
            "surplus", ascending=False
        )
        if origins.empty:
            continue

        for _, o in origins.iterrows():

            remaining = o["surplus"]

            dests = (
                p[p["Region"] != o["Region"]]
                .sort_values("product_forecast", ascending=False)
            )

            for _, d in dests.iterrows():

                units = int(
                    min(
                        remaining * origen_pct,
                        d["product_forecast"] * destino_pct,
                    )
                )
                if units < min_units:
                    continue

                dist = haversine(
                    REGION_COORDS[o["Region"]]["lat"],
                    REGION_COORDS[o["Region"]]["lon"],
                    REGION_COORDS[d["Region"]]["lat"],
                    REGION_COORDS[d["Region"]]["lon"],
                )

                rows.append({
                    "Product_id":           pid,
                    "Producto":             o["Product_name"],
                    "Categoría":            o["Category"],
                    "Subcategoría":         o["Subcategory"],
                    "Origen":               o["Region"],
                    "Destino":              d["Region"],
                    "Unidades_sugeridas":   units,
                    "Exceso_origen":        round(o["surplus"], 0),
                    "Forecast_destino":     round(d["product_forecast"], 0),
                    "Sell_through_origen":  round(o["avg_sell_through"], 1),
                    "Sell_through_destino": round(d["avg_sell_through"], 1),
                    "Distancia_km":         dist,
                })

                remaining -= units
                if remaining < min_units:
                    break

    return (
        pd.DataFrame(rows)
        .sort_values("Unidades_sugeridas", ascending=False)
        .drop_duplicates(subset=["Product_id", "Origen", "Destino"])
        .reset_index(drop=True)
    )


# ══════════════════════════════════════════════════════════════════════
# TRAZAS DEL MAPA ANIMADO
# ══════════════════════════════════════════════════════════════════════

def make_node_trace(
    highlight_origen: str | None = None,
    highlight_destino: str | None = None,
) -> go.Scattergeo:
    """
    Genera el trace de nodos del mapa.

    Colores
    -------
    🔴 #ef4444  →  región que envía (origen activo)
    🟢 #22c55e  →  región que recibe (destino activo)
    🔵 #2563eb  →  sin movimiento en este frame
    """
    regions_list  = list(REGION_COORDS.keys())
    region_lats   = [REGION_COORDS[r]["lat"] for r in regions_list]
    region_lons   = [REGION_COORDS[r]["lon"] for r in regions_list]
    region_cities = [REGION_COORDS[r]["city"] for r in regions_list]

    colors, sizes = [], []
    for r in regions_list:
        if r == highlight_origen:
            colors.append("#ef4444"); sizes.append(22)
        elif r == highlight_destino:
            colors.append("#22c55e"); sizes.append(22)
        else:
            colors.append("#2563eb"); sizes.append(15)

    return go.Scattergeo(
        lat=region_lats,
        lon=region_lons,
        mode="markers+text",
        marker=dict(
            size=sizes,
            color=colors,
            line=dict(width=2, color="white"),
        ),
        text=region_cities,
        textposition="top center",
        hovertext=[REG_LABEL.get(r, r) for r in regions_list],
        hoverinfo="text",
        showlegend=False,
    )


def make_route_trace(
    row: pd.Series,
    horizon: int,
) -> go.Scattergeo:
    """
    Genera el trace de la ruta activa (línea verde) para un frame.

    Parámetros
    ----------
    row     : fila de transfer_df
    horizon : meses del horizonte (para el tooltip)
    """
    o = REGION_COORDS[row["Origen"]]
    d = REGION_COORDS[row["Destino"]]

    return go.Scattergeo(
        lat=[o["lat"], d["lat"]],
        lon=[o["lon"], d["lon"]],
        mode="lines",
        line=dict(width=5, color="#22c55e"),
        hovertemplate=(
            f"<b>{REG_LABEL.get(row['Origen'])} "
            f"→ {REG_LABEL.get(row['Destino'])}</b><br>"
            f"Producto: <b>{row['Producto']}</b><br>"
            f"Categoría: <b>{row['Categoría']}</b><br>"
            f"Subcategoría: <b>{row['Subcategoría']}</b><br>"
            f"Unidades: <b>{row['Unidades_sugeridas']:,} u</b><br>"
            f"Exceso origen: <b>{row['Exceso_origen']:,.0f} u</b><br>"
            f"Forecast destino ({horizon} meses): "
            f"<b>{row['Forecast_destino']:,.0f} u</b><br>"
            f"Sell-through origen: <b>{row['Sell_through_origen']}%</b><br>"
            f"Sell-through destino: <b>{row['Sell_through_destino']}%</b><br>"
            f"Distancia: <b>{row['Distancia_km']:,} km</b>"
            "<extra></extra>"
        ),
        showlegend=False,
    )


# ══════════════════════════════════════════════════════════════════════
# LAYOUT DEL MAPA (reutilizable)
# ══════════════════════════════════════════════════════════════════════

GEO_LAYOUT = dict(
    scope="north america",
    projection_scale=4.8,
    center=dict(lat=23.6, lon=-102.5),
    showland=True,   landcolor="#0f172a",
    showocean=True,  oceancolor="#020617",
    showlakes=True,  lakecolor="#020617",
    showcountries=True,
    countrycolor="rgba(255,255,255,.12)",
    subunitcolor="rgba(255,255,255,.08)",
    coastlinecolor="rgba(255,255,255,.08)",
    bgcolor="rgba(0,0,0,0)",
)