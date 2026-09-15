---
domain: tech
type: decision
---

# ADR-007 — Mapeo de meses a estaciones del año (hemisferio sur)

## Estado

`Aceptada`

(El estado vive en `02-System/decisions.json`; acá se refleja para lectura.)

## Fecha

2026-09-08

## Contexto

TECH-050 requiere una columna derivada `Estacion` para agrupar datos por período estacional
y responder preguntas del tipo "¿cómo varía la tasa según la estación?". El dataset es de
la provincia de Buenos Aires (hemisferio sur), por lo que las estaciones están desfasadas
6 meses respecto al hemisferio norte.

Existen dos convenciones de corte estacional:
1. **Meteorológica** (meses completos): trimestres fijos de tres meses.
2. **Astronómica** (~21 de cada mes): requiere lógica de fecha exacta por año.

## Opciones consideradas

### Opción A — Estaciones meteorológicas (hemisferio sur, meses completos)

Mapeo:
- Verano: diciembre, enero, febrero (12, 1, 2)
- Otoño: marzo, abril, mayo (3, 4, 5)
- Invierno: junio, julio, agosto (6, 7, 8)
- Primavera: septiembre, octubre, noviembre (9, 10, 11)

- Pros: implementación simple (lookup por número de mes); coincide con el lenguaje cotidiano
  del usuario rural; estándar en informes agropecuarios argentinos (SMN, INTA).
- Contras: no coincide exactamente con los equinoccios/solsticios astronómicos (diferencia
  de ±21 días en los extremos).

### Opción B — Estaciones astronómicas

- Pros: más preciso.
- Contras: complejidad mayor (lógica por año y día exacto); diferencia real con la opción A
  es despreciable para agregaciones de tasa forrajera a escala mensual/estacional.

## Decisión

Se elige **Opción A — estaciones meteorológicas hemisferio sur**. La diferencia de ±21 días
respecto a la astronómica es irrelevante para las preguntas del chatbot (que agregan datos
sobre 30–90 días). El lookup por mes es determinista, sin ambigüedad de borde de año.

Orden canónico en gráficos: Primavera → Verano → Otoño → Invierno (ciclo productivo).

## Consecuencias

- Positivas: una línea de mapeo con `pd.cut` o `map`; columna `Estacion` con 4 valores fijos
  ("Verano", "Otoño", "Invierno", "Primavera") usable como `x`/`category` en cualquier tool.
- Deuda / costo asumido: el corte dic–feb parte el verano entre dos años calendario, lo que
  interactúa con la decisión de campaña como año calendario (ADR-006). Para enero/febrero de
  un año X, el verano corresponde a la campaña X, aunque biológicamente es el pico del ciclo
  que comenzó en primavera del año X-1. Se acepta como limitación del MVP.
- Habilita: TECH-050 puede exponer la columna `Estacion` directamente como dimensión de
  agrupación en las tools existentes.

## Relacionadas

- ADR-006 (definición de campaña, complementaria)
- TECH-050 (binning temporal, origen de esta decisión)
