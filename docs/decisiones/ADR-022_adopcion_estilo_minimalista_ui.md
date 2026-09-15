---
domain: tech
type: decision
---

# ADR-022 — Adopción del estilo `minimalista` de Sue como base visual del chatbot

## Estado

`Aceptada`

(El estado vive en `02-System/decisions.json`; acá se refleja para lectura.)

## Fecha

2026-09-12

## Contexto

ADR-021 fijó la superficie de personalización visual permitida (tema `config.toml`, un bloque
CSS inyectado desde `app.py`, `app.py` y matplotlib en `charts.py`). Sobre esa superficie,
TECH-097..106 relevaron el estado visual actual y compararon la UI contra los 7 estilos y los 7
tipos de página del catálogo de Sue; el resultado está en `docs/diseno/consolidado.md`
(71 recomendaciones, 13 grupos de duplicados, 9 cambios finales). Hace falta fijar qué estilo
base adopta el chatbot antes de capturar y ejecutar esos cambios, para que los tickets de
implementación compartan una única fuente de valores (los 56 tokens del contrato de
`knowledge/estilos/README.md`) y no mezclen identidades.

Fuerzas: el usuario es un productor rural que espera "un técnico de confianza" (no un panel
administrativo ni una consola); el gráfico y la explicación son el contenido principal y la UI
no debe competir con ellos; MVP sin sobre-ingeniería; conexión posiblemente limitada (sin
fuentes web); Streamlit re-ejecuta el script en cada interacción (tipo `app-interactiva`).

## Opciones consideradas

Los 7 estilos se puntuaron en aptitud para el chatbot (tabla completa en
`docs/diseno/consolidado.md`, "Selección de estilo base"). Tres empataron en el máximo (3/5):

### Opción A — `minimalista`

- Pros: es el más cercano al tema claro que Streamlit ya usa de facto (menor riesgo dentro de
  ADR-021); ningún cambio requiere dependencias ni fuentes web; monocromo, no compite con el
  gráfico; sus propias RECs resuelven las debilidades detectadas (paleta de gráfico, foco,
  contraste de avisos).
- Contras: valor diferencial moderado; gran parte del contrato de 56 tokens solo se alcanza vía
  CSS inyectado.

### Opción B — `empresarial`

- Pros: mejor encaje con el eje evaluador (contraste alto, foco obligatorio); casi todo
  declarativo vía `theme.*`.
- Contras: su formalidad institucional (sidebar, navbar, tablas densas) aleja el tono
  conversacional cercano que espera el productor.

### Opción C — `elegante`

- Pros: mejora objetiva de contraste en primario/avisos y en la paleta de gráfico.
- Contras: su identidad tipográfica real exige cargar una fuente web; el whitespace generoso
  compite con ver varios turnos de chat en celular sin scroll.

### Opción D — `minimalista` con overrides de otros estilos

- Pros: tomar lo mejor de cada uno (p. ej. la paleta de `elegante`).
- Contras: dos fuentes de valores para mantener; las debilidades de `minimalista` ya las cubren
  sus propias RECs, así que la mezcla no agrega valor real.

## Decisión

Se adopta **`minimalista` como único estilo base, sin overrides** (Opción A), y
**`app-interactiva`** como tipo de página de referencia. Criterio decisivo: es el estilo que
menos se aparta de lo que la app ya muestra, cumple "confianza sin tecnicismos" y no requiere
nada fuera de la superficie de ADR-021. Del tipo `app-interactiva` solo se toman el gráfico
responsive y el `page_icon`; no se agregan sidebar, cards ni auth.

## Consecuencias

- Positivas: una sola fuente de valores (los 56 tokens de `minimalista`) para
  `.streamlit/config.toml`, `src/chatbot/ui_theme.py` y la paleta de `charts.py`; los 9 cambios
  (`CAMBIO-01..09` de `consolidado.md`) son de esfuerzo S/M y no tocan la lógica del agente.
- Deuda / costo asumido: los selectores `data-testid` del CSS inyectado están verificados contra
  Streamlit 1.63.0 y pueden romperse al actualizar; se documentan con la versión.
- Habilita: cambiar de estilo más adelante es reemplazar los valores de `ui_theme.py` y
  `config.toml`, no reescribir la UI. Bloquea: identidad de marca fuerte o fuentes web (ambas
  fuera de esta decisión y de ADR-021).

## Relacionadas

- Relacionada con: ADR-003 (Streamlit), ADR-021 (superficie visual), TECH-106 (consolidado),
  TECH-107 (captura de cambios); ADR-003/004/005 de Sue.
- Fuente: `docs/diseno/consolidado.md`.
