import streamlit as st
import pandas as pd
from src.database import buscar_columna


def crear_filtros_sidebar(df_base):
    col_fecha = buscar_columna(df_base, ["fecha", "date", "fecha_venta", "fecha_compra"])
    col_region = buscar_columna(df_base, ["region", "región", "zona", "sucursal", "ciudad"])
    col_categoria = buscar_columna(df_base, ["categoria", "categoría", "category", "subcategoria", "subcategoría"])

    with st.sidebar:
        st.markdown("### Filtros")

        filtros = {}

        if col_fecha:
            df_base[col_fecha] = pd.to_datetime(df_base[col_fecha], errors="coerce")
            fechas_validas = df_base[col_fecha].dropna()

            if not fechas_validas.empty:
                fecha_min = fechas_validas.min().date()
                fecha_max = fechas_validas.max().date()

                rango_fechas = st.date_input(
                    "Rango de fechas",
                    value=(fecha_min, fecha_max),
                    min_value=fecha_min,
                    max_value=fecha_max,
                    key="filtro_fecha"
                )

                filtros["fecha"] = {
                    "columna": col_fecha,
                    "valor": rango_fechas
                }

        if col_region:
            regiones = sorted(df_base[col_region].dropna().astype(str).unique().tolist())

            region = st.selectbox(
                "Región",
                ["Todas"] + regiones,
                key="filtro_region"
            )

            filtros["region"] = {
                "columna": col_region,
                "valor": region
            }

        if col_categoria:
            categorias = sorted(df_base[col_categoria].dropna().astype(str).unique().tolist())

            categoria = st.selectbox(
                "Categoría",
                ["Todas"] + categorias,
                key="filtro_categoria"
            )

            filtros["categoria"] = {
                "columna": col_categoria,
                "valor": categoria
            }

    return filtros


def aplicar_filtros(df, filtros):
    df_filtrado = df.copy()

    if "fecha" in filtros:
        col = filtros["fecha"]["columna"]
        valor = filtros["fecha"]["valor"]

        if col in df_filtrado.columns and len(valor) == 2:
            fecha_inicio, fecha_fin = valor
            df_filtrado[col] = pd.to_datetime(df_filtrado[col], errors="coerce")

            df_filtrado = df_filtrado[
                (df_filtrado[col].dt.date >= fecha_inicio) &
                (df_filtrado[col].dt.date <= fecha_fin)
            ]

    if "region" in filtros:
        col = filtros["region"]["columna"]
        valor = filtros["region"]["valor"]

        if col in df_filtrado.columns and valor != "Todas":
            df_filtrado = df_filtrado[df_filtrado[col].astype(str) == valor]

    if "categoria" in filtros:
        col = filtros["categoria"]["columna"]
        valor = filtros["categoria"]["valor"]

        if col in df_filtrado.columns and valor != "Todas":
            df_filtrado = df_filtrado[df_filtrado[col].astype(str) == valor]

    return df_filtrado