import pandas as pd

from chatbot.data import enrich_temporal, is_numeric, schema_summary


def test_load_csv_equivalente(sample_df):
    assert len(sample_df) > 0
    assert "categoria" in sample_df.columns


def test_schema_summary_mentions_columns(sample_df):
    summary = schema_summary(sample_df)
    assert "categoria" in summary
    assert "ventas" in summary
    assert f"Filas: {len(sample_df)}" in summary


def test_is_numeric(sample_df):
    assert is_numeric(sample_df, "ventas")
    assert not is_numeric(sample_df, "categoria")


def test_enrich_temporal_estacion():
    fechas = pd.to_datetime([
        "2023-12-15", "2023-01-10", "2023-02-20",  # Verano
        "2023-03-01", "2023-04-15", "2023-05-30",  # Otoño
        "2023-06-10", "2023-07-20", "2023-08-05",  # Invierno
        "2023-09-01", "2023-10-15", "2023-11-25",  # Primavera
    ])
    df = pd.DataFrame({"Fecha": fechas})
    result = enrich_temporal(df)
    assert list(result["Estacion"][:3]) == ["Verano", "Verano", "Verano"]
    assert list(result["Estacion"][3:6]) == ["Otoño", "Otoño", "Otoño"]
    assert list(result["Estacion"][6:9]) == ["Invierno", "Invierno", "Invierno"]
    assert list(result["Estacion"][9:12]) == ["Primavera", "Primavera", "Primavera"]


def test_enrich_temporal_anio():
    df = pd.DataFrame({"Fecha": pd.to_datetime(["2021-03-15", "2022-07-01", "2023-06-15"])})
    result = enrich_temporal(df)
    assert list(result["Anio"]) == ["2021", "2022", "2023"]
    assert not pd.api.types.is_numeric_dtype(result["Anio"])


def test_enrich_temporal_fecha_como_string():
    df = pd.DataFrame({"Fecha": ["2023-06-15", "2023-12-01", "2023-09-20"]})
    assert not pd.api.types.is_datetime64_any_dtype(df["Fecha"])
    result = enrich_temporal(df)
    assert "Anio" in result.columns
    assert "Estacion" in result.columns
    assert list(result["Anio"]) == ["2023", "2023", "2023"]
    assert list(result["Estacion"]) == ["Invierno", "Verano", "Primavera"]


def test_enrich_temporal_con_nat():
    df = pd.DataFrame({"Fecha": [pd.Timestamp("2023-06-15"), pd.NaT, pd.Timestamp("2024-01-10")]})
    result = enrich_temporal(df)
    # Filas válidas deben tener el año sin decimales
    assert result["Anio"].iloc[0] == "2023"
    assert result["Anio"].iloc[2] == "2024"
    # Fila con NaT no debe producir los strings "NaT" ni "nan"
    nat_val = result["Anio"].iloc[1]
    assert nat_val != "NaT" and nat_val != "nan", f"Se esperaba un valor nulo, se obtuvo el string {nat_val!r}"


def test_enrich_temporal_mes_espanol():
    fechas = pd.to_datetime(["2023-01-15", "2023-06-01", "2023-12-25"])
    df = pd.DataFrame({"Fecha": fechas})
    result = enrich_temporal(df)
    assert list(result["Mes"]) == ["Enero", "Junio", "Diciembre"]


def test_enrich_temporal_mes_ausente_sin_fecha():
    df = pd.DataFrame({"valor": [1, 2, 3]})
    result = enrich_temporal(df)
    assert "Mes" not in result.columns


def test_schema_summary_rango_temporal():
    fechas = pd.to_datetime(["2021-06-15", "2022-12-01", "2023-03-10", "2023-09-20"])
    df = pd.DataFrame({"Fecha": fechas, "valor": [1.0, 2.0, 3.0, 4.0]})
    result = enrich_temporal(df)
    summary = schema_summary(result)

    assert "2021-06-15" in summary
    assert "2023-09-20" in summary
    assert "temporal" in summary
    assert "Cobertura" in summary
    # Ya no debe listarse la fecha como valores frecuentes de una categórica.
    assert "valores frecuentes: 2021-06-15" not in summary


def test_schema_summary_categorica_tres_valores_lista_completa():
    df = pd.DataFrame({"grupo": ["a", "b", "c", "a", "b"]})
    summary = schema_summary(df)
    assert "a" in summary and "b" in summary and "c" in summary
    assert "muestra no exhaustiva" not in summary


def test_schema_summary_categorica_cincuenta_valores_muestra():
    df = pd.DataFrame({"codigo": [f"cod{i}" for i in range(50)]})
    summary = schema_summary(df)
    assert "muestra no exhaustiva de 50 valores" in summary
    codigo_line = next(line for line in summary.splitlines() if line.strip().startswith("- codigo:"))
    # Solo se listan 5 valores frecuentes, no los 50.
    listados = codigo_line.split("valores frecuentes: ")[1].split(";")[0]
    assert len(listados.split(", ")) == 5


def test_schema_summary_categorica_todo_nan():
    df = pd.DataFrame({"x": [1, 2, 3], "vacia": [None, None, None]})
    summary = schema_summary(df)
    assert "vacia" in summary
    assert "categórica" in summary


def test_schema_summary_con_temporal():
    fechas = pd.to_datetime([
        "2021-06-15",  # Invierno, 2021
        "2022-12-01",  # Verano, 2022
        "2023-03-10",  # Otoño, 2023
        "2023-09-20",  # Primavera, 2023
    ])
    df = pd.DataFrame({"Fecha": fechas, "valor": [1.0, 2.0, 3.0, 4.0]})
    result = enrich_temporal(df)
    summary = schema_summary(result)

    # Anio y Estacion deben aparecer como categóricas
    assert "Anio" in summary
    assert "Estacion" in summary

    lines = {line.split(":")[0].strip(): line for line in summary.splitlines() if ":" in line}
    anio_line = next((v for k, v in lines.items() if "Anio" in k), "")
    estacion_line = next((v for k, v in lines.items() if "Estacion" in k), "")

    assert "categórica" in anio_line, f"Anio no es categórica en schema_summary: {anio_line!r}"
    assert "categórica" in estacion_line, f"Estacion no es categórica en schema_summary: {estacion_line!r}"

    # No deben mostrarse como numéricas
    assert "min=" not in anio_line
    assert "max=" not in anio_line
    assert "min=" not in estacion_line
    assert "max=" not in estacion_line
