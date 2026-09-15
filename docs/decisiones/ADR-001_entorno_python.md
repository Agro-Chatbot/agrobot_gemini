---
domain: tech
type: decision
---

# ADR-001 — Entorno Python del proyecto

## Estado

`Aceptada`

(El estado vive en `02-System/decisions.json`; acá se refleja para lectura.)

## Fecha

2026-08-28

## Contexto

El `python3` del sistema es 3.7, incompatible con el stack (streamlit, pandas 2.x,
matplotlib 3.7, y sintaxis 3.10+ del código). El `.venv` actual se creó con el intérprete
Python 3.11 del env conda `elans` (`/opt/anaconda3/envs/elans/bin/python`). Funciona, pero
queda acoplado: si `elans` se borra o modifica, el `.venv` se rompe. Fuerzas en juego:
desacople, mantener la convención `.venv` del resto de los proyectos, y mínimo cambio en el
flujo de activación.

## Opciones consideradas

### Opción A — Env conda dedicado

- Pros: autónomo, desacoplado de `elans`.
- Contras: cambia el flujo de activación (`conda activate chatbot`) vs la convención `.venv`
  del resto de los proyectos; suma dependencia de conda.

### Opción B — Python 3.11+ standalone + `.venv`

- Pros: mantiene la convención `.venv`; desacopla de conda; flujo de activación sin cambios.
- Contras: requiere instalar/gestionar un Python standalone (pyenv o python.org).

### Opción C — Dejar como está (acoplado a `elans`)

- Pros: cero trabajo.
- Contras: acoplamiento no deseado; el `.venv` se rompe si `elans` cambia o se borra.

## Decisión

Opción B — instalar Python 3.11+ standalone (pyenv/python.org) y recrear `.venv` con él.
Criterio decisivo: desacopla de conda sin romper la convención `.venv` común a los demás
proyectos.

## Consecuencias

- Positivas: el `.venv` deja de depender del env conda `elans`; el flujo de activación
  (`source .venv/bin/activate`) se mantiene homogéneo con el resto de los proyectos.
- Deuda / costo asumido: hay que instalar y mantener un Python 3.11 standalone en la máquina.
- Habilita reproducir el setup en otra máquina sin depender de conda.

## Relacionadas

- Relacionada con: TECH-002 (decidir y consolidar el entorno Python).
