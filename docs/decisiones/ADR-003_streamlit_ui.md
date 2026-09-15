---
domain: tech
type: decision
---

# ADR-003 — Streamlit como interfaz de usuario del chatbot

## Estado

`Aceptada`

(El estado vive en `02-System/decisions.json`; acá se refleja para lectura.)

## Fecha

2026-09-03

## Contexto

El chatbot necesita una interfaz web que permita al usuario escribir consultas en lenguaje
natural, ver el gráfico resultante (PNG estático) y leer la explicación textual. El historial
de la sesión debe ser visible durante la conversación.

Fuerzas en juego: velocidad de desarrollo (MVP), stack 100% Python, ausencia de requisitos de
autenticación o despliegue, necesidad de mostrar imágenes junto a texto, y ausencia de un
equipo frontend dedicado. El producto es un prototipo funcional para un único dataset CSV;
la complejidad de la UI no es un valor en sí mismo en esta etapa.

## Opciones consideradas

### Opción A — Streamlit

Framework Python que genera una UI web completa a partir de scripts Python. Incluye
componentes de chat (`st.chat_input`, `st.chat_message`), manejo de estado de sesión
(`st.session_state`), y visualización de imágenes (`st.image`) de forma nativa.

- Pros:
  - UI completa en Python puro: sin HTML, CSS ni JavaScript requeridos.
  - Componentes de chat nativos que encajan directamente con el caso de uso.
  - Hot-reload durante desarrollo: los cambios en `app.py` se reflejan al guardar.
  - Historial de sesión manejado por `st.session_state` sin infraestructura adicional.
  - Visualización de figuras matplotlib (PNG en memoria) con una sola llamada a `st.image`.
  - Tiempo de setup mínimo: `pip install streamlit` + `streamlit run app.py`.

- Contras:
  - Control limitado sobre el layout y estilo de la UI (opinionated).
  - El modelo de ejecución (re-run completo del script en cada interacción) puede ser confuso
    y genera restricciones para lógica de estado compleja.
  - No apto para producción a escala sin ajustes de concurrencia y sesiones independientes.
  - Difícil de testear de forma unitaria: la UI está acoplada al flujo de Streamlit.

### Opción B — Flask + frontend HTML/JS

Micro-framework web Python con una capa frontend separada (HTML, CSS, JavaScript puro o
con una librería ligera como Alpine.js o HTMX).

- Pros:
  - Control total sobre el markup, estilos y comportamiento del frontend.
  - Separación limpia entre backend (Python/Flask) y frontend.
  - Testeable con herramientas estándar (pytest + requests para la API, tests de UI separados).
  - Modelo de ejecución predecible: el servidor responde a requests HTTP explícitos.

- Contras:
  - Requiere mantener dos capas: lógica Python en Flask y presentación en HTML/JS.
  - Manejo de estado conversacional (historial de chat, sesiones) requiere implementación
    explícita (cookies, localStorage, o backend de sesiones).
  - Más código inicial para obtener una UI funcional equivalente a Streamlit.
  - Mostrar imágenes generadas en memoria requiere un endpoint de imagen separado o
    codificación base64 en la respuesta.

### Opción C — FastAPI + React

Stack profesional: FastAPI como backend REST/WebSocket y React como SPA frontend.

- Pros:
  - Máxima flexibilidad en UI/UX: React permite cualquier componente de chat, animaciones,
    streaming de texto, etc.
  - FastAPI provee validación automática de inputs, documentación OpenAPI y performance alta.
  - Arquitectura escalable y desacoplada: frontend y backend pueden desplegarse por separado.
  - Ecosistema de componentes React para chat muy amplio.

- Contras:
  - Complejidad significativa para un MVP: requiere configurar dos proyectos, build pipeline
    de Node/npm, CORS, y gestión de assets.
  - Introduce JavaScript como segundo lenguaje principal, lo que aumenta la superficie de
    mantenimiento para un equipo Python.
  - El tiempo de setup es el más alto de las opciones evaluadas.
  - Sobredimensionado para un prototipo de un solo dataset sin requisitos de escala.

### Opción D — Gradio

Framework similar a Streamlit, orientado a demos de modelos de ML. Genera interfaces web
desde Python con componentes predefinidos (textbox, image, chat).

- Pros:
  - También es Python puro, sin frontend separado.
  - `gr.ChatInterface` provee un componente de chat listo para usar.
  - Fácil de compartir via Hugging Face Spaces si se necesitara demo público.
  - Menos verboso que Streamlit para demos simples.

- Contras:
  - Componentes más rígidos que Streamlit: la personalización del layout es más limitada.
  - El componente de chat de Gradio está orientado a pares pregunta/respuesta simples; mezclar
    texto e imagen en el mismo turno de respuesta requiere workarounds.
  - Historial de sesión y estado persistente entre interacciones es menos ergonómico que
    `st.session_state`.
  - Comunidad y documentación más pequeña que Streamlit para casos de uso no-ML.

## Decisión

Opción A — Streamlit.

Criterio decisivo: el MVP necesita mostrar texto e imagen en el mismo turno de respuesta con
historial de sesión, en Python puro, con el mínimo de código. Streamlit provee exactamente eso
sin introducir un segundo lenguaje o un stack de build. La velocidad de desarrollo sobre la
flexibilidad de UI es la prioridad explícita del MVP.

## Consecuencias

- Positivas: `app.py` es un script Python único de menos de 100 líneas que implementa el chat
  completo con historial; cualquier desarrollador Python puede leerlo y modificarlo sin conocer
  HTML/JS; el ciclo de iteración es inmediato con hot-reload.
- Deuda / costo asumido: el modelo de re-run de Streamlit limita la arquitectura de la UI si
  en el futuro se necesitan interacciones más ricas (streaming token a token, componentes
  personalizados). El layout es opinionated y no permite personalización profunda sin hacks.
- Habilita: prototipos rápidos de nuevas funcionalidades directamente en `app.py`; fácil
  incorporación de nuevos componentes Streamlit (selectboxes, sliders) para filtros futuros.
- Bloquea a futuro: si se necesita autenticación por usuario, roles, o una UI con diseño
  específico de marca, Streamlit requerirá reemplazarse por Flask/FastAPI + frontend. La
  migración no es incremental: implica reescribir la capa de UI.

## Relacionadas

- Relacionada con: TECH-016 (formalización de esta ADR).
- Referencia de implementación: `app.py`.
