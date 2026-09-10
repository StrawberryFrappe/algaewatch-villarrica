# AlgaeWatch Villarrica

Prototipo TRL 2 para monitorear FAI en el Lago Villarrica y evaluar pronósticos
de su cambio a 5–9 días. El proyecto usa Sentinel-2 para FAI, ERA5-Land para
variables meteorológicas y una API FastAPI con frontend React/Leaflet.

> **TRL 2 · resultados no validados en campo.** No hay mediciones in situ
> disponibles todavía. Las salidas no deben interpretarse como alertas sanitarias
> ni operacionales.

**¿Primera vez acá? Leé [`SYSTEM_OVERVIEW.es.md`](SYSTEM_OVERVIEW.es.md)**
([English](SYSTEM_OVERVIEW.md)) — explica el sistema entero de cero: el problema,
las cuatro etapas, qué es real y qué es stub, por qué las líneas base son el
núcleo metodológico, el resultado dicho sin vueltas, y cómo correrlo. Está
escrito para alguien que nunca abrió el repo, incluido quien prepare una
presentación.

## Estado comprobado

- Hay 56 pasadas reales de Sentinel-2 entre septiembre de 2025 y agosto de 2026.
- La grilla histórica contiene 98.886 observaciones reales de agua, 1.888 píxeles
  y ninguna fila rellenada hacia adelante.
- El pipeline meteorológico obtiene temperatura, precipitación y viento horarios
  de ERA5-Land y los agrega por día UTC sobre el área del lago.
- El candidato de modelado usa un objetivo continuo: anomalía FAI futura contra
  la línea base causal de cada píxel. El umbral de alerta queda fuera del
  entrenamiento.
- La validación combina ventanas temporales expansivas, embargo por fecha
  objetivo y bloques espaciales 2×2. Toda métrica se compara en las mismas filas
  contra persistencia y climatología.
- El modelo legado que alimenta actualmente el dashboard es solo evidencia de un
  smoke test: usa coordenadas de estaciones no válidas, filas rellenadas y pierde
  contra sus baselines. No es un modelo listo para producción.
- `src/features/insitu.py` sigue siendo un stub hasta recibir los CSV y las
  coordenadas GPS de SNIA; la API devuelve `null` para esas mediciones.

El estado operativo y las limitaciones vigentes están en
`agents/RUN_STATE.md`; la evidencia reproducible, en
`agents/validation/EVIDENCE_INDEX.md`.

## Instalación local

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm --prefix frontend install
```

Las credenciales reales van en un archivo `.env` **un directorio por encima del
repositorio**, nunca dentro del árbol Git. Partir de `.env.example` y definir:

- `CDS_API_URL` y `CDS_TOKEN` para ERA5-Land;
- `CDSE_CLIENT_ID` y `CDSE_CLIENT_SECRET` para Sentinel-2;
- `GEMINI_API_KEY` para el texto opcional del panel de IA.

El proyecto usa `find_dotenv()`, por lo que no necesita rutas absolutas.

## Pipeline reproducible

```bash
# Recolectar las grillas FAI de las 56 fechas conocidas
.venv/bin/python scripts/collect_fai_grid_series.py

# Recolectar ERA5-Land para esas mismas fechas
.venv/bin/python scripts/collect_era5.py

# Construir pares honestos por píxel y entrenar/evaluar el candidato
.venv/bin/python scripts/build_per_pixel_dataset.py
.venv/bin/python scripts/train_per_pixel.py
```

Los datos crudos quedan bajo `data/raw/` y no se versionan. Las tablas procesadas
compactas permiten volver a ejecutar pruebas y evaluación sin credenciales.

## Aplicación

```bash
.venv/bin/uvicorn backend.app.main:app --reload
npm --prefix frontend run dev
```

Se exponen **dos** modelos, y la distinción importa:

| Endpoint | Modelo | ¿Alimenta el mapa? |
|---|---|---|
| `GET /model/metrics` | Gradient Boosting legacy | **Sí** — `/risk` y `/forecast` corren sobre él |
| `GET /model/candidate` | Red cuantílica per-píxel + ERA5 | **No** — `serving: false` en el payload |

El candidato está evaluado y reportado junto a sus líneas base (persistencia y
climatología) con el detalle por fold, pero no maneja ninguna predicción del
dashboard. La vista Modelo lo muestra etiquetado `NO ALIMENTA EL MAPA`. Devuelve
404 si este checkout nunca corrió `scripts/train_per_pixel.py`, y el frontend
simplemente oculta el panel.

La separación es estricta:

- `src/features/` calcula FAI y variables derivadas; no entrena modelos.
- `src/model/` solo consume tablas ya construidas; no llama APIs externas.
- `src/model/per_pixel_infer.py` carga el artefacto entrenado y predice; es la
  contraparte de `per_pixel.py`, que entrena y escribe.
- `backend/app/data_source.py` es el único puente entre la API y el pipeline.

El frontend sigue `design_handoff_algaewatch_villarrica/README.md`, con las
desviaciones aceptadas documentadas en `agents/adrs/`.

## Verificación

```bash
.venv/bin/pytest -q
npm --prefix frontend run build
python agents/harness_doctor.py --root . --strict
python agents/check_translations.py
```

Para evaluar el gate contra el candidato por píxel:

```bash
ALGAEWATCH_DATASET=data/processed/per_pixel_anomaly_dataset.csv \
ALGAEWATCH_METRICS=src/model/artifacts/per_pixel/metrics.json \
.venv/bin/pytest -q tests/test_model_integrity.py
```
