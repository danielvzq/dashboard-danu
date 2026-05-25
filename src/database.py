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

def buscar_columna(df, candidates):
    """Buscar en un DataFrame la primera columna cuyo nombre coincida
    exactamente o contenga alguno de los valores de `candidates`.

    Devuelve el nombre original de la columna si se encuentra, o `None`.
    """
    if df is None:
        return None

    try:
        cols = list(df.columns)
    except Exception:
        return None

    # Búsqueda por coincidencia exacta (insensible a mayúsculas)
    for cand in candidates:
        for col in cols:
            if col.lower() == cand.lower():
                return col

    # Búsqueda por coincidencia parcial
    for cand in candidates:
        for col in cols:
            if cand.lower() in col.lower():
                return col

    return None