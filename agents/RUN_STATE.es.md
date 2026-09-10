---
source: agents/RUN_STATE.md
source_sha: 2ab9bab4906ac674fe9ab4352455484bc4c4e347
source_sha_algo: git-blob-sha1
translated: 2026-09-10
translator: agent
---

# Estado de Ejecución

## Fase Actual

**El reentrenamiento per-píxel está construido, entrenado y medido (2026-09-10,
ADR-sf-0010), en la rama `feat/per-pixel-retrain-verdict` — todavía sin mergear
y SIN revisión independiente.** Es el primer modelo de este repositorio entrenado
con insumos reales de punta a punta: 56 pasadas Sentinel-2, 13 meses de
ERA5-Land, ninguna fila rellenada.

**Pierde contra ambas líneas base.** MAE 0,001999 ± 0,001501 contra persistencia
0,001402 y climatología 0,001296 — el resultado reportado bajo la regla MI-1, no
un número a mejorar tuneando. Dos de cuatro folds *sí* superan a la climatología;
el fold 2 (2026-02-13..2026-03-08, la ventana más volátil de la serie y la que
importa operativamente) es catastrófico con 0,004568 y arrastra la media sin
ponderar. El intervalo q10–q90 está bien calibrado: cobertura 0,8135 contra un
nominal de 0,80.

**Integrado al producto en la rama `demoday` (basada en la anterior).**
`src/model/per_pixel_infer.py` le da al artefacto su primer camino de carga —
era de solo escritura — y `GET /model/candidate` reporta al candidato junto a
sus líneas base con el detalle por fold. La vista Modelo lo renderiza, con la
etiqueta `NO ALIMENTA EL MAPA`, porque `/risk` y `/forecast` siguen corriendo
los artefactos legacy. Tres bugs corregidos en el camino: un bug de codificación
cp1252 en Windows que mostraba los caveats en español como mojibake, un crash de
`getImageData` con ancho cero en `leaflet.heat` que desmontaba el dashboard
**entero**, y la ausencia de cualquier error boundary de React. Tests: 92
pasados / 8 xfailed.

También en esa rama: las dos preguntas abiertas de `PARA_JUN.md` §3 quedaron
decididas (ADR-sf-0010 D1/D2), y se corrigieron tres defectos encontrados al
correr el runbook de punta a punta — `collect_era5.py` nunca podía completarse,
`baselines.trivial_rule` hacía caer toda la verificación sobre una tabla de
objetivo continuo, y un test de plomería asumía que siempre había etiqueta. Ver
"Bloqueadores" para lo que sigue abierto.

Harness aceptado. Implementación en curso en la mitad de `sf`. **WI-004 está
terminado** — las líneas base y las verificaciones de integridad del modelo son
ahora una suite de tests permanente. **BL-029 a BL-032 están corregidos** — los
cuatro defectos de corrección de la verificación que encontró la revisión de
diseño de WI-005, dos de ellos falsos positivos de paso. **WI-005 está
construido** (ADR-lq-0009): `src/features/lake_anomaly.py`,
`src/model/lake_anomaly.py`, una tabla candidata versionada y artefactos
honestos. El reentrenamiento interino de media de lago **pierde contra ambas
líneas base** — el resultado reportado bajo la regla MI-1. Todo esto estaba en
la rama `fix/sf-model-gate-correctness`, **revisado de forma independiente** —
APROBAR CON CORRECCIONES, sin Críticos, ambos falsos positivos confirmados como
cerrados, la ruta legada confirmada intacta; el único hallazgo Importante (un
falso *negativo* en particiones densas de horizonte variable) y seis hallazgos
Menores corregidos en la misma rama, luego **integrado a `main` el 2026-09-10.**
El brief para el próximo empujón — reentrenar para superar ambas líneas base vía
per-píxel + clima — está en `agents/execution/SESSION_HANDOFF.lq.md`.

## Estado

- **BL-029 a BL-032 corregidos y WI-005 construido, 2026-09-10** (ADR-lq-0009),
  por `lq` haciendo las veces de `sf` en la mitad del modelo. **Revisada de
  forma independiente** (APROBAR CON CORRECCIONES, sin Críticos —
  `implementation-review.lq.md`), todos los hallazgos aplicados, **integrada a
  `main` el 2026-09-10.** Los cuatro defectos de la verificación — dos de ellos
  falsos positivos de paso — están corregidos con
  evidencia de antes/después. El reentrenamiento interino de media de lago
  (`src/features/lake_anomaly.py`, `src/model/lake_anomaly.py`) es honesto y
  **pierde contra persistencia y climatología** (EV-021); cumple PR-3 y descarta
  la etiqueta que hacía de proxy de ubicación. No es desplegable y no llena las
  cuatro tarjetas de estación. La costura `unit_col` está lista para ADR 0004 D3
  (`pixel_id`).
- **El usuario aceptó el harness el 2026-09-10**, liberando GATE-HM. Kernel
  `5dee2cf`, dos contribuyentes, inglés canónico con hermanos en español.
- **GATE-LOCAL no estaba realmente liberado al comenzar esta sesión.** El
  RUN_STATE anterior afirmaba que `agents/local/CAPABILITIES.md` existía; no
  existía, ni en el checkout principal ni en el worktree, y
  `harness_doctor.py --strict` lo reportó como bloqueador duro en la primera
  corrida. Se escribió un escaneo nuevo y el doctor ahora reporta 0 bloqueadores
  y 0 advertencias. Es la segunda vez que una afirmación de RUN_STATE se adelanta
  a la realidad — ver la nota sobre las limitaciones del script en
  `agents/validation/DOCTOR.md`.
- **WI-004 / BL-002 entregado.** `src/model/baselines.py` (persistencia, regla
  trivial, un particionador cronológico con embargo), `src/model/integrity.py`
  (siete verificaciones de GATE-MODEL) y `tests/` (36 pasaron, 7 xfailed).
  EV-016.
- **Revisado por un subagente**, no autorrevisado. Tres hallazgos, todos
  corregidos. El serio: las líneas base se estaban calculando sobre una partición
  reconstruida con un ordenamiento no estable, así que podían haberse medido
  sobre filas distintas a las del modelo. Ver
  `agents/reviews/20260910/implementation-review.sf.md`.
- **`train.py` ahora reporta las líneas base** junto a cada métrica, y
  `src/model/artifacts/metrics.json` lleva `baselines` y `beats_baselines`, ambos
  `false`. La regla MI-1 se cumple en el artefacto. **No** se cumple en pantalla:
  la vista Modelo sigue mostrando métricas desnudas, que es BL-026.
- **Se encontró un defecto nuevo, aguas arriba de los hallazgos de la
  auditoría.** Dos de las cuatro coordenadas de estación no están sobre el lago
  — pucon a 0,77 km y sur a 0,98 km del píxel de agua muestreado más cercano, y
  sur al sur del lago por completo — así que su FAI es vegetación de ribera, no
  agua. EV-014, ADR-sf-0007, BL-027.
- **Las credenciales funcionan.** El endpoint de token de CDSE autentica
  (EV-015). El bloqueador WI-002 registrado aquí estaba obsoleto. `CDS_TOKEN` y
  `GEMINI_API_KEY` están presentes pero aún sin ejercitar.
- **PyTorch instalado con CUDA funcionando** — `2.14.0+cu126` sobre una GTX 1650,
  sm_75 (EV-017). WI-010 / BL-024 liberados.
- **PR-2 restaurada.** El `.env` real estaba *dentro* de la raíz del repositorio,
  en `H:\algaewatch-villarrica\.env`, protegido solo por una línea de gitignore y
  no estructuralmente. Se movió un directorio por encima de la raíz, donde
  `find_dotenv()` lo sigue resolviendo. No hubo filtración: no estaba versionado,
  y EV-006 sigue siendo válido.
- Las reglas del proyecto preexistentes se preservaron y se fusionaron en
  `AGENTS.md` como PR-1 a PR-4.
- Dos lenguas de trabajo, GATE-I18N activo (ADR-sf-0006).
- **El trabajo de frontend de `lq` está integrado, y llegó por `main`.** ADR 0003
  aceptado (Leaflet se mantiene), la pasada de credibilidad de WI-009 terminada
  con capturas — la rampa magma validada para CVD de BL-009, el overlay recortado
  al lago de BL-010, la divulgación de obsolescencia de BL-013, el sello TRL-2 de
  BL-019 ahora sí renderizado, y el vidrio y los halos de BL-021 recortados — más
  un tema pastel claro con barra superior (ADR-lq-0008). Ambos commits fueron
  directo a `main`, que `WORKFLOW.md` reserva para estado liberado integrado desde
  `develop`; `develop` ahora los contiene por merge.
- **Una colisión de IDs, resuelta por orden de acuñación.** Dos ítems de trabajo
  se acuñaron como WI-011: la instalación del venv a las 00:34:51, y la pasada de
  tema claro de `lq` a las 01:17:17 desde una base que no tenía ninguna de las
  dos. WI-011 sigue siendo la instalación del venv; la pasada de tema es WI-013.
  `lq` también volvió a marcar WI-010 como bloqueado en contra de EV-017 — no fue
  un desacuerdo: no había traído la rama que lo registraba. Restaurado a
  terminado, con su alcance ahora declarado como la máquina de `sf`. La nota
  completa está en `WORK_ITEMS.md`; la regla de agregar al final es lo que hizo
  visibles ambas cosas en lugar de silenciarlas.
- **GATE-I18N estaba fallando, y lo que estaba mal era la verificación.** El
  estado de más abajo afirmaba 5 de 5 al día; la primera corrida de la sesión
  siguiente reportó uno obsoleto. `RUN_STATE.es.md` había registrado el sha de
  blob con **CRLF** de una fuente que en realidad había traducido de forma
  correcta y completa. `check_translations.py` hasheaba los bytes en disco, así
  que el hash registrado describía la copia de trabajo de la sesión anterior y no
  el commit. Ahora convierte CRLF a LF antes de hashear. EV-018, commit
  `c875514`; es la tercera vez que una afirmación se adelanta a la realidad, y la
  primera cuyo remedio fue corregir la verificación en lugar de la afirmación —
  ver `DOCTOR.md`.
- **WI-005 está diseñado, no construido (ADR-sf-0008).** Su formulación
  original, "reentrenamiento honesto sobre datos de estación", es nula bajo
  ADR-sf-0007. La señal admisible es `lake_mean_fai` — la media sobre la máscara
  de agua, sin ninguna coordenada de estación en su derivación — que da 35 pares
  honestos. Dos mediciones dieron forma al diseño: la climatología causal (MAE
  0,000945) **le gana** a la persistencia (0,001333), así que ganarle solo a la
  persistencia no prueba nada; y el umbral de bloom registrado, 0,025916, está un
  orden de magnitud por encima del máximo del lago, 0,001999, así que aplicado a
  escala de lago etiqueta todas las filas como negativas y toda la superficie de
  clasificación queda vacía hasta que se recalibre. EV-019, EV-020.
- **La revisión de diseño encontró tres defectos en código ya versionado**, y por
  eso no se implementó nada: `chronological_split` aplica el embargo a la fecha de
  las features en lugar de la fecha del objetivo, y su verificación igual reporta
  "pasa" (BL-029); `trivial_rule` se reduce a "predecir siempre positivo" en una
  tabla de un solo grupo (BL-030); y la guarda de inaplicabilidad debe estar
  dentro de la verificación y no solo en `run_all`, porque los tests la llaman
  directamente (BL-031). Dos de los tres producen un **falso positivo de paso**.

## Próxima Acción

**1. Revisar `feat/per-pixel-retrain-verdict` de forma independiente antes de
mergear.** Definición de Hecho §7. Nadie más que su autor la revisó, y toca
código de verificación (`src/model/baselines.py`,
`tests/test_model_integrity.py`), que es justo la categoría que produjo dos
falsos pases en WI-005. Registrar el veredicto en `agents/reviews/20260910/` y en
`reviews_index.md`.

**2. Decidir qué hacer con `check_no_fabricated_rows` (BL-037).** Falla sobre la
tabla per-píxel con inflación 1,011. Investigado: es un falso positivo. 562
grupos duplicados, *ninguno* compartiendo fecha, sobre un `fai_now` que tiene
solo 1.996 valores distintos en 56.668 filas porque el FAI está cuantizado a 5
decimales. La verificación **no** se tocó a propósito — agregarle `date` a su
clave la haría pasar y además destruiría la detección de forward-fill para la
que existe. La corrección la debe elegir alguien que no sea el autor del
candidato.

**3. Después, si se quiere mejorar el modelo:** el detalle por fold dice que el
problema es volatilidad, no variables. El desvío del objetivo en el fold 2 es
2,35 contra ~0,7 en el resto. Una pérdida de colas más pesadas, una línea base
consciente de la varianza, o simplemente más pasadas son las palancas honestas.
No tunear contra los folds reportados.

Contexto histórico del empujón que produjo esto —
`agents/execution/SESSION_HANDOFF.lq.md`. En
resumen: el modelo interino de media de lago no puede pasar a la climatología
porque la serie de media de lago es ruido alrededor de una media que decae lento
y no tiene change-drivers. El salto real es ADR 0004 D3 + D4 juntos — **muestreo
por píxel** (BL-007: rellenar la grilla FAI sobre las 56 pasadas → ~65.000
muestras, pasarla por el mismo `build_anomaly_pairs` con `unit_col="pixel_id"`) y
**clima de ERA5 como change-drivers** (BL-012). Ambos bloqueados por **WI-011**
(del usuario: `pip install cdsapi rasterio xarray`), más la licencia de ERA5 de
CDS y, para BL-008, PyTorch en esta máquina (ADR 0002).

Resumen de WI-005 (ADR-lq-0009, EV-021): el reentrenamiento interino de media de
lago es honesto y **no** le gana a la persistencia (0,0014) ni a la climatología
(0,0008) — `mae_fai` 0,0039 ± 0,0021 en CV de ventana expansiva de 4 pliegues.
Corrige la fabricación (PR-3) y la etiqueta que hacía de proxy de ubicación; no
es un modelo desplegable, y no llena las cuatro tarjetas de estación del
tablero. `src/model/artifacts/` (el del backend) está intacto byte a byte; los
artefactos honestos están en `src/model/artifacts/lake_anomaly/`.

La mitad de `lq`: ADR 0003 aceptado, WI-008 / WI-009 / WI-013 terminados.
`develop` fue retirado el 2026-09-10 — el trabajo va directo a `main`
(`WORKFLOW.md`).

## Lista de Progreso

Se mantiene al día para que otro contribuyente pueda retomar esto a mitad de
vuelo.

| Paso | Estado |
|---|---|
| Harness aceptado (GATE-HM) | hecho 2026-09-10 |
| Mitad local construida (GATE-LOCAL) | hecho — `agents/local/CAPABILITIES.md`, doctor 0/0 |
| `.env` movido fuera del árbol del repositorio (PR-2) | hecho |
| `src/model/baselines.py` | hecho, commiteado |
| `src/model/integrity.py` | hecho, commiteado |
| Suite `tests/` + `pytest.ini` + `pytest` en requirements | hecho, commiteado |
| `train.py` registra líneas base; artefactos regenerados | hecho, commiteado |
| Evidencia, ADR, backlog, work items y estrategia de test actualizados | hecho |
| Doctor y verificación de traducciones recorridos y registrados | hecho |
| Revisión independiente del diff de WI-004 | hecho — APROBAR CON CORRECCIONES, 3 hallazgos, todos resueltos en `c49c9a5` |
| Corrección del hasheo de GATE-I18N | hecho — EV-018, commit `c875514` |
| Señal y alcance de WI-005 | hecho — ADR-sf-0008, aprobado por el usuario |
| Revisión de diseño de WI-005 | hecho — cuatro defectos en código versionado, BL-029 a BL-032 |
| Correcciones de verificación BL-029 a BL-032 | hecho — ADR-lq-0009; ambos falsos positivos demostrados corregidos; suite por defecto 70 pasaron / 7 xfailed |
| Reentrenamiento WI-005 | hecho — ADR-lq-0009; pierde contra ambas líneas base (EV-021); gate candidato 11 pasaron / 1 omitido / 4 xfailed |
| Revisión independiente del diff de BL-029..032 + WI-005 | hecho — APROBAR CON CORRECCIONES, `implementation-review.lq.md`; 1 Importante + 6 Menores aplicados |
| Integrar `fix/sf-model-gate-correctness` a `main` | hecho 2026-09-10 |
| Brief de reentrenamiento para superar las líneas base | hecho — `agents/execution/SESSION_HANDOFF.lq.md` (per-píxel D3 + ERA5 D4, prerrequisitos, mapa de reúso, restricciones, criterios de hecho) |

## Bloqueadores

- **BL-037 — `check_no_fabricated_rows` se dispara mal sobre la tabla
  per-píxel. ABIERTO.** Inflación 1,011. Investigado y confirmado falso
  positivo (EV-024c): 562 grupos duplicados, ninguno compartiendo fecha, sobre
  un `fai_now` que tiene solo 1.996 valores distintos en 56.668 filas, porque el
  FAI está cuantizado a 5 decimales. **No** se corrigió a propósito por parte
  del autor del candidato — agregarle `date` a la clave lo hace pasar y destruye
  la detección de forward-fill para la que existe. Necesita la decisión de otra
  persona. Bloquea una corrida limpia de GATE-MODEL, no el veredicto en sí.
- **BL-035, BL-036 — resueltos 2026-09-10** (ADR-sf-0010, EV-024). El ensamblado
  de `era5.py` descartaba una columna que su propia proyección ya había sacado,
  así que `collect_era5.py` nunca podía completarse; `baselines.trivial_rule`
  hacía caer toda la verificación sobre una tabla sin `bloom_7d`; y el test de
  plomería asumía que siempre había etiqueta. Los tres corregidos.
- **WI-011 / BL-028 — RESUELTO 2026-09-10.** El pipeline de features corre. Un
  `.venv` nuevo desde `pip install -r requirements.txt` importa `sentinelhub`,
  `cdsapi`, `rasterio`, `xarray`, `netCDF4` y `torch`, y `collect_era5.py`
  completó un backfill entero de 13 meses. Ojo: la entrada anterior estaba a su
  vez desactualizada: **no existía ningún `.venv` en ninguno de los seis
  checkouts** cuando arrancó esta sesión (EV-022).
- **Definición de Hecho §7 — revisión independiente de
  `feat/per-pixel-retrain-verdict`. ABIERTO.** Nadie más que su autor la
  revisó. Había subagentes disponibles y no se usaron; queda registrado como
  pendiente, no como degradado en silencio.

- **BL-029, BL-030, BL-031, BL-032 — liberados el 2026-09-10** (ADR-lq-0009). El
  embargo a la fecha del objetivo, el despacho a climatología en un solo grupo,
  la guarda de inaplicabilidad dentro de la verificación y los tests de
  plomería agnósticos a la forma están todos en su lugar; ambos falsos positivos
  quedan demostrados corregidos. Ya no bloquean BL-003 a BL-006 ni WI-005 —
  WI-005 está construido.
- **WI-011 / BL-028 — el pipeline de features sigue sin poder correr.** En el
  `.venv` de `lq` (2026-09-10) `sentinelhub` 3.11.5 está presente pero `cdsapi`,
  `rasterio` y `xarray` no, así que
  `python -c "import sentinelhub, cdsapi, rasterio, xarray"` todavía falla. Que
  las credenciales funcionen no significa que la recolección funcione. Bloquea
  BL-007, BL-012, BL-014, y BL-008 en la práctica. (La nota anterior de "no hay
  entorno virtual" describía la máquina de `sf`; corregida aquí — existe un
  `.venv` en el checkout de `lq` y corre los tests y ambos reentrenamientos.)
- **WI-012 / BL-027 — coordenadas de estación.** Bloqueado a la espera del GPS
  real que llega con los CSV del SNIA. Hasta entonces, ADR-sf-0007 descalifica el
  FAI de punto de estación como señal de entrenamiento, y
  `check_station_points_on_water` lo hace cumplir.
- **ADR 0003 está resuelto** y ya no bloquea nada. Leaflet se mantiene, aceptado
  por `lq` el 2026-09-10, y WI-008 y WI-009 están ambos terminados.

## Último Estado Verificado

### 2026-09-10, `feat/per-pixel-retrain-verdict` (reentrenamiento per-píxel)

Entorno reconstruido desde cero esta sesión — **no existía `.venv`, ni
`data/raw/era5/`, ni `frontend/node_modules` en el checkout principal ni en
ninguno de los cinco worktrees**, contrario a `PARA_JUN.md` §1. Python 3.11.0,
`torch 2.14.0+cpu` desde un `pip install -r requirements.txt` normal.

- `python -m pytest -q` — **80 pasados, 8 xfailed** (era 78/8; +2 por la costura
  de early stopping).
- `python agents/harness_doctor.py --root . --strict` — 0 bloqueadores, 0
  advertencias. GATE-LOCAL necesitó un `agents/local/CAPABILITIES.md` nuevo; ese
  directorio nunca se commitea, así que **cada worktree nuevo tiene que
  re-escanear**.
- `python agents/check_translations.py` — 5 revisados, 0 problemas.
- `python scripts/collect_era5.py` — 13 meses, **56 filas** a
  `data/processed/era5_daily.csv`. Tardó ~50 min de cola de CDS.
- `python scripts/build_per_pixel_dataset.py` — 56.668 pares, 1.866 píxeles, 34
  anclas. Bloques {0: 3625, 1: 11932, 2: 9977, 3: 31134}. ~30s, sin API.
- `python scripts/train_per_pixel.py` — **MAE 0,001999 ± 0,001501 |
  persistencia 0,001402 | climatología 0,001296 | supera ambas: false.**
- **Corrida de GATE-MODEL del candidato** —
  `ALGAEWATCH_DATASET=data/processed/per_pixel_anomaly_dataset.csv`
  `ALGAEWATCH_METRICS=src/model/artifacts/per_pixel/metrics.json`
  `python -m pytest -q tests/test_model_integrity.py` → **12 pasados, 2
  saltados, 3 fallados.** Los tres fallos son las dos pérdidas honestas de MI-1
  más el falso positivo documentado de `no_fabricated_rows` (BL-037). Ninguna
  verificación se cae más. Ojo: el runbook de `PARA_JUN.md` paso 4 da este
  comando con un nombre de archivo pelado; la variable toma una **ruta relativa
  a la raíz del repo**.
- Dashboard verificado corriendo de punta a punta: `uvicorn
  backend.app.main:app --port 8000` más `npm run dev --prefix frontend`; las
  cuatro vistas renderizan datos reales, `npm run build` limpio en 2,17s. La
  tarjeta de baselines de BL-026 en la vista Modelo se muestra bien.
- `src/model/artifacts/` (el modelo legacy del backend) está **sin cambios salvo
  el string `caveats`**; todas las métricas son idénticas byte a byte, verificado
  clave por clave.

### Anteriores

- `python agents/harness_doctor.py --root . --strict` — 0 bloqueadores, 0
  advertencias. Registrado en `agents/validation/DOCTOR.md`.
- `python agents/check_translations.py` — 5 de 5 al día, después de la corrección
  del hasheo en `c875514`. Re-verificado reescribiendo una fuente con CRLF y
  confirmando que la verificación sigue en verde, así que esta cifra ahora sí es
  transferible entre checkouts.
- `python -m pytest -q` — **70 pasaron, 7 xfailed** en el `.venv` de `lq`
  (py3.13, scikit-learn 1.7.2). Eran 36/7 en EV-016; +34 por las correcciones de
  verificación BL-029..032, WI-005, y los tests de regresión/artefacto de la
  revisión.
- **Corrida candidata de GATE-MODEL** —
  `ALGAEWATCH_DATASET=data/processed/lake_anomaly_dataset.csv`
  `ALGAEWATCH_METRICS=src/model/artifacts/lake_anomaly/metrics.json`
  `python -m pytest -q tests/test_model_integrity.py` → **11 pasaron, 1 omitido,
  4 xfailed**. El reentrenamiento de media de lago pasa `no_fabricated_rows`
  (PR-3) y `label_not_a_proxy` (inaplicable, una unidad); sigue en xfail MI-1
  contra persistencia, la verificación de regla trivial (f1 nulo), la
  verificación de atajo con etiqueta constante, y la procedencia de estaciones.
  El test de MI-2 se omite — su fixture `pipeline_split` es una ruta de cuatro
  estaciones que WI-005 no usa.
- Artefactos del modelo regenerados desde el `training_dataset.csv` versionado.
  Precisión, recall, F1, AUC y la matriz de confusión se reproducen exactamente;
  `mae_fai` se movió de 0,00865 a 0,00867 y la media de CV AUC de 0,9922 a
  0,9925. El artefacto versionado ya discrepaba con la propia reproducción de
  EV-013 antes de este cambio; la deriva y su causa probable quedan registradas
  en `EVIDENCE_INDEX.md` en lugar de reemplazarse en silencio.
- `data/processed/` está intacto byte a byte. Los artefactos se regeneraron
  llamando a `train()` sobre la tabla versionada, no vía
  `scripts/train_model.py`, que habría reconstruido y sobrescrito la tabla a la
  que está anclada cada cifra de evidencia.
- La ruta de carga del backend sigue funcionando contra los artefactos
  regenerados (`src.model.infer.load_artifacts`, `predict_risk`).
- **Código de aplicación modificado esta sesión** (rama
  `fix/sf-model-gate-correctness`): `src/model/baselines.py`,
  `src/model/integrity.py` (BL-029..032); nuevos `src/features/lake_anomaly.py`,
  `src/model/lake_anomaly.py`, `scripts/train_lake_anomaly.py` (WI-005); tests
  nuevos. Datos versionados nuevos: `data/processed/lake_anomaly_dataset.csv`,
  `src/model/artifacts/lake_anomaly/`. `src/model/artifacts/` (el del backend) y
  `src/model/train.py` están intactos byte a byte respecto del estado de WI-004;
  `backend/`, `frontend/` sin tocar por `sf`.
