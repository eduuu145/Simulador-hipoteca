import math
import datetime as dt
from io import BytesIO

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# ===== Configuración de página y branding =====
st.set_page_config(page_title="Simulador Hipotecario", page_icon="🏠", layout="wide")

# Branding mínimo (ajusta colores y nombre comercial)
BRAND_NAME = "LF"  # <-- cambia por tu marca (p.ej., "HabitaLink")
PRIMARY_COLOR = "#1b3b2f"    # oliva oscuro

st.markdown(f"""
<style>
:root {{
  --brand: {PRIMARY_COLOR};
}}
h1, h2, h3, h4, h5 {{ color: var(--brand); }}
.stButton>button {{ border-radius: 10px; }}
</style>
""", unsafe_allow_html=True)

st.title(f"🏠 Simulador Hipotecario · {BRAND_NAME}")
st.caption("Calcula cuota mensual, calendario de amortización, exporta CSV y PDF.")

# Logo si existe (colócalo como logo.png en la misma carpeta)
import os
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", use_column_width=True)

# ===== Sidebar (Entradas) =====
st.sidebar.header("Parámetros de la operación")
valor_vivienda = st.sidebar.number_input("Valor de la vivienda (€)", min_value=1000, value=250000, step=1000)
aporte_pct = st.sidebar.slider("Aporte/Entrada (%)", min_value=0, max_value=80, value=20)
interes_anual = st.sidebar.number_input("Tipo de interés anual (%)", min_value=0.0, value=3.25, step=0.05, format="%.2f")
plazo_anios = st.sidebar.slider("Plazo (años)", min_value=1, max_value=40, value=30)
mes_inicio = st.sidebar.date_input("Fecha de inicio", value=dt.date.today())

# Gastos opcionales
st.sidebar.header("Gastos opcionales (mensuales)")
seguro_hogar = st.sidebar.number_input("Seguro de hogar (€ / mes)", min_value=0.0, value=0.0, step=5.0)
seguro_vida = st.sidebar.number_input("Seguro de vida (€ / mes)", min_value=0.0, value=0.0, step=5.0)
ibi_mensual = st.sidebar.number_input("IBI/Comunidad (€ / mes)", min_value=0.0, value=0.0, step=5.0)

# ===== Cálculos base =====
aporte = valor_vivienda * (aporte_pct / 100)
principal = max(valor_vivienda - aporte, 0)
n = plazo_anios * 12
r = (interes_anual / 100) / 12  # tipo mensual

def cuota_mensual(L, r, n):
    if n <= 0:
        return 0.0
    if r == 0:
        return L / n
    return L * r / (1 - (1 + r) ** (-n))

cuota = cuota_mensual(principal, r, n)
gastos_fijos = seguro_hogar + seguro_vida + ibi_mensual
cuota_total = cuota + gastos_fijos

# ===== Calendario de amortización =====
def tabla_amortizacion(L, r, n, start_date):
    saldo = L
    rows = []
    fecha = dt.date(start_date.year, start_date.month, 1)
    for i in range(1, n + 1):
        if r == 0:
            interes = 0.0
            amort = L / n
        else:
            interes = saldo * r
            amort = cuota - interes
        if amort > saldo:
            amort = saldo
            pago = interes + amort
        else:
            pago = cuota
        saldo = max(saldo - amort, 0.0)

        rows.append({
            "Mes": i,
            "Fecha": fecha + pd.DateOffset(months=i-1),
            "Pago": round(pago, 2),
            "Interés": round(interes, 2),
            "Amortización": round(amort, 2),
            "Saldo": round(saldo, 2)
        })
    return pd.DataFrame(rows)

df = tabla_amortizacion(principal, r, n, mes_inicio)
total_intereses = float(df["Interés"].sum())
total_pagado = float(df["Pago"].sum())
fecha_ultimo_pago = pd.to_datetime(df["Fecha"].iloc[-1]).date() if len(df) else None

# ===== Resumen =====
st.subheader("Resumen")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Importe de hipoteca", f"{principal:,.0f} €")
c2.metric("Cuota mensual (solo préstamo)", f"{cuota:,.2f} €")
c3.metric("Gastos mensuales añadidos", f"{gastos_fijos:,.2f} €")
c4.metric("Cuota total estimada", f"{cuota_total:,.2f} €")

c5, c6, c7 = st.columns(3)
c5.metric("Intereses totales", f"{total_intereses:,.0f} €")
c6.metric("Total pagado (solo préstamo)", f"{total_pagado:,.0f} €")
c7.metric("Último pago", fecha_ultimo_pago.strftime("%d/%m/%Y") if fecha_ultimo_pago else "-")

st.divider()

# ===== Gráficos =====
left, right = st.columns(2)

with left:
    st.markdown("**Evolución del saldo**")
    fig1, ax1 = plt.subplots()
    ax1.plot(df["Fecha"], df["Saldo"])
    ax1.set_xlabel("Fecha")
    ax1.set_ylabel("Saldo pendiente (€)")
    ax1.grid(True, alpha=0.3)
    st.pyplot(fig1, clear_figure=True)

with right:
    st.markdown("**Desglose pago mensual (primer año)**")
    df_12 = df.head(min(12, len(df))).copy()
    fig2, ax2 = plt.subplots()
    ax2.stackplot(df_12["Fecha"], df_12["Interés"], df_12["Amortización"], labels=["Interés", "Amortización"])
    ax2.set_xlabel("Fecha")
    ax2.set_ylabel("€")
    ax2.legend(loc="upper right")
    ax2.grid(True, alpha=0.3)
    st.pyplot(fig2, clear_figure=True)

st.divider()

# ===== Tabla y descargas =====
st.markdown("### Calendario de amortización")
st.dataframe(df, use_container_width=True)

# Descargar CSV completo
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="💾 Descargar CSV",
    data=csv,
    file_name="amortizacion_hipoteca.csv",
    mime="text/csv"
)

# ===== Exportar PDF (resumen) =====
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

def generar_pdf_resumen():
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 2*cm
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.105, 0.231, 0.184)  # aproximación al PRIMARY_COLOR
    c.drawString(2*cm, y, f"Simulador Hipotecario · {BRAND_NAME}")

    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0, 0, 0)
    y -= 1.2*cm
    c.drawString(2*cm, y, f"Valor vivienda: {valor_vivienda:,.0f} €   |   Aporte: {aporte_pct}%   |   Principal: {principal:,.0f} €")
    y -= 0.6*cm
    c.drawString(2*cm, y, f"Interés anual: {interes_anual:.2f}%   |   Plazo: {plazo_anios} años   |   Inicio: {mes_inicio.strftime('%d/%m/%Y')}")
    y -= 0.6*cm
    c.drawString(2*cm, y, f"Cuota préstamo: {cuota:,.2f} €   |   Gastos añadidos: {gastos_fijos:,.2f} €   |   Cuota total: {cuota_total:,.2f} €")
    y -= 0.6*cm
    c.drawString(2*cm, y, f"Intereses totales: {total_intereses:,.0f} €   |   Total pagado (préstamo): {total_pagado:,.0f} €")

    # Encabezado tabla (primeros 12 meses)
    y -= 1.2*cm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, y, "Mes")
    c.drawString(3.5*cm, y, "Fecha")
    c.drawString(6*cm, y, "Pago")
    c.drawString(8*cm, y, "Interés")
    c.drawString(10*cm, y, "Amortiz.")
    c.drawString(12*cm, y, "Saldo")
    c.line(2*cm, y-0.1*cm, width-2*cm, y-0.1*cm)

    c.setFont("Helvetica", 9)
    y -= 0.5*cm
    for _, row in df.head(12).iterrows():
        if y < 2*cm:
            c.showPage()
            y = height - 2*cm
            c.setFont("Helvetica-Bold", 10)
            c.drawString(2*cm, y, "Mes")
            c.drawString(3.5*cm, y, "Fecha")
            c.drawString(6*cm, y, "Pago")
            c.drawString(8*cm, y, "Interés")
            c.drawString(10*cm, y, "Amortiz.")
            c.drawString(12*cm, y, "Saldo")
            c.line(2*cm, y-0.1*cm, width-2*cm, y-0.1*cm)
            c.setFont("Helvetica", 9)
            y -= 0.5*cm
        c.drawString(2*cm, y, f"{int(row['Mes'])}")
        c.drawString(3.5*cm, y, f"{pd.to_datetime(row['Fecha']).date().strftime('%d/%m/%Y')}")
        c.drawRightString(7.8*cm, y, f"{row['Pago']:,.2f} €")
        c.drawRightString(9.8*cm, y, f"{row['Interés']:,.2f} €")
        c.drawRightString(12*cm, y, f"{row['Amortización']:,.2f} €")
        c.drawRightString(width-2*cm, y, f"{row['Saldo']:,.2f} €")
        y -= 0.5*cm

    # Nota legal
    y -= 0.8*cm
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(2*cm, y, "Documento orientativo. No sustituye la oferta vinculante de una entidad.")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

pdf_buffer = generar_pdf_resumen()
st.download_button(
    label="📄 Descargar PDF resumen",
    data=pdf_buffer,
    file_name="resumen_hipoteca.pdf",
    mime="application/pdf"
)

st.info(
    "Este simulador es orientativo y no sustituye la oferta vinculante de una entidad. "
    "Ajusta tipos, plazos y gastos para comparar escenarios."
)
