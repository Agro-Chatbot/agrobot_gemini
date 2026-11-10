import pandas as pd
import pytest
from matplotlib.figure import Figure

from chatbot.charts import ChartError, run_tool, tool_schemas
from chatbot.charts.basic import BAR_CHART_SCHEMA

DATASET_TOOLS = ["bar_chart", "line_chart", "scatter_plot", "histogram", "pie_chart"]


@pytest.fixture
def dfs():
    dt = pd.DataFrame({"Campo": ["A", "B"], "Tasa": [1.0, 2.0]})
    dp = pd.DataFrame({"Anio": [2020, 2020, 2021], "Precipitación mm": [10.0, 20.0, 5.0]})
    return {"tasas": dt, "precipitaciones": dp}


def test_schema_inyectado_solo_en_tools_con_dataset():
    for s in tool_schemas():
        props = s["input_schema"]["properties"]
        if s["name"] in DATASET_TOOLS:
            assert props["dataset"]["enum"] == ["tasas", "precipitaciones"]
            assert "dataset" not in s["input_schema"].get("required", [])
        else:
            assert "dataset" not in props


def test_schemas_originales_no_mutados():
    tool_schemas()
    assert "dataset" not in BAR_CHART_SCHEMA["input_schema"]["properties"]


def test_bar_chart_precipitaciones(dfs):
    fig, summary = run_tool(
        "bar_chart", dfs,
        {"dataset": "precipitaciones", "x": "Anio", "y": "Precipitación mm", "agg": "sum"},
    )
    assert isinstance(fig, Figure)
    assert "30.0" in summary  # suma 2020 de dp; tasas no tiene esa columna


def test_default_tasas(dfs):
    fig, _ = run_tool("bar_chart", dfs, {"x": "Campo", "y": "Tasa", "agg": "sum"})
    assert isinstance(fig, Figure)


def test_no_muta_params(dfs):
    params = {"dataset": "tasas", "x": "Campo", "y": "Tasa", "agg": "sum"}
    run_tool("bar_chart", dfs, params)
    assert "dataset" in params


def test_dataframe_suelto(dfs):
    fig, _ = run_tool("bar_chart", dfs["tasas"], {"x": "Campo", "y": "Tasa", "agg": "sum"})
    assert isinstance(fig, Figure)
    fig, _ = run_tool(
        "bar_chart", dfs["tasas"], {"dataset": "tasas", "x": "Campo", "y": "Tasa", "agg": "sum"}
    )
    assert isinstance(fig, Figure)


def test_dataframe_suelto_otro_dataset(dfs):
    with pytest.raises(ChartError):
        run_tool("bar_chart", dfs["tasas"], {"dataset": "precipitaciones", "x": "Campo"})


def test_dataset_invalido_o_no_cargado(dfs):
    with pytest.raises(ChartError, match="tasas"):
        run_tool("bar_chart", dfs, {"dataset": "xxx", "x": "Campo"})
    with pytest.raises(ChartError, match="no disponible"):
        run_tool("bar_chart", {"tasas": dfs["tasas"]}, {"dataset": "precipitaciones", "x": "Campo"})


def test_soporte_animal_solo_tasas(dfs):
    with pytest.raises(ChartError, match="solo opera sobre tasas"):
        run_tool("soporte_animal", dfs, {"dataset": "precipitaciones"})
