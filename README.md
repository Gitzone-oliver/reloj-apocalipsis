# Reloj del Apocalipsis · índice diario (no oficial)

Contenido:
- `docs/index.html`  → la página (un solo HTML, sin dependencias)
- `spider.py`        → descarga noticias, las analiza con IA y escribe `data.json`
- `app.py`           → mini servidor Flask (solo para la opción PythonAnywhere)
- `.github/workflows/reloj-diario.yml` → ejecución diaria en GitHub Actions
- `raspberry/`       → instalador para Raspberry Pi
- `MANUAL.md`        → **empieza aquí**: flujo, montaje, mantenimiento

Prueba rápida local (sin IA, con palabras clave):
    pip install -r requirements.txt
    DATA_PATH=docs/data.json python spider.py
    cd docs && python -m http.server 8000     # abre http://localhost:8000
