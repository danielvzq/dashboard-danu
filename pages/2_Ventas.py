import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Centro de Ventas", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# ESTILOS CSS
# ==========================================
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1.5rem; }
    h1, h2, h3 { font-weight: 700 !important; color: #1e293b; }

    /* ---- Hero unificado y estricto ---- */
    .hero-section {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 60%, #1e3a8a 100%);
        border-radius: 16px;
        height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .hero-section::before {
        content: ''; position: absolute; top: -60px; right: -60px; width: 240px; height: 240px;
        background: radial-gradient(circle, rgba(37,99,235,0.35) 0%, transparent 70%); border-radius: 50%;
    }
    .hero-section::after {
        content: ''; position: absolute; bottom: -40px; left: -40px; width: 180px; height: 180px;
        background: radial-gradient(circle, rgba(16,185,129,0.20) 0%, transparent 70%); border-radius: 50%;
    }
    .hero-title {
        font-size: 2.4rem !important; font-weight: 800 !important; color: #ffffff !important; margin: 0 0 12px 0 !important; line-height: 1.2; z-index: 1; text-align: center !important;
    }
    .hero-subtitle {
        font-size: 1.05rem; color: #94a3b8; max-width: 650px; line-height: 1.5; z-index: 1; text-align: center;
    }
    .hero-divider {
        width: 60px; height: 3px; background: linear-gradient(90deg, #2563eb, #10b981); border-radius: 2px; margin-top: 18px; z-index: 1;
    }

    /* ---- Títulos de Sección (Blue Theme) ---- */
    .section-title {
        color: #1e3a8a !important;
        border-left: 4px solid #2563eb;
        padding-left: 14px;
        font-size: 1.25rem !important;
        font-weight: 800 !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1.2rem !important;
        background: linear-gradient(90deg, #eff6ff 0%, transparent 100%);
        padding-top: 8px;
        padding-bottom: 8px;
        border-radius: 0 8px 8px 0;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CARGA Y PREPARACIÓN DE DATOS
# ==========================================
@st.cache_data
def cargar_datos():
    df_maestra = pd.read_csv("data/df_Maestra.csv")
    df_maestra["Date"] = pd.to_datetime(df_maestra["Date"])
    df_maestra["Exceso_Porcentual"] = df_maestra["Percentage"] - 100.0
    
    df_maestra["Region"] = df_maestra["Region"].astype(str).str.strip().str.title()
    df_maestra["Category"] = df_maestra["Category"].astype(str).str.strip().str.title()
    df_maestra["Subcategory"] = df_maestra["Subcategory"].astype(str).str.strip().str.title()

    df_ventas = pd.read_csv("data/ventas_limpio.csv")
    df_clientes = pd.read_csv("data/clientes_limpio.csv")
    df_productos = pd.read_csv("data/productos_limpio.csv")

    df_clientes['Segmento_Cliente'] = pd.qcut(
        df_clientes['Average_Ticket'], 
        q=3, 
        labels=['Ticket Bajo', 'Ticket Medio', 'Ticket Alto']
    )

    df_cv = pd.merge(df_ventas, df_clientes, left_on='Client_id', right_on='Client_ID', how='inner')
    df_cv = pd.merge(df_cv, df_productos, on='Product_id', how='left')
    
    df_cv["Region"] = df_cv["Region"].astype(str).str.strip().str.title()
    df_cv["Category"] = df_cv["Category"].astype(str).str.strip().str.title()

    return df_maestra, df_cv

try:
    df_base, df_cv = cargar_datos()
except FileNotFoundError as e:
    st.error("Error al cargar los archivos CSV. Asegúrate de que 'df_Maestra.csv', 'ventas_limpio.csv', 'clientes_limpio.csv' y 'productos_limpio.csv' estén dentro de la carpeta 'data/'.")
    st.stop()

# ==========================================
# VISTA PRINCIPAL
# ==========================================
st.markdown("""
<div class="hero-section">
    <h1 class="hero-title">Centro de Ventas y Demanda</h1>
    <div class="hero-subtitle">
        Analiza los productos motores del negocio, cruza ingresos con sobrestock y 
        descubre el comportamiento real de tus segmentos de clientes.
    </div>
    <div class="hero-divider"></div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### Filtros de Análisis")
    
    cat_options = ["Todas las Categorías"] + sorted(df_base["Category"].unique().tolist())
    categoria_sel = st.selectbox("Categoría", cat_options)
    
    df_filtrado_maestra = df_base.copy()
    df_filtrado_cv = df_cv.copy()

    if categoria_sel != "Todas las Categorías":
        df_filtrado_maestra = df_filtrado_maestra[df_filtrado_maestra["Category"] == categoria_sel]
        df_filtrado_cv = df_filtrado_cv[df_filtrado_cv["Category"] == categoria_sel]

    sub_options = ["Todas las Subcategorías"] + sorted(df_filtrado_maestra["Subcategory"].unique().tolist())
    subcategoria_sel = st.selectbox("Subcategoría", sub_options)
    
    if subcategoria_sel != "Todas las Subcategorías":
        df_filtrado_maestra = df_filtrado_maestra[df_filtrado_maestra["Subcategory"] == subcategoria_sel]
        df_filtrado_cv = df_filtrado_cv[df_filtrado_cv["Subcategory"] == subcategoria_sel]

    st.divider()
    st.markdown("### Configuración de Tablas")
    top_n = st.slider("Cantidad de productos (Top N):", min_value=1, max_value=50, value=10, step=1)

# --- KPI CARDS ---
col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

kpi_style = "background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); border: 1px solid #bfdbfe; padding: 20px; border-radius: 12px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.02); height: 160px; display: flex; flex-direction: column; justify-content: space-between; align-items: center;"

with col_kpi1:
    revenue_total = df_filtrado_maestra["Sales_amount"].sum()
    st.markdown(f"""
    <div style="{kpi_style}">
        <div style="font-size: 0.85rem; font-weight: 700; color: #1d4ed8; text-transform: uppercase; letter-spacing: 1px;">Revenue Generado</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #0f172a;">${revenue_total:,.2f}</div>
        <div style="font-size: 0.8rem; color: #64748b;">Ingresos totales en selección</div>
    </div>
    """, unsafe_allow_html=True)
    
with col_kpi2:
    unidades_vendidas = df_filtrado_maestra["Units_sold"].sum()
    st.markdown(f"""
    <div style="{kpi_style}">
        <div style="font-size: 0.85rem; font-weight: 700; color: #1d4ed8; text-transform: uppercase; letter-spacing: 1px;">Volumen Movido</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: #0f172a;">{unidades_vendidas:,.0f} uds</div>
        <div style="font-size: 0.8rem; color: #64748b;">Total de unidades despachadas</div>
    </div>
    """, unsafe_allow_html=True)
    
with col_kpi3:
    if not df_filtrado_maestra.empty:
        top_product = df_filtrado_maestra.groupby("Product_name")["Sales_amount"].sum().idxmax()
    else:
        top_product = "N/A"
    st.markdown(f"""
    <div style="{kpi_style}">
        <div style="font-size: 0.85rem; font-weight: 700; color: #1d4ed8; text-transform: uppercase; letter-spacing: 1px;">Producto Estrella</div>
        <div style="font-size: 1.2rem; font-weight: 800; color: #0f172a; line-height: 1.2; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">{top_product}</div>
        <div style="font-size: 0.8rem; color: #64748b;">Mayor generador de ingresos</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ==========================================
# 1. MATRIZ: REVENUE VS SOBRESTOCK
# ==========================================
st.markdown('<div class="section-title">Subcategorías que mueven el negocio (Ingresos vs Sobrestock)</div>', unsafe_allow_html=True)

# CAMBIO AQUI: Agrupando por Subcategory en lugar de Product_name
df_matrix = df_filtrado_maestra.groupby("Subcategory").agg(
    Revenue=("Sales_amount", "sum"),
    Exceso=("Exceso_Porcentual", "mean"),
    Stock_Total=("Stock", "sum"),
    Category=("Category", "first")
).reset_index()

df_matrix = df_matrix[(df_matrix["Revenue"] > 0) | (df_matrix["Exceso"] > 0)]

# CAMBIO AQUI: hover_name apunta a Subcategory y size_max aumentado a 45
fig_scatter = px.scatter(
    df_matrix, x="Revenue", y="Exceso", size="Stock_Total", color="Category", hover_name="Subcategory",
    size_max=45, labels={"Revenue": "Ingresos Generados ($)", "Exceso": "Exceso de Inventario (%)"}
)

if not df_matrix.empty:
    fig_scatter.add_vline(x=df_matrix["Revenue"].median(), line_width=1, line_dash="dash", line_color="#94a3b8", annotation_text="Mediana de Ingresos")
    fig_scatter.add_hline(y=0, line_width=2, line_color="#10b981")

fig_scatter.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=400, plot_bgcolor="rgba(248, 250, 252, 0.5)")
st.plotly_chart(fig_scatter, use_container_width=True)

# ==========================================
# 2. COMPORTAMIENTO POR SEGMENTO DE CLIENTE
# ==========================================
st.write("")
col_c1, col_c2 = st.columns(2)

with col_c1:
    st.markdown('<div class="section-title">Categorías por Perfil de Comprador</div>', unsafe_allow_html=True)
    if not df_filtrado_cv.empty:
        df_perfiles = df_filtrado_cv.groupby(["Segmento_Cliente", "Category"], observed=False)["Sales_amount"].sum().reset_index()
        
        fig_bar = px.bar(
            df_perfiles, x="Segmento_Cliente", y="Sales_amount", color="Category", barmode="group",
            labels={"Sales_amount": "Ventas ($)", "Segmento_Cliente": "Segmento"},
            color_discrete_sequence=px.colors.qualitative.Set2 
        )
        fig_bar.update_layout(margin=dict(t=10, l=10, r=10, b=10), height=380, plot_bgcolor="rgba(0,0,0,0)", legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1))
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Sin datos de clientes para estos filtros.")

with col_c2:
    st.markdown('<div class="section-title">Concentración Geográfica por Segmento</div>', unsafe_allow_html=True)
    if not df_filtrado_cv.empty:
        df_geo = df_filtrado_cv.groupby(["Region", "Segmento_Cliente"], observed=False)["Sales_amount"].sum().reset_index()
        
        orden_regiones = df_geo.groupby("Region")["Sales_amount"].sum().sort_values(ascending=True).index
        
        colores_segmento = {
            "Ticket Bajo": "#3b82f6", 
            "Ticket Medio": "#10b981",
            "Ticket Alto": "#f59e0b"  
        }
        
        fig_geo = px.bar(
            df_geo, 
            x="Sales_amount", 
            y="Region", 
            color="Segmento_Cliente", 
            orientation="h",
            barmode="stack",
            labels={"Sales_amount": "Ventas ($)", "Region": "", "Segmento_Cliente": "Segmento"},
            color_discrete_map=colores_segmento
        )
        
        fig_geo.update_layout(
            margin=dict(t=10, l=10, r=10, b=10), 
            height=380, 
            plot_bgcolor="rgba(0,0,0,0)", 
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
            yaxis=dict(categoryorder="array", categoryarray=orden_regiones)
        )
        st.plotly_chart(fig_geo, use_container_width=True)
    else:
        st.info("Sin datos geográficos para graficar.")

# ==========================================
# 3. TENDENCIA DE VENTAS POR SUBCATEGORÍA
# ==========================================
st.write("")
st.markdown('<div class="section-title">Evolución Anual de Subcategorías</div>', unsafe_allow_html=True)

if not df_filtrado_maestra.empty:
    df_tendencia = df_filtrado_maestra.set_index("Date").groupby([pd.Grouper(freq="ME"), "Subcategory"])["Sales_amount"].sum().reset_index()
    
    fig_line = px.line(
        df_tendencia, x="Date", y="Sales_amount", color="Subcategory", markers=True,
        labels={"Date": "Mes", "Sales_amount": "Ingresos Mensuales ($)"}
    )
    
    fig_line.update_traces(hovertemplate="<b>%{data.name}</b><extra></extra>")
    
    fig_line.update_layout(
        margin=dict(t=10, l=10, r=10, b=10), height=400, plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="#e2e8f0"), xaxis=dict(gridcolor="#e2e8f0", title="", tickformat="%b %Y"), 
        hovermode="closest"
    )
    st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Sin datos para trazar la tendencia temporal.")