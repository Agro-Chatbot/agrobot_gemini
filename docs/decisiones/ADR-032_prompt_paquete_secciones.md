---
domain: tech
type: decision
---

# ADR-032 — System prompt como paquete de secciones (`src/chatbot/prompt/`)

## Estado

`Aceptada`

(El estado vive en `02-System/decisions.json`; acá se refleja para lectura.)

## Fecha

2026-09-15

## Contexto

`agent._system_prompt` es un string monolítico de ~40 líneas. El refinamiento de las capacidades
faltantes de la auditoría `20260914-185756` necesita ampliarlo desde **16 tickets distintos**
(TECH-118..123, TECH-148..158). Como archivo único es un recurso serializado: `run-parallel.sh` no
puede paralelizar y dos coders concurrentes se pisan (cada uno hace read-modify-write del archivo
entero).

## Opciones consideradas

### Opción A — Dejarlo monolítico y serializar los tickets

- Pros: cero refactor.
- Contras: ~16 olas de un ticket cada una; riesgo de pisadas si dos entran en la misma ola.

### Opción B — Un módulo `src/chatbot/prompt.py` con una función por sección

- Pros: mejor legibilidad, cambio chico.
- Contras: sigue siendo un archivo → no habilita paralelismo.

### Opción C — Paquete `src/chatbot/prompt/` con un módulo por tema

- Pros: cada ticket declara `writes` sobre su módulo → paralelismo real con `MAX_PARALLEL=5`;
  habilita tests de prompt, que hoy no existen.
- Contras: una indirección más; `__init__.py` queda como punto compartido.

## Decisión

Opción C. `prompt/__init__.py` expone `system_prompt(schema: str) -> str` y concatena en orden fijo
las secciones de `base, temporal, valores, filtros, recursos, graficos, soporte, ganaderia, clima,
limites`; cada módulo expone `SECCION: str`. `agent._system_prompt` queda como delegador fino para
no romper `answer`/`answer_trace` ni los tests. El enabler (TECH-159) crea los diez módulos de una
vez —vacíos los que aún no tienen contenido— y a partir de ahí `__init__.py` no se toca.

## Consecuencias

- Positivas: seis tickets de prompt pueden correr en la misma ola; `tests/test_prompt.py` pasa a
  existir con un test de contrato (presencia y orden de las secciones).
- Deuda / costo asumido: agregar una sección nueva después del enabler obliga a tocar `__init__.py`.
- Habilita: TECH-148, TECH-149, TECH-150, TECH-151, TECH-153, TECH-155, TECH-123.

## Relacionadas

- Relacionada con: TECH-159; consumida por TECH-148/149/150/151/153/155/123.
