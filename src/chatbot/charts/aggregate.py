import pandas as pd

from ..data import is_numeric
from .errors import ChartError
from .filters import _require_column

AGGS = {"sum": "sum", "mean": "mean", "count": "count"}


def _require_numeric(df, column):
    _require_column(df, column)
    if not is_numeric(df, column):
        raise ChartError(f"La columna '{column}' no es numérica.")


def _aggregate_mean_frame(df, x, y, universe=None):
    """Agregación `agg='mean'` que devuelve un frame con `valor` (promedio por grupo),
    `n` (filas del grupo, incluyendo nulos) y `n_no_nulo` (valores no nulos de `y`).

    `universe`, si se pasa, es una lista de valores de `x` que deben aparecer en el
    resultado aunque no tengan ninguna fila en `df` (el subconjunto ya filtrado): se
    agregan con `valor=NaN`, `n=0`, `n_no_nulo=0` en vez de desaparecer del summary
    (TECH-153; caso: una categoría sin mediciones en el período filtrado).
    """
    grouped = df.groupby(x)[y]
    frame = pd.DataFrame(
        {"valor": grouped.mean(), "n": grouped.size(), "n_no_nulo": grouped.count()}
    )
    if universe:
        faltantes = [v for v in universe if v not in frame.index]
        if faltantes:
            extra = pd.DataFrame(
                {"valor": float("nan"), "n": 0, "n_no_nulo": 0},
                index=pd.Index(faltantes, name=frame.index.name),
            )
            frame = pd.concat([frame, extra])
    return frame.sort_index()


def _format_summary(frame):
    """String de summary a partir de un frame indexado por categoría con columnas
    `valor`/`n`/`n_no_nulo` (el formato que produce `_aggregate_mean_frame`). Reutilizable
    por otros callers de agg='mean' (diseño pensado para TECH-119/TECH-122)."""
    lineas = []
    for idx, row in frame.iterrows():
        valor = row["valor"]
        valor_str = "sin datos" if pd.isna(valor) else f"{valor:.4g}"
        lineas.append(
            f"{idx}    {valor_str}  (n={int(row['n'])}, n_no_nulo={int(row['n_no_nulo'])})"
        )
    return "\n".join(lineas)


def _aggregate(df, x, y, agg, universe=None):
    if agg not in AGGS:
        raise ChartError(f"Agregación '{agg}' inválida. Use: {', '.join(AGGS)}.")
    if agg != "count" and y is None:
        raise ChartError(
            f"Falta el parámetro 'y': para la agregación '{agg}' es necesario indicar "
            "una columna numérica. Especificá 'y' con una columna numérica, o usá agg='count' "
            "para contar registros sin necesitar columna numérica."
        )
    if agg == "count":
        return df.groupby(x).size()
    _require_numeric(df, y)
    if agg == "mean":
        return _aggregate_mean_frame(df, x, y, universe=universe)
    return getattr(df.groupby(x)[y], agg)()


def _aggregate_group_by(df, x, y, group_by, agg):
    """Agregación con dos categóricas (`x`, `group_by`) para comparar N series en una sola
    tool call (TECH-122 / ADR-036): `df.groupby([x, group_by])[y].agg(agg)` + `unstack()`.

    Devuelve `(pivot, summary_frame)`:
    - `pivot`: frame indexado por `x`, con una columna por valor de `group_by` y la
      agregación como valores — listo para graficar barras agrupadas o múltiples líneas.
    - `summary_frame`: frame largo con **una fila por cada combinación del producto
      cartesiano** de los valores de `x` y `group_by` observados en `df` (no solo las
      combinaciones que efectivamente tienen datos), con columnas `valor`, `n` (filas del
      grupo) y `n_no_nulo` (valores no nulos de `y`), siguiendo el mismo respaldo muestral
      que `_aggregate_mean_frame` (TECH-153), pero para cualquier `agg` (no solo 'mean'):
      con dos o más series en juego, el `n` por serie es igual de relevante para
      'sum'/'count'. Una combinación `x`/`group_by` sin ninguna fila en `df` (ej. una
      categoría de `x` presente en una serie de `group_by` pero ausente en otra) se
      completa con `valor=NaN`, `n=0`, `n_no_nulo=0` en vez de desaparecer en silencio del
      summary (TECH-122, hallazgo P1 del reviewer): `x`/`group_by` solo tienen datos
      efectivos para las combinaciones que aparecen en `df`, pero el `groupby([x,
      group_by])` de pandas solo produce filas para esas combinaciones — el hueco es
      visible en `pivot` (vía `unstack`) pero no en el texto sin este backfill.
    """
    if agg not in AGGS:
        raise ChartError(f"Agregación '{agg}' inválida. Use: {', '.join(AGGS)}.")
    if agg != "count" and y is None:
        raise ChartError(
            f"Falta el parámetro 'y': para la agregación '{agg}' es necesario indicar "
            "una columna numérica. Especificá 'y' con una columna numérica, o usá agg='count' "
            "para contar registros sin necesitar columna numérica."
        )
    if agg == "count":
        sizes = df.groupby([x, group_by]).size()
        valor, n, n_no_nulo = sizes, sizes, sizes
    else:
        _require_numeric(df, y)
        grouped = df.groupby([x, group_by])[y]
        valor = getattr(grouped, agg)()
        n = grouped.size()
        n_no_nulo = grouped.count()
    pivot = valor.unstack(group_by)
    # Producto cartesiano de los valores de x y group_by observados (unión, no intersección):
    # `pivot.index`/`pivot.columns` ya son esos valores únicos ordenados (resultado de
    # unstack). Reindexar contra ese producto completo backfillea las combinaciones sin
    # datos en vez de que `summary_frame` las omita.
    full_index = pd.MultiIndex.from_product([pivot.index, pivot.columns], names=[x, group_by])
    valor = valor.reindex(full_index)
    n = n.reindex(full_index, fill_value=0)
    n_no_nulo = n_no_nulo.reindex(full_index, fill_value=0)
    summary_frame = pd.DataFrame({"valor": valor, "n": n, "n_no_nulo": n_no_nulo}).reset_index()
    return pivot, summary_frame


def _format_summary_group_by(summary_frame, x, group_by):
    """String de summary para el caso `group_by` (TECH-122): una sección por serie
    (valor de `group_by`), listando cada categoría de `x` con su valor y su `n`/`n_no_nulo`,
    en el mismo formato de línea que `_format_summary`."""
    lineas = []
    for serie, grupo in summary_frame.groupby(group_by):
        lineas.append(f"-- {group_by}={serie} --")
        for _, row in grupo.iterrows():
            valor = row["valor"]
            valor_str = "sin datos" if pd.isna(valor) else f"{valor:.4g}"
            lineas.append(
                f"{row[x]}    {valor_str}  (n={int(row['n'])}, n_no_nulo={int(row['n_no_nulo'])})"
            )
    return "\n".join(lineas)


def _apply_top_n(grouped, top_n=None, order="desc"):
    """Recorta el resultado de `_aggregate` (Series para agg count/sum, o frame
    valor/n/n_no_nulo para agg='mean') a las `top_n` categorías de mayor (`order='desc'`,
    default) o menor (`order='asc'`) valor, aplicado después de `_aggregate` y antes de
    graficar (TECH-119). Sin `top_n`, devuelve `grouped` sin modificar (retrocompatible).
    Un `top_n` mayor a la cantidad de categorías disponibles devuelve todas, sin error.
    """
    if top_n is None:
        return grouped
    if isinstance(top_n, bool) or not isinstance(top_n, int) or top_n < 1:
        raise ChartError("El parámetro 'top_n' debe ser un entero mayor o igual a 1.")
    if order not in ("asc", "desc"):
        raise ChartError(f"El parámetro 'order' debe ser 'asc' o 'desc' (recibido: '{order}').")
    valores = grouped["valor"] if isinstance(grouped, pd.DataFrame) else grouped
    ordenado = valores.sort_values(ascending=(order == "asc"), na_position="last")
    return grouped.loc[ordenado.head(top_n).index]
