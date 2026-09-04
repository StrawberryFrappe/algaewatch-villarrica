# Frontend (React + Vite)

Recrea las 4 vistas del handoff (`../design_handoff_algaewatch_villarrica`)
consumiendo el backend FastAPI (`../backend`).

**Mapa**: en vez de Mapbox (requiere token de pago) se usa **Leaflet +
OpenStreetMap/Esri**, 100% gratis y sin cuenta:
- Base: Esri World Imagery (satélite)
- Overlay: Esri World Boundaries and Places (nombres de ciudades/lugares)
- Ambos se oscurecen con un filtro CSS (`filter: brightness/saturate` sobre
  `.leaflet-tile-pane` en `styles/mapview.css`) para acercarse a la estética
  oscura del handoff, ya que no se puede re-estilizar un tile raster como se
  haría con un estilo vectorial de Mapbox/MapLibre.
- El heatmap de riesgo (`components/MapView/HeatLayer.jsx`, plugin
  `leaflet.heat`) es un **placeholder** interpolado desde los 4 puntos de
  estación — se reemplaza por el ráster real derivado del FAI de Sentinel-2
  cuando el backend sirva ese overlay (`GET /risk`'s campo `overlay`).
- Los marcadores de estación usan las coordenadas reales (`lat`/`lng`) que
  devuelve `GET /stations`, no posiciones de un lienzo dibujado a mano.

## Ejecutar

```bash
npm install
cp .env.example .env   # ajustar VITE_API_BASE_URL si el backend no está en localhost:8000
npm run dev
```

Requiere el backend corriendo (`../backend`, ver su README) — `VITE_API_BASE_URL`
apunta ahí por defecto.

## Separación de datos por vista (importante para no romper el contrato)

- **Mapa / Estaciones**: usan `GET /risk` — el estado *presente* (riesgo actual,
  derivado de FAI + variables in situ del día seleccionado).
- **Panel Análisis IA** (dentro de Mapa): usa `GET /forecast` — la salida del
  *modelo* (proyección a 7 días + resumen redactado por Gemini 2.5 Flash en
  el servidor a partir de esos números, ver `backend/app/gemini.py`). No
  mezclar con el riesgo presente de arriba.
- **Tendencias / sparklines**: se calculan en el cliente a partir de
  `GET /observations` (promedio del lago por día) — series históricas medidas,
  no salida del modelo.
- **Modelo**: usa `GET /model/metrics` — no depende de la fecha seleccionada.

## Estructura

```
src/
  api.js                 # cliente fetch para el backend
  hooks/useAppData.js     # estado compartido (view, day, hover, pinned, open) + fetching
  components/
    Header.jsx            # marca, control segmentado, slider temporal
    MapView/               # lienzo SVG placeholder, tarjeta flotante, panel analítico
    StationsView.jsx
    TrendsView.jsx
    ModelView.jsx          # + ModelFooter (footer exclusivo de esta vista)
  data/stationLayout.js    # posiciones placeholder del SVG (bajará con Mapbox)
  utils/format.js, risk.js
  styles/                  # tokens.css (design tokens), app.css, mapview.css, views.css
```
