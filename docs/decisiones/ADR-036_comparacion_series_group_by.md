---
domain: tech
type: decision
---

# ADR-036 — Comparación de dos series: `group_by` en una tool call, no dos tool calls

## Estado

`Aceptada`

(El estado vive en `02-System/decisions.json`; acá se refleja para lectura.)

## Fecha

2026-09-15

## Contexto

11 preguntas de la auditoría piden comparar dos series (campañas, períodos, recursos). `answer()`
ejecuta una tool call válida por consulta, y TECH-057 fuerza `disable_parallel_tool_use` justamente
para que el loop no se rompa cuando el modelo emite dos bloques `tool_use`.

## Opciones consideradas

### Opción A — Dos tool calls secuenciales combinadas en un gráfico

- Pros: expresa cualquier par de consultas.
- Contras: cambia el loop de `answer()`, duplica llamadas y reabre el riesgo que TECH-057 cierra.

### Opción B — Tools de comparación dedicadas (`bar_chart_comparado`)

- Pros: explícita.
- Contras: duplica la superficie de schema.

### Opción C — Parámetro `group_by` opcional en `bar_chart` / `line_chart`

- Pros: `groupby([x, group_by])` + `unstack()` → barras agrupadas o múltiples líneas; el loop no
  cambia; con `x='Estacion'`, `group_by='Anio'` se responde "este verano vs. el del año pasado".
- Contras: no expresa dos ventanas de fecha arbitrarias y discontinuas.

## Decisión

Opción C. El límite de los rangos discontinuos queda declarado por las reglas de transparencia
(TECH-149), no resuelto en silencio.

## Consecuencias

- Positivas: cubre también la anomalía estacional de forma visual (la base estacional se ve como
  serie), por lo que no hace falta una métrica de anomalía con umbral — que además quedó no
  determinable por ADR-033.
- Deuda / costo asumido: comparaciones de dos ventanas temporales discontinuas siguen sin soporte.

## Relacionadas

- Relacionada con TECH-122, TECH-157, TECH-057 (deslinde); usa ADR-034.
