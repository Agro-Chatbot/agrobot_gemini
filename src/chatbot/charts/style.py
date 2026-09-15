import matplotlib

matplotlib.use("Agg")  # backend sin display, para servidor / tests
import matplotlib.pyplot as plt

# Etiquetas legibles en español para cada clave de AGGS, usadas en los títulos
# de los gráficos (el `summary` que vuelve al agente conversacional no usa
# este mapeo y no cambia).
AGG_LABELS = {"sum": "Suma", "mean": "Promedio", "count": "Cantidad"}

TITLE_FONTSIZE = 14
TITLE_FONTWEIGHT = "bold"


def _titulo(agg, y, x):
    """Título legible para gráficos agregados: 'Suma de X por Y' en vez de 'sum de X por Y'."""
    label = AGG_LABELS.get(agg, agg.capitalize())
    variable = y or "registros"
    return f"{label} de {variable} por {x}"


# Paleta de gráficos accesible (ADR-022; tokens del estilo "minimalista" tomados
# tal cual del Anexo de docs/diseno/consolidado.md). Reemplaza el ciclo `tab10`
# default de matplotlib, que incluye 4 colores por debajo de 3:1 contra fondo
# blanco (naranja, rosa, oliva, cian; ver docs/diseno/00-estado-actual.md).
# Ratios contra #FFFFFF (fórmula de luminancia relativa WCAG documentada en
# docs/diseno/00-estado-actual.md), todos >= 3:1:
#   --color-primary        #111111  18.88:1
#   --color-error          #b42318   6.57:1
#   --color-success        #1a7f37   5.08:1
#   --color-warning        #9a6700   4.87:1
#   --color-text-secondary #555555   7.46:1
#   --color-text-muted     #8a8a8a   3.45:1
CHART_PALETTE = ["#111111", "#b42318", "#1a7f37", "#9a6700", "#555555", "#8a8a8a"]


def _new_figure(figsize):
    """Crea (fig, ax) con fondo blanco explícito y el ciclo de color propio (CHART_PALETTE)."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_prop_cycle(color=CHART_PALETTE)
    return fig, ax
