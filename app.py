import streamlit as st

st.set_page_config(
    page_title="RocketData Dashboard",
    page_icon="🚀",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background-color: #050505;
    color: white;
}

[data-testid="stSidebar"] {
    background-color: #111111;
}

.main-card {
    background-color: #080808;
    border: 1px solid #1f1f1f;
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 24px;
}

.chart-card {
    background-color: #000000;
    border: 1px solid #222222;
    border-radius: 16px;
    padding: 18px;
    min-height: 340px;
}

h1, h2, h3 {
    color: white;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🚀 RocketData")
    st.caption("admin123@gmail.com")
    st.markdown("---")
    st.button("🏠 Home", use_container_width=True)
    st.button("📊 Analytics", use_container_width=True)
    st.markdown("<br><br><br><br><br><br><br>", unsafe_allow_html=True)
    st.button("⚙️ Settings", use_container_width=True)

st.title("Dashboard")

st.markdown('<div class="main-card">', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.subheader("El mayor riesgo de inventario se concentra en pocos productos")
    st.write("Aquí va la gráfica 1")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.subheader("Días de inventario promedio por categoría")
    st.write("Aquí va la gráfica 2")
    st.markdown('</div>', unsafe_allow_html=True)

col3, col4 = st.columns(2)

with col3:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.subheader("Stock total vs Unidades vendidas por mes")
    st.write("Aquí va la gráfica 3")
    st.markdown('</div>', unsafe_allow_html=True)

with col4:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.subheader("Distribución de días de inventario")
    st.write("Aquí va la gráfica 4")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)