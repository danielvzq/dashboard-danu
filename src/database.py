# src/database.py

def obtener_datos_inventario():
    """
    Simula una consulta a una base de datos (Backend).
    Retorna la lista de productos y su estado actual.
    """
    # Nota para el futuro: Aquí se inicializarán las credenciales 
    # y se hará la consulta real a la base de datos (ej. firestore.client())
    
    catalogo = [
        {"SKU": "ZAP-001", "Producto": "Tenis Deportivos Runner Pro", "Categoría": "Calzado", "Stock Actual": 250, "Estado": "Overstock"},
        {"SKU": "RAQ-042", "Producto": "Raqueta de Tenis Máster V2", "Categoría": "Equipamiento", "Stock Actual": 80, "Estado": "Overstock"},
        {"SKU": "SUD-089", "Producto": "Sudadera Entrenamiento", "Categoría": "Ropa Deportiva", "Stock Actual": 15, "Estado": "Stock Bajo"},
        {"SKU": "BAL-012", "Producto": "Paquete Pelotas Tenis (x3)", "Categoría": "Equipamiento", "Stock Actual": 500, "Estado": "Saludable"},
        {"SKU": "GOP-005", "Producto": "Gorra Ajustable", "Categoría": "Ropa Deportiva", "Stock Actual": 45, "Estado": "Saludable"},
    ]
    
    return catalogo


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