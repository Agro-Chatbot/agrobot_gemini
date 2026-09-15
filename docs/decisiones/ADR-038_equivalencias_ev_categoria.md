---
domain: tech
type: decision
---

# ADR-038 — Equivalencias EV por categoría animal (extiende ADR-010)

## Estado

`Aceptada`

(El estado vive en `02-System/decisions.json`; acá se refleja para lectura.)

## Fecha

2026-09-15

## Contexto

ADR-010 fija la ración de 8 kg MS/día por EV y descartó explícitamente las categorías animales
("complejidad innecesaria para el MVP"). La auditoría (M018, clave `equivalencia-categoria-ev`)
muestra que el productor pregunta en cabezas de una categoría, no en EV, y el agente improvisa.

## Opciones consideradas

### Opción A — Mantener solo EV (statu quo)

- Pros: sin cambios.
- Contras: el agente improvisa la conversión o la ignora.

### Opción B — Tabla de referencia en el prompt, conversión en texto

- Pros: barata, revisable, sin tocar la tool.
- Contras: la conversión no queda en el `summary`.

### Opción C — Parámetro `categoria_animal` en `soporte_animal`

- Pros: la conversión queda en el cálculo.
- Contras: agrega superficie a la tool para una multiplicación.

## Decisión

Opción B (valores confirmados por el usuario): vaca de cría **1,0** · vaquillona **0,7** · novillo
**0,8** · ternero/a **0,5** · toro **1,3** EV, en `prompt/ganaderia.py`, con la salvedad obligatoria
de que son promedios de referencia y el productor ajusta por peso vivo real. La conversión es
aritmética sobre `ev_soportados`, que TECH-121 expone en el summary.

## Consecuencias

- Positivas: responde en la unidad del productor sin tocar el modelo de cálculo.
- Deuda / costo asumido: con rodeo mixto la conversión la hace el agente en texto y no queda en el
  summary.

## Relacionadas

- Extiende ADR-010 (no la supersede). Relacionada con TECH-155, TECH-121.
