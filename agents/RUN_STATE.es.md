---
source: agents/RUN_STATE.md
source_sha: 414532090372649b81d085721182dec689560df7
source_sha_algo: git-blob-sha1
translated: 2026-09-10
translator: agent
---

# Estado de Ejecución

## Fase Actual

Harness aceptado. Implementación en curso en la mitad de `sf`. **WI-004 está
terminado** — las líneas base y las verificaciones de integridad del modelo son
ahora una suite de tests permanente. **WI-005 está diseñado y bloqueado**: su
señal y su alcance quedaron resueltos en ADR-sf-0008, y una revisión de diseño
encontró tres defectos en código ya versionado (BL-029 a BL-031) que hay que
corregir antes de poder juzgar honestamente cualquier reentrenamiento.

## Estado

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

Corregir **BL-029, BL-030, BL-031 y BL-032**, en ese orden, antes de implementar
WI-005. Las cuatro son correcciones a la verificación y a sus líneas base; dos de
ellas hoy producen un falso positivo de paso, que es peor que una falla. La
verificación es lo que hace comprobable un reentrenamiento, así que primero tiene
que estar bien.

Después implementar WI-005 según ADR-sf-0008: un nuevo módulo
`lake_anomaly.py` bajo `src/features/`, sin importar `sentinelhub`, parametrizado por una
columna de unidad espacial para que ADR 0004 D3 sustituya `pixel_id` en lugar de
forzar una reescritura; una línea base móvil causal calculada sobre observaciones
estrictamente **anteriores** a `t`; Ridge en lugar de GradientBoosting sobre 35
filas; `mae_fai` con su dispersión de CV como cifra principal y las cifras de
clasificación en `null` bajo PR-3. Los artefactos honestos van a un directorio
nuevo — `src/model/artifacts/` no debe sobrescribirse, porque el backend lo carga
al importar y sirve por estación, así que un modelo de lago completo no puede
llenar cuatro tarjetas de estación. Recablear la ruta de servicio no es WI-005.

**WI-011 es el ítem de mayor apalancamiento del tablero y le corresponde al
usuario.** Cuatro instalaciones — `sentinelhub`, `cdsapi`, `rasterio`, `xarray` —
convierten credenciales que funcionan en un pipeline ejecutable, lo que le da a
BL-007 la grilla por píxel, lo que convierte 35 filas en unas 65.000 (EV-008).

La mitad de `lq` avanzó: ADR 0003 aceptado, WI-008 y WI-009 terminados, más una
pasada de tema claro (WI-013). Integrado a `develop` al final de esta sesión.

Hay un traspaso de sesión que cubre lo hecho, lo que el backlog espera a
continuación, y cómo retomar desde `develop`, en
`agents/execution/SESSION_HANDOFF.sf.md`.

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
| Revisión de diseño de WI-005 | hecho — tres defectos en código versionado, BL-029 a BL-031 |
| Reentrenamiento WI-005 | **bloqueado** por BL-029, BL-030, BL-031, BL-032 |

## Bloqueadores

- **BL-029, BL-030, BL-031, BL-032 — la corrección de la propia verificación.**
  Dos de las cuatro producen un falso positivo de paso en lugar de una falla:
  `chronological_split` aplica el embargo a la fecha de las features y no a la del
  objetivo, y `check_chronological_split` compara solo contra la constante
  `HORIZON_DAYS = 7`; y `check_label_not_stratified_by_station` reporta una
  dispersión de 0,000 como aprobada en una tabla de un solo grupo. Estas bloquean
  WI-005 y, a través de él, BL-003 a BL-006.
- **WI-011 / BL-028 — el pipeline de features no puede correr en esta máquina.**
  `sentinelhub`, `cdsapi`, `rasterio` y `xarray` están todos ausentes del
  intérprete en el PATH y no hay entorno virtual. Que las credenciales funcionen
  no significa que la recolección funcione. Esto bloquea BL-007, BL-012 y BL-014,
  y por lo tanto BL-008 en la práctica.
- **WI-012 / BL-027 — coordenadas de estación.** Bloqueado a la espera del GPS
  real que llega con los CSV del SNIA. Hasta entonces, ADR-sf-0007 descalifica el
  FAI de punto de estación como señal de entrenamiento, y
  `check_station_points_on_water` lo hace cumplir.
- **ADR 0003 está resuelto** y ya no bloquea nada. Leaflet se mantiene, aceptado
  por `lq` el 2026-09-10, y WI-008 y WI-009 están ambos terminados.

## Último Estado Verificado

- `python agents/harness_doctor.py --root . --strict` — 0 bloqueadores, 0
  advertencias. Registrado en `agents/validation/DOCTOR.md`.
- `python agents/check_translations.py` — 5 de 5 al día, después de la corrección
  del hasheo en `c875514`. Re-verificado reescribiendo una fuente con CRLF y
  confirmando que la verificación sigue en verde, así que esta cifra ahora sí es
  transferible entre checkouts.
- `python -m pytest -q` — 36 pasaron, 7 xfailed (EV-016).
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
- **El código de aplicación ya fue modificado**, por primera vez desde el fork:
  `src/model/train.py` y los artefactos bajo `src/model/artifacts/`, más los
  módulos y tests nuevos. `src/features/`, `backend/`, `frontend/`, `scripts/` y
  `data/` siguen tal como los dejó el autor original.
