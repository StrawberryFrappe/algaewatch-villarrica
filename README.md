# AlgaeWatch Villarrica

Prototipo TRL2 de monitoreo y predicción de floraciones de algas en el Lago Villarrica.
El entregable central es un modelo de Gradient Boosting que predice el riesgo de floración
a 7 días. El dashboard y la API exponen ese modelo; no lo reemplazan.

Ver `design_handoff_algaewatch_villarrica/README.md` para la especificación de diseño
(fuente de verdad del frontend: contrato de API, 4 vistas, tokens visuales).

## Estructura

```
data/
  raw/            # descargas crudas por fuente (sentinel2, era5, insitu) — no versionadas
  processed/       # dataset unificado por fecha/estación, listo para entrenar
src/
  features/        # cálculo del FAI (Sentinel-2) y variables derivadas (ERA5-Land) — SOLO feature engineering, sin modelo
  model/           # entrenamiento, validación e inferencia del Gradient Boosting — SOLO el modelo, consume features ya calculadas
backend/
  app/             # FastAPI: expone /stations, /observations, /risk, /forecast, /model/metrics
frontend/          # React + Mapbox GL JS, fiel a design_handoff_algaewatch_villarrica
notebooks/         # EDA
```

Separación estricta: `src/features` nunca importa `src/model`, y viceversa.
El backend consume `src/model` para inferencia y sirve datos mock hasta que el
pipeline de datos reales esté listo (ver plan de trabajo en la conversación con el equipo).

## Variables de entorno

Ver `.env.example` para la lista completa. Copiar como `.env` **un nivel
arriba de este repo** (nunca dentro) — así el archivo con credenciales reales
queda estructuralmente fuera del árbol de git, no solo ignorado.

- `CDS_TOKEN` — ERA5-Land vía CDS API (`cdsapi`)
- `CDSE_CLIENT_ID`, `CDSE_CLIENT_SECRET` — Sentinel-2 vía Copernicus Data Space Ecosystem (`sentinelhub-py`)
- `GEMINI_API_KEY` — genera el texto del panel "Análisis IA" en el servidor (`backend/app/gemini.py`)

El código busca `.env` con `python-dotenv` `find_dotenv()`, que sube directorios
automáticamente — no hay rutas absolutas hardcodeadas, para que corra igual en
un servidor Linux (Ciencia2030).

## Pipeline de datos reales

```
src/features/
  config.py          # credenciales CDSE/CDS desde .env, bbox del lago
  stations.py        # catálogo canónico de las 4 estaciones (real, coords placeholder pendiente SNIA)
  fai.py             # FAI real desde Sentinel-2 L2A (CDSE / sentinelhub-py) — fórmula, sin entrenamiento
  era5.py            # ERA5-Land vía CDS API (cdsapi) — temp/viento/precipitación
  insitu.py          # STUB explícito — pendiente CSVs de SNIA
  build_dataset.py   # arma la tabla unificada: FAI histórico + ERA5 + in-situ -> target a 7 días
src/model/
  train.py           # Gradient Boosting (clasificación bloom_7d + regresión FAI), CV 5-fold + hold-out temporal
  infer.py           # carga artefactos entrenados y predice para el backend
scripts/
  collect_fai.py       # recolecta FAI real para un rango de fechas -> data/processed/fai_series_raw.csv
  collect_fai_grid.py  # grilla real (~1.800 pts) de la última pasada despejada -> data/processed/fai_grid_latest.csv
  train_model.py       # arma el dataset y entrena -> src/model/artifacts/
```

**Estado real verificado** (04-sep-2026) — **sin mocks, todo el backend corre sobre datos reales**:
- ✅ Autenticación CDSE (Sentinel-2) funciona con las credenciales del `.env`.
- ✅ `fai.py` calcula FAI real desde escenas Sentinel-2 L2A en vivo, con máscara de agua vía banda SCL.
- ✅ Licencia de CDS aceptada — `era5.py` queda desbloqueado, pendiente de correr un backfill real (ver "Para escalar a producción" abajo).
- ✅ **Bug real encontrado y corregido**: el punto placeholder de la estación "sur" caía siempre en tierra (radio de búsqueda insuficiente en `at_latlon`), dejando esa columna 100% vacía. Corregido el radio + agregado un *fallback* al promedio del lago cuando un punto no encuentra agua cercana (`backend/app/data_source.py::get_fai`).
- ✅ **Corrida real completa de punta a punta**: `collect_fai.py` recolectó FAI real para 56 fechas despejadas (sep-2025 a sep-2026, cloud cover ≤15%); `train_model.py` armó 1.356 filas (FAI histórico forward-filled + calibración de umbral de bloom por mezcla gaussiana bimodal: **0,0259**, no copiado de literatura) y entrenó Gradient Boosting con CV 5-fold + hold-out temporal. Métricas reales: precisión 0,84 · recall 0,47 · F1 0,60 · AUC-ROC 0,90 · MAE FAI 0,009 (ver `src/model/artifacts/metrics.json`).
- ✅ **Backend conectado al modelo real** (`backend/app/data_source.py`) — `mock_data.py` fue eliminado. `/risk` lee el FAI real y lo mapea a un puntaje 0-100 con una función determinística (no el modelo — es la lectura del presente); `/forecast` sí usa el modelo real para la predicción a 7 días.
- ✅ **Heatmap real**: `GET /risk/grid` sirve ~1.800 puntos muestreados directamente del raster FAI (no una interpolación entre las 4 estaciones) — ver `fai.py::sample_grid` y `collect_fai_grid.py`.
- ⚠️ **Caveat importante**: el modelo usa **solo FAI histórico** como feature (ERA5 aún no recolectado con backfill; in situ sigue en stub) — sigue siendo un smoke test real del pipeline completo, no un modelo listo para producción.
- ⏳ **In situ**: stub explícito (`insitu.py`) hasta que lleguen los CSVs de SNIA — por eso `/observations` devuelve `null` en temp/pH/oxígeno/viento.

### Para escalar a producción

1. Correr un backfill real de `era5.py` para las mismas fechas de `fai_series_raw.csv` (licencia ya aceptada).
2. Reemplazar `src/features/insitu.py` cuando lleguen los CSVs de SNIA, y actualizar `src/features/stations.py` con las coordenadas reales.
3. Correr `collect_fai.py` sobre un rango histórico más largo (2024–2026) — cada fecha tarda ~10-60s vía Process API, así que un backfill completo debe correr como job de fondo, respetando cuotas de la API.
4. Volver a correr `train_model.py` con el feature set completo (FAI + ERA5 + in-situ) y una muestra mayor.
5. Re-correr `collect_fai_grid.py` periódicamente (~cada 5 días, cadencia de revisita de Sentinel-2) para mantener el heatmap del mapa actualizado.
