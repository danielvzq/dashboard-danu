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