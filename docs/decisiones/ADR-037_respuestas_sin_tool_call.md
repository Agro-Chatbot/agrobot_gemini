---
domain: tech
type: decision
---

# ADR-037 — Respuestas sin tool call: `tool_choice=auto` desde el intento 0 y `(None, texto)`

## Estado

`Aceptada`

(El estado vive en `02-System/decisions.json`; acá se refleja para lectura.)

## Fecha

2026-09-15

## Contexto

`answer()` usa `tool_choice={"type": "any"}` en el intento 0 y trata la ausencia de `tool_use` como
`RuntimeError`; `app.py` lo muestra como "Ocurrió un error al procesar tu consulta". Es decir: hoy
el sistema hace **imposible** abstenerse o pedir una aclaración. TECH-149 (pedir el lote ante "lote
X") y TECH-150 (abstenerse sin dato climático, ADR-033) son inimplementables sin cambiar esto.

## Opciones consideradas

### Opción A — Mantener `any` y devolver un gráfico con un aviso

- Pros: sin cambios.
- Contras: es exactamente el comportamiento que la auditoría marca como engañoso.

### Opción B — `auto` desde el intento 0; `answer()` devuelve `(fig | None, texto)`

- Pros: habilita abstención y aclaración; `app.py` renderiza solo texto cuando `fig is None`.
- Contras: con `auto` el modelo puede dejar de graficar preguntas que sí eran graficables.

### Opción C — Tool `responder_sin_grafico`

- Pros: conserva el contrato actual.
- Contras: séptima tool que confunde la comparación `tool_esperada` de la auditoría.

## Decisión

Opción B, con `disable_parallel_tool_use: True` en ambos intentos y en `answer_trace` (alinea las
dos funciones y adelanta la corrección de TECH-057). Sin `tool_use` **y** sin texto sigue siendo
`RuntimeError` (ese sí es un fallo real). `app.py` guarda `img_bytes=None` en el historial y el
re-render lo tolera. `test_answer_no_tool_use_raises` se reemplaza por
`test_answer_no_tool_use_devuelve_texto_sin_figura` + `test_answer_no_tool_use_sin_texto_raises`.

## Consecuencias

- Positivas: habilita TECH-149, TECH-150 y la regla de placeholders; alinea `answer` con
  `answer_trace` (que es lo que corre el golden set, así la corrida de verificación mide el cambio).
- Deuda / costo asumido: riesgo de que el modelo deje de graficar algo graficable; el contrapeso son
  las reglas de `prompt/limites.py` y la contra-hipótesis registrada en TECH-163.

## Relacionadas

- Relacionada con TECH-162, TECH-149, TECH-150, TECH-057, TECH-058; habilita ADR-033.
