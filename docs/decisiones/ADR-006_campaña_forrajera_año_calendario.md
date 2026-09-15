---
domain: tech
type: decision
---

# ADR-006 — Definición de "campaña forrajera" como año calendario (ene–dic)

## Estado

`Aceptada`

(El estado vive en `02-System/decisions.json`; acá se refleja para lectura.)

## Fecha

2026-09-08

## Contexto

TECH-050 requiere binning de fechas en una dimensión "campaña" para comparar rendimiento entre
años. En el dominio forrajero/ganadero argentino existen dos convenciones posibles:

1. **Año calendario** (ene–dic): "campaña 2023" abarca el 1/1/2023 al 31/12/2023.
2. **Ciclo productivo** (jul–jun): "campaña 2022/2023" abarca el 1/7/2022 al 30/6/2023,
   alineado con el ciclo de crecimiento de pasturas templadas (rebrote primaveral en
   septiembre, pico en diciembre/enero, senescencia en otoño).

El dataset cubre 2019→2026, con preguntas del tipo "¿cómo fue la campaña 2023?".

## Opciones consideradas

### Opción A — Año calendario (ene–dic)

- Pros: etiqueta simple ("2023"), sin ambigüedad al nombrar la campaña, alineado con
  cómo los ganaderos registran años en libros y tablas; fácil de implementar con
  `df['Fecha'].dt.year`; coincide con la expectativa natural del usuario no técnico.
- Contras: corta la primavera-verano (el pico productivo de sep–feb) entre dos años
  distintos, lo que subestima la comparación de rendimiento estacional.

### Opción B — Ciclo productivo (jul–jun)

- Pros: refleja mejor la biología de las pasturas templadas; estándar en informes CREA y
  INTA para análisis técnicos.
- Contras: etiqueta compuesta ("2022/2023") requiere lógica adicional de mapeo; el usuario
  rural no técnico esperaría "campaña 2023" pero el sistema devolvería "campaña 2022/2023";
  mayor complejidad de implementación y de comunicación en el chatbot.

## Decisión

Se elige **Opción A — año calendario**. El MVP prioriza la comunicabilidad con el usuario
rural no técnico; la etiqueta simple ("2023") es inequívoca en el contexto de la UI. El
system prompt del agente puede incluir una nota aclaratoria de que "campaña X" abarca
enero–diciembre del año X.

Si en una versión futura se requiere análisis de ciclo productivo, se puede agregar una
columna `Campaña_ciclo` (format `YYYY/YY+1`) sin romper la existente.

## Consecuencias

- Positivas: implementación trivial (`dt.year`), sin lógica de mapeo, etiqueta limpia en
  gráficos.
- Deuda / costo asumido: la comparación de campañas parte el pico productivo (dic–feb) entre
  dos años. Para análisis técnicos rigurosos, esto puede distorsionar. Se acepta para MVP.
- Habilita: TECH-050 puede implementarse con una línea de código en `data.py`.

## Relacionadas

- TECH-050 (binning temporal, origen de esta decisión)
- ADR-007 (mapeo de estaciones, complementaria)
