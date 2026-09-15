import pandas as pd

from .errors import ChartError

_MAX_VALORES_SUGERIDOS = 30


def _require_column(df, column):
    if column not in df.columns:
        raise ChartError(
            f"La columna '{column}' no existe. Columnas disponibles: "
            f"{', '.join(df.columns)}."
        )


def _valores_sugeridos(available):
    if len(available) > _MAX_VALORES_SUGERIDOS:
        mostrados = available[:_MAX_VALORES_SUGERIDOS]
        resto = len(available) - _MAX_VALORES_SUGERIDOS
        return f"{mostrados}, y {resto} más"
    return f"{available}"


def _normalize_filter_entries(filter_col, filter_val, filters):
    """Normaliza filter_col/filter_val (legacy) y filters (ADR-034) a una lista de
    entradas {col, vals}, aplicadas en AND en el orden: legacy primero, luego filters."""
    entries = []
    if filter_col is not None:
        if filter_val is None:
            raise ChartError("filter_val es requerido cuando se especifica filter_col.")
        entries.append({"col": filter_col, "vals": filter_val})

    if filters is not None:
        if not isinstance(filters, list):
            raise ChartError("filters debe ser una lista de objetos {col, vals}.")
        for entry in filters:
            if not isinstance(entry, dict) or "col" not in entry or "vals" not in entry:
                raise ChartError(
                    "Cada entrada de filters debe ser un objeto con 'col' y 'vals'."
                )
            entries.append(entry)

    return entries


def _apply_filter_entry(df, entry):
    col = entry["col"]
    vals = entry["vals"]
    _require_column(df, col)

    if isinstance(vals, str):
        vals_list = [vals]
    elif isinstance(vals, list):
        vals_list = vals
    else:
        raise ChartError(
            f"El valor de 'vals' para la columna '{col}' debe ser un string o una lista de strings."
        )
    if not vals_list:
        raise ChartError(f"La lista de 'vals' para la columna '{col}' no puede estar vacía.")

    available = sorted(df[col].dropna().unique().tolist())
    missing = [v for v in vals_list if v not in df[col].values]
    if missing:
        faltantes_str = ", ".join(f"'{v}'" for v in missing)
        raise ChartError(
            f"El/los valor(es) {faltantes_str} no existe(n) en la columna '{col}'. "
            f"Valores disponibles: {_valores_sugeridos(available)}"
        )

    return df[df[col].isin(vals_list)]


def _apply_filters(df, filter_col=None, filter_val=None, date_from=None, date_to=None, filters=None):
    for entry in _normalize_filter_entries(filter_col, filter_val, filters):
        df = _apply_filter_entry(df, entry)

    if date_from is not None or date_to is not None:
        _require_column(df, "Fecha")
        df = df.copy()
        try:
            df["Fecha"] = pd.to_datetime(df["Fecha"])
        except (ValueError, TypeError) as e:
            raise ChartError(f"La columna 'Fecha' no pudo convertirse a fecha: {e}") from e
        if date_from is not None:
            try:
                df = df[df["Fecha"] >= pd.Timestamp(date_from)]
            except (ValueError, TypeError):
                raise ChartError(
                    f"Formato de fecha inválido en date_from: '{date_from}'. "
                    "Usá formato ISO 8601 (ej: '2022-01-01')."
                )
        if date_to is not None:
            try:
                df = df[df["Fecha"] <= pd.Timestamp(date_to)]
            except (ValueError, TypeError):
                raise ChartError(
                    f"Formato de fecha inválido en date_to: '{date_to}'. "
                    "Usá formato ISO 8601 (ej: '2023-12-31')."
                )

    if len(df) == 0:
        raise ChartError(
            "El filtro aplicado no devuelve datos. "
            "Verificá los valores de filter_col/filter_val/filters o el rango de fechas."
        )

    return df


_FILTER_PROPERTIES = {
    "filter_col": {
        "type": "string",
        "description": (
            "Columna por la que filtrar categorías (ej: 'Recurso', 'Lote', 'Campo', 'Anio', 'Estacion'). "
            "Requiere filter_val. Para filtrar por dos o más columnas a la vez (ej: Campo y Lote), "
            "o por varios valores de una misma columna, usar 'filters' en su lugar."
        ),
    },
    "filter_val": {
        "type": "string",
        "description": "Valor exacto a conservar en filter_col (ej: 'Campo natural', 'Lote 1', '2023').",
    },
    "filters": {
        "type": "array",
        "description": (
            "Filtro compuesto: lista de entradas {col, vals} combinadas con AND entre entradas "
            "y con OR (isin) entre los valores de una misma entrada. Usar cuando la consulta "
            "requiere dos o más columnas simultáneas (ej: Campo + Lote, porque el mismo nombre de "
            "Lote puede repetirse en distintos Campos y filtrar solo por Lote mezclaría datos de "
            "otro campo) o varios valores de una columna (ej: dos lotes a la vez)."
        ),
        "items": {
            "type": "object",
            "properties": {
                "col": {
                    "type": "string",
                    "description": "Columna a filtrar (ej: 'Campo', 'Lote', 'Recurso', 'Estacion').",
                },
                "vals": {
                    "description": "Valor único (string) o lista de valores (OR) a conservar en esta columna.",
                    "oneOf": [
                        {"type": "string"},
                        {"type": "array", "items": {"type": "string"}},
                    ],
                },
            },
            "required": ["col", "vals"],
        },
    },
    "date_from": {
        "type": "string",
        "description": "Fecha de inicio del rango (ISO 8601, ej: '2022-01-01'). Filtra por la columna 'Fecha'.",
    },
    "date_to": {
        "type": "string",
        "description": "Fecha de fin del rango (ISO 8601, ej: '2023-12-31'). Filtra por la columna 'Fecha'.",
    },
}
