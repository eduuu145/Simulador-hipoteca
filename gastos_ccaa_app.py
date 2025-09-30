import pandas as pd
import streamlit as st

st.set_page_config(page_title="Gastos de Compra por CCAA", page_icon="📑", layout="wide")

BRAND_NAME = "Loanpath"   # cámbialo por tu marca
PRIMARY_COLOR = "#1b3b2f"

st.markdown(f"""
<style>
:root {{ --brand: {PRIMARY_COLOR}; }}
h1, h2, h3 {{ color: var(--brand); }}
.stButton>button {{ border-radius: 10px; }}
</style>
""", unsafe_allow_html=True)

st.title(f"📑 Gastos de Compra por CCAA · {BRAND_NAME}")
st.caption("Estimación orientativa de impuestos y gastos por Comunidad Autónoma. Las tasas se pueden editar.")

st.sidebar.header("Parámetros de la operación")
precio = st.sidebar.number_input("Precio de la vivienda (€)", min_value=10000, value=250000, step=1000)
obra_nueva = st.sidebar.selectbox("Tipo de vivienda", ["Segunda mano (ITP)", "Obra nueva (IVA + AJD)"])
hipoteca = st.sidebar.number_input("Importe de hipoteca (€) [opcional]", min_value=0, value=200000, step=1000)

st.sidebar.header("Gastos fijos estimados (ajustables)")
notaria = st.sidebar.number_input("Notaría (€)", min_value=0, value=800, step=50)
registro = st.sidebar.number_input("Registro (€)", min_value=0, value=400, step=25)
gestoria = st.sidebar.number_input("Gestoría (€)", min_value=0, value=350, step=25)
tasacion = st.sidebar.number_input("Tasación (€)", min_value=0, value=350, step=25)

st.sidebar.header("IVA (solo obra nueva)")
iva_pct = st.sidebar.number_input("IVA %", min_value=0.0, value=10.0, step=0.5, format="%.1f")

st.markdown("#### Tasas por CCAA (edítalas si conoces las vigentes)")
uploaded = st.file_uploader("Cargar CSV propio (CCAA, ITP_estimado_%, AJD_estimado_%)", type=["csv"], accept_multiple_files=False)
if "tasas" not in st.session_state:
    st.session_state["tasas"] = None

if uploaded is not None:
    tasas = pd.read_csv(uploaded)
    st.session_state["tasas"] = tasas
elif st.session_state["tasas"] is None:
    tasas = pd.read_csv("ccaa_tasas.csv")
    st.session_state["tasas"] = tasas.copy()
else:
    tasas = st.session_state["tasas"]

edited = st.data_editor(tasas, num_rows="dynamic", use_container_width=True)
st.session_state["tasas"] = edited

st.download_button("⬇️ Descargar CSV actualizado", data=edited.to_csv(index=False).encode("utf-8"),
                   file_name="ccaa_tasas_actualizado.csv", mime="text/csv")

ccaa = st.selectbox("Selecciona Comunidad Autónoma", edited["CCAA"].tolist())

itp_pct = float(edited.loc[edited["CCAA"] == ccaa, "ITP_estimado_%"].iloc[0])
ajd_pct = float(edited.loc[edited["CCAA"] == ccaa, "AJD_estimado_%"].iloc[0])

st.divider()
st.subheader("Resultado")

if obra_nueva.startswith("Obra nueva"):
    iva = precio * (iva_pct / 100.0)
    ajd = precio * (ajd_pct / 100.0)
    impuestos = iva + ajd
    detalle_imp = {
        "IVA": iva,
        f"AJD {ajd_pct:.2f}%": ajd
    }
else:
    itp = precio * (itp_pct / 100.0)
    impuestos = itp
    detalle_imp = {f"ITP {itp_pct:.2f}%": itp}

gastos = notaria + registro + gestoria + tasacion
total = impuestos + gastos

c1, c2, c3 = st.columns(3)
c1.metric("Impuestos estimados", f"{impuestos:,.0f} €")
c2.metric("Gastos (notaría/registro/gestoría/tasación)", f"{gastos:,.0f} €")
c3.metric("Total aprox. a desembolsar", f"{total:,.0f} €")

st.markdown("**Detalle de impuestos**")
for k, v in detalle_imp.items():
    st.write(f"- {k}: **{v:,.0f} €**")

st.info("Valores **orientativos**. Revisa ITP/AJD vigentes en tu CCAA y posibles tipos reducidos (jóvenes, familia numerosa, VPO, discapacidad, etc.).")