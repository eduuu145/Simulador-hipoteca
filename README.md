# Simulador Hipotecario (Streamlit)

Calcula cuota mensual, calendario de amortización, intereses totales y permite exportar CSV y PDF.
Incluye secciones de branding básicas (logo y nombre comercial).

## 1) Requisitos locales
- Python 3.9+ instalado
- Instalar dependencias:
  ```bash
  py -m pip install -r requirements.txt
  ```

## 2) Ejecutar en local
```bash
py -m streamlit run app.py
```

## 3) Publicar gratis (Streamlit Community Cloud)
1. Crea un repositorio en GitHub y sube estos archivos: `app.py`, `requirements.txt`, `README.md` (y opcionalmente `logo.png`).
2. Ve a https://share.streamlit.io/ e inicia sesión con GitHub.
3. Elige tu repo, rama principal y el archivo `app.py`. Pulsa **Deploy**.
4. Obtendrás una **URL pública** para compartir con clientes.

## 4) Personalización de marca
- Sustituye `MARCA_NOMBRE` por tu nombre comercial (por ej. *HabitaLink*).
- Añade un `logo.png` en la misma carpeta que `app.py`. Se mostrará automáticamente en la barra lateral si existe.
- Ajusta colores en el bloque CSS del inicio del archivo.

## 5) Generar PDF
- El botón **"📄 Descargar PDF resumen"** genera un PDF con:
  - Parámetros de la operación
  - Cuota, totales e intereses
  - Primeros 12 meses del calendario
- El CSV completo se descarga con el botón **"💾 Descargar CSV"**.

> **Nota**: Este simulador es orientativo y no sustituye la oferta vinculante de una entidad.