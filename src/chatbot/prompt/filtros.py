"""Parámetros de filtrado disponibles en todas las tools de graficado."""

SECCION = (
    "## Parámetros de filtrado disponibles en todas las tools\n\n"
    "Todas las tools de graficado aceptan cuatro parámetros opcionales de filtrado:\n\n"
    "- **filter_col** (str): Columna categórica por la que filtrar. Columnas filtrables del dataset: Campo, Lote, Recurso, Anio, Estacion (y otras categóricas).\n"
    "- **filter_val** (str): Valor exacto a conservar. Requerido si se especifica filter_col. Ejemplo: \"Campo natural\", \"2023\".\n"
    "- **date_from** (str): Fecha de inicio del rango en formato ISO 8601 (ej: \"2022-01-01\"). Filtra por la columna Fecha.\n"
    "- **date_to** (str): Fecha de fin del rango en formato ISO 8601 (ej: \"2023-12-31\"). Filtra por la columna Fecha.\n\n"
    "Ejemplo de uso: para \"¿tasa de crecimiento del campo natural entre 2022 y 2023?\" usar "
    "bar_chart con filter_col=\"Recurso\", filter_val=\"Campo natural\", date_from=\"2022-01-01\", date_to=\"2023-12-31\".\n\n"
    "**Regla de comparación multivalor:** cuando la consulta compare dos o más valores de una "
    "misma columna (ej: \"comparar Lote 1 vs Lote 2\", \"Recurso A contra Recurso B\"), usá esa "
    "columna como `x` (o como agrupador) y `filters` con **todos** los valores comparados en la "
    "misma entrada `vals`. Nunca filtres por uno solo de los valores comparados: eso deja al "
    "otro lado de la comparación afuera del gráfico sin que se note."
)
