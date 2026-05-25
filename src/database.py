from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


@st.cache_data
def cargar_csv(nombre_archivo):
    ruta = DATA_DIR / nombre_archivo
    df = pd.read_csv(ruta)
    df.columns = df.columns.str.strip()
    return df


@st.cache_data
def cargar_datos():
    datos = {
        "clientes": cargar_csv("clientes_limpio.csv"),
        "maestra": cargar_csv("df_Maestra.csv"),
        "inventario": cargar_csv("inventario_limpio.csv"),
        "productos": cargar_csv("productos_limpio.csv"),
        "ventas": cargar_csv("ventas_limpio.csv"),
    }

    return datos


def buscar_columna(df, posibles_nombres):
    columnas = {col.lower().strip(): col for col in df.columns}

    for nombre in posibles_nombres:
        nombre = nombre.lower().strip()
        if nombre in columnas:
            return columnas[nombre]

    return None