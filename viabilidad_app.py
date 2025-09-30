import math
from io import BytesIO
import datetime as dt

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# ========= Configuración y branding =========
st.set_page_config(page_title="Calculadora de Viabilidad Hipotecaria", page_icon="✅", layout="wide")

BRAND_NAME = "Loanpath"   # cámbialo por tu marca
PRIMARY_COLOR = "#1b3b2f"

st.markdown(f"""
<style>
:root {{ --brand: {PRIMARY_COLOR}; }}
h1, h2, h3 {{ color: var(--brand); }}
.stButton>button {{ border-radius: 10px; }}
</style>
""", unsafe_allow_html=True)

st.title(f"✅ Calculadora de Viabilidad Hipotecaria · {BRAND_NAME}")
st.caption("Estima la cuota máxima razonable y el importe de hipoteca que podrías obtener según tus ingresos y deudas.")

# ========= Entradas =========
st.sidebar.header("Datos financieros")
ingresos = st.sidebar.number_input("Ingresos NETOS mensuales (€)", min_value=0.0, step=100.0, value=2500.0)
gastos_fijos = st.sidebar.number_input("Gastos fijos mensuales (no deudas) (€)", min_value=0.0, step=50.0, value=600.0)
deudas_mensuales = st.sidebar.number_input("Pagos mensuales por deudas (préstamos, tarjetas, etc.) (€)", min_value=0.0, step=50.0, value=200.0)

st.sidebar.header("Hipoteca objetivo")
ratio_esfuerzo = st.sidebar.slider("Ratio de esfuerzo sobre ingresos (%)", min_value=20, max_value=45, value=35, step=1)
interes_anual = st.sidebar.number_input("Tipo de interés anual (%)", min_value=0.0, value=3.25, step=0.05, format="%.2f")
plazo_anios = st.sidebar.slider("Plazo (años)", min_value=1, max_value=40, value=30)
entrada_pct = st.sidebar.slider("Ahorro/Entrada (%)", min_value=0, max_value=80, value=20)

stress = st.sidebar.checkbox("Añadir prueba de estrés (+2% interés)", value=True)

# ========= Cálculos =========
def cuota_to_principal(cuota, r, n):
    # Inversa de la anualidad: L = P * (1 - (1+r)^-n) / r
    if n <= 0: return 0.0
    if r == 0: return cuota * n
    return cuota * (1 - (1 + r) ** (-n)) / r

def principal_to_cuota(L, r, n):
    if n <= 0: return 0.0
    if r == 0: return L / n
    return L * r / (1 - (1 + r) ** (-n))

n = plazo_anios * 12
r = (interes_anual / 100) / 12

# Ratio de esfuerzo permitido
cuota_max_por_ratio = ingresos * (ratio_esfuerzo / 100.0)

# Cuota disponible tras deudas y gastos fijos opcionales
cuota_max_real = max(cuota_max_por_ratio - deudas_mensuales, 0.0)

# Sugerencia conservadora (restar también parte de gastos no deuda)
cuota_sugerida = max(cuota_max_real - max(gastos_fijos * 0.25, 0), 0.0)

principal_max = cuota_to_principal(cuota_max_real, r, n)
principal_sugerido = cuota_to_principal(cuota_sugerida, r, n)

# Precio de vivienda estimado según entrada
precio_max = principal_max / (1 - entrada_pct/100) if (1 - entrada_pct/100) > 0 else principal_max
precio_sugerido = principal_sugerido / (1 - entrada_pct/100) if (1 - entrada_pct/100) > 0 else principal_sugerido

# Stress test
if stress:
    r_stress = ((interes_anual + 2.0) / 100) / 12
    cuota_stress = principal_to_cuota(principal_sugerido, r_stress, n)
else:
    cuota_stress = None

# ========= Salida/Resumen =========
st.subheader("Resumen de viabilidad")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Ingresos netos", f"{ingresos:,.0f} €")
c2.metric("Deudas mensuales", f"{deudas_mensuales:,.0f} €")
c3.metric("Cuota máxima por ratio", f"{cuota_max_por_ratio:,.0f} €")
c4.metric("Cuota disponible (tras deudas)", f"{cuota_max_real:,.0f} €")

c5, c6, c7 = st.columns(3)
c5.metric("Cuota sugerida", f"{cuota_sugerida:,.0f} €")
c6.metric("Hipoteca sugerida", f"{principal_sugerido:,.0f} €")
c7.metric("Precio vivienda sugerido", f"{precio_sugerido:,.0f} €")

if stress and cuota_stress is not None:
    st.info(f"🧪 **Prueba de estrés** (+2% interés): la cuota subiría a **{cuota_stress:,.0f} €**.")

# ========= Gráficos =========
st.divider()
st.markdown("### Visualización")

# Curva de cuota vs. interés para el principal sugerido
intereses = np.linspace(max(interes_anual-2, 0.1), interes_anual+3, 25)
cuotas = [principal_to_cuota(principal_sugerido, (i/100)/12, n) for i in intereses]

fig, ax = plt.subplots()
ax.plot(intereses, cuotas)
ax.set_xlabel("Interés anual (%)")
ax.set_ylabel("Cuota (€)")
ax.set_title("Evolución de la cuota según interés (principal sugerido)")
ax.grid(True, alpha=0.3)
st.pyplot(fig, clear_figure=True)

# ========= Exportables =========
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

def pdf_resumen():
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    y = h - 2*cm

    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.105, 0.231, 0.184)
    c.drawString(2*cm, y, f"Viabilidad Hipotecaria · {BRAND_NAME}")
    c.setFillColorRGB(0,0,0)
    c.setFont("Helvetica", 10)

    y -= 1.0*cm; c.drawString(2*cm, y, f"Ingresos: {ingresos:,.0f} €  |  Deudas: {deudas_mensuales:,.0f} €  |  Gastos: {gastos_fijos:,.0f} €")
    y -= 0.6*cm; c.drawString(2*cm, y, f"Ratio esfuerzo: {ratio_esfuerzo}%  |  Interés: {interes_anual:.2f}%  |  Plazo: {plazo_anios} años")
    y -= 0.6*cm; c.drawString(2*cm, y, f"Cuota máx. por ratio: {cuota_max_por_ratio:,.0f} €  |  Cuota disponible: {cuota_max_real:,.0f} €")
    y -= 0.6*cm; c.drawString(2*cm, y, f"Cuota sugerida: {cuota_sugerida:,.0f} €  |  Hipoteca sugerida: {principal_sugerido:,.0f} €")
    y -= 0.6*cm; c.drawString(2*cm, y, f"Precio vivienda sugerido (con {entrada_pct}% entrada): {precio_sugerido:,.0f} €")
    if stress and cuota_stress is not None:
        y -= 0.6*cm; c.drawString(2*cm, y, f"Prueba de estrés (+2%): cuota ≈ {cuota_stress:,.0f} €")

    y -= 1.0*cm
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(2*cm, y, "Documento orientativo. No sustituye evaluación de riesgo ni oferta vinculante.")

    c.showPage(); c.save(); buf.seek(0)
    return buf

st.download_button("📄 Descargar PDF resumen", data=pdf_resumen(), file_name="viabilidad_hipotecaria.pdf", mime="application/pdf")