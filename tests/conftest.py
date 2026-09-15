import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import pytest

matplotlib.use("Agg")


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "categoria": ["Electrónica", "Ropa", "Hogar", "Electrónica", "Ropa"],
            "ventas": [1500.0, 800.0, 400.0, 2200.0, 600.0],
            "region": ["Norte", "Sur", "Norte", "Sur", "Norte"],
            "unidades": [10, 5, 8, 15, 4],
        }
    )


@pytest.fixture(autouse=True)
def close_matplotlib_figures():
    yield
    plt.close("all")


@pytest.fixture
def filterable_df():
    """DataFrame con columnas Recurso, valor y Fecha para tests de filtrado."""
    return pd.DataFrame(
        {
            "Recurso": ["Campo natural", "Campo natural", "Pradera", "Pradera", "Campo natural"],
            "Lote": ["L1", "L2", "L1", "L2", "L1"],
            "valor": [10.0, 20.0, 30.0, 40.0, 50.0],
            "Fecha": pd.to_datetime(
                ["2022-03-01", "2022-09-01", "2023-01-01", "2023-06-01", "2023-11-01"]
            ),
        }
    )


@pytest.fixture
def soporte_df():
    """DataFrame mínimo para tests de soporte_animal con 2 lotes conocidos."""
    return pd.DataFrame(
        {
            "Lote": ["L1", "L1", "L1", "L2", "L2", "L2"],
            "Kg MS ha/día": [10.0, 20.0, 30.0, 5.0, 15.0, 25.0],
            "Superficie ha": [100.0, 100.0, 100.0, 200.0, 200.0, 200.0],
        }
    )
