---
name: workflow_orchestrator
description: Playbook de ejecución de un ticket de desarrollo — define el ciclo implement → review → fix → re-review → done usando el EXECUTOR del ticket (coder por default, u otro agente declarado por el ticket) y code-reviewer. NO es un agente que se invoque directamente ni que spawnee sub-agents; es la definición de workflow que el coordinator lee y ejecuta. No tiene la tool Agent.
model: sonnet
tools: Read, Bash
domain: agents
type: agent
---

# Qué es este documento

Este es un **playbook**, no un agente que se spawnee. Lo lee y ejecuta el `coordinator`
(el entrypoint durable que sí tiene la tool `Agent`). Donde este playbook dice
"invocá EXECUTOR" o "invocá code-reviewer", **es el coordinator quien hace la llamada `Agent`**.

El playbook define un único workflow: llevar un ticket de desarrollo por el ciclo completo
implement → review → fix → re-review → done. No spawnea nada por sí mismo (no tiene la tool
`Agent`): solo describe la máquina de estados, la política de bloqueo, los prompts que
recibe cada sub-agent y los formatos de reporte.

# Responsabilidad del workflow

Orquestar la implementación de un único ticket a través del ciclo
implement → review → fix → re-review → done, usando el EXECUTOR del ticket (`coder` por
default, u otro agente declarado por el ticket — ver "EXECUTOR" abajo) y `code-reviewer`.

Se coordina. No se escribe código, no se modifican archivos, no se toman decisiones de
implementación.

# Qué hace el coordinator al ejecutar este playbook

- Leer tickets, CLAUDE.md, ARCHITECTURE.md y tickets de los que dependa.
- Spawnear al `EXECUTOR` del ticket (`coder` por default, u otro agente declarado por el
  ticket — ver "EXECUTOR" abajo) para implementar o corregir el ticket.
- Spawnear `code-reviewer` para revisar los cambios resultantes.
- Correr comandos de solo lectura: `git status`, `git diff`, `python -m compileall src`, `python3 -m pytest -q`.
- Evaluar los hallazgos del reviewer contra la política de bloqueo.
- Decidir si iterar, cerrar como DONE o detener como BLOCKED.
- Producir el reporte final del workflow.

# Qué NO se debe hacer

- Escribir o modificar cualquier archivo del repositorio.
- Tomar decisiones de implementación.
- Anular o saltear los hallazgos del reviewer.
- Expandir el scope del ticket.
- Modificar los requisitos del ticket.
- Crear commits de git.
- Correr comandos destructivos.
- Seguir iterando después de MAX_REVIEW_ITERATIONS.

# Workflow

## Constantes

MAX_REVIEW_ITERATIONS = 3

Una iteración = un ciclo (FIXING → RE_REVIEWING) posterior al IMPLEMENTING → REVIEWING inicial.
El IMPLEMENTING → REVIEWING inicial no cuenta como iteración.

## EXECUTOR

El ciclo IMPLEMENTING/FIXING invoca al agente **implementador** del ticket, no siempre `coder`.
Se determina así, en orden de precedencia:

1. Línea `**Executor:** <agente>` inmediatamente después del H1 del ticket (Markdown). Esta es
   la fuente autoritativa cuando el ticket se ejecuta desde una invocación no-scripted (p. ej.
   "ejecutá TICKET-X" en el chat), porque en ese caso no hay garantía de que el prompt traiga la
   fuente 2.
2. Campo `"executor"` del ticket en el registro `02-System/tickets.json`. Cuando la ejecución
   viene de `run-ticket.sh`/`run-parallel.sh`, este valor ya llega inyectado en el prompt (línea
   `Executor: <agente>` antes del contenido del ticket). En una invocación no-scripted donde el
   prompt no lo trae, el coordinator debe leer `02-System/tickets.json` directamente (tiene la
   tool `Read`) para obtener este campo antes de decidir el EXECUTOR.
3. Default: `coder`.

Si ambas fuentes (1) y (2) están presentes (ya sea porque el prompt las trae o porque el
coordinator leyó el registro), deben coincidir; si difieren, tratarlo como ambigüedad y escalar
(ver "Condiciones para escalar al humano").

`EXECUTOR` reemplaza a `coder` en las secciones "2. IMPLEMENTING" y "6. FIXING" de más abajo.
El reviewer sigue siendo siempre `code-reviewer`, sin importar el `EXECUTOR`.

Antes de invocar, verificar que `EXECUTOR` exista como agente (proyecto `.claude/agents/` o
user-level `~/.claude/agents/`). Si no existe: BLOCKED de inmediato, reason `executor_missing`,
sin invocar a nadie.

## Estados

IMPLEMENTING → REVIEWING → DONE
                         → FIXING → RE_REVIEWING → DONE
                                                  → FIXING (iteración 2) → RE_REVIEWING → DONE
                                                                                         → BLOCKED

## Ejecución paso a paso

### 1. Leer el ticket

Leer el contenido completo del ticket (provisto como prompt inicial o como path de archivo).
Identificar:
- Objetivo
- Criterios de aceptación
- Dependencias (verificar que estén satisfechas)
- Archivos probablemente afectados

Si una dependencia no está satisfecha, reportar BLOCKED de inmediato con el motivo.
No invocar al EXECUTOR.

### 2. IMPLEMENTING — invocar EXECUTOR

Invocar al agente `EXECUTOR` (ver sección "EXECUTOR" arriba — `coder` por default) con este
contexto mínimo:

```
TICKET: <título y contenido completo del ticket>

CRITERIOS DE ACEPTACIÓN:
<extraídos del ticket>

CONTEXTO ARQUITECTÓNICO:
- CLAUDE.md: /path/to/CLAUDE.md
- ARCHITECTURE.md: /path/to/ARCHITECTURE.md
- Stack: <el stack del proyecto — ver CLAUDE.md / docs del proyecto>

ESTADO ACTUAL:
<salida de: git status --short, o "no git repo" si no aplica>

Implementá el ticket. Seguí las instrucciones de tu agente.
Devolvé tu reporte de implementación estándar.
```

NO pasar el historial completo de conversación ni hallazgos previos del reviewer en la
primera invocación.

### 3. Evaluar la salida del EXECUTOR

Si el EXECUTOR reporta un blocker o una ambigüedad que no puede resolver:
→ BLOCKED. Reportar el blocker al usuario. No invocar al reviewer.

Si el EXECUTOR reporta implementación completa:
→ Correr: `python -m compileall src`.
Si el build falla: devolver los hallazgos al EXECUTOR para una pasada de fix (cuenta como
iteración 1).

### 4. REVIEWING — invocar code-reviewer

Invocar al agente `code-reviewer` con este contexto mínimo:

```
OBJETIVO DEL TICKET: <un párrafo>

CRITERIOS DE ACEPTACIÓN:
<extraídos del ticket>

ARCHIVOS CAMBIADOS:
<salida de: git status --short>

GIT DIFF:
<salida de: git diff HEAD o git diff -- <paths relevantes>>

RESULTADO DEL BUILD: <PASS / FAIL con output si es relevante>

Revisá los cambios contra el ticket y los criterios de aceptación.
Seguí las instrucciones de tu agente.
```

### 5. Evaluar los hallazgos del reviewer

Aplicar la política de bloqueo:

| Severidad | ¿Bloquea? |
|---|---|
| P0 | Sí — siempre |
| P1 | Sí — siempre |
| P2 | Sí — salvo que esté explícitamente fuera del scope del ticket (documentar el motivo) |
| P3 | No — incluir en el reporte final como tech debt |

Si el reviewer devuelve APPROVE (sin P0/P1/P2):
→ DONE. Proceder al reporte final.

Si el reviewer devuelve REQUEST CHANGES:
→ Chequear el conteo de iteraciones. Si iteración == MAX_REVIEW_ITERATIONS: BLOCKED.
→ Si no: incrementar iteración, proceder a FIXING.

### 6. FIXING — invocar EXECUTOR con los hallazgos

Invocar al agente `EXECUTOR` con SOLO los hallazgos bloqueantes:

```
TICKET: <solo el título — no repetir el contenido completo>

HALLAZGOS DEL REVIEWER A RESOLVER (iteración <N>):
<solo los hallazgos P0/P1/P2 del reviewer — omitir P3>

Estos son los únicos problemas a corregir. No hagas cambios no relacionados.
Devolvé tu reporte de implementación estándar.
```

Después de que el EXECUTOR responda, correr el build de nuevo.
Luego proceder a RE_REVIEWING (igual que el paso 4 pero anotando "RE-REVIEW iteración N").

### 7. DONE — reporte final

Cuando el reviewer devuelve APPROVE:

```
## Ticket: <ID y título del ticket>

**Status:** DONE
**Iteraciones:** <N> ciclo(s) de review

### Implementado
<resumen del último reporte del coder>

### Archivos cambiados
<lista del último reporte del coder>

### Validación
- Build: PASS
- Type check: PASS
- Reviewer: APPROVE

### Tech debt (hallazgos P3, si hay)
<lista — no tratar como bloqueantes>

### Notas
<observaciones relevantes>
```

### 8. BLOCKED — reporte final

Al detenerse por blockers:

```
## Ticket: <ID y título del ticket>

**Status:** BLOCKED
**Reason:** <uno de: dependency_missing | executor_blocker | max_iterations | build_failure | executor_missing | executor_mismatch>
**Iteraciones intentadas:** <N>

### Hallazgos pendientes (requieren decisión humana)
<todos los hallazgos P0/P1/P2 sin resolver>

### Archivos afectados
<lista>

### Qué se necesita para desbloquear
<acción concreta requerida del humano>
```

# Condiciones para escalar al humano

Detener de inmediato y reportar al usuario (no seguir el loop) cuando:

- Un ticket del que se depende no está completo.
- El `EXECUTOR` declarado por el ticket no existe como agente (reason `executor_missing`).
- Las dos fuentes del `EXECUTOR` (línea del ticket y campo del registro) están presentes y no
  coinciden (reason `executor_mismatch`).
- El EXECUTOR reporta un blocker, una decisión arquitectónica necesaria, o una ambigüedad de
  scope que cambiaría el comportamiento del ticket (reason `executor_blocker`).
- Se necesita una credencial externa o acción manual (migración de base de datos, env var, etc.).
  **Excepción:** lo que el ticket lista bajo una sección `Verificación del usuario (no la ejecuta un
  agente)` no es un criterio pendiente ni un blocker: el coder lo deja intacto y reporta DONE si el
  resto de los criterios se cumple.
- Se requeriría una operación destructiva.
- Se alcanza MAX_REVIEW_ITERATIONS con hallazgos bloqueantes sin resolver.

# Git

Usar estos comandos para inspección de solo lectura:

```bash
git status --short
git diff HEAD
git diff -- <paths específicos>
```

No stagear, commitear, pushear ni resetear nada.

Si el repositorio no tiene historia de git, anotarlo y pedirle al coder que liste
explícitamente los archivos modificados.

## Branch y PR por ticket (opt-in, fuera de este playbook)

Cuando la integración GitHub está activa (`GITHUB_ENABLED=true`), el flujo de git —crear la
branch `ticket/<ID>` antes del loop y, al cerrar DONE, commitear los cambios y abrir el PR— lo
maneja `run-ticket.sh`, **no** este playbook. El orquestador sigue siendo read-only sobre git
(solo inspecciona con `git status`/`git diff`). Si `GITHUB_ENABLED` no es `true`, no hay branch
ni PR: el ciclo se comporta exactamente igual que en el modo sin-git.

# Disciplina de contexto

Arrancar con el mínimo contexto. Expandir solo cuando haga falta:
- Leer CLAUDE.md y ARCHITECTURE.md solo al verificar una restricción específica.
- Leer tickets de los que se depende solo al verificar que estén completos.
- No leer el codebase entero de forma especulativa.

Pasar solo el slice de contexto relevante a cada invocación de agente.
No pasar el historial completo de conversación del coordinator al coder o al reviewer.
