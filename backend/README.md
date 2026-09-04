# Backend (FastAPI)

Sirve el contrato de API que el frontend espera (ver
`../design_handoff_algaewatch_villarrica/README.md`). **Sin datos mock**:
`/risk`, `/forecast` y `/model/metrics` se sirven desde `app/data_source.py`,
que carga el FAI real recolectado (`../data/processed/fai_series_raw.csv`) y
el modelo Gradient Boosting ya entrenado (`../src/model/artifacts/`). El
campo `source` en cada respuesta ahora siempre dice `"model"`.

**Requisito para levantar el backend**: debe existir
`data/processed/fai_series_raw.csv` y `src/model/artifacts/` (correr
`scripts/collect_fai.py` y `scripts/train_model.py` primero — ver el README
de la raíz). Si faltan, `data_source.py` lanza `DataNotReadyError` al
importar el módulo y el servidor no arranca.

**Limitación actual, honesta**: el modelo solo usa FAI histórico como feature
(ERA5-Land e in-situ aún no están wired in — ver el README de la raíz). Por
eso `/observations` devuelve `null` en los campos de temperatura/pH/oxígeno/
viento, y `/risk` refleja mayormente niveles MUY_BAJO (agua clara real en el
período recolectado, no un error).

## Ejecutar

```bash
python3 -m venv .venv          # desde la raíz del proyecto (un nivel arriba)
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m uvicorn backend.app.main:app --reload --port 8000
```

Docs interactivas en `http://localhost:8000/docs`.

## Endpoints

| Endpoint | Descripción |
| --- | --- |
| `GET /stations` | Catálogo de las 4 estaciones IoT |
| `GET /observations?from&to&station` | FAI real por estación/día (in-situ en `null` hasta SNIA) |
| `GET /risk?date` | Riesgo actual por estación, derivado directamente del FAI real (no el modelo — ver más abajo) |
| `GET /risk/grid` | Grilla real de ~1.800 puntos muestreados del raster FAI (última pasada despejada) — heatmap del mapa |
| `GET /forecast?date` | Salida del modelo real: riesgo a 7 días + resumen IA (server-side) |
| `GET /model/metrics` | Métricas reales del último entrenamiento (`src/model/artifacts/metrics.json`) |
| `GET /health` | Liveness check |

## `/risk` vs. `/forecast` — la separación FAI/modelo, en la API

- `/risk` (y `/risk/grid`) leen el FAI real y lo mapean a un puntaje 0-100 con
  una función determinística centrada en el umbral calibrado (`fai_to_risk`
  en `app/data_source.py`) — **no es el modelo**, es una lectura directa del
  presente, tal como especifica el proyecto.
- `/forecast` sí usa el modelo (`src/model/infer.py`) para predecir el riesgo
  a 7 días a partir del FAI histórico (rezagos de 1/3/7 días).

## Notas

- Coordenadas de estaciones en `src/features/stations.py` son aproximadas
  (placeholder dentro del bbox del lago); se reemplazan con las coordenadas
  reales cuando lleguen los CSVs de SNIA.
- `CORS_ORIGINS` (env, coma-separado) controla qué orígenes puede llamar la
  API; por defecto habilita `localhost:5173` y `localhost:3000` (Vite/CRA).

## Panel "Análisis IA" (Gemini)

`GET /forecast` genera `summary` y `recommendation` con **Gemini 2.5 Flash**
(`app/gemini.py`), a partir de los valores YA calculados por el modelo —
Gemini solo redacta, nunca calcula riesgo ni FAI. Requiere `GEMINI_API_KEY`
en el `.env` de la raíz del repo.

Si la key falta, la llamada falla, o la respuesta no tiene el formato
esperado, el endpoint cae automáticamente a un texto plantilla determinista
(nunca rompe `/forecast` por una falla del servicio externo). El campo
`ai_generated` en la respuesta indica cuál de los dos se usó.
