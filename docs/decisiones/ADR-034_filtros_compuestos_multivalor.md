---
domain: tech
type: decision
---

# ADR-034 — Filtros: lista de pares columna/valores (`filters`) con retrocompatibilidad

## Estado

`Aceptada`

(El estado vive en `02-System/decisions.json`; acá se refleja para lectura.)

## Fecha

2026-09-15

## Contexto

`_apply_filters` admite un solo par `filter_col`/`filter_val` por igualdad exacta. Faltan (i) dos
columnas simultáneas (`filtro-compuesto-campo-lote`, 16 preguntas; contamina datos en silencio —
caso P03: un lote homónimo de otro campo entra al gráfico) y (ii) varios valores de una columna
(`filtro-multivalor*`, 3 preguntas). Además el `ChartError` vuelca los 622 lotes al modelo.

## Opciones consideradas

### Opción A — `filter_col_2` / `filter_val_2`

- Pros: trivial.
- Contras: tope rígido en dos columnas; no resuelve multivalor.

### Opción B — Arrays paralelos `filter_cols` / `filter_vals`

- Pros: N columnas.
- Contras: se desalinean fácil; no expresan multivalor por columna.

### Opción C — `filters: [{"col": str, "vals": string | array}]`

- Pros: AND entre entradas, `isin` dentro de cada entrada; una sola forma para ambos casos.
- Contras: objeto anidado en el JSON schema (más superficie de error de parámetros).

## Decisión

Opción C. Se agrega `filters` a las seis tools; `filter_col`/`filter_val` se conservan como alias
que se normalizan a `filters` al entrar a `_apply_filters`, así los schemas siguen teniendo las
cuatro propiedades de filtro que asserta `test_filter_schemas_tienen_cuatro_propiedades_filtro`.
`ChartError` valida cada valor de cada entrada, nombra los inexistentes y **trunca la lista de
válidos a 30** (`… y N más`).

## Consecuencias

- Positivas: una sola decisión resuelve TECH-118, TECH-152 y el mecanismo de TECH-123; el agente
  gana expresividad sin tool calls extra; se corta el volcado de 622 valores al modelo.
- Deuda / costo asumido: más superficie de error de parámetros (cubierta por el loop de reintento
  con `ChartError`); el truncado del error es un cambio observable en las trazas.

## Relacionadas

- Extiende ADR-009. Relacionada con TECH-118, TECH-152, TECH-123, TECH-151.
