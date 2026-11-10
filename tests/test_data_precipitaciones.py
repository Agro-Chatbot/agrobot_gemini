from pathlib import Path

import pandas as pd
import pytest

from chatbot import config
from chatbot.data import load_csv, load_datasets, load_precipitaciones

HEADER = "CAMPO,lat,lon,Atributo,fecha,año,mes,dia,milimetros\r\n".encode("latin-1")
ROWS = (
    "Santa Fé,-36.6,-59.7,20180101_precipitation,20180101,2018,01,01,26.9\r\n"
    "Santa Fé,-36.6,-59.7,20180106_precipitation,20180106,2018,01,06,0.8\r\n"
    "Carro Quemado,-36.6,-59.7,20180101_precipitation,20180101,2018,01,01,3.5\r\n"
).encode("utf-8")
COLS = ["Fecha", "Campo", "Precipitación mm", "Anio", "Estacion", "Mes"]


@pytest.fixture
def precip_csv(tmp_path):
    p = tmp_path / "precip.csv"
    p.write_bytes(HEADER + ROWS)
    return p


@pytest.fixture
def tasas_csv(tmp_path):
    p = tmp_path / "tasas.csv"
    p.write_text("Fecha,Campo,Tasa\n2018-01-01,Santa Fé,10.5\n", encoding="utf-8")
    return p


def test_load_precipitaciones_sintetico(precip_csv):
    df = load_precipitaciones(precip_csv)
    assert list(df.columns) == COLS
    assert pd.api.types.is_datetime64_any_dtype(df["Fecha"])
    assert set(df["Campo"]) == {"Santa Fé", "Carro Quemado"}
    assert df["Anio"].iloc[0] == "2018"
    assert df["Fecha"].iloc[1] == pd.Timestamp("2018-01-06")


def test_load_datasets_con_precipitaciones(tasas_csv, precip_csv):
    dfs, schema = load_datasets(tasas_csv, precip_csv)
    assert set(dfs) == {"tasas", "precipitaciones"}
    assert "### Dataset `tasas`" in schema
    assert "### Dataset `precipitaciones`" in schema


def test_load_datasets_sin_precipitaciones(tasas_csv, tmp_path, capsys):
    dfs, schema = load_datasets(tasas_csv, tmp_path / "no_existe.csv")
    assert set(dfs) == {"tasas"}
    assert "### Dataset `tasas`" in schema
    assert "precipitaciones" not in schema
    assert "no se encontró" in capsys.readouterr().err


def test_csv_real():
    if not config.PRECIP_CSV_PATH.exists() or not config.CSV_PATH.exists():
        pytest.skip("CSV real no disponible")
    precip = load_precipitaciones(config.PRECIP_CSV_PATH)
    assert len(precip) == 19968
    assert set(precip["Campo"]) == set(load_csv(config.CSV_PATH)["Campo"])
