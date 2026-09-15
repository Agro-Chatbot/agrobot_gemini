"""Tools de graficado predefinidas.

Cada función recibe el DataFrame + params validados y devuelve
(figura_matplotlib, resumen_datos_texto). Si un parámetro es inválido se
levanta ChartError con un mensaje legible que Claude puede usar para corregir.
"""

from .aggregate import AGGS, _aggregate, _require_numeric
from .basic import bar_chart, histogram, line_chart, pie_chart, scatter_plot
from .errors import ChartError
from .filters import _apply_filters, _require_column
from .registry import TOOLS, run_tool, tool_schemas
from .soporte import soporte_animal
from .style import AGG_LABELS, CHART_PALETTE, TITLE_FONTSIZE, TITLE_FONTWEIGHT

__all__ = [
    "ChartError",
    "TOOLS",
    "tool_schemas",
    "run_tool",
    "bar_chart",
    "line_chart",
    "scatter_plot",
    "histogram",
    "pie_chart",
    "soporte_animal",
    "_apply_filters",
    "_aggregate",
    "_require_column",
    "_require_numeric",
    "CHART_PALETTE",
    "AGG_LABELS",
    "AGGS",
    "TITLE_FONTSIZE",
    "TITLE_FONTWEIGHT",
]
