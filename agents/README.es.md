---
source: agents/README.md
source_sha: a6461b3a08e1ebc846a9c32f97e4aa919faddc5b
source_sha_algo: git-blob-sha1
translated: 2026-09-09
translator: agent
---

# Harness de Agentes del Proyecto

Este directorio es el harness activo y específico del proyecto. Es el contrato
operativo del trabajo agéntico en este repositorio.

## Dos Mitades

Lo que vive acá es **verdad del proyecto**: compartida, commiteada, igual para
todos.

La **verdad del entorno** — qué puede hacer tu agente, dónde está tu checkout,
qué binarios invocas — vive en `agents/local/`, que nunca se commitea. Todo clon
llega sin ella, y construirla es la forma en que el harness se adapta a la
máquina en la que aterrizó. Empieza por `agents/LOCAL_SETUP.md`.

## Orden de Lectura

1. `AGENTS.md`
2. `agents/RUN_STATE.md`
3. `agents/LOCAL_SETUP.md`, y tu propio `agents/local/CAPABILITIES.md`
4. `agents/intake/PROJECT_BRIEF.md`
5. `agents/intake/PROJECT_PROFILE.md`
6. `agents/intake/SOURCE_MANIFEST.md`
7. `agents/intake/QUESTIONS_SUMMARY.md`
8. `agents/planning/ROADMAP.md`
9. `agents/planning/BACKLOG.md`
10. `agents/architecture/TECH_STACK.md`
11. `agents/validation/GATES.md`
12. `agents/execution/WORKFLOW.md`
13. `agents/i18n/TRANSLATION_PROTOCOL.md`, cuando el proyecto trabaja en más de
    un idioma
14. La review fechada más reciente en `agents/reviews/`
15. Las notas de logbook local relevantes en `agents/local/logbook/`, cuando
    estén disponibles

## Reglas Operativas

- No iniciar la implementación hasta que el harness montado sea aceptado.
- No iniciar la implementación hasta que exista la mitad local. Ver GATE-LOCAL en
  `agents/validation/GATES.md`.
- Las reglas existentes del proyecto se preservan y se fusionan en este harness.
- Preguntar al usuario cuando las decisiones de producto, stack, despliegue,
  calidad o evidencia no estén claras.
- Decidir la fuerza de la review a partir de tu propio capability scan, no de un
  documento commiteado ni de la review de otro colaborador.
- Mantener la verdad del entorno bajo `agents/local/`; nunca se commitea.
- Mantener las entradas de logbook bajo `agents/local/logbook/`; promover los
  hechos duraderos a documentos commiteados.
- Promover las decisiones importantes a ADRs, documentos de planificación, de
  validación o de arquitectura.
- Citar artefactos en lugar de afirmarlos. Una cita es verificable, y el doctor
  comprueba que las rutas citadas existan.
- Si se detecta deriva del harness, detenerse, escribir un handoff y pedir la
  continuación con contexto refrescado.

## Estándar de Finalización

El trabajo está completo sólo cuando pasan los gates de validación específicos
del proyecto, o cuando el bloqueante restante está explícitamente documentado y
aceptado por el usuario.
