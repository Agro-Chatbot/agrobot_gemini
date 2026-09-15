import pandas as pd

from .aggregate import (
    AGGS,
    _aggregate,
    _aggregate_group_by,
    _apply_top_n,
    _format_summary,
    _format_summary_group_by,
    _require_numeric,
)
from .errors import ChartError
from .filters import (
    _FILTER_PROPERTIES,
    _apply_filter_entry,
    _apply_filters,
    _normalize_filter_entries,
    _require_column,
)
from .style import CHART_PALETTE, TITLE_FONTSIZE, TITLE_FONTWEIGHT, _new_figure, _titulo


def _universo_categorias(df, col, filter_col, filter_val, filters):
    """Universo de valores de `col` a considerar para el summary de `agg='mean'`.

    Aplica todos los filtros categóricos (`filter_col`/`filter_val`/`filters`), incluidos
    los que targetean a `col` mismo (ej. comparar explícitamente Lote 1 vs Lote 2): así el
    universo respeta un filtro/comparación explícito del usuario sobre la misma columna
    usada como `x`/`category` en vez de reintroducir categorías que el usuario excluyó a
    propósito (TECH-153). Deliberadamente NO aplica `date_from`/`date_to`: así una
    categoría que el rango de fechas deja sin filas sigue apareciendo en el summary con
    `n=0` en vez de desaparecer sin aviso.

    Si `col` es la columna de fecha misma ("Fecha"), no se calcula universo: agrupar por
    fecha cruda no es categórico, y aplicar este backfill bypasearía el propio filtro de
    fecha para su columna (TECH-153).

    Si algún filtro categórico es inválido, devuelve `None` y deja que `_apply_filters`
    levante el `ChartError` correspondiente más adelante en el flujo normal.

    Limitación conocida: si `col` está correlacionada con la fecha pero no es la columna
    de fecha misma (ej. `col='Anio'` junto con `date_from`/`date_to`), esto puede listar
    con `n=0` categorías fuera del rango pedido a propósito, no solo las que faltan dentro
    del período. No hay, en este dataset, una fuente de verdad estable para distinguir
    ambos casos sin asumir un dominio propio por columna (ver ticket).
    """
    if col == "Fecha":
        return None
    try:
        entries = _normalize_filter_entries(filter_col, filter_val, filters)
    except ChartError:
        return None
    universo_df = df
    try:
        for entry in entries:
            universo_df = _apply_filter_entry(universo_df, entry)
    except ChartError:
        return None
    if col not in universo_df.columns:
        return None
    return universo_df[col].dropna().unique().tolist()


def _grouped_values_and_summary(grouped):
    """A partir de lo que devuelve `_aggregate`: una Series (agg count/sum) o un frame
    valor/n/n_no_nulo (agg mean) — separa los valores a graficar del texto de summary."""
    if isinstance(grouped, pd.DataFrame):
        return grouped["valor"], _format_summary(grouped)
    return grouped, grouped.to_string()


def _add_reference_line(ax, valores, reference_line):
    """Dibuja una línea de referencia horizontal sobre `ax` y devuelve el texto de summary
    correspondiente, o `""` si `reference_line` es `None` (TECH-119). Por ahora solo soporta
    `reference_line='mean'`: promedio del subconjunto ya graficado (post top_n si aplica)."""
    if reference_line is None:
        return ""
    if reference_line != "mean":
        raise ChartError(f"reference_line '{reference_line}' inválido. Use 'mean'.")
    valores_validos = valores.dropna()
    if valores_validos.empty:
        raise ChartError("No hay valores numéricos para calcular reference_line='mean'.")
    promedio = valores_validos.mean()
    ax.axhline(promedio, color=CHART_PALETTE[1], linestyle="--", linewidth=1.5, label=f"Promedio: {promedio:.4g}")
    ax.legend()
    por_encima = valores_validos[valores_validos > promedio].index.tolist()
    por_debajo = valores_validos[valores_validos < promedio].index.tolist()
    return (
        f"\n\nLínea de referencia (promedio): {promedio:.4g}\n"
        f"Por encima del promedio: {', '.join(str(v) for v in por_encima) if por_encima else '(ninguna)'}\n"
        f"Por debajo del promedio: {', '.join(str(v) for v in por_debajo) if por_debajo else '(ninguna)'}"
    )


def _validar_group_by(x, group_by, top_n, reference_line=None):
    """Validaciones compartidas por `bar_chart`/`line_chart` cuando se pasa `group_by`
    (TECH-122/ADR-036): no puede coincidir con `x`, y no se combina con `top_n`/
    `reference_line` (operan sobre una única serie, no sobre N series agrupadas)."""
    if group_by == x:
        raise ChartError(
            "El parámetro 'group_by' no puede ser igual a 'x'. Elegí una columna distinta "
            "para comparar series (ej. x='Estacion', group_by='Anio')."
        )
    if top_n is not None:
        raise ChartError(
            "El parámetro 'top_n' no es compatible con 'group_by' (agrupación en N series). "
            "Usá uno u otro."
        )
    if reference_line is not None:
        raise ChartError(
            "El parámetro 'reference_line' no es compatible con 'group_by' (agrupación en "
            "N series). Usá uno u otro."
        )


def bar_chart(df, x, y=None, agg="sum", filter_col=None, filter_val=None, date_from=None, date_to=None, filters=None, top_n=None, order="desc", reference_line=None, group_by=None):
    if group_by is not None:
        _validar_group_by(x, group_by, top_n, reference_line)
        df = _apply_filters(df, filter_col, filter_val, date_from, date_to, filters)
        _require_column(df, x)
        _require_column(df, group_by)
        pivot, summary_frame = _aggregate_group_by(df, x, y, group_by, agg)
        summary = _format_summary_group_by(summary_frame, x, group_by)
        fig, ax = _new_figure((8, 5))
        pivot.plot.bar(ax=ax, color=CHART_PALETTE)
        ax.set_xlabel(x)
        ax.set_ylabel(f"{agg}({y})" if agg != "count" else "cantidad")
        ax.set_title(_titulo(agg, y, x), fontsize=TITLE_FONTSIZE, fontweight=TITLE_FONTWEIGHT)
        ax.legend(title=group_by)
        fig.tight_layout()
        return fig, summary

    universo = _universo_categorias(df, x, filter_col, filter_val, filters) if agg == "mean" else None
    df = _apply_filters(df, filter_col, filter_val, date_from, date_to, filters)
    _require_column(df, x)
    grouped = _aggregate(df, x, y, agg, universe=universo)
    grouped = _apply_top_n(grouped, top_n, order)
    valores, summary = _grouped_values_and_summary(grouped)
    fig, ax = _new_figure((8, 5))
    valores.plot.bar(ax=ax, color=CHART_PALETTE)
    ax.set_xlabel(x)
    ax.set_ylabel(f"{agg}({y})" if agg != "count" else "cantidad")
    ax.set_title(_titulo(agg, y, x), fontsize=TITLE_FONTSIZE, fontweight=TITLE_FONTWEIGHT)
    summary += _add_reference_line(ax, valores, reference_line)
    fig.tight_layout()
    return fig, summary


def line_chart(df, x, y=None, agg="sum", filter_col=None, filter_val=None, date_from=None, date_to=None, filters=None, top_n=None, order="desc", group_by=None):
    if group_by is not None:
        _validar_group_by(x, group_by, top_n)
        df = _apply_filters(df, filter_col, filter_val, date_from, date_to, filters)
        _require_column(df, x)
        _require_column(df, group_by)
        pivot, summary_frame = _aggregate_group_by(df, x, y, group_by, agg)
        pivot = pivot.sort_index()
        summary = _format_summary_group_by(summary_frame, x, group_by)
        fig, ax = _new_figure((8, 5))
        pivot.plot.line(ax=ax, marker="o", color=CHART_PALETTE)
        ax.set_xlabel(x)
        ax.set_ylabel(f"{agg}({y})" if agg != "count" else "cantidad")
        ax.set_title(_titulo(agg, y, x), fontsize=TITLE_FONTSIZE, fontweight=TITLE_FONTWEIGHT)
        ax.legend(title=group_by)
        fig.tight_layout()
        return fig, summary

    universo = _universo_categorias(df, x, filter_col, filter_val, filters) if agg == "mean" else None
    df = _apply_filters(df, filter_col, filter_val, date_from, date_to, filters)
    _require_column(df, x)
    grouped = _aggregate(df, x, y, agg, universe=universo)
    grouped = _apply_top_n(grouped, top_n, order).sort_index()
    valores, summary = _grouped_values_and_summary(grouped)
    fig, ax = _new_figure((8, 5))
    valores.plot.line(ax=ax, marker="o", color=CHART_PALETTE[0])
    ax.set_xlabel(x)
    ax.set_ylabel(f"{agg}({y})" if agg != "count" else "cantidad")
    ax.set_title(_titulo(agg, y, x), fontsize=TITLE_FONTSIZE, fontweight=TITLE_FONTWEIGHT)
    fig.tight_layout()
    return fig, summary


def scatter_plot(df, x, y, filter_col=None, filter_val=None, date_from=None, date_to=None, filters=None):
    df = _apply_filters(df, filter_col, filter_val, date_from, date_to, filters)
    _require_numeric(df, x)
    _require_numeric(df, y)
    fig, ax = _new_figure((8, 5))
    ax.scatter(df[x], df[y], alpha=0.6)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(f"{y} vs {x}", fontsize=TITLE_FONTSIZE, fontweight=TITLE_FONTWEIGHT)
    fig.tight_layout()
    corr = df[[x, y]].corr().iloc[0, 1]
    corr_str = f"{corr:.3f}" if pd.notna(corr) else "N/A (varianza cero)"
    return fig, f"n={len(df)}, correlación({x}, {y})={corr_str}"


def histogram(df, column, bins=20, filter_col=None, filter_val=None, date_from=None, date_to=None, filters=None):
    df = _apply_filters(df, filter_col, filter_val, date_from, date_to, filters)
    _require_numeric(df, column)
    fig, ax = _new_figure((8, 5))
    ax.hist(df[column].dropna(), bins=int(bins))
    ax.set_xlabel(column)
    ax.set_ylabel("frecuencia")
    ax.set_title(f"Distribución de {column}", fontsize=TITLE_FONTSIZE, fontweight=TITLE_FONTWEIGHT)
    fig.tight_layout()
    return fig, df[column].describe().to_string()


def pie_chart(df, category, value=None, agg="sum", filter_col=None, filter_val=None, date_from=None, date_to=None, filters=None, top_n=None, order="desc"):
    universo = (
        _universo_categorias(df, category, filter_col, filter_val, filters)
        if agg == "mean" else None
    )
    df = _apply_filters(df, filter_col, filter_val, date_from, date_to, filters)
    _require_column(df, category)
    grouped = _aggregate(df, category, value, agg, universe=universo)
    grouped = _apply_top_n(grouped, top_n, order)
    valores, summary = _grouped_values_and_summary(grouped)
    # Las categorías con n=0 (agg='mean') no tienen valor numérico para dibujar una
    # porción: se listan en el summary pero se excluyen del gráfico.
    valores_grafico = valores.dropna()
    if (valores_grafico < 0).any():
        raise ChartError(
            "El gráfico de torta requiere valores no negativos. "
            "La agregación actual produce valores negativos."
        )
    fig, ax = _new_figure((7, 7))
    valores_grafico.plot.pie(ax=ax, autopct="%1.1f%%", colors=CHART_PALETTE)
    ax.set_ylabel("")
    ax.set_title(
        _titulo(agg, value, category), fontsize=TITLE_FONTSIZE, fontweight=TITLE_FONTWEIGHT
    )
    fig.tight_layout()
    return fig, summary


# --- Definiciones de tools para el SDK de Anthropic ---

# Parámetros de ranking top/bottom-N (TECH-119), compartidos por bar_chart/line_chart/pie_chart.
_TOP_N_PROPERTIES = {
    "top_n": {
        "type": "integer",
        "description": (
            "Si se especifica, recorta el resultado agregado a las N categorías de mayor o "
            "menor valor (ver 'order'), ya ordenadas. Sin este parámetro se muestran todas "
            "las categorías (comportamiento por defecto). Usar para preguntas de ranking "
            "(ej: 'los 3 lotes con menor tasa de crecimiento' -> top_n=3, order='asc')."
        ),
    },
    "order": {
        "type": "string",
        "enum": ["asc", "desc"],
        "description": (
            "Orden para 'top_n': 'desc' (mayor a menor, default) para las N categorías de "
            "mayor valor, 'asc' (menor a mayor) para las N de menor valor. Sin efecto si no "
            "se especifica top_n."
        ),
    },
}

# Comparación de dos o más series en una sola tool call (TECH-122/ADR-036), compartido por
# bar_chart/line_chart.
_GROUP_BY_PROPERTY = {
    "group_by": {
        "type": "string",
        "description": (
            "Columna categórica adicional para comparar dos o más series en el mismo "
            "gráfico (ej: comparar campañas, lotes o recursos entre sí). Agrupa por "
            "[x, group_by]: bar_chart dibuja barras agrupadas y line_chart dibuja una línea "
            "por cada valor de group_by. También sirve para comparación estacional: "
            "x='Estacion', group_by='Anio' responde 'este verano vs. el verano del año "
            "pasado'. El summary lista, por serie, cada categoría de x con su valor y su "
            "'n' (TECH-153). No combinable con 'top_n'/'order'/'reference_line' (usar uno u "
            "otro). No soporta comparar dos ventanas de fecha arbitrarias y discontinuas "
            "(ej. dos rangos de fechas puntuales que no correspondan a valores de una misma "
            "columna categórica como Anio/Estacion): ese caso no está soportado, hay que "
            "declararlo como límite en la explicación en vez de inventar un resultado."
        ),
    },
}

BAR_CHART_SCHEMA = {
    "name": "bar_chart",
    "description": "Gráfico de barras: agrega una columna numérica por una categórica.",
    "input_schema": {
        "type": "object",
        "properties": {
            "x": {"type": "string", "description": "Columna para el eje X (categoría o etiqueta)."},
            "y": {"type": "string", "description": "Columna numérica para el eje Y. Omitir si agg='count'."},
            "agg": {"type": "string", "enum": list(AGGS), "description": "Cómo agregar la Y por cada X."},
            "reference_line": {
                "type": "string",
                "enum": ["mean"],
                "description": (
                    "Dibuja una línea horizontal de referencia sobre el gráfico. 'mean': "
                    "promedio del subconjunto graficado (ya filtrado, y recortado por top_n "
                    "si se usó). El valor de la referencia y qué categorías quedan por "
                    "encima/por debajo se incluyen en el summary de texto. No combinable con "
                    "'group_by'."
                ),
            },
            **_TOP_N_PROPERTIES,
            **_GROUP_BY_PROPERTY,
            **_FILTER_PROPERTIES,
        },
        "required": ["x", "agg"],
    },
}

LINE_CHART_SCHEMA = {
    "name": "line_chart",
    "description": "Gráfico de líneas: tendencia de una columna agregada por otra (ej. por fecha).",
    "input_schema": {
        "type": "object",
        "properties": {
            "x": {"type": "string", "description": "Columna para el eje X (categoría o etiqueta)."},
            "y": {"type": "string", "description": "Columna numérica para el eje Y. Omitir si agg='count'."},
            "agg": {"type": "string", "enum": list(AGGS), "description": "Cómo agregar la Y por cada X."},
            **_TOP_N_PROPERTIES,
            **_GROUP_BY_PROPERTY,
            **_FILTER_PROPERTIES,
        },
        "required": ["x", "agg"],
    },
}

SCATTER_PLOT_SCHEMA = {
    "name": "scatter_plot",
    "description": "Dispersión entre dos columnas numéricas para ver su relación.",
    "input_schema": {
        "type": "object",
        "properties": {
            "x": {"type": "string", "description": "Columna numérica eje X."},
            "y": {"type": "string", "description": "Columna numérica eje Y."},
            **_FILTER_PROPERTIES,
        },
        "required": ["x", "y"],
    },
}

HISTOGRAM_SCHEMA = {
    "name": "histogram",
    "description": "Histograma de la distribución de una columna numérica.",
    "input_schema": {
        "type": "object",
        "properties": {
            "column": {"type": "string", "description": "Columna numérica a distribuir."},
            "bins": {"type": "integer", "description": "Cantidad de bins (default 20)."},
            **_FILTER_PROPERTIES,
        },
        "required": ["column"],
    },
}

PIE_CHART_SCHEMA = {
    "name": "pie_chart",
    "description": "Gráfico de torta: proporción de una columna agregada por categoría.",
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {"type": "string", "description": "Columna categórica."},
            "value": {"type": "string", "description": "Columna numérica a agregar. Omitir si agg='count'."},
            "agg": {"type": "string", "enum": list(AGGS)},
            **_TOP_N_PROPERTIES,
            **_FILTER_PROPERTIES,
        },
        "required": ["category", "agg"],
    },
}
