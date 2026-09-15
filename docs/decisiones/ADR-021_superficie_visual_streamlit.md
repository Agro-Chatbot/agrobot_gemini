---
domain: tech
type: decision
---

# ADR-021 — Superficie de personalización visual permitida en la UI Streamlit

## Estado

`Aceptada`

(El estado vive en `02-System/decisions.json`; acá se refleja para lectura.)

## Fecha

2026-09-12

## Contexto

La UI del chatbot es Streamlit puro (ADR-003): `app.py` usa el tema por defecto, no hay
`.streamlit/config.toml` ni CSS propio, y los gráficos de `src/chatbot/charts.py` salen con la
paleta y tipografía default de matplotlib. Se quiere mejorar visualmente la app comparándola
contra los 7 estilos y los 7 tipos de página del catálogo de Sue
(`/Users/lreinoso/Asistente/04-Proyectos/sue_generadora_de_paginas_web/knowledge/`), cuyo
contrato son 56 variables CSS por estilo (`knowledge/estilos/README.md`). Streamlit no expone
esas 56 variables: su tema nativo cubre ~5 claves (`primaryColor`, `backgroundColor`,
`secondaryBackgroundColor`, `textColor`, `font`), y todo lo demás requiere inyectar CSS sobre
selectores internos del framework. ADR-003 ya advierte que "una UI con diseño específico de
marca" implicaría reemplazar Streamlit.

Antes de escribir los tickets de comparación (TECH-097..TECH-107) hay que fijar qué pueden
recomendar los informes, para que las recomendaciones sean aplicables y comparables entre sí.

## Opciones consideradas

### Opción A — Solo tema nativo (`config.toml`) y widgets de `app.py`

- Pros: cero riesgo de rotura entre versiones de Streamlit; sin `unsafe_allow_html`; cambios
  triviales de revisar.
- Contras: de las 56 variables del contrato solo ~5 tienen equivalente; no hay control de
  tipografía de títulos, espaciado, bordes, radios ni foco. Las comparaciones de estilo
  quedarían casi vacías.

### Opción B — Tema nativo + un bloque acotado de CSS inyectado + `app.py` + matplotlib

- Pros: permite mapear las 56 variables como custom properties y aplicar un subconjunto
  acotado de reglas sobre selectores estables (`[data-testid="stChatMessage"]`,
  `[data-testid="stChatInput"]`, `[data-testid="stExpander"]`, `h1`, `[data-testid="stCaptionContainer"]`);
  los gráficos (paleta, grilla, fuente, `figsize`) se alinean con el mismo estilo; sigue siendo
  Streamlit, sin dependencias nuevas ni reescritura.
- Contras: `unsafe_allow_html=True` y selectores `data-testid` internos que Streamlit puede
  cambiar entre versiones (hoy 1.63.0); hay que concentrar el CSS en un único lugar para
  poder revisarlo y revertirlo.

### Opción C — Migrar la UI a un starter de Sue (`app-interactiva`, React + Vite)

- Pros: control total del diseño; los 56 tokens aplican tal cual.
- Contras: reescritura completa de la capa UI (ADR-003: "la migración no es incremental"),
  segundo lenguaje, build de Node, y un backend HTTP nuevo para `answer()`. Fuera del alcance
  del MVP y del TP.

## Decisión

Opción B. Criterio decisivo: es la única que hace útiles las comparaciones de estilo sin
salir de Streamlit ni del MVP. La superficie de cambio queda fijada así, y es **normativa**
para todos los tickets de análisis y para los cambios que salgan de ellos:

1. `.streamlit/config.toml` — sección `[theme]` (`base`, `primaryColor`, `backgroundColor`,
   `secondaryBackgroundColor`, `textColor`, `font`).
2. Un único bloque CSS inyectado desde un módulo nuevo `src/chatbot/ui_theme.py` (una función
   que devuelve el `<style>` y `app.py` la llama una vez con `st.markdown(..., unsafe_allow_html=True)`):
   declara las 56 variables del contrato de Sue como custom properties en `:root` y aplica
   reglas acotadas sobre selectores estables. Cada selector `data-testid` usado se documenta
   con la versión de Streamlit contra la que se verificó.
3. Layout y widgets de `app.py` (`layout`, título, caption, expander de ejemplos, orden y
   agrupación de elementos, sidebar si aplica).
4. Parámetros visuales de matplotlib en `src/chatbot/charts.py` (paleta, `figsize`, grilla,
   fuente, tamaño de títulos/ejes) — sin cambiar las firmas de las tools, sus validaciones ni
   el `summary` que devuelven.

Prohibido: dependencias nuevas en `pyproject.toml`; reescribir la UI fuera de Streamlit;
tocar `src/chatbot/agent.py`, `llm.py`, `data.py`; romper `.venv/bin/pytest -q`.

## Consecuencias

- Positivas: las 7 comparaciones de estilo y la de tipos de página tienen un marco común de
  qué es aplicable; el CSS queda en un solo archivo revisable y reversible; los gráficos y la
  UI comparten estilo.
- Deuda / costo asumido: dependencia de selectores internos de Streamlit — una actualización
  del framework puede degradar visualmente la app (no funcionalmente); `unsafe_allow_html`
  queda restringido a ese único bloque generado por código propio, sin contenido del usuario.
- Habilita: cambiar de estilo reemplazando el bloque de custom properties (mismo mecanismo
  `tokens.css` de Sue). Bloquea: cualquier recomendación que necesite componentes
  personalizados o layout fuera de lo que Streamlit permite (se descarta en el consolidado).

## Relacionadas

- Relacionada con: ADR-003 (Streamlit como UI), TECH-097..TECH-107 (comparaciones y
  consolidado), ADR-003/ADR-004 de Sue (`sue_generadora_de_paginas_web/02-System/decisions/`).
