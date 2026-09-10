---
source: SYSTEM_OVERVIEW.md
source_sha: fcb7fbd5899fcdd608ae2d183d2af7af4b94c0c7
source_sha_algo: git-blob-sha1
translated: 2026-09-10
translator: agent
---

# AlgaeWatch Villarrica — Visión General del Sistema

Qué es el sistema, cómo encajan las piezas, qué puede afirmar honestamente y qué
no. Escrito para leerse de principio a fin por alguien que nunca abrió el
repositorio — incluido el caso en que esa persona está preparando una
presentación sobre esto.

Estado al **2026-09-10**. TRL 2: un prototipo funcional de punta a punta sobre
datos reales, no un producto validado.

---

## 1. El problema

El Lago Villarrica (176 km², Araucanía, Chile) tiene floraciones recurrentes de
cianobacterias. Las floraciones son un problema de salud pública y de turismo, y
la respuesta actual de monitoreo es el muestreo in situ: alguien sale en bote,
llena botellas, y un laboratorio devuelve números días después. Eso es preciso,
lento, espacialmente disperso y caro.

La pregunta que hace este prototipo es angosta y testeable:

> ¿Pueden imágenes satelitales de acceso libre, más clima, pronosticar el índice
> de algas del lago a ~7 días **mejor que adivinar trivialmente**?

La frase "mejor que adivinar trivialmente" es toda la columna metodológica del
proyecto, y la sección 5 trata sobre eso.

---

## 2. Qué hace el sistema

Cuatro etapas, cada una ejecutable e inspeccionable por separado.

```
Sentinel-2 L2A  ──►  FAI por píxel  ──┐
(Copernicus, libre)  src/features/    │
                                      ├──►  tabla de entrenamiento ──►  modelo  ──►  API  ──►  dashboard
ERA5-Land       ──►  clima diario   ──┘     data/processed/             src/model/  backend/  frontend/
(Copernicus CDS)     src/features/
```

**Etapa 1 — el índice satelital.** Sentinel-2 pasa sobre el lago cada ~5 días.
Para cada pasada sin nubes calculamos el **Floating Algae Index (FAI)**, una
combinación aritmética de bandas infrarrojo cercano y rojo que responde a
biomasa algal flotante. El agua se aísla con la banda SCL de clasificación de la
propia escena, así que tierra y nubes nunca entran al promedio. Es un índice
publicado, no algo inventado acá; en esta etapa no interviene ningún modelo.

**Etapa 2 — el clima.** El reanálisis ERA5-Land aporta temperatura media diaria,
precipitación acumulada y viento medio sobre el bounding box del lago. Son los
*change drivers*: un índice de algas dice dónde hay biomasa ahora, el clima es
parte de lo que la mueve.

**Etapa 3 — el modelo.** Una red **cuantílica** chica en PyTorch predice la
anomalía estandarizada de cada píxel a un horizonte de ~7 días, y reporta tres
cuantiles (10, 50, 90) en vez de un número único — así la salida es un rango con
confianza declarada, no una falsa certeza puntual.

**Etapa 4 — entrega.** Un backend FastAPI sirve el modelo y los datos
recolectados; un dashboard React + Leaflet renderiza cuatro vistas (Mapa,
Estaciones, Tendencias, Modelo).

---

## 3. De dónde salen los números

Todo lo de abajo está medido, sobre datos commiteados, y es reproducible con los
comandos de `agents/validation/EVIDENCE_INDEX.md`.

| Cantidad | Valor |
|---|---|
| Pasadas Sentinel-2 sin nubes | **56** (2025-09-04 → 2026-08-22) |
| Píxeles de agua muestreados por pasada | ~1.888 |
| Cobertura ERA5-Land | **13 meses**, 56 días coincidentes |
| Pares honestos ancla→objetivo | **56.668** |
| Píxeles distintos / fechas ancla | 1.866 / 34 |

"Honesto" carga peso acá. **Ninguna fila está interpolada, rellenada por
forward-fill ni inventada.** Si un píxel quedó tapado por nubes en una fecha,
esa fecha simplemente no tiene fila para ese píxel. Una versión anterior de este
proyecto infló 363 observaciones reales a 1.356 filas de entrenamiento con
forward-fill, lo que hacía ver al modelo mucho mejor de lo que era; ahora una
verificación automática permanente lo rechaza (regla PR-3).

---

## 4. Qué es real y qué no

Ser preciso acá sirve más que sobrevender, sobre todo en una presentación donde
alguien puede preguntar.

| Componente | Estado |
|---|---|
| Imágenes Sentinel-2 y FAI | **Real.** Escenas en vivo, credenciales reales, enmascarado de agua real |
| Clima ERA5-Land | **Real.** 13 meses backfilleados desde la API del CDS de Copernicus |
| Entrenamiento y evaluación | **Real.** No hay datos mock en ninguna parte del pipeline |
| Dashboard y API | **Real.** `mock_data.py` fue eliminado; cada endpoint sirve datos recolectados |
| Mediciones in situ (temp, pH, O₂ disuelto) | **Ausentes.** Stub deliberado — el dashboard muestra `—`, nunca un número fabricado. Bloqueado en datos de SNIA (BL-027) |
| Las cuatro "estaciones de monitoreo" | **Provisorias.** Dos de las cuatro coordenadas placeholder no están sobre el agua (a 0,77 km y 0,98 km), así que sus lecturas son vegetación de orilla. El GPS real está bloqueado en SNIA (BL-027) |
| Clasificación de floración (precisión/recall/F1) | **Reportada como `null`, con razón.** Ver sección 6 |

---

## 5. El núcleo metodológico: las líneas base

Esta es la parte que vale la pena presentar, porque es lo que separa una demo de
la evidencia.

Un modelo que reporta "MAE 0,002" no dice nada. La pregunta honesta es: **¿cuánto
da ese mismo número para un método que no hace ningún trabajo?** Se calculan dos
de esos métodos sobre exactamente las mismas filas, en cada evaluación:

- **Persistencia** — "mañana se parece a hoy". Predecir el valor actual de FAI.
- **Climatología** — "predecir el promedio histórico del propio píxel", usando
  solo observaciones *anteriores* a la fecha de predicción.

Una regla que impone la suite de tests (**MI-1**) dice que una métrica registrada
sin ambas líneas base al lado no es evidencia y no puede entrar al índice de
evidencia. La vista Modelo del dashboard muestra la comparación en pantalla, no
solo en un archivo.

Dos reglas más importan:

- **MI-2 — embargo temporal.** Los datos de entrenamiento tienen que terminar
  antes de la fecha objetivo de validación. Si no, el modelo vio el futuro.
- **BL-016 — hold-out espacial.** Los píxeles vecinos del lago están muy
  correlacionados, así que los splits aleatorios filtran mucho. Cada fold de
  evaluación deja afuera un cuadrante geográfico entero del lago, y el modelo se
  puntúa sobre una región que nunca vio.

Esto lo imponen ~88 tests automatizados, no las buenas intenciones.

---

## 6. El resultado, dicho sin vueltas

El modelo per-píxel, entrenado con todos los insumos reales y evaluado bajo
embargo temporal más hold-out espacial:

| | MAE (unidades FAI) |
|---|---|
| **Modelo** | **0,001999** ± 0,001501 |
| Línea base de persistencia | 0,001402 |
| Línea base de climatología | 0,001296 |

**El modelo no supera a ninguna de las dos líneas base en el promedio.** Ese es
el resultado reportado. No se tuneó hacia un número mejor, y una cifra baja y
honesta la propia verificación del proyecto la trata como aprobada, mientras que
una cifra alta salida de un pipeline con fuga la trata como fallada.

El detalle fold por fold es más interesante que el promedio, y es la versión
honesta de la historia:

| Fold | Región del lago excluida | Modelo | Climatología | |
|---|---|---|---|---|
| 1 | NO | 0,001444 | 0,001543 | **supera** |
| 2 | NE | 0,004568 | 0,001882 | falla feo |
| 3 | SO | 0,001192 | 0,000929 | pierde |
| 4 | SE | 0,000792 | 0,000828 | **supera** |

**Dos de cuatro folds superan a la climatología.** El fold 2 solo arrastra el
promedio sin ponderar por encima de ella. La ventana de validación del fold 2 es
2026-02-13 → 2026-03-08 — fines de verano del hemisferio sur, el tramo más
volátil de toda la serie (desvío estándar del objetivo 2,35 contra ~0,7 en el
resto). Dicho de otro modo:

> El modelo es menos confiable justo cuando el lago es más variable — que es
> exactamente cuando un pronóstico de floración importaría.

Ese es el titular honesto, y es mejor decirlo en voz alta que un promedio que lo
esconde.

**Un resultado sí funcionó.** El intervalo entre percentiles 10 y 90 logró
**81,35%** de cobertura empírica contra un nominal de 80%. La cuantificación de
incertidumbre está bien calibrada aunque el pronóstico puntual no agregue nada
sobre la climatología con este tamaño de muestra. Un "no sabemos, y acá está
cuánto no sabemos" bien calibrado es un entregable real.

**La clasificación se reporta como `null`, a propósito.** El umbral de floración
heredado de trabajo anterior (0,025916) es unas diez veces el FAI per-píxel más
alto realmente observado. Aplicado a datos reales etiqueta cada fila como
negativa, lo que haría que precisión, recall y F1 fueran perfectos de manera
vacua. En vez de hornear un umbral equivocado en las etiquetas de entrenamiento,
la superficie de clasificación se reporta como `null` con la razón registrada en
el artefacto (regla MI-3).

---

## 7. Por qué probablemente rinde por debajo

Candidatos honestos, en orden aproximado de probabilidad:

1. **Tamaño de muestra en el tiempo.** 56 pasadas en un año son 34 fechas ancla
   utilizables. Las 56.668 filas son espacialmente numerosas pero temporalmente
   flacas, y los píxeles dentro de una misma fecha están lejos de ser
   independientes.
2. **El objetivo es difícil.** Predecir una *anomalía estandarizada* significa
   que el modelo tiene que superar a "predecir cero", que es exactamente la
   climatología. Sobre una señal débilmente autocorrelacionada esa es una vara
   genuinamente alta.
3. **El clima es grueso.** ERA5-Land es una media sobre el bounding box. El lago
   tiene 176 km²; una sola temperatura media diaria puede no resolver lo que
   dispara floraciones locales.
4. **No hay verdad de campo in situ.** Nutrientes, perfil de temperatura y
   oxígeno disuelto son los verdaderos disparadores de floración y ninguno está
   disponible todavía (BL-027).

Notar qué *no* está en esta lista: fuga de datos. Versiones anteriores de este
proyecto puntuaban mucho mejor precisamente porque filtraban, y las
verificaciones actuales existen para que eso no vuelva a pasar en silencio.

---

## 8. Cómo correrlo

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt

# Backend (necesita data/processed/ y src/model/artifacts/, ambos commiteados)
.venv/Scripts/python -m uvicorn backend.app.main:app --port 8000

# Frontend
npm install --prefix frontend
npm run dev --prefix frontend        # http://localhost:5173
```

Las credenciales viven en un `.env` **un directorio arriba del repositorio**, así
el archivo con secretos reales queda estructuralmente fuera del árbol de Git y no
solo ignorado. Solo los scripts de recolección los necesitan; el dashboard corre
desde datos commiteados sin ninguna credencial.

Para reproducir el modelo desde cero:

```bash
.venv/Scripts/python scripts/collect_era5.py             # ~50 min, cola del CDS
.venv/Scripts/python scripts/build_per_pixel_dataset.py  # ~30 s, sin API
.venv/Scripts/python scripts/train_per_pixel.py          # el veredicto
```

---

## 9. Qué haría de esto un producto

En orden de dependencia:

1. **Coordenadas reales de estaciones y datos in situ** desde SNIA (BL-027). Esto
   desbloquea a la vez la verdad de campo y las cuatro tarjetas de estación que
   el dashboard hoy no puede llenar.
2. **Un historial satelital más largo.** 2024–2026 en vez de un año, lo que
   aproximadamente triplica las fechas ancla.
3. **Recalibrar el umbral de floración** sobre la distribución per-píxel real,
   para que la superficie de clasificación se pueda reportar.
4. **Validación de campo.** Nada de esto se contrastó contra una floración
   observada. Hasta que se haga, TRL 2 es la etiqueta correcta.

---

## 10. Dónde mirar en el repositorio

| Pregunta | Archivo |
|---|---|
| Estado actual, qué hacer después | `agents/RUN_STATE.md` |
| Cada número, con un comando que lo reproduce | `agents/validation/EVIDENCE_INDEX.md` |
| Por qué se tomó una decisión | `agents/adrs/` |
| El índice satelital | `src/features/fai.py` |
| Clima | `src/features/era5.py` |
| El modelo | `src/model/per_pixel.py` |
| Las reglas que lo mantienen honesto | `src/model/integrity.py`, `tests/test_model_integrity.py` |
