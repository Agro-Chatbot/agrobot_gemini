from .basic import (
    BAR_CHART_SCHEMA,
    HISTOGRAM_SCHEMA,
    LINE_CHART_SCHEMA,
    PIE_CHART_SCHEMA,
    SCATTER_PLOT_SCHEMA,
    bar_chart,
    histogram,
    line_chart,
    pie_chart,
    scatter_plot,
)
from .errors import ChartError
from .soporte import SOPORTE_ANIMAL_SCHEMA, soporte_animal

TOOLS = {
    "bar_chart": {"fn": bar_chart, "schema": BAR_CHART_SCHEMA},
    "line_chart": {"fn": line_chart, "schema": LINE_CHART_SCHEMA},
    "scatter_plot": {"fn": scatter_plot, "schema": SCATTER_PLOT_SCHEMA},
    "histogram": {"fn": histogram, "schema": HISTOGRAM_SCHEMA},
    "pie_chart": {"fn": pie_chart, "schema": PIE_CHART_SCHEMA},
    "soporte_animal": {"fn": soporte_animal, "schema": SOPORTE_ANIMAL_SCHEMA},
}


def tool_schemas():
    return [t["schema"] for t in TOOLS.values()]


def run_tool(name, df, params):
    if name not in TOOLS:
        raise ChartError(f"Tool desconocida: {name}.")
    try:
        return TOOLS[name]["fn"](df, **params)
    except TypeError as e:
        raise ChartError(f"Parámetros inválidos para '{name}': {e}") from e
