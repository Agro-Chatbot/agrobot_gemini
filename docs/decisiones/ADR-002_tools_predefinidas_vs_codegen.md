---
domain: tech
type: decision
---

# ADR-002 — Tools de graficado predefinidas vs ejecución de código generado por LLM

## Estado

`Aceptada`

(El estado vive en `02-System/decisions.json`; acá se refleja para lectura.)

## Fecha

2026-09-03

## Contexto

El chatbot recibe consultas en lenguaje natural y debe producir un gráfico como respuesta.
Claude necesita tomar una decisión sobre qué graficar y con qué parámetros. La pregunta
es cómo materializar esa decisión en código que el sistema pueda ejecutar de forma segura
y predecible.

Fuerzas en juego: seguridad (no ejecutar código arbitrario), predecibilidad del output,
velocidad de desarrollo del MVP, extensibilidad futura, y compatibilidad con el SDK de
Anthropic (tool use nativo).

## Opciones consideradas

### Opción A — Tools predefinidas con tool use del SDK

El sistema expone un conjunto fijo de funciones de graficado (`bar_chart`, `line_chart`,
`scatter_plot`, `histogram`, `pie_chart`) descritas como schemas JSON al SDK de Anthropic.
Claude elige la tool apropiada y sus parámetros; el sistema ejecuta la función Python
correspondiente (código escrito por el equipo, no por el LLM). Cada función valida columnas
y tipos, levanta `ChartError` con mensaje legible, y el agente puede reintentar una vez si
los parámetros son inválidos.

- Pros:
  - Sin ejecución de código arbitrario: el surface de ataque se limita a los parámetros
    (strings/ints) que Claude puede pasar, no a código Python completo.
  - Output determinístico para el mismo input: la función siempre produce el mismo gráfico
    dado el mismo DataFrame y parámetros.
  - Validación explícita: errores de columna/tipo son detectados antes de tocar matplotlib,
    con mensajes que Claude puede interpretar para corregir.
  - Integración nativa con el SDK (tool use + `tool_choice`): flujo de un único turno con
    reintentos bien definidos.
  - Fácil de testear: cada función de graficado es una función Python pura con inputs/outputs claros.

- Contras:
  - Tipos de gráfico limitados al conjunto predefinido (5 al momento de la decisión).
  - Agregar un tipo de gráfico nuevo requiere escribir código Python y actualizar los schemas.
  - Consultas muy específicas (ej. gráfico con dos ejes Y) no pueden satisfacerse sin
    ampliar el conjunto de tools.

### Opción B — Ejecución de código Python generado por el LLM (code interpreter / exec)

Claude genera código Python (pandas + matplotlib) como string, y el sistema lo ejecuta
mediante `exec()` o un sandbox equivalente. El código resultante tiene acceso al DataFrame
y produce una figura que el sistema captura.

- Pros:
  - Flexibilidad total: cualquier gráfico expresable en pandas/matplotlib es posible,
    incluidos casos complejos con múltiples series, subplots, estilos personalizados, etc.
  - Claude puede adaptar el código a la consulta sin restricciones de schema.
  - No requiere mantener un catálogo de tools; cada respuesta es ad hoc.

- Contras:
  - Riesgo de seguridad significativo: `exec()` con código generado por un LLM puede
    ejecutar operaciones arbitrarias sobre el filesystem, red u otros recursos del proceso.
    Requiere sandboxing no trivial para ser seguro en producción.
  - Output no determinístico: el LLM puede generar código distinto para la misma consulta,
    dificultando la reproducibilidad y el debugging.
  - Errores de runtime difíciles de diagnosticar: un `NameError` o `KeyError` en el código
    generado no tiene un mensaje estructurado que el sistema pueda interpretar fácilmente.
  - Complejidad de captura de figuras: requiere instrumentar `plt.savefig()` o capturar
    el figure handle del contexto de ejecución, lo que no es trivial con `exec()`.
  - Más difícil de testear y auditar.

### Opción C — Templates de gráfico parametrizados (sin tool use)

El sistema mantiene templates de gráfico (strings de código con placeholders) y Claude
elige un template y completa los placeholders. El sistema instancia el template y lo ejecuta.

- Pros:
  - Reduce la superficie de ejecución vs codegen puro: el código base es conocido.
  - Más flexible que tools predefinidas para variaciones dentro de un tipo.

- Contras:
  - Más complejo de mantener que funciones Python: los templates son strings propensos a
    errores de formato e interpolación.
  - Sigue requiriendo alguna forma de `exec()` para instanciar el template, con los
    riesgos asociados.
  - No aprovecha el tool use nativo del SDK, que es la abstracción diseñada para este caso.
  - Validación de parámetros más difícil que en funciones Python tipadas.

## Decisión

Opción A — tools predefinidas con tool use del SDK de Anthropic.

Criterio decisivo: seguridad y predecibilidad son prioritarias en el MVP. No ejecutar
código generado por el LLM elimina la clase de riesgo más significativa. El conjunto de
5 tipos de gráfico cubre los casos de uso del MVP (distribuciones, comparaciones,
tendencias, correlaciones, proporciones), y el mecanismo de tool use del SDK provee
una interfaz limpia para que Claude elija y parametrice sin ambigüedad.

## Consecuencias

- Positivas: el sistema no ejecuta código arbitrario en ningún flujo normal; cada tool
  es una función Python testeable con validación explícita; los errores de parámetro
  son recuperables mediante el mecanismo de reintento del agente (`MAX_RETRIES = 1`).
- Deuda / costo asumido: el catálogo de tools debe mantenerse a mano; consultas que
  requieran visualizaciones fuera del conjunto predefinido no pueden satisfacerse sin
  ampliar el código.
- Bloquea a futuro: si se necesita visualización libre o notebooks interactivos, esta
  arquitectura requiere un rediseño del módulo de graficado (o un modo alternativo con
  sandboxing explícito). No se puede agregar codegen sin revisar el modelo de seguridad.
- Habilita: testeo unitario simple de cada tool, validaciones de columna/tipo reutilizables,
  y extensión incremental del catálogo de gráficos sin cambiar el agente.

## Relacionadas

- Relacionada con: TECH-015 (formalización de esta ADR).
- Referencia de implementación: `src/chatbot/charts.py` (dict `TOOLS`), `src/chatbot/agent.py` (función `answer`).
