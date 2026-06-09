# utils/forecast_engine.py
# ══════════════════════════════════════════════════════════════════════
# DANUStore — Motor de Pronósticos
# Carga de datos · Modelo Prophet · Cache
# ══════════════════════════════════════════════════════════════════════

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import streamlit as st
from prophet import Prophet


# ══════════════════════════════════════════════════════════════════════
# CARGA Y PREPARACIÓN DE DATOS
# ══════════════════════════════════════════════════════════════════════

@st.cache_data
def load_data() -> pd.DataFrame:
    """
    Lee df_Maestra.csv y agrega columnas derivadas para análisis
    de inventario y pronósticos.

    Columnas nuevas
    ---------------
    YearMonth       : período mensual (Period)

    Excess_stock    : sobrestock real del mes, calculado con la fórmula:
                        Stock − (Units_sold × 1.2)
                      = Stock − (ventas reales + 20% buffer de seguridad)
                      Se lee directamente de "Sobrestock crítico por MES"
                      (ya viene calculada en el CSV con esa fórmula).
                      Siempre ≥ 0 (nunca hay registro de déficit aquí).

    Excedente       : presión acumulada de sobrestock mes a mes.
                        Excedente_mes = Sobrestock_mes − Excedente_mes_anterior
                      El primer registro de cada producto arranca en 0.
                      Puede ser negativo (el sobrestock se está reduciendo)
                      o positivo (el sobrestock está creciendo).
                      Lee directamente la columna "Excedente" del CSV.

    Gap_units       : unidades que NO están en sobrestock en ese mes
                        = Stock − Excess_stock
                      Equivale a la parte del stock "tolerada" = Units_sold × 1.2.
                      Siempre positivo dado que Excess_stock ≤ Stock.

    Gap_pct         : porcentaje del stock que está en sobrestock
                        = Excess_stock / Stock × 100
                      Refleja qué fracción del inventario supera la demanda
                      esperada con su buffer. Rango típico: 68 % – 96 %.
    """
    df = pd.read_csv(
        "data/df_Maestra.csv",
        parse_dates=["Date"],
    )
    df.columns = df.columns.str.strip()

    df["YearMonth"] = df["Date"].dt.to_period("M")

    # ── Sobrestock real: usar la columna precalculada del CSV ──────────
    # Fórmula original: Stock − (Units_sold × 1.2)
    # La columna "Sobrestock crítico por MES" ya la implementa correctamente.
    # No recalculamos para evitar diferencias de redondeo vs el CSV.
    df["Excess_stock"] = pd.to_numeric(
        df["Sobrestock crítico por MES"], errors="coerce"
    ).clip(lower=0).fillna(0)

    # ── Excedente acumulado: leer directamente del CSV ─────────────────
    # Fórmula: Excedente_mes = Sobrestock_mes − Excedente_mes_anterior
    # Primer registro de cada producto = 0.
    # Negativo → sobrestock bajando; positivo → sobrestock creciendo.
    df["Excedente"] = pd.to_numeric(
        df["Excedente"], errors="coerce"
    ).fillna(0)

    # ── Gap: unidades fuera del sobrestock (parte "tolerada") ──────────
    df["Gap_units"] = df["Stock"] - df["Excess_stock"]

    # ── Gap porcentual: fracción del stock en sobrestock ───────────────
    df["Gap_pct"] = (
        df["Excess_stock"] / df["Stock"].replace(0, np.nan)
    ) * 100

    return df


# ══════════════════════════════════════════════════════════════════════
# MODELO PROPHET
# ══════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def fit_prophet(
    group_col: str,
    group_val: str,
    region: str,
    periods: int,
) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """
    Entrena Prophet para una combinación grupo × región y devuelve
    el histórico mensual y el dataframe de predicción.

    Parámetros
    ----------
    group_col : columna de agrupación, p.ej. "Subcategory"
    group_val : valor del grupo, p.ej. "Shirts"
    region    : nombre de la región tal como aparece en el CSV
    periods   : meses a pronosticar (3 o 6)

    Retorna
    -------
    (hist_df, forecast_df)  — (None, None) si hay < 6 meses de datos
    """
    df = load_data()

    mask = (
        (df["Region"]    == region) &
        (df[group_col]   == group_val)
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
        changepoint_prior_scale=0.05,
        seasonality_mode="additive",
        uncertainty_samples=300,
        yearly_seasonality=False,
        weekly_seasonality=False,
        daily_seasonality=False,
    )
    if len(sub) >= 12:
        model.add_seasonality(
            name="semestral",
            period=182.5,
            fourier_order=1 if len(sub) < 24 else 3,
        )

    model.fit(sub)
    future = model.make_future_dataframe(periods=periods, freq="MS")
    fc = model.predict(future)

    return sub, fc


# ══════════════════════════════════════════════════════════════════════
# FORECAST AGREGADO POR SUBCATEGORÍA (usado en KPIs del dashboard)
# ══════════════════════════════════════════════════════════════════════

def build_forecast_summary(
    df_filtrado: pd.DataFrame,
    region_prophet: str,
    horizon: int,
) -> pd.DataFrame:
    """
    Calcula el resumen de forecast para cada subcategoría presente
    en df_filtrado. Devuelve un DataFrame con columnas:

        Subcategory | Hist_avg | Forecast_avg | Growth_pct
    """
    rows = []

    for sc in sorted(df_filtrado["Subcategory"].dropna().unique()):

        hist, fc = fit_prophet("Subcategory", sc, region_prophet, horizon)

        if hist is None:
            continue

        futuro   = fc[fc["ds"] > hist["ds"].max()]
        hist_avg = hist["y"].mean()
        fut_avg  = futuro["yhat"].mean()

        growth = (
            ((fut_avg - hist_avg) / hist_avg) * 100
            if hist_avg > 0
            else 0.0
        )

        rows.append({
            "Subcategory":  sc,
            "Hist_avg":     hist_avg,
            "Forecast_avg": fut_avg,
            "Growth_pct":   growth,
        })

    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════
# FORECAST POR SUBCATEGORÍA × REGIÓN (usado en redistribución)
# ══════════════════════════════════════════════════════════════════════

def build_subcat_region_forecast(
    df_master: pd.DataFrame,
    horizon: int,
) -> dict[tuple[str, str], float]:
    """
    Corre Prophet para cada par (subcategoría, región) y acumula
    la demanda pronosticada total para el horizonte indicado.

    Retorna
    -------
    dict  →  {(subcategory, region): demanda_total_horizonte}
    """
    result: dict[tuple[str, str], float] = {}

    all_subcats = df_master["Subcategory"].dropna().unique()
    all_regions = df_master["Region"].dropna().unique()

    for sc in all_subcats:
        for rg in all_regions:

            hist_tmp, fc_tmp = fit_prophet("Subcategory", sc, rg, horizon)

            if hist_tmp is None or fc_tmp is None:
                result[(sc, rg)] = 0.0
                continue

            future_mask = fc_tmp["ds"] > hist_tmp["ds"].max()
            val = max(fc_tmp.loc[future_mask, "yhat"].sum(), 0.0)
            result[(sc, rg)] = val

    return result


# ══════════════════════════════════════════════════════════════════════
# FORECAST POR REGIÓN (tarjeta mejor/peor — no cambia con filtros)
# ══════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def build_region_forecast(horizon: int) -> pd.DataFrame:
    """
    Corre Prophet para cada región usando el total de ventas mensuales.
    No acepta filtros — siempre usa el dataset completo para que
    la tarjeta mejor/peor región sea estable e independiente de filtros.

    Retorna DataFrame con columnas:
        Region | Region_label | Hist_avg | Forecast_avg | Forecast_total | Growth_pct
    """
    from src.redistribucion import REG_LABEL

    df = load_data()

    rows = []
    for region in sorted(df["Region"].dropna().unique()):

        sub = (
            df[df["Region"] == region]
            .groupby("YearMonth")
            .agg(y=("Units_sold", "sum"))
            .reset_index()
        )

        if len(sub) < 6:
            continue

        sub["ds"] = sub["YearMonth"].dt.to_timestamp()
        sub = sub[["ds", "y"]]

        model = Prophet(
            changepoint_prior_scale=0.05,
            seasonality_mode="additive",
            uncertainty_samples=300,
            yearly_seasonality=False,
            weekly_seasonality=False,
            daily_seasonality=False,
        )
        if len(sub) >= 12:
            model.add_seasonality(
                name="semestral",
                period=182.5,
                fourier_order=1 if len(sub) < 24 else 3,
            )
        model.fit(sub)

        future    = model.make_future_dataframe(periods=horizon, freq="MS")
        fc        = model.predict(future)
        future_fc = fc[fc["ds"] > sub["ds"].max()]

        hist_avg     = float(sub["y"].mean())
        forecast_avg = float(future_fc["yhat"].mean())
        forecast_tot = float(future_fc["yhat"].sum())
        growth       = ((forecast_avg - hist_avg) / hist_avg * 100) if hist_avg > 0 else 0.0

        rows.append({
            "Region":         region,
            "Region_label":   REG_LABEL.get(region, region),
            "Hist_avg":       hist_avg,
            "Forecast_avg":   forecast_avg,
            "Forecast_total": forecast_tot,
            "Growth_pct":     growth,
        })

    return (
        pd.DataFrame(rows)
        .sort_values("Forecast_total", ascending=False)
        .reset_index(drop=True)
    )