import copy

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


DATASETS = ("tasas", "precipitaciones")
DATASET_TOOLS = {"bar_chart", "line_chart", "scatter_plot", "histogram", "pie_chart"}
_DATASET_PROPERTY = {
    "type": "string",
    "enum": list(DATASETS),
    "description": (
        "Dataset sobre el que opera: 'tasas' (tasas de crecimiento, default) o "
        "'precipitaciones' (lluvia en mm por campo y péntada)."
    ),
}


def tool_schemas():
    schemas = copy.deepcopy([t["schema"] for t in TOOLS.values()])
    for s in schemas:
        if s["name"] in DATASET_TOOLS:
            s["input_schema"]["properties"]["dataset"] = dict(_DATASET_PROPERTY)
    return schemas


def run_tool(name, df, params):
    if name not in TOOLS:
        raise ChartError(f"Tool desconocida: {name}.")
    params = dict(params)
    dataset = params.pop("dataset", "tasas")
    if name not in DATASET_TOOLS and dataset != "tasas":
        raise ChartError(f"{name} solo opera sobre tasas.")
    if isinstance(df, dict):
        if dataset not in df:
            raise ChartError(
                f"Dataset '{dataset}' no disponible. Disponibles: {', '.join(df)}."
            )
        df = df[dataset]
    elif dataset != "tasas":
        raise ChartError(
            f"Dataset '{dataset}' no está cargado. Disponibles: tasas."
        )
    try:
        return TOOLS[name]["fn"](df, **params)
    except TypeError as e:
        raise ChartError(f"Parámetros inválidos para '{name}': {e}") from e
