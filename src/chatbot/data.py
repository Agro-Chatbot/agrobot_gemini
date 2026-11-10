import sys
from pathlib import Path

import pandas as pd
from pandas.api.types import is_numeric_dtype

from . import config

_MONTH_TO_ESTACION = {
    12: "Verano", 1: "Verano", 2: "Verano",
    3: "Otoño", 4: "Otoño", 5: "Otoño",
    6: "Invierno", 7: "Invierno", 8: "Invierno",
    9: "Primavera", 10: "Primavera", 11: "Primavera",
}

_MONTH_TO_NOMBRE = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

# Umbral de cardinalidad: por debajo (o igual), schema_summary lista todos los
# valores distintos de una columna categórica; por encima, solo una muestra.
CARDINALITY_THRESHOLD = 40


def enrich_temporal(df: pd.DataFrame) -> pd.DataFrame:
    if "Fecha" not in df.columns:
        return df
    df = df.copy()
    fecha = df["Fecha"]
    if not pd.api.types.is_datetime64_any_dtype(fecha):
        fecha = pd.to_datetime(fecha)
        df["Fecha"] = fecha
    df["Anio"] = fecha.dt.year.apply(lambda y: str(int(y)) if pd.notna(y) else pd.NA)
    df["Estacion"] = fecha.dt.month.map(_MONTH_TO_ESTACION)
    df["Mes"] = fecha.dt.month.map(_MONTH_TO_NOMBRE)
    return df


def load_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    return enrich_temporal(df)


def load_precipitaciones(path: str | Path) -> pd.DataFrame:
    # Header en latin-1 y filas en UTF-8: se lee como UTF-8 con reemplazo y se
    # descartan año/mes/dia por posición (el nombre de "año" sale roto).
    df = pd.read_csv(path, encoding="utf-8", encoding_errors="replace")
    df = df.rename(columns={"CAMPO": "Campo", "milimetros": "Precipitación mm"})
    df["Fecha"] = pd.to_datetime(df["fecha"].astype(str), format="%Y%m%d")
    df = df[["Fecha", "Campo", "Precipitación mm"]]
    return enrich_temporal(df)


def load_datasets(
    tasas_path: str | Path | None = None, precip_path: str | Path | None = None
) -> tuple[dict[str, pd.DataFrame], str]:
    tasas = load_csv(tasas_path or config.CSV_PATH)
    dfs = {"tasas": tasas}
    schema = "### Dataset `tasas`\n" + schema_summary(tasas)
    precip_path = Path(precip_path or config.PRECIP_CSV_PATH)
    if not precip_path.exists():
        print(
            f"Aviso: no se encontró el CSV de precipitaciones ({precip_path}); "
            "se usa solo el dataset de tasas.",
            file=sys.stderr,
        )
        return dfs, schema
    precip = load_precipitaciones(precip_path)
    dfs["precipitaciones"] = precip
    schema += "\n\n### Dataset `precipitaciones`\n" + schema_summary(precip)
    return dfs, schema


def is_numeric(df: pd.DataFrame, column: str) -> bool:
    return is_numeric_dtype(df[column])


def _temporal_desc(fecha: pd.Series) -> str:
    valid = fecha.dropna()
    if valid.empty:
        return "temporal (sin datos válidos)"
    min_iso = valid.min().date().isoformat()
    max_iso = valid.max().date().isoformat()
    return f"temporal (rango: {min_iso} → {max_iso}; {valid.nunique()} fechas distintas)"


def _coverage_line(fecha: pd.Series) -> str:
    """Marca las campañas (años calendario, HANK-ADR-006) con cobertura parcial en los
    bordes del rango de fechas (al menos la primera y la última)."""
    valid = fecha.dropna()
    if valid.empty:
        return ""
    min_ts, max_ts = valid.min(), valid.max()
    first_year, last_year = min_ts.year, max_ts.year
    start_partial = not (min_ts.month == 1 and min_ts.day == 1)
    end_partial = not (max_ts.month == 12 and max_ts.day == 31)

    notes = []
    if first_year == last_year:
        parts = []
        if start_partial:
            parts.append(f"desde {min_ts.date().isoformat()}")
        if end_partial:
            parts.append(f"hasta {max_ts.date().isoformat()}")
        if parts:
            notes.append(f"{first_year} parcial ({', '.join(parts)})")
    else:
        if start_partial:
            notes.append(f"{first_year} parcial (desde {min_ts.date().isoformat()})")
        if end_partial:
            notes.append(f"{last_year} parcial (hasta {max_ts.date().isoformat()})")

    if not notes:
        return "Cobertura: todas las campañas completas"
    return f"Cobertura: {', '.join(notes)}"


def _categorical_desc(series: pd.Series, top_n: int) -> str:
    counts = series.astype(str).value_counts()
    n = len(counts)
    if n <= CARDINALITY_THRESHOLD:
        valores = counts.index.tolist()
        return f"categórica (valores: {', '.join(valores)})"
    top = counts.head(top_n).index.tolist()
    return (
        f"categórica (valores frecuentes: {', '.join(top)}; "
        f"muestra no exhaustiva de {n} valores)"
    )


def schema_summary(df: pd.DataFrame, top_n: int = 5) -> str:
    """Resumen compacto del dataset para el system prompt de Claude."""
    lines = [f"Filas: {len(df)}", "Columnas:"]
    for col in df.columns:
        series = df[col]
        if pd.api.types.is_datetime64_any_dtype(series):
            lines.append(f"  - {col}: {_temporal_desc(series)}")
            coverage = _coverage_line(series)
            if coverage:
                lines.append(f"    {coverage}")
        elif is_numeric(df, col):
            if series.isna().all():
                desc = "numérica (sin datos válidos)"
            else:
                desc = (
                    f"numérica (min={series.min():.2f}, "
                    f"max={series.max():.2f}, media={series.mean():.2f})"
                )
            lines.append(f"  - {col}: {desc}")
        else:
            lines.append(f"  - {col}: {_categorical_desc(series, top_n)}")
    return "\n".join(lines)
