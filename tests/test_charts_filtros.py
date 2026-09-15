from pathlib import Path

import pandas as pd
import pytest
from matplotlib.figure import Figure

from chatbot.charts import ChartError, bar_chart, line_chart, tool_schemas

# --- Tests TECH-051: filtros por categoría y rango de fecha ---


def test_filter_col_val_reduce_dataframe(filterable_df):
    """filter_col/filter_val correcto: el gráfico usa solo las filas coincidentes."""
    fig, summary = bar_chart(
        filterable_df, x="Lote", y="valor", agg="sum",
        filter_col="Recurso", filter_val="Campo natural"
    )
    assert isinstance(fig, Figure)
    # Solo L1 (10+50=60) y L2 (20) deben aparecer; Pradera no está
    assert "L1" in summary
    assert "60" in summary


def test_filter_col_inexistente_lanza_chart_error(filterable_df):
    """filter_col que no existe en el DataFrame lanza ChartError."""
    with pytest.raises(ChartError, match="no existe"):
        bar_chart(filterable_df, x="Lote", y="valor", agg="sum",
                  filter_col="NoExiste", filter_val="algo")


def test_filter_val_inexistente_lanza_chart_error_con_valores(filterable_df):
    """filter_val que no existe en la columna lanza ChartError con valores disponibles."""
    with pytest.raises(ChartError, match="Campo artificial"):
        bar_chart(filterable_df, x="Lote", y="valor", agg="sum",
                  filter_col="Recurso", filter_val="Campo artificial")


def test_filter_col_sin_filter_val_lanza_chart_error(filterable_df):
    """filter_col sin filter_val lanza ChartError."""
    with pytest.raises(ChartError, match="filter_val"):
        bar_chart(filterable_df, x="Lote", y="valor", agg="sum",
                  filter_col="Recurso")


def test_date_from_date_to_filtra_rango(filterable_df):
    """date_from/date_to retiene solo filas en el rango."""
    fig, summary = bar_chart(
        filterable_df, x="Recurso", y="valor", agg="sum",
        date_from="2023-01-01", date_to="2023-12-31"
    )
    assert isinstance(fig, Figure)
    # En 2023 hay: Pradera L1 30, Campo natural L1 50, Pradera L2 40 → Pradera suma 70, Campo natural suma 50
    assert "Pradera" in summary


def test_solo_date_from_sin_date_to(filterable_df):
    """Solo date_from: filtra desde esa fecha en adelante."""
    fig, summary = line_chart(
        filterable_df, x="Recurso", y="valor", agg="sum",
        date_from="2023-01-01"
    )
    assert isinstance(fig, Figure)


def test_solo_date_to_sin_date_from(filterable_df):
    """Solo date_to: filtra hasta esa fecha."""
    fig, summary = bar_chart(
        filterable_df, x="Recurso", y="valor", agg="sum",
        date_to="2022-12-31"
    )
    assert isinstance(fig, Figure)
    # Solo filas de 2022: Campo natural 10+20=30, Pradera 30
    assert "Campo natural" in summary


def test_filtro_vacio_lanza_chart_error(filterable_df):
    """Rango de fechas que no contiene datos lanza ChartError."""
    with pytest.raises(ChartError, match="no devuelve datos"):
        bar_chart(
            filterable_df, x="Recurso", y="valor", agg="sum",
            date_from="2000-01-01", date_to="2000-12-31"
        )


def test_filtro_val_inexistente_lanza_chart_error_vacio(filterable_df):
    """filter_val inexistente lanza ChartError antes de evaluar si queda vacío."""
    with pytest.raises(ChartError):
        bar_chart(filterable_df, x="Lote", y="valor", agg="sum",
                  filter_col="Recurso", filter_val="No existe")


def test_sin_filtros_comportamiento_igual(filterable_df):
    """Sin parámetros de filtro, bar_chart funciona igual que antes."""
    fig, summary = bar_chart(filterable_df, x="Recurso", y="valor", agg="sum")
    assert isinstance(fig, Figure)
    assert "Campo natural" in summary
    assert "Pradera" in summary


def test_date_from_invalida_lanza_chart_error(filterable_df):
    """date_from con formato inválido lanza ChartError (no DateParseError)."""
    with pytest.raises(ChartError, match="ISO 8601"):
        bar_chart(filterable_df, x="Recurso", y="valor", agg="sum",
                  date_from="maniana")


def test_date_to_invalida_lanza_chart_error(filterable_df):
    """date_to con formato inválido lanza ChartError (no DateParseError)."""
    with pytest.raises(ChartError, match="ISO 8601"):
        bar_chart(filterable_df, x="Recurso", y="valor", agg="sum",
                  date_to="Q1-2023")


def test_filter_schemas_tienen_cuatro_propiedades_filtro():
    """Todos los schemas de tools incluyen los 4 parámetros de filtrado."""
    schemas = tool_schemas()
    filter_keys = {"filter_col", "filter_val", "date_from", "date_to"}
    for schema in schemas:
        props = set(schema["input_schema"]["properties"].keys())
        assert filter_keys.issubset(props), (
            f"Tool '{schema['name']}' falta propiedades de filtro: {filter_keys - props}"
        )


def test_filter_schemas_incluyen_filters():
    """Todos los schemas de tools exponen además la propiedad compuesta 'filters' (ADR-034)."""
    schemas = tool_schemas()
    for schema in schemas:
        props = schema["input_schema"]["properties"]
        assert "filters" in props, f"Tool '{schema['name']}' no expone 'filters'."


# --- Tests TECH-118: filtro compuesto multi-columna y multivalor (ADR-034) ---


def test_filters_compuesto_and_dos_columnas(filterable_df):
    """filters con dos entradas (Recurso + Lote) hace AND: intersección exacta."""
    fig, summary = bar_chart(
        filterable_df, x="Lote", y="valor", agg="sum",
        filters=[
            {"col": "Recurso", "vals": "Campo natural"},
            {"col": "Lote", "vals": "L1"},
        ],
    )
    assert isinstance(fig, Figure)
    # Campo natural + L1: filas con valor 10 y 50 -> suma 60. Sin L2 (20).
    assert "60" in summary
    assert "L2" not in summary


def test_filters_multivalor_or_una_entrada(filterable_df):
    """Una entrada de filters con lista de valores aplica OR (isin) dentro de esa columna."""
    fig, summary = bar_chart(
        filterable_df, x="Lote", y="valor", agg="sum",
        filters=[{"col": "Lote", "vals": ["L1", "L2"]}],
    )
    assert isinstance(fig, Figure)
    assert "L1" in summary
    assert "L2" in summary


def test_filters_valor_inexistente_lo_nombra_explicitamente(filterable_df):
    """Un valor inexistente en cualquier entrada de filters se nombra en el ChartError."""
    with pytest.raises(ChartError, match="Campo artificial"):
        bar_chart(
            filterable_df, x="Lote", y="valor", agg="sum",
            filters=[
                {"col": "Recurso", "vals": "Campo artificial"},
                {"col": "Lote", "vals": "L1"},
            ],
        )


def test_filters_col_inexistente_lanza_chart_error(filterable_df):
    """Una columna inexistente en una entrada de filters lanza ChartError."""
    with pytest.raises(ChartError, match="no existe"):
        bar_chart(
            filterable_df, x="Lote", y="valor", agg="sum",
            filters=[{"col": "NoExiste", "vals": "algo"}],
        )


def test_filters_entrada_invalida_sin_col_o_vals(filterable_df):
    """Una entrada de filters sin 'col' o sin 'vals' lanza ChartError."""
    with pytest.raises(ChartError, match="col.*vals|vals.*col"):
        bar_chart(
            filterable_df, x="Lote", y="valor", agg="sum",
            filters=[{"col": "Lote"}],
        )


def test_filters_trunca_valores_sugeridos_a_30():
    """Cuando la columna filtrada tiene más de 30 valores posibles, el mensaje
    de ChartError trunca la lista sugerida (formato '... y N más')."""
    df = pd.DataFrame(
        {
            "categoria": [f"cat_{i}" for i in range(35)],
            "valor": list(range(35)),
        }
    )
    with pytest.raises(ChartError) as exc_info:
        bar_chart(df, x="categoria", y="valor", agg="sum",
                  filters=[{"col": "categoria", "vals": "no_existe"}])
    msg = str(exc_info.value)
    assert "y " in msg
    assert "más" in msg
    assert msg.index("y ") < msg.rindex("más")


def test_filters_legacy_filter_col_filter_val_sigue_igual(filterable_df):
    """filter_col/filter_val (legacy) sigue produciendo el mismo resultado que antes."""
    fig, summary = bar_chart(
        filterable_df, x="Lote", y="valor", agg="sum",
        filter_col="Recurso", filter_val="Campo natural",
    )
    assert isinstance(fig, Figure)
    assert "L1" in summary
    assert "60" in summary


# --- Verificación anti-P03: mismo nombre de Lote en distintos Campos (data real) ---

_TAPALQUEII_PATH = Path(__file__).resolve().parents[1] / "data" / "tapalqueii.csv"


@pytest.fixture(scope="module")
def tapalqueii_df():
    if not _TAPALQUEII_PATH.exists():
        pytest.skip("data/tapalqueii.csv no disponible en este entorno.")
    return pd.read_csv(_TAPALQUEII_PATH)


def test_anti_p03_filtro_compuesto_campo_lote_no_mezcla_campos(tapalqueii_df):
    """Un Lote homónimo entre dos Campos: filtrar por Campo+Lote a la vez devuelve
    solo las filas del Campo pedido, sin mezclar el otro Campo con el mismo Lote."""
    dup = tapalqueii_df[["Campo", "Lote"]].drop_duplicates()
    counts = dup.groupby("Lote")["Campo"].nunique()
    repetidos = counts[counts > 1]
    assert len(repetidos) > 0, "El CSV real debería tener al menos un Lote repetido entre Campos."

    lote = repetidos.index[0]
    campos = dup[dup["Lote"] == lote]["Campo"].tolist()
    campo_a, campo_b = campos[0], campos[1]

    fig, summary = bar_chart(
        tapalqueii_df, x="Campo", agg="count",
        filters=[
            {"col": "Campo", "vals": campo_a},
            {"col": "Lote", "vals": lote},
        ],
    )
    assert isinstance(fig, Figure)
    assert campo_a in summary
    assert campo_b not in summary

    esperado = tapalqueii_df[
        (tapalqueii_df["Campo"] == campo_a) & (tapalqueii_df["Lote"] == lote)
    ]
    otro_campo = tapalqueii_df[
        (tapalqueii_df["Campo"] == campo_b) & (tapalqueii_df["Lote"] == lote)
    ]
    assert len(esperado) > 0
    assert len(otro_campo) > 0
    # El conteo del filtro compuesto es exactamente el de campo_a, no el total
    # combinado con campo_b (que es lo que pasaría si el filtro mezclara campos).
    assert str(len(esperado)) in summary
    total_combinado = len(esperado) + len(otro_campo)
    assert total_combinado != len(esperado)
    assert str(total_combinado) not in summary
