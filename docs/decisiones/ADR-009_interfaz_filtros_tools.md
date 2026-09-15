---
domain: tech
type: decision
---

# ADR-009 — Interfaz de filtros: parámetros en las tools vs pre-filtrado en el agente

## Estado

`Aceptada`

(El estado vive en `02-System/decisions.json`; acá se refleja para lectura.)

## Fecha

2026-09-08

## Contexto

TECH-051 requiere que el usuario pueda acotar el DataFrame antes de graficar, por rango de
fechas y/o por valor exacto de una columna categórica (Campo, Lote, Recurso). Hoy las tools
operan sobre el DataFrame completo.

La interfaz de filtrado debe integrarse con el ciclo tool-use del agente (`agent.py`):
Claude elige la tool y sus parámetros; el agente ejecuta; si hay `ChartError`, Claude corrige.
El filtrado debe ser validado para que errores (columna o valor inexistente) sean legibles.

## Opciones consideradas

### Opción A — Parámetros opcionales de filtro en las tools (`filter_col`, `filter_val`, `date_from`, `date_to`)

Agregar a los schemas JSON de `bar_chart`, `line_chart`, `pie_chart` (y opcionalmente las
demás) cuatro parámetros opcionales:
- `filter_col`: columna categórica por la que filtrar (p. ej. "Recurso").
- `filter_val`: valor exacto de esa columna (p. ej. "Campo natural").
- `date_from` / `date_to`: rango de fechas ISO 8601 (p. ej. "2023-01-01").

Cada tool aplica el filtro internamente antes de agregar, y lanza `ChartError` si la
columna o el valor no existen.

- Pros: Claude especifica el filtro en el mismo `tool_use` call; el error de filtro entra
  al ciclo de reintento existente (ChartError → Claude corrige); sin lógica en `agent.py`;
  consistente con el principio de que la validación vive en las tools.
- Contras: los schemas de tools se amplían (breaking change menor: Claude debe aprender
  los nuevos parámetros opcionales); `scatter_plot` e `histogram` necesitan los mismos
  parámetros o una función helper compartida.

### Opción B — Pre-filtrado en `agent.py` antes de llamar a la tool

`agent.py` interpreta la query y construye un DataFrame filtrado antes de pasarlo a la tool.

- Pros: las tools no cambian.
- Contras: el agente necesita lógica de NLP para detectar filtros en la query (frágil);
  los errores de filtro no entran al ciclo de reintento (ChartError); duplica responsabilidades
  entre agente y tools.

### Opción C — Helper de pre-filtrado compartido, invocado desde dentro de las tools

Función `_apply_filters(df, filter_col, filter_val, date_from, date_to)` en `charts.py`,
llamada al inicio de cada tool. Mismo resultado que Opción A pero con implementación
centralizada.

- Pros: lógica de filtrado en un solo lugar; schemas de tools siguen siendo la interfaz.
- Cons: es una sub-opción de implementación de A, no una opción de interfaz distinta.

## Decisión

Se elige **Opción A con implementación tipo C**: los parámetros de filtro se agregan a los
schemas de las tools existentes (interfaz explícita para Claude), y la lógica de filtrado se
centraliza en una función helper privada `_apply_filters` en `charts.py`. Esto mantiene la
validación y los `ChartError` donde corresponde, sin lógica en el agente.

Los cuatro parámetros son opcionales; si se omiten, el comportamiento es idéntico al actual.

## Consecuencias

- Positivas: el ciclo de reintento (ChartError → Claude corrige) cubre también errores de
  filtro (p. ej. lote inexistente); sin cambios en `agent.py`; retrocompatible (los params
  son opcionales); una sola función helper para los cuatro params.
- Deuda / costo asumido: los schemas JSON de las tools se amplían; si Claude hallucina un
  valor de columna, se produce un ChartError legible que Claude puede corregir. No hay
  autocompletado de valores disponibles (el system prompt / schema_summary los informa).
- Habilita: TECH-052 puede usar `filter_col`/`filter_val` para acotar por lote antes de
  calcular soporte animal.

## Relacionadas

- ADR-008 (columnas derivadas, complementaria — `Anio`/`Estacion` son filtrables con esta interfaz)
- TECH-051 (origen de esta decisión)
- TECH-052 (se beneficia de los filtros para el cálculo de soporte animal)
