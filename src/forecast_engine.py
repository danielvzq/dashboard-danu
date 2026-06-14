# utils/forecast_engine.py

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import streamlit as st
from prophet import Prophet

# CARGA Y PREPARACIÓN DE DATOS

@st.cache_data
def load_data() -> pd.DataFrame:

    df = pd.read_csv(
        "data/df_Maestra.csv",
        parse_dates=["Date"],
    )
    df.columns = df.columns.str.strip()

    df["YearMonth"] = df["Date"].dt.to_period("M")

    # Sobrestock real: usar la columna precalculada del CSV 

    df["Excess_stock"] = pd.to_numeric(
        df["Sobrestock crítico por MES"], errors="coerce"
    ).clip(lower=0).fillna(0)

    #  Excedente acumulado: leer directamente del CSV 
    df["Excedente"] = pd.to_numeric(
        df["Excedente"], errors="coerce"
    ).fillna(0)

    # Gap: unidades fuera del sobrestock (parte "tolerada")
    df["Gap_units"] = df["Stock"] - df["Excess_stock"]

    #  Gap porcentual: fracción del stock en sobrestock
    df["Gap_pct"] = (
        df["Excess_stock"] / df["Stock"].replace(0, np.nan)
    ) * 100

    return df

# MODELO PROPHET

@st.cache_data(show_spinner=False)
def fit_prophet(
    group_col: str,
    group_val: str,
    region: str | None,
    periods: int,
) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    
    df = load_data()

    if region is None:
        mask = df[group_col] == group_val
    else:
        mask = (
            (df["Region"]  == region) &
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

# FORECAST AGREGADO POR SUBCATEGORÍA (usado en KPIs del dashboard)

def build_forecast_summary(
    df_filtrado: pd.DataFrame,
    region_prophet: str | None,
    horizon: int,
) -> pd.DataFrame:
    
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

# FORECAST POR SUBCATEGORÍA × REGIÓN (usado en redistribución)

def build_subcat_region_forecast(
    df_master: pd.DataFrame,
    horizon: int,
) -> dict[tuple[str, str], float]:

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

# FORECAST POR REGIÓN (tarjeta mejor/peor — no cambia con filtros)

@st.cache_data(show_spinner=False)
def build_region_forecast(horizon: int) -> pd.DataFrame:

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