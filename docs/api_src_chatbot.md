<!-- Regenerado manualmente a partir del código el 2026-10-01 (no hay run-docs.sh en este proyecto) -->
# API de src/chatbot y app.py

Documentación de la superficie pública de `src/chatbot/` (módulos `config`, `llm`, `data`, `charts/`, `prompt/`, `ui_theme`, `agent`) y del entrypoint `app.py` (en la raíz del proyecto). Cada sección corresponde a un módulo o paquete del código fuente. Las funciones con prefijo `_` son internas; solo se listan las que ayudan a entender el flujo.

## config

Módulo de configuración: carga variables de entorno desde el `.env` en la raíz del proyecto y resuelve rutas absolutas. No expone funciones; su superficie pública son constantes de nivel de módulo evaluadas al importar.

### Constantes / Globales

| Constante | Tipo | Descripción |
|---|---|---|
| `PROJECT_ROOT` | `pathlib.Path` | Raíz del proyecto (dos niveles por encima de `src/chatbot/`). Base para resolver el `.env`, el CSV y el directorio de salida. |
| `ANTHROPIC_API_KEY` | `str` | Leída de la variable de entorno `ANTHROPIC_API_KEY`. Cadena vacía si no está definida. |
| `LLM_MODEL` | `str` | Modelo de Claude; leído de `LLM_MODEL`. Por defecto `"claude-sonnet-4-6"`. |
| `CSV_PATH` | `pathlib.Path` | Ruta al dataset, leída de `CSV_PATH` (default `"data/sample.csv"`). Si es relativa, se resuelve contra `PROJECT_ROOT`. |
| `OUTPUT_DIR` | `pathlib.Path` | Directorio de salida de gráficos (`PROJECT_ROOT / "output"`). |

**Nota:** al importar el módulo se ejecuta `load_dotenv(PROJECT_ROOT / ".env")`.

## llm

Acceso al cliente de Anthropic. Construcción perezosa y cacheada en una única instancia de módulo (`_client`).

### get_client

```python
def get_client() -> anthropic.Anthropic
```

Devuelve el cliente de Anthropic, construyéndolo la primera vez y reutilizándolo después.

**Valor de retorno:** `anthropic.Anthropic`, inicializado con `config.ANTHROPIC_API_KEY`.

**Errores relevantes:**
- `RuntimeError` — si `config.ANTHROPIC_API_KEY` está vacía.

## data

Carga e inspección del dataset. Produce el resumen de esquema que alimenta el system prompt.

### Constantes / Globales

| Constante | Tipo | Descripción |
|---|---|---|
| `CARDINALITY_THRESHOLD` | `int` | `40`. Una columna categórica con hasta ese número de valores distintos se lista completa en `schema_summary`; por encima, solo una muestra. |

### enrich_temporal

```python
def enrich_temporal(df: pd.DataFrame) -> pd.DataFrame
```

Si `df` tiene la columna `Fecha`, devuelve una copia con `Fecha` convertida a datetime y tres columnas derivadas: `Anio` (año calendario como texto), `Estacion` (Verano/Otoño/Invierno/Primavera, hemisferio sur) y `Mes` (nombre del mes en español). Si no hay `Fecha`, devuelve `df` sin cambios.

### load_csv

```python
def load_csv(path: str | Path) -> pd.DataFrame
```

Carga un CSV con `pandas.read_csv` y aplica `enrich_temporal`.

**Errores relevantes:** `FileNotFoundError` si la ruta no existe (lo maneja `app.py`); excepciones de parseo de pandas.

### is_numeric

```python
def is_numeric(df: pd.DataFrame, column: str) -> bool
```

`True` si la columna tiene dtype numérico. Lanza `KeyError` si la columna no existe.

### schema_summary

```python
def schema_summary(df: pd.DataFrame, top_n: int = 5) -> str
```

Resumen compacto del dataset para el system prompt: número de filas y, por columna, su descripción:

- datetime: rango de fechas, cantidad de fechas distintas y una línea `Cobertura:` que marca las campañas (años calendario) parciales en los bordes del rango;
- numérica: min/max/media (o "sin datos válidos");
- categórica: todos los valores si hay `CARDINALITY_THRESHOLD` o menos; si no, los `top_n` más frecuentes indicando que es una muestra no exhaustiva.

Helpers internos: `_temporal_desc(fecha: pd.Series) -> str`, `_coverage_line(fecha: pd.Series) -> str`, `_categorical_desc(series: pd.Series, top_n: int) -> str`.

## charts (paquete)

`src/chatbot/charts/` agrupa las tools de graficado. Cada tool recibe el `DataFrame` más parámetros y devuelve `(figura_matplotlib, resumen_texto)`. Ante un parámetro inválido levanta `ChartError` con un mensaje legible que Claude puede usar para corregir. Usa el backend `Agg` de matplotlib. El `__init__` reexporta: `ChartError`, `TOOLS`, `tool_schemas`, `run_tool`, `bar_chart`, `line_chart`, `scatter_plot`, `histogram`, `pie_chart`, `soporte_animal`, `AGGS`, `CHART_PALETTE`, `AGG_LABELS`, `TITLE_FONTSIZE`, `TITLE_FONTWEIGHT` y los helpers `_apply_filters`, `_aggregate`, `_require_column`, `_require_numeric`.

Submódulos: `aggregate`, `basic`, `errors`, `filters`, `registry`, `soporte`, `style`.

### charts.errors

```python
class ChartError(ValueError)
```

Parámetro inválido para una tool de graficado. Su mensaje se devuelve a Claude como `tool_result` con `is_error=True` para que reintente.

### charts.style

Constantes: `AGG_LABELS` (`{"sum": "Suma", "mean": "Promedio", "count": "Cantidad"}`), `TITLE_FONTSIZE` (`14`), `TITLE_FONTWEIGHT` (`"bold"`), `CHART_PALETTE` (lista de 6 colores hex con contraste >= 3:1 sobre blanco; ADR-022).

```python
def _titulo(agg, y, x)
def _new_figure(figsize)
```

- `_titulo`: título legible tipo "Suma de Y por X".
- `_new_figure`: crea `(fig, ax)` con fondo blanco y el ciclo de color `CHART_PALETTE`.

### charts.aggregate

Constante `AGGS = {"sum": "sum", "mean": "mean", "count": "count"}`: agregaciones soportadas (valida `agg` y puebla los `enum` de los schemas).

Helpers internos (firmas reales):

```python
def _require_numeric(df, column)
def _aggregate_mean_frame(df, x, y, universe=None)
def _format_summary(frame)
def _aggregate(df, x, y, agg, universe=None)
def _aggregate_group_by(df, x, y, group_by, agg)
def _format_summary_group_by(summary_frame, x, group_by)
def _apply_top_n(grouped, top_n=None, order="desc")
```

- `agg="mean"` produce por grupo `valor`, `n` (filas) y `n_no_nulo`; con `universe` incluye categorías sin filas (valor NaN, `n=0`).
- `_aggregate_group_by` arma el pivot por `[x, group_by]` para comparar series.
- `_apply_top_n` recorta a las N categorías de mayor (`"desc"`) o menor (`"asc"`) valor.

### charts.filters

Filtrado compartido por todas las tools. Todo es interno salvo `_FILTER_PROPERTIES` (fragmento de `input_schema` con `filter_col`, `filter_val`, `filters`, `date_from`, `date_to`).

```python
def _require_column(df, column)
def _valores_sugeridos(available)
def _normalize_filter_entries(filter_col, filter_val, filters)
def _apply_filter_entry(df, entry)
def _apply_filters(df, filter_col=None, filter_val=None, date_from=None, date_to=None, filters=None)
```

- `filter_col`/`filter_val` (forma simple) y `filters` (lista de `{col, vals}`; AND entre entradas, OR entre los `vals` de una entrada; ADR-034) se combinan en AND.
- `date_from`/`date_to` (ISO 8601) filtran por `Fecha`.
- Lanza `ChartError` si la columna o el valor no existen (con valores sugeridos), si `filter_col` no trae `filter_val`, si la fecha es inválida o si el resultado queda vacío.

### charts.basic

Tools de graficado generales y sus schemas (`BAR_CHART_SCHEMA`, `LINE_CHART_SCHEMA`, `SCATTER_PLOT_SCHEMA`, `HISTOGRAM_SCHEMA`, `PIE_CHART_SCHEMA`). Todas las tools devuelven `tuple[matplotlib.figure.Figure, str]` y aceptan los parámetros de filtrado (`filter_col`, `filter_val`, `date_from`, `date_to`, `filters`) descritos en `charts.filters`.

#### bar_chart

```python
def bar_chart(df, x, y=None, agg="sum", filter_col=None, filter_val=None, date_from=None, date_to=None, filters=None, top_n=None, order="desc", reference_line=None, group_by=None)
```

Barras: agrega `y` (numérica; omitir con `agg="count"`) por `x`. `top_n`/`order` recortan a ranking. `reference_line="mean"` dibuja el promedio del subconjunto graficado y lo informa en el summary. `group_by` dibuja barras agrupadas por una segunda columna categórica (ADR-036); no se combina con `top_n` ni `reference_line`, y no puede ser igual a `x`.

#### line_chart

```python
def line_chart(df, x, y=None, agg="sum", filter_col=None, filter_val=None, date_from=None, date_to=None, filters=None, top_n=None, order="desc", group_by=None)
```

Líneas: tendencia de `y` agregada por `x`, ordenada por índice. Con `group_by` dibuja una línea por valor (no combinable con `top_n`).

#### scatter_plot

```python
def scatter_plot(df, x, y, filter_col=None, filter_val=None, date_from=None, date_to=None, filters=None)
```

Dispersión entre dos columnas numéricas; el summary trae `n` y la correlación (o `"N/A (varianza cero)"`).

#### histogram

```python
def histogram(df, column, bins=20, filter_col=None, filter_val=None, date_from=None, date_to=None, filters=None)
```

Histograma de una columna numérica; el summary es el `describe()` de la columna.

#### pie_chart

```python
def pie_chart(df, category, value=None, agg="sum", filter_col=None, filter_val=None, date_from=None, date_to=None, filters=None, top_n=None, order="desc")
```

Torta por categoría. Lanza `ChartError` si la agregación produce valores negativos. Con `agg="mean"`, las categorías sin datos se listan en el summary pero no se dibujan.

Errores comunes de las tools de `basic`: `ChartError` por columna inexistente, `agg` inválido, `y` faltante con `agg` distinto de `count`, columna no numérica o filtros que no devuelven datos.

Helpers internos: `_universo_categorias(df, col, filter_col, filter_val, filters)`, `_grouped_values_and_summary(grouped)`, `_add_reference_line(ax, valores, reference_line)`, `_validar_group_by(x, group_by, top_n, reference_line=None)`.

### charts.soporte

```python
def soporte_animal(df, filter_col=None, filter_val=None, date_from=None, date_to=None, racion_kg_dia=8.0, filters=None, group_by="Lote", n_ev=None)
```

Estima la capacidad de carga (EV soportados y EV/ha) a partir de `Kg MS ha/día` y `Superficie ha`. `racion_kg_dia` (kg MS/día por EV) debe ser > 0; `group_by` admite `"Lote"`, `"Campo"` o `"Recurso"`; `n_ev` (opcional, > 0) agrega las hectáreas requeridas al summary. Devuelve `(fig, resumen)`; la figura muestra EV soportados por grupo. El resumen incluye la nota de que es una estimación de capacidad potencial máxima. Schema: `SOPORTE_ANIMAL_SCHEMA`.

**Errores relevantes:** `ChartError` si `racion_kg_dia` o `n_ev` son <= 0, si `group_by` es inválido, si faltan las columnas requeridas o si el subconjunto queda vacío.

### charts.registry

```python
TOOLS = {...}  # bar_chart, line_chart, scatter_plot, histogram, pie_chart, soporte_animal
def tool_schemas()
def run_tool(name, df, params)
```

- `TOOLS`: cada clave mapea a `{"fn": <función>, "schema": <schema SDK>}`. Seis tools registradas.
- `tool_schemas()` → `list[dict]` con el `schema` de cada tool, para el parámetro `tools` de `messages.create`.
- `run_tool(name, df, params)` despacha la tool por nombre expandiendo `params` como kwargs. Devuelve lo que devuelva la tool. Lanza `ChartError` si `name` es desconocida o si los parámetros no coinciden con la firma (`TypeError` reenvasado), además de los `ChartError` propios de la tool.

## prompt (paquete)

`src/chatbot/prompt/` ensambla el system prompt a partir de secciones, una por archivo (TECH-159). Cada módulo expone `SECCION: str`, salvo `base` que expone `seccion(schema)` porque interpola el esquema.

### Constantes / Globales

| Constante | Tipo | Descripción |
|---|---|---|
| `SECCIONES` | `tuple[str, ...]` | Orden fijo de las secciones: `base`, `temporal`, `valores`, `filtros`, `recursos`, `graficos`, `soporte`, `ganaderia`, `clima`, `limites`. |

### system_prompt

```python
def system_prompt(schema: str) -> str
```

Concatena las secciones no vacías en el orden de `SECCIONES`, separadas por una línea en blanco. Es lo que usa `agent._system_prompt`.

### base.seccion

```python
def seccion(schema: str) -> str
```

Rol del asistente más el bloque "Esquema del dataset" con `schema`.

### Secciones (`SECCION`)

| Módulo | Contenido |
|---|---|
| `temporal` | Columnas derivadas (`Anio`, `Estacion`) y resolución de expresiones temporales relativas contra la última fecha con datos. |
| `valores` | Resolución de valores categóricos y coloquialismos; no negar un valor sin haber probado la tool. |
| `filtros` | Parámetros de filtrado disponibles en todas las tools y regla de comparación multivalor. |
| `recursos` | Categorías de dominio agregadas sobre `Recurso` (ADR-035), traducidas a `filters`. |
| `graficos` | Salvedades de composición al leer el summary de `agg='mean'` (`n`, `n_no_nulo`). |
| `soporte` | Cuándo y cómo usar la tool `soporte_animal`. |
| `ganaderia` | Guía de dominio ganadero: equivalencias EV por categoría (ADR-038). |
| `clima` | El dataset no tiene variables climáticas: responder sin tool call, sin proxy (ADR-033). |
| `limites` | Transparencia sobre los límites de las tools en la explicación. |

## ui_theme

Tokens de estilo de la interfaz. No expone funciones.

| Constante | Tipo | Descripción |
|---|---|---|
| `THEME_CSS` | `str` | Bloque `<style>` con las 56 custom properties CSS del contrato de estilo (estilo `minimalista`, `:root`) más reglas sobre selectores de Streamlit: anillo de foco del input del chat, separación entre turnos, contraste AA de `st.warning`/`st.error` y tipografía monoespaciada del caption. `app.py` lo inyecta una vez con `st.markdown(..., unsafe_allow_html=True)` tras `st.set_page_config`. |

Los `data-testid` usados están verificados para Streamlit 1.63.0 y pueden cambiar entre versiones.

## agent

Orquestación: consulta en lenguaje natural → Claude elige (o no) una tool → se renderiza el gráfico → Claude explica el resultado. Ante parámetros inválidos (`ChartError`) devuelve el error a Claude para que corrija y reintenta.

### Constantes / Globales

| Constante | Tipo | Descripción |
|---|---|---|
| `MAX_TOKENS` | `int` | Límite de tokens por llamada a Claude (`1024`). |
| `MAX_RETRIES` | `int` | Reintentos si Claude pasa parámetros inválidos (`1`). El bucle corre `MAX_RETRIES + 1` intentos. |

### answer

```python
def answer(query: str, df, schema: str)
```

Punto de entrada de la orquestación. En todos los intentos (incluido el reintento tras un `ChartError`) llama a Claude con `tool_choice={"type": "auto", "disable_parallel_tool_use": True}`: Claude puede elegir una tool o responder solo con texto, y nunca emite varias tool calls en paralelo (ADR-037).

| Parámetro | Tipo | Descripción |
|---|---|---|
| `query` | `str` | Consulta del usuario en lenguaje natural. |
| `df` | `pandas.DataFrame` | Dataset sobre el que responder. |
| `schema` | `str` | Resumen del esquema (de `data.schema_summary`) para el system prompt. |

**Valor de retorno:** tupla `(fig, texto)`.
- Con tool call: `fig` es la `matplotlib.figure.Figure` generada y `texto` la explicación (2-4 frases, obtenida con `_explain`).
- Sin tool call pero con texto (p. ej. una aclaración o abstención porque el dato no existe, como en `prompt/clima`): `fig` es `None` y `texto` es el texto de Claude (`return None, text`). Es un caso válido, no un error (ADR-037). Quien llama debe tolerar `fig is None` (`app.py` renderiza solo texto).

**Errores relevantes:**
- `RuntimeError` — si Claude no elige tool **y** no devuelve texto; si se agotan los reintentos tras `ChartError` ("No se pudo generar un gráfico válido tras varios intentos."); o si `_explain` falla (la figura se cierra con `plt.close` antes de propagar).
- Los `ChartError` intermedios se capturan y se devuelven a Claude como `tool_result` con `is_error=True`; no se propagan desde `answer`.
- Puede propagar errores del cliente de Anthropic.

### answer_trace

```python
def answer_trace(query: str, df, schema: str) -> dict
```

Ejecuta el mismo loop agéntico que `answer` (mismo `tool_choice` y mismos reintentos) pero, en vez de devolver la figura, registra las tool calls y la explicación. Está pensada para auditorías en batch (golden set): no renderiza ni guarda el gráfico (cierra la figura) y no lanza en los casos borde, para no abortar un batch por una sola pregunta.

**Valor de retorno:** `dict` con las claves:

| Clave | Descripción |
|---|---|
| `query` | La consulta recibida. |
| `calls` | Lista de `{"name", "input"}` de cada tool call hecha, incluidos reintentos; las que fallaron llevan además `"error"`. |
| `summary` | Resumen de datos de la tool exitosa, o `None`. |
| `explanation` | Texto de explicación. Sin tool call es el texto de Claude (puede ser `""`); si la explicación falla, una nota entre guiones bajos. |
| `status` | `"ok"`; `"ok_sin_texto"` (gráfico generado pero `_explain` falló); `"no_tool"` (Claude respondió sin tool, ADR-037); `"failed"` (reintentos agotados). |

### _explain

```python
def _explain(client, system, messages, assistant_content, tool_use, summary)
```

Interna. Segunda llamada a Claude (sin `tools`), pasándole el `tool_result` con el resumen de datos, para obtener la explicación (2-4 frases). Devuelve `str`; lanza `RuntimeError` si Claude no devuelve texto.

### _system_prompt

```python
def _system_prompt(schema: str) -> str
```

Interna. Delega en `prompt.system_prompt(schema)`.

## app

Entrypoint de la interfaz web (Streamlit), en la raíz del proyecto (`app.py`, se ejecuta con `streamlit run app.py`). No expone funciones públicas reutilizables.

### _load

```python
@st.cache_data
def _load()
```

Interna, cacheada por Streamlit. Carga `config.CSV_PATH` con `load_csv` y calcula `schema_summary`. Devuelve `tuple[pandas.DataFrame, str]`.

**Flujo del script (nivel de módulo):**
- Configura la página, inyecta `ui_theme.THEME_CSS` y muestra el título.
- Carga `df, schema` con `_load()`; `FileNotFoundError` y otras excepciones se registran en `stderr`, se muestra un error amigable y se detiene la app (`st.stop`).
- Muestra un caption con nombre del dataset, filas y columnas.
- Mantiene `st.session_state.history` (lista de `{query, img_bytes, text}`) y la re-renderiza en cada rerun; `img_bytes` es `None` en las respuestas sin gráfico, y en ese caso solo se escribe el texto.
- Muestra un expander con ejemplos de preguntas mientras el historial está vacío.
- Valida la consulta: rechaza vacías y las que superen `MAX_QUERY_LEN = 2000`.
- Invoca `answer(query, df, schema)` dentro de un spinner; captura `ChartError`, `RuntimeError` y `Exception` con mensajes específicos y traceback en `stderr`.
- Si `fig is None` (ADR-037), escribe el texto y lo guarda en el historial con `img_bytes=None`. Si hay figura, guarda `ultimo_grafico.png` en `config.OUTPUT_DIR`, renderiza la imagen y el texto, agrega al historial y cierra la figura con `plt.close` en `finally`.

## Ver también
- [Flujo end-to-end del chatbot](flujo_producto.md): narrativa paso a paso y diagrama
  Mermaid del flujo completo, desde la entrada del usuario hasta la respuesta en pantalla.
- [ADR-037](decisiones/ADR-037_respuestas_sin_tool_call.md): respuestas sin tool call, `tool_choice` auto y retorno `(None, texto)`.
