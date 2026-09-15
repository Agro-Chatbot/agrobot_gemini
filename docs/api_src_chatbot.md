<!-- Generado por run-docs.sh el 2026-09-08 04:24 -->
# API de src/chatbot y app.py

Documentación de la superficie pública de los módulos de `src/chatbot/` y del entrypoint `app.py`. Cada sección corresponde a un archivo del código fuente.

## config

Módulo de configuración: carga variables de entorno desde el `.env` en la raíz del proyecto y resuelve rutas absolutas. No expone funciones; su superficie pública son constantes de nivel de módulo evaluadas al importar.

### Constantes / Globales

| Constante | Tipo | Descripción |
|---|---|---|
| `PROJECT_ROOT` | `pathlib.Path` | Raíz del proyecto, resuelta como dos niveles por encima de `src/chatbot/`. Base para resolver el `.env`, el CSV y el directorio de salida. |
| `ANTHROPIC_API_KEY` | `str` | Clave de API de Anthropic leída de la variable de entorno `ANTHROPIC_API_KEY`. Cadena vacía si no está definida. |
| `LLM_MODEL` | `str` | Modelo de Claude a usar; leído de `LLM_MODEL`. Por defecto `"claude-sonnet-4-6"`. |
| `CSV_PATH` | `pathlib.Path` | Ruta al dataset CSV, leída de `CSV_PATH` (default `"data/sample.csv"`). Si es relativa, se resuelve contra `PROJECT_ROOT`. |
| `OUTPUT_DIR` | `pathlib.Path` | Directorio de salida para gráficos (`PROJECT_ROOT / "output"`). |

**Nota:** al importar el módulo se ejecuta `load_dotenv(PROJECT_ROOT / ".env")`, por lo que las variables del `.env` se cargan como efecto secundario del import.

## llm

Módulo de acceso al cliente de Anthropic. Encapsula la construcción perezosa (lazy) y cacheada del cliente SDK en una única instancia de módulo (`_client`).

### get_client

```python
def get_client() -> anthropic.Anthropic
```

Devuelve el cliente de Anthropic, construyéndolo la primera vez y reutilizándolo (singleton de módulo) en llamadas posteriores.

| Parámetro | Tipo | Descripción |
|---|---|---|
| — | — | No recibe parámetros. |

**Valor de retorno:** `anthropic.Anthropic` — instancia del cliente SDK, inicializada con `config.ANTHROPIC_API_KEY`.

**Errores relevantes:**
- `RuntimeError` — si `config.ANTHROPIC_API_KEY` está vacía (falta la clave en el `.env`).

## data

Utilidades de carga e inspección del dataset. Cargan el CSV en un `DataFrame` de pandas y producen el resumen de esquema que alimenta el system prompt de Claude.

### load_csv

```python
def load_csv(path: str | Path) -> pd.DataFrame
```

Carga un archivo CSV en un `DataFrame` de pandas.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `path` | `str \| pathlib.Path` | Ruta al archivo CSV a cargar. |

**Valor de retorno:** `pandas.DataFrame` — el dataset cargado.

**Errores relevantes:**
- `FileNotFoundError` — si la ruta no existe (propagado por `pandas.read_csv`; manejado en `app.py`).
- Otras excepciones de parseo de pandas (p. ej. `pandas.errors.ParserError`).

### is_numeric

```python
def is_numeric(df: pd.DataFrame, column: str) -> bool
```

Indica si una columna del `DataFrame` es de tipo numérico.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `df` | `pandas.DataFrame` | Dataset sobre el que se consulta. |
| `column` | `str` | Nombre de la columna a evaluar. |

**Valor de retorno:** `bool` — `True` si la columna tiene dtype numérico, `False` en caso contrario.

**Errores relevantes:**
- `KeyError` — si la columna no existe en el `DataFrame`.

### schema_summary

```python
def schema_summary(df: pd.DataFrame, top_n: int = 5) -> str
```

Genera un resumen compacto del dataset (filas, columnas y estadísticas por columna) destinado al system prompt de Claude.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `df` | `pandas.DataFrame` | Dataset a resumir. |
| `top_n` | `int` | Cantidad de valores frecuentes a listar por columna categórica. Default `5`. |

**Valor de retorno:** `str` — texto multilínea: número de filas y, por cada columna, si es numérica (min/max/media, o "sin datos válidos" si todo es NaN) o categórica (valores más frecuentes).

**Errores relevantes:** ninguno específico; asume que `df` es un `DataFrame` válido.

## charts

Tools de graficado predefinidas. Cada función recibe el `DataFrame` más parámetros validados y devuelve `(figura_matplotlib, resumen_datos_texto)`. Ante un parámetro inválido levantan `ChartError` con un mensaje legible que Claude puede usar para corregir. Usa el backend `Agg` de matplotlib (sin display), apto para servidor/tests.

### Constantes / Globales

| Constante | Tipo | Descripción |
|---|---|---|
| `AGGS` | `dict[str, str]` | Agregaciones soportadas: `{"sum", "mean", "count"}`. Se usa para validar el parámetro `agg` y para poblar los `enum` de los schemas. |
| `TOOLS` | `dict[str, dict]` | Registro de tools disponibles. Cada clave (`bar_chart`, `line_chart`, `scatter_plot`, `histogram`, `pie_chart`) mapea a un dict con `"fn"` (la función Python) y `"schema"` (definición de tool para el SDK de Anthropic: `name`, `description`, `input_schema`). |

### ChartError

```python
class ChartError(ValueError)
```

Excepción que representa un parámetro inválido para una tool de graficado. Su mensaje es legible y está pensado para devolverse a Claude como `tool_result` con `is_error=True`, de modo que reintente con parámetros corregidos. Al heredar de `ValueError`, puede capturarse también como tal.

### bar_chart

```python
def bar_chart(df, x, y=None, agg="sum")
```

Gráfico de barras: agrega una columna numérica (`y`) por una categórica (`x`) según `agg`.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `df` | `pandas.DataFrame` | Dataset de origen. |
| `x` | `str` | Columna categórica para el eje X (agrupación). |
| `y` | `str \| None` | Columna numérica a agregar. Debe omitirse/`None` cuando `agg="count"`. |
| `agg` | `str` | Agregación: `"sum"`, `"mean"` o `"count"`. Default `"sum"`. |

**Valor de retorno:** `tuple[matplotlib.figure.Figure, str]` — la figura y el resumen textual de la serie agrupada.

**Errores relevantes:**
- `ChartError` — si `x` no existe, si `agg` es inválido, si falta `y` para una agregación distinta de `count`, o si `y` no es numérica.

### line_chart

```python
def line_chart(df, x, y=None, agg="sum")
```

Gráfico de líneas: tendencia de una columna agregada (`y`) por otra (`x`, p. ej. una fecha), ordenada por índice.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `df` | `pandas.DataFrame` | Dataset de origen. |
| `x` | `str` | Columna para el eje X (categoría o etiqueta, típicamente temporal). |
| `y` | `str \| None` | Columna numérica a agregar. Omitir/`None` cuando `agg="count"`. |
| `agg` | `str` | Agregación: `"sum"`, `"mean"` o `"count"`. Default `"sum"`. |

**Valor de retorno:** `tuple[matplotlib.figure.Figure, str]` — la figura y el resumen textual de la serie agrupada y ordenada.

**Errores relevantes:**
- `ChartError` — si `x` no existe, si `agg` es inválido, si falta `y` para agregación distinta de `count`, o si `y` no es numérica.

### scatter_plot

```python
def scatter_plot(df, x, y)
```

Gráfico de dispersión entre dos columnas numéricas, para observar su relación. Incluye la correlación en el resumen.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `df` | `pandas.DataFrame` | Dataset de origen. |
| `x` | `str` | Columna numérica para el eje X. |
| `y` | `str` | Columna numérica para el eje Y. |

**Valor de retorno:** `tuple[matplotlib.figure.Figure, str]` — la figura y un resumen con `n` y la correlación entre `x` e `y` (o `"N/A (varianza cero)"` si no es calculable).

**Errores relevantes:**
- `ChartError` — si `x` o `y` no existen o no son numéricas.

### histogram

```python
def histogram(df, column, bins=20)
```

Histograma de la distribución de una columna numérica.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `df` | `pandas.DataFrame` | Dataset de origen. |
| `column` | `str` | Columna numérica a distribuir. |
| `bins` | `int` | Cantidad de bins. Default `20` (se castea con `int()`). |

**Valor de retorno:** `tuple[matplotlib.figure.Figure, str]` — la figura y el resumen `describe()` de la columna.

**Errores relevantes:**
- `ChartError` — si `column` no existe o no es numérica.

### pie_chart

```python
def pie_chart(df, category, value=None, agg="sum")
```

Gráfico de torta: proporción de una columna (`value`) agregada por categoría (`category`).

| Parámetro | Tipo | Descripción |
|---|---|---|
| `df` | `pandas.DataFrame` | Dataset de origen. |
| `category` | `str` | Columna categórica que define los sectores. |
| `value` | `str \| None` | Columna numérica a agregar. Omitir/`None` cuando `agg="count"`. |
| `agg` | `str` | Agregación: `"sum"`, `"mean"` o `"count"`. Default `"sum"`. |

**Valor de retorno:** `tuple[matplotlib.figure.Figure, str]` — la figura y el resumen textual de la serie agrupada.

**Errores relevantes:**
- `ChartError` — si `category` no existe, si `agg` es inválido, si falta `value` para agregación distinta de `count`, si `value` no es numérica, o si la agregación produce valores negativos (la torta exige valores no negativos).

### tool_schemas

```python
def tool_schemas()
```

Devuelve la lista de schemas de tools en el formato esperado por el SDK de Anthropic, para pasar en el parámetro `tools` de `messages.create`.

| Parámetro | Tipo | Descripción |
|---|---|---|
| — | — | No recibe parámetros. |

**Valor de retorno:** `list[dict]` — lista de los `schema` de cada entrada de `TOOLS`.

**Errores relevantes:** ninguno.

### run_tool

```python
def run_tool(name, df, params)
```

Despacha la ejecución de una tool de graficado por nombre, aplicando sus parámetros al `DataFrame`.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `name` | `str` | Nombre de la tool (clave de `TOOLS`, p. ej. `"bar_chart"`). |
| `df` | `pandas.DataFrame` | Dataset de origen. |
| `params` | `dict` | Parámetros de la tool (se expanden como kwargs a la función). |

**Valor de retorno:** `tuple[matplotlib.figure.Figure, str]` — lo que devuelva la tool invocada.

**Errores relevantes:**
- `ChartError` — si `name` no está en `TOOLS`, si los parámetros no coinciden con la firma de la función (`TypeError` reenvasado), o cualquier `ChartError` propagado desde la tool concreta.

## agent

Orquestación del flujo: consulta en lenguaje natural → Claude elige una tool (tool use) → se renderiza el gráfico → Claude explica el resultado. Reintenta una vez ante parámetros inválidos, devolviéndole el error a Claude para que corrija.

### Constantes / Globales

| Constante | Tipo | Descripción |
|---|---|---|
| `MAX_TOKENS` | `int` | Límite de tokens por llamada a Claude (`1024`). |
| `MAX_RETRIES` | `int` | Reintentos si Claude pasa parámetros inválidos (`1`). El bucle corre `MAX_RETRIES + 1` intentos. |

### answer

```python
def answer(query: str, df, schema: str)
```

Punto de entrada de la orquestación: dada una consulta en lenguaje natural, obtiene de Claude la elección de tool, genera el gráfico y devuelve su explicación. En el primer intento fuerza el uso de tool (`tool_choice="any"`); en el reintento usa `"auto"`.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `query` | `str` | Consulta del usuario en lenguaje natural. |
| `df` | `pandas.DataFrame` | Dataset sobre el que responder. |
| `schema` | `str` | Resumen del esquema (de `data.schema_summary`) que se inyecta al system prompt. |

**Valor de retorno:** `tuple[matplotlib.figure.Figure, str]` — la figura generada y el texto explicativo (2–4 frases).

**Errores relevantes:**
- `RuntimeError` — si Claude responde con texto sin elegir tool; si no se logra un gráfico válido tras agotar los reintentos; o si la explicación falla (en cuyo caso la figura se cierra con `plt.close` antes de propagar).
- `ChartError` — puede propagarse desde `run_tool` en el último intento fallido (los intentos intermedios se capturan y se reintentan).
- Además puede propagar errores del cliente de Anthropic (p. ej. de `messages.create`).

### _explain

```python
def _explain(client, system, messages, assistant_content, tool_use, summary)
```

Función interna (privada por convención `_`). Realiza una segunda llamada a Claude, pasándole el `tool_result` con el resumen de datos, para obtener la explicación textual del gráfico. No forma parte de la superficie pública, pero se documenta por completitud.

| Parámetro | Tipo | Descripción |
|---|---|---|
| `client` | `anthropic.Anthropic` | Cliente SDK ya inicializado. |
| `system` | `str` | System prompt usado en toda la conversación. |
| `messages` | `list[dict]` | Historial de mensajes acumulado hasta el momento. |
| `assistant_content` | `list` | Contenido de la respuesta del asistente que contenía el `tool_use`. |
| `tool_use` | `object` | Bloque `tool_use` elegido por Claude (aporta `id` y `name`). |
| `summary` | `str` | Resumen textual de los datos del gráfico generado. |

**Valor de retorno:** `str` — texto explicativo del gráfico (2–4 frases).

**Errores relevantes:**
- `RuntimeError` — si Claude no devuelve texto en la explicación.

## app

Entrypoint de la interfaz web (Streamlit). Carga el dataset (cacheado), muestra el chat con historial de sesión, valida la entrada del usuario, invoca `agent.answer` y renderiza el gráfico + explicación. No expone funciones públicas reutilizables: es un script ejecutado por Streamlit (`streamlit run app.py`).

### _load

```python
@st.cache_data
def _load()
```

Función interna cacheada por Streamlit. Carga el CSV configurado y calcula su resumen de esquema una sola vez por sesión.

| Parámetro | Tipo | Descripción |
|---|---|---|
| — | — | No recibe parámetros; usa `config.CSV_PATH`. |

**Valor de retorno:** `tuple[pandas.DataFrame, str]` — el dataset cargado y su `schema_summary`.

**Errores relevantes:**
- `FileNotFoundError` — capturado en el cuerpo del script para mostrar un error amigable y detener la app (`st.stop`).
- Otras excepciones de carga — capturadas genéricamente, se registra el traceback en `stderr` y se detiene la app.

**Flujo del script (nivel de módulo):**
- Configura la página y el título; carga `df, schema` vía `_load()` con manejo de errores.
- Muestra un caption con nombre del dataset, filas y columnas.
- Mantiene `st.session_state.history` (lista de `{query, img_bytes, text}`) y la re-renderiza en cada rerun.
- Valida la consulta contra `MAX_QUERY_LEN = 2000` y rechaza vacías.
- Invoca `answer(query, df, schema)` dentro de un spinner; captura `ChartError`, `RuntimeError` y `Exception` mostrando mensajes específicos y registrando el traceback en `stderr`.
- En éxito: crea `OUTPUT_DIR`, guarda `ultimo_grafico.png`, renderiza la imagen en el chat, agrega al historial y cierra la figura con `plt.close` en `finally`.

## Ver también
- [Flujo end-to-end del chatbot](flujo_producto.md): narrativa paso a paso y diagrama
  Mermaid del flujo completo, desde la entrada del usuario hasta la respuesta en pantalla.
