---
source: AGENTS.md
source_sha: d10f6506fe451cc71e0e49212853bb7c315f1ced
source_sha_algo: git-blob-sha1
translated: 2026-09-09
translator: agent
---

# Instrucciones para Agentes — AlgaeWatch Villarrica

Este proyecto usa un Agent Harness Kernel montado en `agents/`.

## Orden de Lectura Obligatorio

1. `agents/README.md`
2. `agents/RUN_STATE.md`
3. `agents/LOCAL_SETUP.md`
4. `agents/intake/PROJECT_BRIEF.md`
5. `agents/intake/PROJECT_PROFILE.md`
6. `agents/intake/SOURCE_MANIFEST.md`
7. `agents/validation/GATES.md`
8. `agents/execution/WORKFLOW.md`
9. `agents/i18n/TRANSLATION_PROTOCOL.md` — este proyecto trabaja en dos idiomas
10. La review relevante más reciente en `agents/reviews/`

Antes de tocar cualquier cosa bajo `src/model/`, leer además
`agents/adrs/0004-per-pixel-anomaly-redesign.md`,
`agents/validation/EVIDENCE_INDEX.md` y `agents/validation/TEST_STRATEGY.md`.

## La Mitad Local

`agents/` es verdad del proyecto y se commitea. Lo que tu agente puede hacer,
dónde vive tu checkout y qué binarios invocas son **verdad del entorno**, y viven
en `agents/local/`, que nunca se commitea.

Por lo tanto un clon nuevo llega incompleto a propósito. Construye la mitad local
antes de cualquier trabajo de implementación — `agents/LOCAL_SETUP.md` explica
cómo, y GATE-LOCAL lo hace cumplir.

## Idiomas

El inglés es canónico. Las traducciones al español viven junto a sus fuentes como
`FOO.es.md` y las siguen por hash. Ver `agents/i18n/TRANSLATION_PROTOCOL.md` y
ADR-sf-0006. Donde una traducción y su fuente no coincidan, gana la fuente.

## Reglas Centrales

- No implementar código de aplicación hasta que el harness montado sea aceptado,
  salvo que el usuario lo anule explícitamente tras revelar el riesgo. Este gate
  es incondicional — no se levanta por alcance pequeño, alta confianza ni
  contexto completo. Los supuestos rellenados desde el contexto, incluso los
  "seguros", deben exponerse para que el usuario los verifique antes de seguir.
- No implementar código de aplicación hasta que exista
  `agents/local/CAPABILITIES.md`.
- Preservar las reglas existentes del proyecto y fusionarlas en este archivo y en
  `agents/`.
- Preguntar al usuario cuando las decisiones de producto, stack, despliegue,
  evidencia o calidad no estén claras.
- Decidir la fuerza de la review a partir de tu propio capability scan. No
  asumas una capacidad porque un documento commiteado la mencione.
- Mantener la verdad del entorno, la memoria cruda y los registros de tareas bajo
  `agents/local/`; nunca commitearlos.
- Promover las decisiones duraderas a ADRs, documentos de planificación, de
  arquitectura, de validación o resúmenes de review.
- Este proyecto tiene dos colaboradores. Los nombres de archivo de ADRs y reviews
  llevan un slug de autor — `sf` y `lq`; ver ADR-sf-0005 y las reglas de
  nomenclatura en `agents/execution/WORKFLOW.md`.
- Citar artefactos en lugar de afirmarlos. Una cita es verificable, y el doctor
  comprueba que las rutas citadas existan.
- Si detectas deriva respecto del harness, detén el trabajo hacia adelante y
  produce un handoff.

## Reglas Preservadas del Proyecto

Estas reglas son anteriores al harness. Vienen del `README.md` raíz y de la
estructura de código existente, y siguen siendo vinculantes.

### PR-1 — Separación estricta feature/modelo

`src/features/` nunca debe importar de `src/model/`, y `src/model/` nunca debe
importar de `src/features/` ni llamar directamente a las APIs de Sentinel-2 / CDS.

- `src/features/` calcula el FAI y variables derivadas, nada más. Sin
  entrenamiento.
- `src/model/` sólo entrena e infiere. Consume una tabla ya construida.
- `backend/app/data_source.py` es el único puente entre el backend y el pipeline.
  Los routers llaman a `data_source`, nunca a `src/` directamente.

### PR-2 — Las credenciales viven fuera del árbol del repositorio

Las credenciales reales van en un `.env` **un directorio por encima de la raíz
del repositorio**, no dentro. El código lo resuelve con `find_dotenv()` de
`python-dotenv`, que sube directorios, así que no hay rutas absolutas hardcodeadas
y el archivo queda estructuralmente fuera del árbol de git, no meramente
gitignoreado.

Verificado el 2026-09-09: no hay secretos versionados y ninguno aparece en el
historial de git. No agregar credenciales al repo, y no debilitar esta convención.

### PR-3 — Nunca fabricar mediciones

Donde no haya datos reales, devolver `null` / `NaN` y marcar la fuente como stub.
`src/features/insitu.py` es un stub explícito porque los CSVs del SNIA no han
llegado; por eso `/observations` devuelve `null` en temperatura, pH, oxígeno
disuelto y viento. No reemplazar datos ausentes con valores inventados.

Esta regla ahora se extiende a los datos de entrenamiento — ver ADR 0004. Aplicar
relleno hacia adelante a observaciones satelitales dispersas sobre una grilla
diaria y entrenar sobre el resultado cuenta como fabricación y está prohibido.

### PR-4 — El design handoff gobierna el frontend

`design_handoff_algaewatch_villarrica/README.md` es la fuente de verdad del
frontend para layout, estructura de vistas e interacción. Las desviaciones están
permitidas pero deben registrarse como ADRs. Ya hay una registrada (ADR 0003,
librería de mapas).

Dos textos de ese handoff deben preservarse explícitamente: el sello
"TRL 2 · resultados no validados en campo" y el disclaimer del panel de IA.

El cumplimiento actual es parcial, verificado el 2026-09-09. El disclaimer del
panel de IA está correctamente hardcodeado en `backend/app/routers/forecast.py`.
El sello TRL-2 **no** se renderiza: `backend/app/routers/model_metrics.py` lo
provee sólo como argumento por defecto de `m.get("caveats", ...)`, y
`metrics.json` siempre completa `caveats`, así que el texto en español exigido es
código muerto inalcanzable. Registrado como BL-019. No tratar esta regla como
satisfecha actualmente.

## Reglas de Integridad del Modelo

Son específicas del proyecto y se agregaron tras la auditoría del 2026-09-09.

### MI-1 — Ningún modelo se entrega sin comparación contra líneas base

Todo modelo de floración debe reportarse junto a, como mínimo:

- una línea base de **persistencia** (predecir "lo mismo que hoy"), y
- una **línea base de regla trivial** (por ejemplo, predecir sólo por ubicación).

Un modelo que no le gane a ambas se reporta como que no les gana. Ver
`agents/validation/TEST_STRATEGY.md`.

### MI-2 — Sólo validación temporal

Las particiones deben ser cronológicas. El k-fold aleatorio o barajado sobre
filas ordenadas en el tiempo está prohibido. Dejar un embargo de al menos el
horizonte de pronóstico entre el fin del entrenamiento y el inicio de la
validación.

### MI-3 — Los umbrales son política, no etiquetas

No incrustar un umbral absoluto de alerta en las etiquetas de entrenamiento.
Predecir una cantidad continua; aplicar los umbrales aguas abajo, donde puedan
cambiarse sin reentrenar.
