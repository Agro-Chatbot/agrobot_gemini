---
domain: tech
type: decision
---

# ADR-033 — Sin datos climáticos en el MVP: limitación declarada, sin proxy ni atribución causal

## Estado

`Aceptada`

(El estado vive en `02-System/decisions.json`; acá se refleja para lectura.)

## Fecha

2026-09-15

## Contexto

`data/tapalqueii.csv` no tiene lluvia ni temperatura. Es la clave más frecuente de la auditoría
después de la fecha de referencia (`columna-lluvia`, 19 preguntas; `columna-temperatura`, 2), y
"impacto de sequía/clima" es uno de los cinco casos de uso de `CLAUDE.md`. La auditoría muestra al
agente graficando sustitutos y afirmando que la sequía "queda claramente reflejada en los datos"
(M010, M019) — es decir, atribuyendo causas que el dataset no sostiene.

## Opciones consideradas

### Opción A — Incorporar una fuente meteorológica externa

- Pros: responde las preguntas tal como se formularon.
- Contras: cruce por fecha, licencia, calidad y tabla auxiliar; excede el MVP y arrastra TECH-037.

### Opción B — Proxy declarado (campaña de menor crecimiento = "año seco")

- Pros: barato.
- Contras: fabrica una variable que no existe e invita a atribuciones circulares (el crecimiento
  explicando el crecimiento).

### Opción C — Declarar la ausencia y no atribuir

- Pros: honestidad verificable; el productor sabe qué no puede preguntarle al sistema.
- Contras: ~10 preguntas del golden set quedan sin respuesta sustantiva.

## Decisión

Opción C (decisión del usuario). El MVP no tiene variables climáticas, no las infiere y no atribuye
causas climáticas. Ante una pregunta cuyo núcleo es clima, el agente responde **sin tool call**
declarando la ausencia y ofrece la consulta expresable equivalente. Corolarios: "año seco" y "año
frío" quedan **no determinables** con este dataset; "salida del invierno" sí se define como
**1-ago a 30-sep** vía `date_from`/`date_to` (uso agronómico; `Estacion=Primavera` de ADR-007 es
sep–nov y no sirve para esa expresión).

## Consecuencias

- Positivas: sube el piso de honestidad de ~10 respuestas del golden set; cierra TECH-120 (salvo la
  columna `Mes`) y TECH-154.
- Deuda / costo asumido: preguntas legítimas del productor quedan sin responder; la corrida de
  verificación debería mostrar más `status no_tool` y menos `rechaza` por atribución inventada.
- Reversible: si aparece una fuente meteorológica, un ADR nuevo supersede esta.

## Relacionadas

- Supersede el alcance climático de TECH-120 y TECH-154; habilita TECH-150; relacionada con ADR-007, TECH-037.
