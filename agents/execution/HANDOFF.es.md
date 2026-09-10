---
source: agents/execution/HANDOFF.md
source_sha: 50718dc683007fbd9ecb0ee0266ad028f3f79aeb
source_sha_algo: git-blob-sha1
translated: 2026-09-09
translator: agent
---

# Handoff

Escrito el 2026-09-09, para **Luchosqi** (`lq`), autor original de `4b37bea`.

El original en inglés está en `agents/execution/HANDOFF.md`. El inglés es
canónico (ADR-sf-0006), así que donde ambos difieran, gana ese archivo.

## Qué Es Esto

Vos escribiste AlgaeWatch Villarrica. Se le hizo un fork, se auditó, y se le
montó un harness de agentes en `agents/`. El repositorio se te devuelve, y este
documento es la entrega: qué se encontró, qué se está reconstruyendo, qué te
toca, y qué queda abierto.

**No se cambió código de aplicación.** Todo bajo `src/`, `backend/`, `frontend/`,
`scripts/` y `data/` está exactamente como lo dejaste en `4b37bea`. Lo único que
se agregó es `AGENTS.md`, el árbol `agents/`, `.gitattributes` y esto.

## La Versión Corta

El pipeline satelital que construiste está **correcto** y se conserva. La fórmula
del FAI coincide con Hu (2009), el enmascarado de agua por la banda SCL está
bien, y los rásters están co-registrados por bbox y resolución fijos. Se revisó
específicamente para no reescribirlo junto con todo lo demás.

La **capa de modelo no predice**, y las métricas en
`src/model/artifacts/metrics.json` no son cifras de desempeño. Seis hallazgos,
abajo, todos reproducibles desde CSVs que ya están en el repositorio. Cada uno
tiene un comando para que lo verifiques vos mismo en lugar de creerlo por
confianza.

## Los Seis Hallazgos

Los comandos de reproducción están en `agents/validation/EVIDENCE_INDEX.md`
(EV-001 a EV-013). Toda cifra citada en cualquier parte del harness tiene uno; es
una regla, adoptada después de que dos cifras sin comando resultaran haber
derivado.

| # | Hallazgo | La cifra |
|---|---|---|
| 1 | **La etiqueta codifica ubicación, no floraciones.** Con el umbral único agrupado de 0,0259, las tasas de floración por estación son sur 0,98, pucón 0,50, norte 0,00, toltén 0,00 | Una regla que lee sólo el nombre de la estación obtiene P 0,97 / R 0,74 / F1 0,84 — le gana al clasificador entrenado (0,84 / 0,47 / 0,60) en todas las métricas |
| 2 | **Se fabricaron filas de entrenamiento.** 218 lecturas reales (56 fechas de pasada × 4 estaciones, menos 6 celdas sin píxel de agua) se rellenaron hacia adelante hasta 1.356 filas diarias | Sólo existen 363 combinaciones únicas de (estación, fai_now, fai_future); el 85% de las filas tiene `fai_now` idéntico a `fai_lag_1d` |
| 3 | **La validación cruzada filtró.** `StratifiedKFold(shuffle=True)` sobre esas filas duplicadas puso copias de la misma observación en train y en validación | AUC 0,99 en CV contra AUC 0,90 en el conjunto de validación temporal — esa brecha es la firma |
| 4 | **El conjunto de validación temporal también filtra en la costura.** Train y validación comparten la fecha límite 2026-06-09 sin ningún período de embargo entre medio | Los targets a 7 días de las últimas filas de entrenamiento caen dentro de la ventana de validación |
| 5 | **El regresor pierde contra persistencia.** "Predecir lo mismo que hoy" da MAE 0,00603 | El regresor entrenado da 0,00865 — 43% peor |
| 6 | **El clasificador relee el presente.** Aplicar un umbral directamente sobre `fai_now` reproduce la etiqueta `bloom_7d` en el 90% de las filas | No está pronosticando; está reformulando el día de hoy |

Estos son hallazgos sobre un pipeline, no un veredicto sobre vos. Cada uno de
ellos es un error que llega a producción en ML con regularidad, y el número 2 es
el que vuelve casi inevitables a los otros cinco — si primero rellenás hacia
adelante, la CV barajada no puede sino filtrar después.

Tres causas de raíz: el target se binariza contra una constante absoluta
agrupada, lo que codifica el lugar; las filas se fabricaron por relleno hacia
adelante; la validación barajó filas duplicadas ordenadas en el tiempo.

## Qué Se Está Reconstruyendo, Y Por Qué

`agents/adrs/0004-per-pixel-anomaly-redesign.md`. Cuatro cambios, adoptados en
conjunto porque adoptar un subconjunto reintroduce el defecto que arreglan los
otros:

- **D1** — predecir una cantidad continua y aplicar los umbrales al momento de
  servir.
- **D2** — expresar el target como una anomalía contra una línea base *local*, no
  contra una constante agrupada del lago.
- **D3** — entrenar sobre píxeles de lago en lugar de cuatro estaciones
  placeholder. Tu `FaiRaster.sample_grid` ya produce ~1.860 píxeles de agua por
  pasada y hoy sólo se usa para dibujar el heatmap. Entrenar sobre eso lleva el
  conteo honesto de muestras de ~140 a ~65.000 en 35 pares de fechas utilizables,
  usando datos ya descargados.
- **D4** — particiones cronológicas con un embargo de al menos el horizonte de
  pronóstico.

Las métricas reportadas **van a bajar**, y ese es el resultado buscado. El
supervisor pidió mejorar el entrenamiento y que el equipo entienda los números
que maneja (SRC-002). Un número honesto y bajo con metodología correcta aprueba;
un número alto producido por filtración, no.

Algo que vale decir sin vueltas: ganarle a persistencia probablemente requiera
variables de cambio que el proyecto no tiene — viento, temperatura, radiación,
escorrentía. Eso reencuadra el backfill faltante de ERA5-Land: pasa de ser una
tarea pendiente a ser la *explicación* principal del fallo contra persistencia.

## Tu Mitad

División acordada (ADR-sf-0005). Por subsistema, así las dos mitades no comparten
archivos.

**Vos tomás el frontend.** El detalle completo está en
`agents/planning/BACKLOG.md`.

| Ítem | Qué |
|---|---|
| BL-009 | Reemplazar la paleta de riesgo de 4 paradas en `frontend/src/utils/risk.js`. Azul/verde/naranja/rojo no es perceptualmente uniforme, y verde/naranja/rojo es justo el conjunto confundible en las deficiencias de visión de color más comunes — en lo que nominalmente es una señal de salud pública |
| BL-010 | Recortar la capa de riesgo a la superficie del lago. Hoy se pinta riesgo sobre tierra |
| BL-013 | Extender la exposición de la antigüedad del dato más allá del header. `Header.jsx` ya marca correctamente una última pasada vieja vía `overlay.updated_at`; el slider de fechas, la capa del mapa y las tarjetas de estación no |
| BL-019 | Renderizar el sello obligatorio `TRL 2 · resultados no validados en campo` en la vista Modelo. Hoy es inalcanzable: `backend/app/routers/model_metrics.py` lo provee sólo como valor por defecto de `m.get("caveats", ...)`, y `metrics.json` siempre completa `caveats` |
| BL-021 | Reducir el exceso visual de plantilla generada — los dos halos de color difuminados en `app.css`, y el `backdrop-filter: blur(18px) saturate(140%)` aplicado a todos los paneles. Restyle completo si alcanza el tiempo; quitar el exceso decorativo es el piso |

**`sf` se queda con la capa de modelo**: WI-004 (convertir las líneas base de
persistencia y de regla trivial en verificaciones permanentes y re-ejecutables) y
después WI-005 (el reentrenamiento honesto). El contexto de la auditoría vive
ahí, y traspasarlo implicaría transferir primero toda la sesión de auditoría.

## Qué Te Toca Decidir A Vos

**ADR 0003 — la librería de mapas.** El design handoff
(`design_handoff_algaewatch_villarrica/README.md`) exige Mapbox GL JS; el código
usa Leaflet con tiles satelitales de Esri. Esa desviación se registró como
**provisional justamente a la espera de tu opinión**, y ahora es tu decisión
porque el frontend es tuyo. Leaflet se mantiene hasta que respondas. El trabajo
de frontend no debería empezar antes — una reversión tardía cuesta horas.

## Antes De Empezar

**Construí tu mitad local.** `agents/` está commiteado y compartido;
`agents/local/` nunca se commitea y llega vacío. Copiá
`agents/templates/capability-scan-template.md` a `agents/local/CAPABILITIES.md` y
completalo para *tu* máquina. `agents/LOCAL_SETUP.md` explica por qué, y
GATE-LOCAL bloquea el trabajo de implementación hasta que exista.

Esto no es burocracia. No leas el scan commiteado en
`agents/reviews/20260909/capability_scan.md` como si fuera actual — describe una
máquina Windows en un día, y un agente que se lo crea va a planificar reviews
delegadas que quizá no pueda correr, y después las va a reportar como hechas.

**Corré las verificaciones.** Ambas viven dentro del harness, así que viajan con
él:

```bash
python agents/harness_doctor.py --root . --strict
python agents/check_translations.py
```

**Convenciones que si no van a morder.** Los nombres de archivo de ADRs y reviews
llevan un slug de autor — el tuyo es `lq`, así que tu próximo ADR es
`lq-0007-nombre.md`. Agregá filas nuevas al *final* de las tablas índice, para
que las ediciones concurrentes den conflicto visible en lugar de entremezclarse
en silencio. Nunca compartas un working tree con otra sesión de agente
concurrente.

## Qué Sigue Bloqueado

| Bloqueante | Efecto |
|---|---|
| Credenciales del Copernicus Data Space Ecosystem (WI-002) | Bloquean BL-007 y BL-008, y por lo tanto el hito M3, el rediseño por píxel. **No** bloquean M2, el reentrenamiento honesto sin credenciales, que es el entregable garantizado |
| PyTorch no instalado | El ADR 0002 lo hace vinculante por indicación del supervisor. Detectado en el scan del 2026-09-09; bloquea BL-008 con independencia de las credenciales. M2 no se ve afectado — se queda deliberadamente en scikit-learn |
| Aceptación del harness (GATE-HM) | Ningún código de aplicación empieza hasta que el propietario acepte el harness montado |
| Sin suite de tests | GATE-TEST no tiene nada que correr hasta que aterrice BL-002 |

## Cosas Que No Son Obvias Desde El Código

- El pitch es aproximadamente el 2026-09-10 (ASM-001). Confirmar antes de
  planificar alrededor de esa fecha.
- `src/model/artifacts/metrics.json` se conserva **sólo por procedencia**. Su
  propio campo `caveats` es honesto; la prosa del README que lo rodea no.
- `data/processed/training_dataset.csv` nunca debe entrenar un modelo que se
  entregue. Se conserva como evidencia del defecto auditado.
- Las coordenadas de las cuatro estaciones son **placeholders**. No tienen
  significado científico, y una de ellas caía originalmente en tierra firme — un
  bug real, encontrado y corregido, en el radio de búsqueda de `at_latlon`.
- El `README.md` raíz sobredimensiona lo que corre sobre datos reales. "Sin
  mocks, todo el backend corre sobre datos reales" es cierto sólo para la mitad
  del FAI: ERA5 nunca se recolectó, in situ es un stub, y las coordenadas de las
  estaciones son placeholders. Registrado como BL-011, sin asignar.
- El proyecto corre el backend y el dashboard con **cero credenciales** contra
  datos commiteados. Eso es deliberado. Protegelo.
- Una corrida verde de `harness_doctor.py` es una verificación estructural, no de
  verdad. Una vez reportó cero bloqueantes mientras `RUN_STATE.md` afirmaba un
  documento de review que no existía.
- Toda cifra citada en un documento del harness debe llevar un comando de
  reproducción en `EVIDENCE_INDEX.md`. Todas las cifras que lo tenían siguieron
  siendo exactas; las dos que no lo tenían habían derivado para cuando se
  revisaron.

## Lecturas Obligatorias

1. `AGENTS.md` — las reglas operativas, incluidas las propias del proyecto
   PR-1…PR-4 y las de integridad del modelo MI-1…MI-3
2. `agents/RUN_STATE.md` — dónde está realmente el proyecto
3. `agents/LOCAL_SETUP.md` — y después construí tu mitad local
4. `agents/planning/BACKLOG.md` — tus cinco ítems completos
5. `agents/adrs/0003-map-library-leaflet-provisional.md` — tu decisión

Antes de tocar `src/model/` en absoluto: ADR 0004,
`agents/validation/EVIDENCE_INDEX.md`, `agents/validation/TEST_STRATEGY.md`.
