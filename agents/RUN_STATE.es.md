---
source: agents/RUN_STATE.md
source_sha: a3700d65c79b2c751369495591f6a7314aa8e18e
source_sha_algo: git-blob-sha1
translated: 2026-09-10
translator: agent
---

# Estado de Ejecución

## Fase Actual

Harness aceptado. Implementación en curso en la mitad de `sf`. **WI-004 está
terminado** — las líneas base y las verificaciones de integridad del modelo son
ahora una suite de tests permanente — y el siguiente paso es WI-005, el
reentrenamiento honesto.

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

## Próxima Acción

`sf` comienza **WI-005** — el reentrenamiento honesto: objetivo continuo, anomalía
contra una línea base local, solo pares de observaciones reales, y particiones
cronológicas con un embargo del largo del horizonte (BL-003 a BL-006). La
verificación ya está escrita, así que el éxito está definido de antemano: los
xfail de `tests/test_model_integrity.py` deben pasar a verde y sus marcas deben
retirarse en el mismo cambio.

Leer la frase "sobre datos de estación" de WI-005 a la luz de ADR-sf-0007. Las
correcciones de modelado siguen siendo correctas y valen la pena; por sí solas no
pueden hacer que cuatro coordenadas provisorias midan el lago. El muestreo por
píxel (ADR 0004 D3) es el camino hacia un modelo que sí trate sobre agua, y
requiere WI-011 primero.

`lq` sigue debiendo ADR 0003 antes de que empiece el trabajo de frontend.

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
| Reentrenamiento WI-005 | sin empezar |

## Bloqueadores

- **WI-011 / BL-028 — el pipeline de features no puede correr en esta máquina.**
  `sentinelhub`, `cdsapi`, `rasterio` y `xarray` están todos ausentes del
  intérprete en el PATH y no hay entorno virtual. Que las credenciales funcionen
  no significa que la recolección funcione. Esto bloquea BL-007, BL-012 y BL-014,
  y por lo tanto BL-008 en la práctica.
- **WI-012 / BL-027 — coordenadas de estación.** Bloqueado a la espera del GPS
  real que llega con los CSV del SNIA. Hasta entonces, ADR-sf-0007 descalifica el
  FAI de punto de estación como señal de entrenamiento, y
  `check_station_points_on_water` lo hace cumplir.
- **ADR 0003** (biblioteca de mapas) le corresponde a `lq` y todavía no ha
  respondido. El trabajo de frontend no debería empezar antes de eso.

## Último Estado Verificado

- `python agents/harness_doctor.py --root . --strict` — 0 bloqueadores, 0
  advertencias. Registrado en `agents/validation/DOCTOR.md`.
- `python agents/check_translations.py` — 5 de 5 al día.
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
