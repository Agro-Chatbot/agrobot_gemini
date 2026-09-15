# AgroBot-Hank

Chatbot de análisis de datos forrajeros/ganaderos orientado a un usuario rural no técnico.
Recibe consultas en lenguaje natural sobre un dataset CSV de tasas de crecimiento de
pasturas y responde con un **gráfico + un texto que lo explica**.

Casos de uso principales:

- Tasas de crecimiento de pasturas por lote/campaña/período.
- Soporte animal (cantidad de animales que soporta un lote o campaña en un período).
- Comparación entre campañas (rendimiento relativo de lotes o períodos).
- Impacto de sequía/clima en el crecimiento del recurso forrajero.
- Demanda animal y raciones (cuánto pasto necesita un conjunto de animales).

## Cómo funciona

Consulta en lenguaje natural → Claude (Anthropic) elige una **tool de graficado predefinida**
con parámetros validados vía *tool use* → pandas + Matplotlib generan el gráfico → Claude
explica los datos agregados → Streamlit muestra gráfico + texto. El modelo nunca ejecuta
código generado por sí mismo: siempre pasa por una tool predefinida con su propio schema y
validación (decisión de seguridad/predecibilidad del MVP).

Este proyecto es el Trabajo Práctico Integrador de la materia IA Agéntica, Maestría en
Explotación de Datos (UBA).

## Setup

Requiere Python 3.11 (se recomienda instalarlo vía [pyenv](https://github.com/pyenv/pyenv),
no el Python del sistema ni un entorno conda).

```bash
# Instalar Python 3.11 con pyenv (si no está instalado)
pyenv install 3.11.13

# Crear el entorno virtual con el intérprete de pyenv
~/.pyenv/versions/3.11.13/bin/python3.11 -m venv .venv

# Activar e instalar dependencias
source .venv/bin/activate
pip install -r requirements.txt && pip install -e .

cp .env.example .env    # completar ANTHROPIC_API_KEY
```

El uso del chatbot consume la API de Anthropic (`ANTHROPIC_API_KEY`), que se factura
**pay per token** — no está incluido en ninguna suscripción de Claude Code ni similar.

## Datos

Este repo incluye `data/sample.csv`, un dataset **sintético** (no son datos reales de
ningún establecimiento) generado con semilla fija para reproducibilidad, con el mismo
esquema que un dataset forrajero real:

```
Fecha, CREA, Campo, Lote, Recurso, Kg MS ha/día, Superficie ha
```

- `Fecha`: fecha del registro (`YYYY-MM-DD`).
- `CREA`, `Campo`, `Lote`: identificadores jerárquicos del establecimiento.
- `Recurso`: tipo de recurso forrajero (campo natural, pasturas implantadas, verdeos,
  promociones de raigrás — ver `src/chatbot/prompt/` para el vocabulario completo).
- `Kg MS ha/día`: tasa de crecimiento de materia seca.
- `Superficie ha`: superficie del lote en hectáreas.

`.env.example` apunta `CSV_PATH=data/sample.csv` por defecto. Para usar tus propios datos,
apuntá `CSV_PATH` en el `.env` a un CSV propio con columnas equivalentes.

`data/sample.csv` se generó con un script del toolkit de desarrollo interno
(`make_agrobot_sample.py`, semilla fija = 42, determinista: misma semilla → mismo archivo byte
a byte), que no forma parte de esta publicación. Si querés tu propio dataset sintético con el
mismo esquema, escribí un generador propio que produzca columnas `Fecha, CREA, Campo, Lote,
Recurso, Kg MS ha/día, Superficie ha` con los valores de `Recurso` documentados arriba.

## Uso

```bash
streamlit run app.py
```

Preguntas de ejemplo (ver el listado completo en
[`docs/preguntas/00-preguntas_ejemplo.md`](docs/preguntas/00-preguntas_ejemplo.md)):

- "¿Cuál es la tasa de crecimiento promedio (Kg MS/ha/día) por tipo de recurso forrajero?"
- "¿Cómo evolucionó la tasa de crecimiento promedio a lo largo del tiempo?"
- "¿Qué campo tiene el mejor rendimiento forrajero promedio?"
- "¿Cuántos animales puede soportar el lote X en este período?"
- "¿Cómo se comparan las tasas de crecimiento promedio entre campañas?"
- "¿Qué proporción de la superficie total corresponde a cada tipo de recurso?"

### Tests

```bash
pytest -q
```

Los tests de `data.py` y `charts/` no requieren API key.

## Estructura del código

```
src/chatbot/
  config.py     carga .env (API key, modelo, ruta del CSV)
  llm.py        cliente Anthropic singleton
  data.py       carga del CSV + resumen de esquema
  agent.py      orquestación query -> tool_use -> explicación
  ui_theme.py   estilos de la interfaz Streamlit
  prompt/       system prompt, organizado por secciones (filtros, gráficos, soporte
                animal, ganadería, clima, límites, recursos, temporal, valores)
  charts/       tools predefinidas de graficado (bar_chart, line_chart, scatter_plot,
                histogram, pie_chart, soporte_animal) + validación de parámetros
app.py          UI Streamlit (chat con historial de sesión)
```

## Documentación

- `docs/arquitectura_sistema.md` — arquitectura del sistema.
- `docs/api_src_chatbot.md` — referencia de la API interna (`src/chatbot/`).
- `docs/flujo_producto.md` — flujo end-to-end del producto, con diagrama.
- `docs/presentaciones/` — consignas del TP y propuesta.
- `docs/preguntas/` — golden set de preguntas de ejemplo y su cobertura actual.
- `docs/decisiones/` — decisiones de arquitectura de producto (ADR).

## Nota

Este repositorio se genera automáticamente por export desde un toolkit de desarrollo interno que no forma parte de esta publicación.
