---
domain: tech
type: decision
---

# ADR-035 — Buckets de dominio sobre `Recurso`: mapeo en el prompt, no columna derivada

## Estado

`Aceptada`

(El estado vive en `02-System/decisions.json`; acá se refleja para lectura.)

## Fecha

2026-09-15

## Contexto

El usuario nombra categorías agregadas ("pasturas implantadas", "verdeos") que no son valores del
CSV: `Recurso` tiene 16 valores concretos. ADR-008 fijó que el binning se hace por columnas
derivadas en `data.py`.

## Opciones consideradas

### Opción A — Columna derivada `GrupoRecurso` en `enrich_temporal`

- Pros: consistente con ADR-008.
- Contras: congela la taxonomía dentro de los datos, obliga a recargar para cambiarla y asume que
  los buckets son una partición.

### Opción B — Mapeo en el system prompt + `filters` multivalor (ADR-034)

- Pros: el agente arma la lista de valores reales; la taxonomía es versionable y discutible.
- Contras: desvío de ADR-008; el prompt crece.

### Opción C — Tool de lookup de taxonomía

- Pros: explícita.
- Contras: séptima tool que ensucia la métrica `tool_esperada` de la auditoría.

## Decisión

Opción B, con desvío explícito de ADR-008: los buckets de `Recurso` no son binning de una variable
continua sino **vocabulario de dominio**, discutible y potencialmente no ortogonal; vive en
`prompt/recursos.py`. Taxonomía acordada con el usuario: `pasturas implantadas` = los 5 `Pastura *`
(consociada, de festuca, de agropiro, de agropiro y festuca, base alfalfa); `verdeos` = los 7
`Verdeo de *`; `promociones de raigrás` = `Promocion de raigras` + `Promocion intensiva de raigras`
(**categoría propia, no verdeos**); `Silo de maiz` y `Campo natural`, cada uno aparte.

## Consecuencias

- Positivas: cierra M039/M040/M047/M048 sin tocar el pipeline de datos.
- Deuda / costo asumido: el agente debe enumerar el bucket usado en la explicación; si algún día se
  agrega la columna derivada, la taxonomía se duplica conceptualmente (este ADR es la fuente única).

## Relacionadas

- Desvío justificado de ADR-008; usa ADR-034. Relacionada con TECH-123.
