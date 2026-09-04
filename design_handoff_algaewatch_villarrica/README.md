# Handoff: AlgaeWatch Villarrica — plataforma de monitoreo y predicción de floraciones de algas

## Overview

AlgaeWatch Villarrica es una plataforma web de monitoreo y predicción de floraciones de algas (blooms de cianobacterias) en el Lago Villarrica, Región de La Araucanía, Chile. Prototipo científico-tecnológico de nivel **TRL 2** para un proyecto universitario de biorecursos.

La interfaz combina tres fuentes de información:

1. **Datos satelitales** — imágenes multiespectrales (Sentinel-2 L2A) de las que se deriva el índice **FAI** (Floating Algae Index) y la temperatura superficial del agua. Esta es la fuente principal del mapa de calor de riesgo.
2. **Estaciones de monitoreo in situ** — sensores IoT que aportan temperatura, pH, oxígeno disuelto y viento.
3. **Modelo predictivo** — Gradient Boosting que proyecta el índice de riesgo de floración a 7 días, más una síntesis en lenguaje natural generada por IA.

La aplicación está segmentada en cuatro vistas conmutadas desde un control segmentado en la cabecera: **Mapa**, **Estaciones**, **Tendencias**, **Modelo**.

## About the Design Files

Los archivos de este paquete son **referencias de diseño creadas en HTML**: prototipos que muestran la apariencia y el comportamiento previstos, **no código de producción para copiar directamente**.

La tarea es **recrear estos diseños en el entorno existente del codebase destino** (React, Vue, Next.js, SwiftUI, nativo, etc.) usando sus patrones y librerías establecidos. Si aún no existe un entorno, elegir el framework más apropiado para el proyecto e implementar los diseños allí.

Dos notas específicas de implementación que **no** están resueltas en el prototipo y sí deben resolverse en producción:

### 1. El mapa se implementará con Mapbox GL JS

En el prototipo el lago es un **SVG esquemático dibujado a mano** (un contorno aproximado, un heatmap de elipses con degradados radiales y marcadores posicionados en coordenadas del `viewBox`). Es un *placeholder visual*: comunica la composición y la jerarquía, no la geografía real.

En producción, esa sección debe ser un mapa **Mapbox GL JS**:

- **Estilo base**: `mapbox://styles/mapbox/satellite-streets-v12` (satelital con etiquetas) o `satellite-v9` si se prefiere sin rotulación. Para conservar la estética oscura del prototipo, considerar un estilo propio en Mapbox Studio derivado de `dark-v11` con la capa satelital encima y saturación reducida.
- **Encuadre inicial**: centro aproximado `[-72.08, -39.28]`, zoom `10.2`, `pitch: 0`, `bearing: 0`. Restringir con `maxBounds` a la cuenca del lago para que el usuario no se pierda; `minZoom: 9`, `maxZoom: 14`.
- **Overlay de riesgo**: dos alternativas válidas
  - *raster* — servir el ráster de riesgo derivado del FAI como tiles (`raster` source, XYZ o TileJSON) y aplicar la paleta en el pipeline de generación. Es la opción correcta para una superficie continua derivada de píxeles satelitales.
  - *heatmap* — si el riesgo llega como puntos/celdas vectoriales, usar una capa `heatmap` con `heatmap-color` interpolado por la propiedad `risk` (0–100), respetando la escala de color de más abajo.
  - En ambos casos, **recortar el overlay a la superficie del lago** (máscara con el polígono del lago, p. ej. una capa `fill` inversa sobre tierra o un `line-gradient`/`clip` según la técnica elegida). En el prototipo esto se simula con `clipPath`.
- **Estaciones**: capa `circle` sobre un `geojson` source, con `circle-color` mapeado al nivel de riesgo y `circle-stroke-width: 2` en negro traslúcido. Etiquetas en una capa `symbol` con `text-allow-overlap: false`.
- **Tarjeta flotante**: `mapboxgl.Popup` (con `closeButton: false`, `offset: 18`, `className` propio) o un componente React posicionado con `map.project(lngLat)`. El prototipo la posiciona en porcentajes del contenedor porque no tiene proyección real; **eso se descarta** al usar Mapbox.
- **Slider temporal**: cambiar la fecha debe actualizar el `source` del overlay (nuevo tile set o `setData` del GeoJSON) sin recrear el mapa. Prefetch de las fechas adyacentes para que el barrido se sienta continuo.
- **Token**: `MAPBOX_ACCESS_TOKEN` desde variables de entorno; nunca embebido en el bundle del cliente si el proyecto tiene backend.

### 2. Los datos provienen de satélite (más sensores in situ)

Todos los valores del prototipo son **mock data determinista** generada en el cliente (ver *State Management*). En producción:

- **Satélite**: Sentinel-2 MSI nivel L2A (Copernicus Data Space Ecosystem / Sentinel Hub, o AWS Open Data). Se calcula el índice **FAI** por píxel a partir de las bandas NIR/SWIR y rojo, se enmascara nube y tierra, y se remuestrea a la grilla del lago. Cadencia de revisita ~5 días; el campo "última actualización de datos" de la cabecera debe reflejar la **hora de la pasada satelital** utilizada, no la hora del servidor.
- **In situ**: 4 estaciones IoT (temperatura del agua, pH, oxígeno disuelto, viento) con muestreo horario; en la UI se muestra la última medición válida de la fecha seleccionada.
- **Modelo**: entrenado sobre la serie histórica combinada (satélite + in situ + meteorología), produce el índice de riesgo 0–100 por celda y por estación, con horizonte de 7 días.
- La UI debe declarar explícitamente la procedencia y el nivel de madurez: el prototipo lo hace con el sello "TRL 2 · resultados no validados en campo" y con el descargo del panel de IA. **Conservar esos textos.**

## Fidelity

**High-fidelity (hifi)** en tipografía, color, densidad y comportamiento: la paleta, la escala tipográfica, los radios y los estados están definidos y deben recrearse con fidelidad usando las librerías del codebase.

**Excepción explícita — low-fidelity:** el mapa SVG del lago. Su geometría, el contorno, la posición exacta de los marcadores y el heatmap de elipses son un *boceto*; la implementación real es Mapbox (ver arriba). De ese bloque solo son normativos: la composición (mapa a sangre ocupando la mayor parte del área), la escala de color del riesgo, el contenido y el estilo de la tarjeta flotante, la leyenda y las anotaciones de esquina.

## Screens / Views

Estructura común a todas las vistas — **shell de tres bandas**, `height: 100vh`, `overflow: hidden`, columna flex:

1. `<header>` fijo (dos filas), margen `12px 12px 0`, radio `14px`, tarjeta de vidrio.
2. `<main>` `flex: 1`, `padding: 12px`, `gap: 12px`, `min-height: 0` (imprescindible para que el hijo con scroll no desborde).
3. `<footer>` — **solo visible en la vista Modelo**, margen `0 12px 12px`.

El fondo del shell es común: negro con dos halos de acento.

```css
background:
  radial-gradient(900px 620px at 16% 4%, rgba(10,132,255,0.14) 0%, transparent 62%),
  radial-gradient(820px 560px at 90% 96%, rgba(48,209,88,0.10) 0%, transparent 64%),
  linear-gradient(180deg, #000 0%, #0a0a0d 60%, #000 100%);
```

Más dos círculos decorativos `position: absolute` de 520px y 600px, `border-radius: 50%`, `filter: blur(10px)`, `pointer-events: none`, con degradado radial azul (arriba-izquierda, `top:-140px; left:-90px`) y verde (abajo-derecha, `bottom:-180px; right:8%`).

---

### Cabecera (común)

**Propósito**: identidad, navegación entre vistas, control temporal y procedencia del dato.

**Layout**: contenedor de vidrio en columna, sin altura fija.

- Fila 1 — `display:flex; align-items:center; gap:18px; padding:10px 16px`
  - **Marca** (izquierda, `flex:0 0 auto`): logotipo SVG 30×30 + dos líneas de texto.
    - Logotipo: tres círculos concéntricos (r=13.2 trazo `#0A84FF` a 50% de opacidad; r=7.6 trazo `#30D158`; r=2.1 relleno `#FF9F0A`) y una onda `path` de trazo `#0A84FF` 1.6px con extremos redondeados. Es un mark original; puede sustituirse por el logotipo real del proyecto.
    - Título: `15px / 700 / letter-spacing -0.4px`, "AlgaeWatch" en `#F5F5F7` + "Villarrica" en `#0A84FF`.
    - Bajada: `9.5px / letter-spacing 0.6px / #98989D`, texto `MONITOREO Y PREDICCIÓN DE FLORACIONES · TRL 2`.
  - **Control segmentado** (`flex:0 0 auto`): contenedor `padding:2px; border-radius:10px; background:rgba(118,118,128,0.24)`, `gap:2px`. Cada opción es un `<button>` `padding:6px 14px; border-radius:8px; font-size:12.5px; letter-spacing:-0.2px; border:0`.
    - Inactiva: `color:#AEAEB2; background:transparent; font-weight:400`.
    - Activa: `color:#FFFFFF; background:rgba(120,120,128,0.36); font-weight:600; box-shadow:0 1px 3px rgba(0,0,0,0.35)`.
    - Opciones: `Mapa`, `Estaciones`, `Tendencias`, `Modelo`.
    - En producción: rol `tablist`/`tab`, navegación con flechas, y sincronizar con la ruta (`/mapa`, `/estaciones`, …) para que la vista sea enlazable.
  - **Espaciador** `flex:1 1 auto`.
  - **Última actualización** (derecha, `flex:0 0 auto`, `white-space:nowrap`): punto de 7px `#30D158` con `box-shadow:0 0 10px #30D158` y animación `aw-live` (opacidad 1 → 0.2 → 1, 2.4s, `ease-in-out`, infinita), más tres líneas alineadas a la derecha:
    - `ÚLTIMA ACTUALIZACIÓN` — `9.5px / #98989D / letter-spacing 0.5px`
    - `04 sep 2026 · 06:40 UTC−3` — `11.5px / #E5E5EA`
    - `Sentinel-2 L2A · 4 estaciones IoT` — `9.5px / #8E8E93`
- Fila 2 — `display:flex; align-items:center; gap:16px; padding:10px 16px 11px; border-top:1px solid rgba(255,255,255,0.10)`
  - **Ventana temporal** (`flex:1 1 auto; min-width:0`): etiqueta `VENTANA TEMPORAL` (`9.5px / #98989D`) sobre un `<input type="range">` `min=0 max=20 step=1`, ancho 100%, `accent-color:#0A84FF`. Los 21 pasos son días del 15 ago al 4 sep de 2026.
  - **Fecha seleccionada** (`flex:0 0 auto`, `border-left:1px solid rgba(255,255,255,0.12)`, `padding-left:16px`): etiqueta `FECHA SELECCIONADA` + valor `15px / 500 / #FFFFFF` (`04 sep 2026`).
  - En producción, el slider debería ir acompañado de un date picker para saltos largos, y el rango de fechas debe derivarse de las pasadas satelitales disponibles.

Superficie de vidrio de la cabecera (y de todos los paneles de nivel superior):

```css
border: 1px solid rgba(255,255,255,0.14);
border-radius: 14px;                 /* paneles de contenido: 16px */
background: rgba(28,28,30,0.58);
backdrop-filter: blur(18px) saturate(140%);
box-shadow: 0 8px 32px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.09);
```

---

### Vista 1 — Mapa (por defecto)

**Propósito**: leer de un vistazo dónde está el riesgo hoy y consultar el detalle de una estación.

**Layout**: `display:flex; gap:12px`. Mapa `flex:1`, panel derecho `flex:0 0 382px` (colapsable a 48px).

#### 1a. Lienzo del mapa

- Panel de vidrio, `border-radius:16px`, `overflow:hidden`, `background:rgba(22,22,24,0.45)`, `backdrop-filter: blur(14px)`.
- **Contenido (a reemplazar por Mapbox)**: superficie del lago con overlay de riesgo, 4 marcadores de estación y etiquetas.
  - Marcador: círculo de 9px de radio con el color del nivel de riesgo y trazo `2.4px rgba(0,0,0,0.85)`; anillo exterior de 18px de radio, trazo 2px del mismo color a 40% de opacidad. Si el nivel es **ALTO**, el anillo pulsa: `aw-pulse` — radio 13 → 32 y opacidad 0.8 → 0, 2.6s, `ease-out`, infinita.
  - Etiqueta de estación: `10.5px / letter-spacing 0.8px / #E5E5EA`, `text-shadow: 0 1px 5px rgba(0,0,0,0.95)`, `white-space:nowrap`, `pointer-events:none`. Textos: `E-01 LITORAL PUCÓN`, `E-02 ZONA NORTE`, `E-03 DESEMB. RÍO TOLTÉN`, `E-04 BAHÍA SUR`.
  - Anotaciones de referencia geográfica (en Mapbox las aporta el estilo base): `Pucón`, `Villarrica`, `Volcán Villarrica · 2.847 m`, `Río Toltén · efluente`.
- **Anotación superior izquierda** (`top:16px; left:18px`, `pointer-events:none`):
  - `LAGO VILLARRICA · 39°17′S 72°05′O` — `11px / letter-spacing 0.8px / #AEAEB2`
  - `Superficie 176 km² · Prof. máx. 165 m · Cuenca Toltén` — `10px / #8E8E93`
- **Leyenda inferior izquierda** (`bottom:14px; left:16px`): tarjeta de vidrio `padding:11px 13px; border-radius:12px; background:rgba(28,28,30,0.62); border:1px solid rgba(255,255,255,0.14)`.
  - Título `ÍNDICE DE RIESGO DE FLORACIÓN` — `9.5px / #98989D`
  - Barra de 206×9px, `border-radius:999px`, `background: linear-gradient(90deg,#64D2FF,#30D158,#FF9F0A,#FF453A)`; a su derecha `0 → 100` en `10px / #AEAEB2`
  - Cuatro etiquetas `10px`: `Muy bajo`, `Bajo`, `Medio` (en `#C7C7CC`) y `Alto` en `#FF453A`
- **Escala inferior derecha** (`bottom:18px; right:18px`): `0` — línea de 84×1px `#98989D` — `5 km`, todo en `10px / #98989D`. Con Mapbox, sustituir por `ScaleControl`.

#### 1b. Tarjeta flotante de estación

Se muestra al **hacer hover o clic** sobre un marcador (o sobre una fila de la lista del panel derecho). El clic fija/suelta la selección; el hover la muestra temporalmente y tiene prioridad sobre la fija.

- Ancho 300px (`max-width: calc(100% - 32px)`), `padding:14px 16px`, `border-radius:14px`, `pointer-events:none`, `z-index:4`.
- `background: rgba(28,28,30,0.74)`, `backdrop-filter: blur(16px)`, `border: 1px solid <color del nivel>`, `box-shadow: 0 12px 40px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.12)`.
- Se ancla al lado del marcador con 16–18px de separación y se voltea al lado opuesto cuando no hay espacio.
- Contenido, en orden:
  1. Nombre de la estación — `14.5px / 600 / #FFFFFF / line-height 1.25`
  2. Fila: código y sector (`9px / letter-spacing 1px / #98989D`, p. ej. `E-02 · BAHÍA NORTE · IoT-2`) y fecha/hora de la medición alineada a la derecha (`9px / #8E8E93`, p. ej. `04 sep 2026 05:20`)
  3. Chip de riesgo — pill `padding:4px 11px; border-radius:999px; font-size:10px; letter-spacing:1px`, `border: 1px solid <color>`, fondo `<color>` a 16–18% de opacidad, texto `<color>`; contenido `RIESGO ALTO · 97/100`
  4. Rejilla `2 × 2`, `gap: 10px 14px` — etiqueta `9px / letter-spacing 0.5px / #98989D` sobre valor `15px / #FFFFFF`:
     `TEMP. AGUA` (`21,1 °C`), `pH` (`8,06`), `OXÍGENO DISUELTO` (`7,4 mg/L`), `FAI / CLOROFILA` (`0,266`)

#### 1c. Panel lateral derecho (colapsable)

Panel de vidrio de 382px, `overflow-y:auto`.

- **Encabezado**: `PANEL ANALÍTICO` (`9.5px / #98989D`) y botón `COLAPSAR ›` — pill `padding:5px 10px; border-radius:999px; font-size:10px`, `background:rgba(10,132,255,0.12)`, `border:1px solid rgba(255,255,255,0.24)`, `color:#C7C7CC`; en hover `background:rgba(10,132,255,0.24); color:#FFFFFF`.
- **Colapsado**: la columna pasa a 48px y muestra el botón `‹` y el rótulo `PANEL ANALÍTICO · ANÁLISIS IA` en vertical (`writing-mode: vertical-rl`, `9.5px / #98989D`).

**Panel "Análisis IA"** — deliberadamente diferenciado del resto de la UI, como un copiloto:

- `margin:14px`, `padding:15px`, `border-radius:14px`
- `border: 1px solid rgba(10,132,255,0.45)`
- `background: linear-gradient(160deg, rgba(10,132,255,0.16), rgba(48,209,88,0.08))`
- `backdrop-filter: blur(10px)`
- `box-shadow: inset 0 1px 0 rgba(255,255,255,0.14), 0 0 30px rgba(10,132,255,0.10)`
- Encabezado: ícono de destello 18×18 (estrella de cuatro puntas `#0A84FF` + círculo `#30D158` de 2.2px en la esquina), rótulo `ANÁLISIS IA` (`10px / letter-spacing 0.7px / #64D2FF`) y, a la derecha, `CONFIANZA 78%` (`9.5px / #98989D`).
- Cuerpo: resumen en lenguaje natural, `13.5px / line-height 1.55 / #F5F5F7`, `text-wrap: pretty`. Texto de ejemplo (generado a partir del estado del modelo):

  > Riesgo alto proyectado en Litoral Pucón para los próximos 7 días (97/100, +10 vs. semana anterior). La temperatura superficial alcanza 21,1 °C y el viento medio cae a 8,3 km/h, lo que reduce la circulación y favorece la acumulación de cianobacterias en superficie. El índice FAI derivado de Sentinel-2 se sitúa en 0,266 con pH 8,06.

- Recomendación: `12.5px / line-height 1.5 / #AEAEB2`.

  > Recomendación: reforzar muestreo in situ en Litoral Pucón y Zona Norte; activar aviso a la mesa de gestión del lago si el FAI supera 0,30 en dos pasadas consecutivas.

- Tres micro-métricas en fila (`gap:8px`), cada una `padding:8px 9px; border-radius:10px; background:rgba(0,0,0,0.30); border:1px solid rgba(255,255,255,0.16)`: etiqueta `8.5px / #98989D` sobre valor `15px` coloreado.
  `RIESGO MEDIO LAGO` (color según nivel), `ESTACIONES EN ALERTA` (`#FF9F0A` si >1, si no `#30D158`), `HORIZONTE` (`7 d`, `#AEAEB2`).
- Descargo al pie, sobre `border-top`: `9px / letter-spacing 0.4px / #8E8E93` — `ALGAEWATCH-LM · SÍNTESIS SOBRE LA SALIDA DEL MODELO, NO VALIDADA EN CAMPO`. **Obligatorio conservarlo** en cualquier superficie que muestre texto generado.

**Mini-gráficos de tendencia** (3): rótulo de sección `TENDENCIAS · PROMEDIO LAGO`. Cada tarjeta `padding:12px 13px 9px; border-radius:12px; background:rgba(58,58,60,0.30); border:1px solid rgba(255,255,255,0.10)`:

- Fila superior: nombre (`12.5px / 600 / #E5E5EA`) y valor actual (`14px`, color de la serie).
- Sparkline SVG `viewBox="0 0 320 78"`, `preserveAspectRatio="none"`, alto 78px: línea base y línea superior punteada en `rgba(255,255,255,0.12)` / `0.09`; área rellena con el color de la serie al 16%; trazo de 1.8px `stroke-linejoin: round`; guía vertical punteada `rgba(255,255,255,0.32)` en la fecha seleccionada y punto de 3.4px sobre la curva.
- Pie: `15 AGO`, rango min–max, `04 SEP` en `9px / #8E8E93`.
- Series: **Temperatura superficial** `#0A84FF` (1 decimal, `°C`), **pH** `#30D158` (2 decimales), **Índice FAI (clorofila-a)** `#FF9F0A` (3 decimales).

**Lista de estaciones**: rótulo `ESTACIONES · <fecha>`; filas de `padding:9px 11px; border-radius:10px; background:rgba(58,58,60,0.30)`, `gap:6px` entre filas, con punto de 8px del color del nivel, nombre (`12.5px / #E5E5EA`) y riesgo `nn/100` (`12px`, color del nivel). Hover: `background: rgba(10,132,255,0.14)`. Hover y clic sincronizan con la tarjeta del mapa.

---

### Vista 2 — Estaciones

**Propósito**: comparar las mediciones in situ de las cuatro estaciones para la fecha seleccionada.

**Layout**: un único panel de vidrio (`flex:1`, `overflow-y:auto`, `padding:18px 20px`).

- Rótulo `ESTACIONES DE MONITOREO · <fecha>` (`9.5px / #98989D`) y título `Mediciones in situ y riesgo por estación` (`19px / 600 / letter-spacing -0.4px / #FFFFFF`).
- Rejilla `repeat(auto-fit, minmax(300px, 1fr))`, `gap:12px`, `margin-top:16px`.
- Tarjeta por estación (`padding:14px 16px; border-radius:14px; background:rgba(58,58,60,0.30); border:1px solid rgba(255,255,255,0.10)`):
  1. Nombre (`15px / 600 / letter-spacing -0.3px / #FFFFFF`) y riesgo `nn/100` (`13px`, color del nivel).
  2. Código y sector — `9.5px / #98989D`.
  3. Barra de riesgo: canal de 6px `border-radius:999px; background:rgba(255,255,255,0.10)`; relleno de ancho `= risk%` con el color del nivel.
  4. Rejilla `2 × 3`, `gap:10px 14px`: `TEMP. AGUA`, `pH`, `OXÍGENO DISUELTO`, `FAI / CLOROFILA`, `VIENTO MEDIO`, `ÚLTIMA MEDICIÓN` — etiqueta `9.5px / #98989D` sobre valor `16px / #FFFFFF` (la fecha, `13px / #E5E5EA`).
- Hover en una tarjeta selecciona esa estación (comparte estado con la vista Mapa).

---

### Vista 3 — Tendencias

**Propósito**: leer la evolución de las variables clave en la ventana temporal completa.

**Layout**: panel de vidrio único con scroll.

- Rótulo `TENDENCIAS · PROMEDIO LAGO · 15 AGO – 04 SEP 2026` y título `Variables clave del modelo`.
- Tres tarjetas apiladas (`gap:12px`), mismas series y colores que los mini-gráficos del panel lateral, pero con el SVG a **118px** de alto y el nombre a `14.5px / 600`, el valor a `17px`.
- Pie de cada tarjeta: `15 AGO` · `Rango <min> – <max>` · `04 SEP`.
- En producción conviene añadir tooltip por punto y selección de rango por arrastre; el prototipo solo marca la fecha activa del slider.

---

### Vista 4 — Modelo

**Propósito**: dar cuenta técnica del modelo a una audiencia experta sin abrumar.

**Layout**: panel de vidrio con scroll + `<footer>` de métricas (el footer **solo** existe en esta vista).

- Rótulo `MODELO PREDICTIVO · v0.4.1` y título `Gradient Boosting + índice FAI Sentinel-2`.
- Rejilla `repeat(auto-fit, minmax(240px, 1fr))`, `gap:12px`, con tres tarjetas:
  1. **`MATRIZ DE CONFUSIÓN · UMBRAL FAI ≥ 0,30`** — cuatro filas etiqueta (`12.5px / #AEAEB2`) / valor (`16px`, coloreado): Verdaderos positivos `164` (`#30D158`), Falsos positivos `16` (`#FF9F0A`), Falsos negativos `24` (`#FF453A`), Verdaderos negativos `1.638` (`#0A84FF`).
  2. **`IMPORTANCIA DE VARIABLES`** — cinco filas con etiqueta + porcentaje (`12.5px`) y barra de 5px (`background:rgba(255,255,255,0.10)`, relleno `#0A84FF`): Temperatura superficial (SST) 32%, Índice FAI Sentinel-2 27%, Viento medio 72 h 18%, Nitrógeno total (in situ) 13%, pH y oxígeno disuelto 10%.
  3. **`VALIDACIÓN`** — texto `13px / line-height 1.6 / #E5E5EA`: `1.842 observaciones · 2024–2026`, `Validación cruzada 5-fold + hold-out temporal`, `Reentrenado el 28 ago 2026`, `Horizonte de predicción: 7 días`; y descargo `11.5px / #8E8E93`: `TRL 2 · resultados no validados en campo; el índice FAI se calibra con muestreo in situ estacional.`
- **Footer de métricas** — una fila, `padding:12px 16px`, `gap:14px`, `flex-wrap:nowrap`:
  - Izquierda: `MODELO PREDICTIVO` / `Gradient Boosting + FAI` (`12.5px / 600`) / `v0.4.1 · reentrenado 28 ago 2026` (`9.5px / #8E8E93`).
  - Centro: cinco fichas `flex:1 1 0`, `padding:8px 10px; border-radius:12px; background:rgba(58,58,60,0.30)`; etiqueta `8.5px / #98989D`, valor `17px / #FFFFFF / line-height 1`, barra de 4px con `linear-gradient(90deg,#0A84FF,#30D158)` y nota `8.5px / #8E8E93`:
    `PRECISIÓN 0,91` (91%, VP 164/FP 16) · `RECALL 0,87` (87%, FN 24) · `F1-SCORE 0,89` (89%, floración) · `AUC-ROC 0,94` (94%, hold-out) · `MAE FAI 0,027` (73%, error medio).
  - Derecha, tras `border-left`: `VALIDACIÓN` / `1.842 obs · CV 5-fold` / `Umbral de alerta: FAI ≥ 0,30`.

## Interactions & Behavior

| Interacción | Comportamiento |
| --- | --- |
| Clic en pestaña del control segmentado | Cambia de vista; el estado temporal y la selección de estación se conservan. En producción, reflejar en la URL. |
| Arrastre del slider temporal | Recalcula **todo**: overlay de riesgo, marcadores, tarjeta flotante, resumen de IA, micro-métricas, tendencias (guía vertical) y lista de estaciones. Debe sentirse inmediato: mantener el cálculo por debajo de un frame o interpolar entre fechas ya cargadas. |
| Hover sobre marcador / tarjeta / fila de estación | Muestra la tarjeta flotante de esa estación; se prioriza sobre la selección fijada. |
| Clic sobre marcador o fila | Fija la selección; volver a hacer clic la suelta. |
| `COLAPSAR ›` / `‹` | Colapsa el panel derecho a 48px y lo restaura. Transición sugerida: `width 240ms cubic-bezier(0.4, 0, 0.2, 1)` (el prototipo cambia sin animar). |
| Nivel de riesgo ALTO | El anillo del marcador pulsa (`aw-pulse`, 2.6s). No usar sonido ni parpadeo agresivo. |
| Indicador de datos en vivo | Punto verde con `aw-live` (2.4s). Si el dato está obsoleto (> 6 días sin pasada satelital útil), pasar a `#FF9F0A` y rotular `DATO DESACTUALIZADO`. |
| Estados de carga | No están diseñados. Recomendado: esqueletos con el mismo radio y fondo `rgba(58,58,60,0.30)`, y para el mapa mantener el estilo base visible mientras carga el overlay. |
| Estados de error | No están diseñados. Recomendado: mantener el shell y sustituir el contenido del panel por un mensaje con acción de reintento; para nubosidad total del día seleccionado, indicarlo explícitamente en la leyenda (`sin dato satelital útil`) en lugar de mostrar riesgo 0. |
| Responsive | El prototipo asume escritorio ≥1280px (centro de monitoreo). Por debajo de ~1100px: colapsar el panel derecho por defecto; por debajo de ~820px: apilar mapa y panel verticalmente y convertir el control segmentado en scroll horizontal. |
| Accesibilidad | El color codifica el riesgo, así que el nivel **siempre** va acompañado de texto (`RIESGO ALTO · 97/100`); mantener esa regla. `prefers-reduced-motion` debe desactivar `aw-pulse` y `aw-live`. |

## State Management

Estado de la vista (en el prototipo, estado local del componente):

| Variable | Tipo | Descripción |
| --- | --- | --- |
| `view` | `'mapa' \| 'estaciones' \| 'tendencias' \| 'modelo'` | Vista activa. Inicial: `mapa`. Candidata a vivir en la ruta. |
| `day` | `0…20` | Índice del día dentro de la ventana temporal. Inicial: `20` (el más reciente). |
| `hover` | `stationId \| null` | Estación bajo el cursor. |
| `pinned` | `stationId \| null` | Estación fijada por clic. Inicial: `null`. |
| `open` | `boolean` | Panel derecho expandido. Inicial: `true`. |

La estación mostrada en la tarjeta es `hover ?? pinned`.

**Datos**. El prototipo genera series deterministas en el cliente (ruido pseudoaleatorio sembrado por estación, 21 días) y calcula el riesgo con una fórmula heurística sobre temperatura, FAI, pH, oxígeno y viento. **Esto es andamiaje del prototipo, no el modelo.** En producción se necesita:

- `GET /stations` — catálogo de estaciones (id, nombre, sector, coordenadas).
- `GET /observations?from&to&station` — series in situ.
- `GET /risk?date` — riesgo por estación **y** referencia al tileset/GeoJSON del overlay para esa fecha.
- `GET /forecast?date` — proyección a 7 días y el resumen en lenguaje natural con su nivel de confianza.
- `GET /model/metrics` — métricas, matriz de confusión, importancia de variables, metadatos de versión.
- El resumen de IA debe generarse **en el servidor**, a partir de la salida del modelo, y viajar con su marca de tiempo y confianza; no reconstruir texto en el cliente.

## Design Tokens

Sistema visual: lenguaje de Apple — tipografía del sistema (San Francisco), superficies translúcidas oscuras (vibrancy) y colores del sistema.

### Tipografía

```
font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Helvetica, sans-serif;
font-variant-numeric: tabular-nums;   /* aplicado globalmente: las cifras no bailan al mover el slider */
```

| Rol | Tamaño | Peso | Tracking |
| --- | --- | --- | --- |
| Título de vista | 19px | 600 | −0.4px |
| Marca | 15px | 700 | −0.4px |
| Título de tarjeta | 14.5–15px | 600 | −0.3px |
| Valor grande (métrica) | 16–17px | 400 | — |
| Cuerpo (IA) | 13.5px | 400 | — · `line-height 1.55` |
| Cuerpo secundario | 12.5–13px | 400 | — |
| Pestaña | 12.5px | 400 / 600 activa | −0.2px |
| Micro-etiqueta (mayúsculas) | 8.5–10px | 400 | 0.4–0.8px |

### Color

| Rol | Valor |
| --- | --- |
| Fondo | `#000000` (+ halos `rgba(10,132,255,0.14)` y `rgba(48,209,88,0.10)`) |
| Texto primario | `#FFFFFF` |
| Texto | `#F5F5F7` |
| Texto secundario | `#E5E5EA` |
| Texto terciario | `#C7C7CC` / `#AEAEB2` |
| Texto de etiqueta | `#98989D` |
| Texto atenuado | `#8E8E93` |
| Acento (interfaz, no alerta) | `#0A84FF` |
| Acento claro (IA, riesgo muy bajo) | `#64D2FF` |
| Riesgo bajo / positivo | `#30D158` |
| Riesgo medio / advertencia | `#FF9F0A` |
| Riesgo alto / alerta | `#FF453A` |

**Escala de riesgo 0–100** — reservada exclusivamente al riesgo; ámbar y rojo no se usan en ningún otro rol:

| Rango | Nivel | Color |
| --- | --- | --- |
| 0–24 | MUY BAJO | `#64D2FF` |
| 25–44 | BAJO | `#30D158` |
| 45–67 | MEDIO | `#FF9F0A` |
| 68–100 | ALTO | `#FF453A` |

Degradado de la leyenda: `linear-gradient(90deg, #64D2FF, #30D158, #FF9F0A, #FF453A)`.

### Superficies

| Superficie | Valor |
| --- | --- |
| Panel de nivel superior | `rgba(28,28,30,0.55–0.58)` + `blur(18px) saturate(140%)` |
| Lienzo del mapa | `rgba(22,22,24,0.45)` + `blur(14px)` |
| Tarjeta interior | `rgba(58,58,60,0.30)` |
| Tarjeta flotante / popup | `rgba(28,28,30,0.74)` + `blur(16px)` |
| Pista de control segmentado | `rgba(118,118,128,0.24)` |
| Pastilla activa del segmentado | `rgba(120,120,128,0.36)` |
| Hairline | `rgba(255,255,255,0.10–0.14)` |
| Hairline enfatizado | `rgba(255,255,255,0.24–0.32)` |
| Canal de barra de progreso | `rgba(255,255,255,0.10)` |
| Selección de texto | `rgba(10,132,255,0.32)` |

Nota de implementación: si el destino no soporta `backdrop-filter` (o hay que sostener 60 fps con el mapa moviéndose debajo), sustituir por fondos opacos equivalentes — `#1C1C1E` para paneles, `#2C2C2E` para tarjetas interiores — antes que degradar el rendimiento del mapa.

### Radios y sombras

```
radius: 8px (pastilla del segmentado) · 10px (fila, pista) · 12px (ficha, leyenda) ·
        14px (cabecera, tarjeta, popup) · 16px (panel de contenido) · 999px (pill, barra)

shadow-panel:  0 8px 32px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.09)
shadow-content: 0 10px 40px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.08)
shadow-popup:  0 12px 40px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.12)
shadow-pill:   0 1px 3px rgba(0,0,0,0.35)
```

### Espaciado

Escala de 2/4px: `2, 4, 6, 8, 9, 10, 11, 12, 14, 16, 18, 20`. Convenciones: margen exterior del shell 12px; `gap` entre paneles 12px; `padding` interior de panel de contenido 18px 20px; `padding` de tarjeta 14px 16px; `gap` de rejilla de datos 10px 14px.

### Animaciones

```css
@keyframes aw-pulse { 0% { r:13; opacity:.8 } 70%,100% { r:32; opacity:0 } }  /* 2.6s ease-out infinite */
@keyframes aw-live  { 0%,100% { opacity:1 } 50% { opacity:.2 } }              /* 2.4s ease-in-out infinite */
```

## Assets

- **Ninguna imagen ni ícono de terceros.** El logotipo (círculos concéntricos con onda) y el ícono de destello del panel de IA son SVG inline originales creados para este prototipo; sustituir el logotipo por el del proyecto cuando exista.
- **Tipografía**: fuentes del sistema, sin webfonts que descargar.
- **Mapa**: en producción, estilo y tiles de **Mapbox** (requiere token) más el ráster/GeoJSON de riesgo generado desde **Sentinel-2 L2A** (Copernicus). El SVG del lago que trae el prototipo es descartable.
- **Iconografía adicional**: si se necesita más, el proyecto no ha fijado un set; en un entorno Apple-like, SF Symbols o un set lineal equivalente de trazo 1.5–2px.

## Files

- `AlgaeWatch Villarrica.dc.html` — el prototipo completo (las cuatro vistas, el mapa esquemático, la generación de datos mock y toda la capa visual). Punto de referencia principal.
- `support.js` — runtime del entorno de prototipado. **No es parte del diseño**; se incluye solo para que el HTML abra y se pueda inspeccionar.

Para revisar el prototipo: abrir el `.dc.html` en un navegador y recorrer las cuatro pestañas moviendo el slider temporal.
