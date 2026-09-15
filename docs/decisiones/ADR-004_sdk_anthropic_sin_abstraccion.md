---
domain: tech
type: decision
---

# ADR-004 — Acoplamiento directo al SDK de Anthropic sin abstracción de LLM

## Estado

`Aceptada`

(El estado vive en `02-System/decisions.json`; acá se refleja para lectura.)

## Fecha

2026-09-03

## Contexto

El agente (`src/chatbot/agent.py`) necesita invocar un LLM con soporte de tool use para
orquestar la generación de gráficos. Al iniciar el MVP se optó implícitamente por llamar
directamente al SDK de Anthropic (`anthropic.Anthropic()`, `client.messages.create(...)`)
sin ninguna capa de abstracción de proveedor.

Fuerzas en juego:
- El MVP usa un único proveedor (Anthropic/Claude). No hay requisito inmediato de portabilidad.
- Tool use es una capacidad central del flujo: la abstracción debe soportarla fielmente o el
  boilerplate crece significativamente.
- Plazo y simplicidad: el MVP debe ser operable cuanto antes; evitar dependencias innecesarias
  reduce la superficie de fallo.
- Reversibilidad: si en el futuro se necesita cambiar de proveedor, la abstracción se puede
  introducir entonces con el caso de uso real delante.

## Opciones consideradas

### Opción A — Acoplamiento directo al SDK de Anthropic

Llamar a `anthropic.Anthropic()` y `client.messages.create(...)` directamente en `agent.py`,
con acceso nativo a todos los parámetros (tool use, tool_choice, streaming futuro, etc.).

- Pros:
  - Cero boilerplate de abstracción.
  - Acceso directo a la API completa del SDK, incluido tool use con parámetros finos
    (`tool_choice={"type": "any"}`, `tool_choice={"type": "none"}`).
  - Sin dependencias adicionales.
  - Mensajes de error nativos del SDK, más fáciles de depurar.
- Contras:
  - Acoplamiento al proveedor: cambiar a otro LLM requiere reescribir `agent.py`.
  - Si se agregan más módulos que llaman al LLM, cada uno importa el SDK directamente.

### Opción B — Capa de abstracción de LLM (LangChain, LiteLLM o interfaz propia)

Introducir una librería de orquestación (LangChain, LiteLLM) o definir una interfaz propia
(`LLMClient`) que encapsule el proveedor y exponga un contrato genérico.

- Pros:
  - Portabilidad de proveedor: cambiar de Anthropic a OpenAI u otro requiere solo actualizar
    la implementación concreta, sin tocar `agent.py`.
  - Facilita tests unitarios con mocks de la interfaz en lugar del SDK real.
- Contras:
  - Overhead inmediato: LangChain y LiteLLM son dependencias pesadas con superficie de fallo
    propia; una interfaz propia requiere diseño y mantenimiento.
  - El soporte de tool use varía entre abstracciones; replicar fielmente `tool_choice` y el
    ciclo de tool_result puede requerir workarounds o perder fidelidad.
  - Para un MVP de un solo proveedor, el costo de la abstracción no está justificado por ningún
    beneficio concreto.

## Decisión

Se elige la Opción A: acoplamiento directo al SDK de Anthropic. El criterio decisivo es que el
MVP tiene un único proveedor y la abstracción agrega complejidad sin beneficio inmediato. Si el
proyecto necesita soportar múltiples proveedores, se introduce la abstracción en ese momento con
el caso de uso real.

## Consecuencias

- Positivas: `agent.py` es simple y directo; el ciclo tool use / tool_result / tool_choice está
  expresado con la API nativa, sin traducciones ni pérdida de capacidades.
- Deuda asumida: cambiar de proveedor de LLM requiere reescribir la lógica de `agent.py`.
  El acoplamiento es conocido y aceptado para el alcance del MVP.
- Qué habilita: velocidad de desarrollo en el MVP; acceso a cualquier feature nueva del SDK
  sin esperar soporte en una capa intermedia.
- Qué bloquea: adoptar un segundo proveedor de LLM sin refactor previo de `agent.py`.

## Relacionadas

- Relacionada con: ADR-002 (tools predefinidas vs codegen), TECH-017
