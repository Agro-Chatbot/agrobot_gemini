---
domain: tech
type: decision
---

# ADR-010 — Modelo de cálculo de soporte animal y demanda forrajera

## Estado

`Aceptada`

(El estado vive en `02-System/decisions.json`; acá se refleja para lectura.)

## Fecha

2026-09-08

## Contexto

TECH-052 requiere estimar cuántos animales puede sostener un conjunto de lotes en un período,
y la superficie necesaria para alimentar N animales. El CSV no tiene datos de stock animal:
solo `Kg MS ha/día` (tasa de crecimiento de materia seca) y `Superficie ha`.

La capacidad de soporte depende de tres variables: producción de materia seca, superficie, y
consumo diario por animal. El estándar zootécnico en Argentina (INTA, CREA) expresa el
consumo en términos de **Equivalente Vaca (EV)** = vaca de 400 kg a mantenimiento.

## Modelo de cálculo

```
MS disponible (kg/día) = media(Kg MS ha/día) × Superficie ha
EV soportados          = MS disponible ÷ ración_EV_kg_día
EV/ha                  = EV soportados ÷ Superficie ha
```

Para la demanda inversa:
```
Superficie necesaria (ha) = N_animales × ración_EV_kg_día ÷ media(Kg MS ha/día)
```

## Opciones consideradas

### Opción A — Ración fija (8 kg MS/día por EV), no configurable

- Pros: máxima simplicidad; sin parámetros que el usuario deba entender.
- Contras: el consumo real varía según categoría (ternero, vaca seca, vaca lechera) y
  sistema productivo; valor fijo puede ser incorrecto para el caso del usuario.

### Opción B — Ración configurable como parámetro de la tool (default 8 kg MS/día)

- Pros: el usuario puede ajustar para su sistema productivo vía consulta natural
  ("¿cuántos animales si la ración es 10 kg?"); valor de 8 kg como default cubre el caso
  estándar (EV de 400 kg a mantenimiento, 2% PV/día = 8 kg MS/día, estándar INTA/CREA).
- Contras: el usuario debe conocer su ración para especificarla; Claude debe incluirlo en el
  tool call.

### Opción C — Múltiples categorías (ternero = 0.5 EV, vaca lechera = 1.5 EV, etc.)

- Pros: más preciso.
- Contras: complejidad innecesaria para MVP; requiere que el usuario sepa su composición
  de rodeo.

## Decisión

Se elige **Opción B**: ración configurable con default de **8 kg MS/día por EV** (estándar
INTA/CREA para vaca de 400 kg). La tool `soporte_animal` expone `racion_kg_dia` como
parámetro opcional; si el usuario no lo menciona, Claude usa 8.0. La salida principal es
en **EV** (cabezas equivalentes) y **EV/ha** (carga animal por hectárea); ambas unidades son
el lenguaje del productor ganadero.

El valor de 8 kg/EV/día debe quedar documentado en el system prompt para que Claude pueda
informarlo cuando el usuario pregunta "¿cuántos animales?" sin especificar la ración.

## Consecuencias

- Positivas: default correcto para el 80% de los casos; parámetro opcional no complica el
  flujo normal; dos métricas de salida (EV totales + EV/ha) son las más usadas en
  planificación forrajera.
- Deuda / costo asumido: el modelo asume que toda la materia seca producida está disponible
  para el consumo animal (no descuenta pérdidas por pisoteo, calidad nutritiva, etc.);
  es una estimación de capacidad potencial máxima, no una recomendación precisa. El system
  prompt debe aclararlo.
- Habilita: TECH-052 puede implementarse como una tool nueva `soporte_animal` que recibe
  parámetros de filtro (lotes, fechas) y ración, calcula EV y EV/ha, y los devuelve con
  un gráfico de barras por lote o período.

## Relacionadas

- ADR-009 (filtros, necesarios para acotar por lote/período en el cálculo)
- TECH-052 (origen de esta decisión)
