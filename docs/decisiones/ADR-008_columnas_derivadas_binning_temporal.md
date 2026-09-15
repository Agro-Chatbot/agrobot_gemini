---
domain: tech
type: decision
---

# ADR-008 — Diseño de binning temporal: columnas derivadas vs parámetro de granularidad

## Estado

`Aceptada`

(El estado vive en `02-System/decisions.json`; acá se refleja para lectura.)

## Fecha

2026-09-08

## Contexto

TECH-050 necesita exponer dimensiones temporales derivadas (año/campaña/estación) a las tools
de graficado. Hay dos enfoques de diseño principales.

El diseño actual de `charts.py` acepta cualquier columna del DataFrame como `x` o `category`.
Las tools no saben nada del tipo de dato: agrupan por los valores que haya en esa columna.
`data.py` ya tiene `schema_summary` que lista las columnas disponibles al LLM.

## Opciones consideradas

### Opción A — Columnas derivadas pre-computadas en `data.py`

Agregar `Anio`, `Estacion` (y opcionalmente `Campaña` como alias de `Anio`) al DataFrame
al momento de cargarlo. Claude las usa como `x`/`category` en las tools existentes igual que
cualquier otra columna categórica.

- Pros: sin cambios en `charts.py` ni en los schemas de tools; Claude aprende las columnas
  desde `schema_summary` igual que las demás; implementación mínima (2–3 líneas en `data.py`);
  columnas disponibles para cualquier tool (bar, line, pie) sin lógica adicional.
- Contras: el DataFrame crece 2–3 columnas; si en el futuro se quieren granularidades
  arbitrarias (semana, bimestre), requiere agregar columnas.

### Opción B — Parámetro de granularidad temporal en las tools

Agregar un parámetro `temporal_bin` ("año"|"estacion"|"mes") a `bar_chart` y `line_chart`.
Las tools agrupan internamente el `x` (fecha) en el bin solicitado.

- Pros: más explícito; no "contamina" el DataFrame con columnas derivadas.
- Contras: requiere cambiar los schemas JSON de las tools (breaking change para Claude);
  lógica de binning dentro de cada tool (duplicación); `scatter_plot`, `pie_chart` e
  `histogram` quedarían sin el parámetro o requerirían duplicar el cambio; mayor superficie
  de testing.

### Opción C — Pre-filtrado/transformación en `agent.py` antes de llamar a la tool

- Pros: separa la transformación de la visualización.
- Contras: Claude no sabe qué transformación se aplicó; el agente tendría que interpretar la
  query para decidir si binear; introduce complejidad en la orquestación.

## Decisión

Se elige **Opción A — columnas derivadas pre-computadas**. Es la más simple y la que mejor
encaja con el diseño actual: zero cambios en `charts.py`, zero cambios en los schemas de
tools, zero lógica adicional en `agent.py`. Las columnas `Anio` y `Estacion` son ciudadanas
de primera clase en el DataFrame, visibles en `schema_summary`, y usables en cualquier tool.

## Consecuencias

- Positivas: implementación en `data.py` solamente (función `enrich_temporal`); las 5 tools
  existentes soportan binning temporal automáticamente; Claude descubre las columnas vía
  `schema_summary` sin instrucción adicional.
- Deuda / costo asumido: columnas siempre presentes aunque no se usen; el `schema_summary`
  las listará como categóricas con sus valores frecuentes (correcto).
- Habilita: TECH-051 puede pre-filtrar antes de llamar a las tools usando estas mismas
  columnas como criterio de filtro (además de `Fecha`).

## Relacionadas

- ADR-006 (campaña = año calendario)
- ADR-007 (estaciones hemisferio sur)
- ADR-009 (interfaz de filtros, complementaria)
- TECH-050 (origen de esta decisión)
