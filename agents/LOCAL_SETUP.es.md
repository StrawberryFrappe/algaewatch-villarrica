---
source: agents/LOCAL_SETUP.md
source_sha: cc783ddc3adb200f830c5991ad4c67dd8e7db2cd
source_sha_algo: git-blob-sha1
translated: 2026-09-09
translator: agent
---

# Configuración Local

El harness está partido en dos. Este archivo se commitea, y explica cómo
construir la mitad que no.

## Por Qué Hay Dos Mitades

La **verdad del proyecto** es compartida y commiteada: qué se está construyendo,
la arquitectura, los ADRs, los gates, las preguntas abiertas, el manifiesto de
fuentes. Idéntica para todo colaborador en toda máquina, y sigue siendo cierta el
año que viene.

La **verdad del entorno** es local y nunca se commitea: qué agente corres, si
tiene subagentes, qué integraciones están conectadas, dónde vive tu checkout, qué
binarios invocas, cómo paralelizas el trabajo. Distinta por persona, por máquina,
y se pone obsoleta.

La prueba para saber a qué mitad pertenece algo:

> **¿Se confundiría el agente de otro colaborador si tuviera esto?**

Si la respuesta es sí, es local. Una ruta que sólo existe en tu máquina, una
capacidad que sólo tiene tu plataforma, una herramienta que sólo tú instalaste.
Commitear eso hace que el agente de todos los demás lea instrucciones que no
puede seguir — y que las crea.

## La Mitad Local Es El Mecanismo De Adaptación

Como `agents/local/` nunca viaja con el repositorio, **todo clon pasa
obligatoriamente por esta configuración.** Ese es el punto, no una limitación.

Un harness que enviara el entorno de su autor llegaría a la máquina siguiente ya
equivocado, y con seguridad. Un harness que sólo envía verdad del proyecto llega
incompleto y *lo dice* — el gate de abajo rechaza el trabajo de implementación
hasta que la máquina nueva se describa a sí misma. El harness se re-adapta a cada
entorno en el que aterriza, porque no puede hacer otra cosa.

## Cómo Se Mantiene Fuera De Git

`agents/local/.gitignore` se distribuye conteniendo:

```
*
!.gitignore
```

El directorio ignora su propio contenido y conserva sólo el archivo de ignore, de
modo que la carpeta existe en un clon nuevo pero llega vacía. Nada fuera necesita
enterarse, y ninguna regla del archivo de ignore raíz del proyecto puede filtrar
el arreglo.

El doctor lo verifica preguntándole a `git check-ignore` si un archivo de prueba
dentro de `agents/local/` está realmente ignorado, en lugar de leer el archivo de
ignore — una comprobación textual no puede ver una negación en un directorio
padre que la anularía en silencio.

## Qué Crear

| Ruta | Propósito |
|---|---|
| `agents/local/CAPABILITIES.md` | **Obligatorio.** Tu capability scan y los hechos de tu máquina |
| `agents/local/logbook/` | Opcional. Notas crudas de sesión; promover los hechos duraderos a documentos commiteados |

Copia `agents/templates/capability-scan-template.md` a
`agents/local/CAPABILITIES.md` y complétalo. Pide:

- qué agente y plataforma corres, y si tiene subagentes;
- qué integraciones están conectadas **y autorizadas**;
- si puedes crear sandboxes o worktrees de git;
- las ubicaciones de tus checkouts y los binarios que este proyecto necesita;
- cómo aíslas el trabajo en paralelo.

Registra lo que verificaste, no lo que supones. Una capacidad afirmada sin
verificar es peor que una ausente, porque el harness planificará contando con
ella.

## El Gate

El trabajo de implementación requiere que exista `agents/local/CAPABILITIES.md`.
El doctor reporta su ausencia como advertencia, y como bloqueante duro con
`--strict`.

Un harness que no sabe qué puede hacer su agente va a planificar trabajo que el
entorno no puede realizar, o va a degradar en silencio una review a una pasada de
un solo agente sin decirlo.

Leer documentos y hacer correcciones triviales no está bloqueado.

## Mantenerlo Honesto

Vuelve a correr el scan cuando cambie el entorno — un agente nuevo, una
integración recién conectada, un permiso revocado. Un capability scan es una
foto, y su fecha es parte de la evidencia.
