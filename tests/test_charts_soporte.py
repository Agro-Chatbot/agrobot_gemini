import pandas as pd
import pytest
from matplotlib.figure import Figure

from chatbot.charts import ChartError, soporte_animal, tool_schemas

# --- Tests TECH-052: soporte_animal ---


def test_soporte_animal_calculo_basico(soporte_df):
    """Dos lotes conocidos → EV soportados correctos con ración default 8.0."""
    fig, resumen = soporte_animal(soporte_df)
    assert isinstance(fig, Figure)
    # L1: tasa_media=20, superficie=100 → ms=2000, ev=250
    # L2: tasa_media=15, superficie=200 → ms=3000, ev=375
    assert "250" in resumen
    assert "375" in resumen
    assert "8.0" in resumen


def test_soporte_animal_racion_customizada(soporte_df):
    """Ración 10 kg produce EV inversamente proporcional a ración 8."""
    _, resumen_8 = soporte_animal(soporte_df, racion_kg_dia=8.0)
    _, resumen_10 = soporte_animal(soporte_df, racion_kg_dia=10.0)
    assert "10.0" in resumen_10
    # EV con ración 10 < EV con ración 8
    # L1 con 10: 2000/10=200; con 8: 2000/8=250
    assert "200" in resumen_10


def test_soporte_animal_columna_faltante():
    """DataFrame sin 'Kg MS ha/día' lanza ChartError."""
    df_sin_col = pd.DataFrame(
        {"Lote": ["L1"], "Superficie ha": [100.0]}
    )
    with pytest.raises(ChartError, match="Kg MS ha/día"):
        soporte_animal(df_sin_col)


def test_soporte_animal_columna_superficie_faltante():
    """DataFrame sin 'Superficie ha' lanza ChartError."""
    df_sin_sup = pd.DataFrame(
        {"Lote": ["L1"], "Kg MS ha/día": [10.0]}
    )
    with pytest.raises(ChartError, match="Superficie ha"):
        soporte_animal(df_sin_sup)


def test_soporte_animal_filtro_vacio(soporte_df):
    """Filtro que deja el df vacío → ChartError antes de calcular."""
    soporte_df["Campo"] = "Fulano"
    with pytest.raises(ChartError):
        soporte_animal(soporte_df, filter_col="Campo", filter_val="No existe")


def test_soporte_animal_racion_cero_lanza_chart_error(soporte_df):
    """racion_kg_dia=0 debe lanzar ChartError."""
    with pytest.raises(ChartError, match="mayor que cero"):
        soporte_animal(soporte_df, racion_kg_dia=0)


def test_soporte_animal_racion_negativa_lanza_chart_error(soporte_df):
    """racion_kg_dia negativa debe lanzar ChartError."""
    with pytest.raises(ChartError, match="mayor que cero"):
        soporte_animal(soporte_df, racion_kg_dia=-5.0)


def test_soporte_animal_en_tools():
    """soporte_animal aparece en tool_schemas con los campos esperados."""
    schemas = tool_schemas()
    names = [s["name"] for s in schemas]
    assert "soporte_animal" in names
    sa_schema = next(s for s in schemas if s["name"] == "soporte_animal")
    props = sa_schema["input_schema"]["properties"]
    assert "racion_kg_dia" in props
    assert "filter_col" in props
    assert props["group_by"]["enum"] == ["Lote", "Campo", "Recurso"]
    assert "n_ev" in props


# --- Tests TECH-121: group_by, n_ev, tasa_media/superficie/ms_disponible ---


@pytest.fixture
def soporte_campo_df():
    """DataFrame con dos Campos conocidos (A: L1+L2, B: L3), sin superficie variable."""
    return pd.DataFrame(
        {
            "Lote": ["L1", "L2", "L3"],
            "Campo": ["A", "A", "B"],
            "Recurso": ["Pastura", "Pastura", "Verdeo"],
            "Kg MS ha/día": [20.0, 10.0, 30.0],
            "Superficie ha": [100.0, 50.0, 200.0],
        }
    )


@pytest.fixture
def soporte_superficie_variable_df():
    """L1 tiene dos registros de Superficie ha distintos (80 y 120); L2 es de otro Campo."""
    return pd.DataFrame(
        {
            "Lote": ["L1", "L1", "L2"],
            "Campo": ["A", "A", "B"],
            "Kg MS ha/día": [10.0, 30.0, 20.0],
            "Superficie ha": [80.0, 120.0, 50.0],
        }
    )


def test_soporte_animal_group_by_default_lote_sin_regresion(soporte_df):
    """Sin pasar group_by, el comportamiento es el mismo que antes de TECH-121 (default 'Lote')."""
    fig_default, resumen_default = soporte_animal(soporte_df)
    fig_explicito, resumen_explicito = soporte_animal(soporte_df, group_by="Lote")
    assert resumen_default == resumen_explicito
    assert "Agrupado por: Lote" in resumen_default
    assert "250" in resumen_default
    assert "375" in resumen_default


def test_soporte_animal_group_by_campo(soporte_campo_df):
    """group_by='Campo' agrega dos lotes en Campo A y uno en Campo B, con EV/EV-ha correctos.

    Campo A: L1 (tasa=20, sup=100, ms=2000) + L2 (tasa=10, sup=50, ms=500)
             -> sup=150, ms=2500, ev=2500/8=312.5, ev/ha=2500/8/150=2.0833...
    Campo B: L3 (tasa=30, sup=200, ms=6000) -> ev=6000/8=750.0
    """
    fig, resumen = soporte_animal(soporte_campo_df, group_by="Campo")
    assert isinstance(fig, Figure)
    assert "Agrupado por: Campo" in resumen
    assert "312.5" in resumen
    assert "750.0" in resumen
    assert "2500.0" in resumen  # ms_disponible Campo A
    assert "6000.0" in resumen  # ms_disponible Campo B


def test_soporte_animal_group_by_campo_no_duplica_superficie_variable(
    soporte_superficie_variable_df,
):
    """Un lote (L1) con dos Superficie ha distintas (80, 120) no duplica hectáreas al
    agrupar por Campo: debe usarse max(80, 120)=120, no 80+120=200."""
    _, resumen = soporte_animal(soporte_superficie_variable_df, group_by="Campo")
    # Campo A = solo L1: superficie=max(80,120)=120 (no 200), tasa_media=mean(10,30)=20,
    # ms=20*120=2400
    assert "120.0" in resumen
    assert "2400.0" in resumen
    assert "200.0" not in resumen  # 80+120 no debe aparecer como superficie sumada


@pytest.fixture
def soporte_lote_repetido_df():
    """El nombre de Lote '1' se repite en Campo A y Campo B (caso real del dataset:
    61 lotes repetidos entre campos distintos). No deben fundirse al agrupar por Campo."""
    return pd.DataFrame(
        {
            "Lote": ["1", "1", "2"],
            "Campo": ["A", "B", "A"],
            "Kg MS ha/día": [10.0, 40.0, 20.0],
            "Superficie ha": [50.0, 200.0, 100.0],
        }
    )


def test_soporte_animal_group_by_campo_no_funde_lotes_con_mismo_nombre(
    soporte_lote_repetido_df,
):
    """group_by='Campo' con un Lote cuyo nombre se repite en dos Campo distintos: ambos
    campos deben aparecer en el resultado, cada uno con sus propios valores agregados.

    Campo A: lote "1"@A (tasa=10, sup=50, ms=500) + lote "2"@A (tasa=20, sup=100, ms=2000)
             -> sup=150, ms=2500, ev=2500/8=312.5
    Campo B: lote "1"@B (tasa=40, sup=200, ms=8000) -> sup=200, ms=8000.0, ev=8000/8=1000.0
    """
    fig, resumen = soporte_animal(soporte_lote_repetido_df, group_by="Campo")
    assert isinstance(fig, Figure)
    detalle = resumen.split("Detalle por campo:")[1]
    # Ambos campos deben aparecer como filas del detalle (Campo B no debe desaparecer por
    # la fusión del Lote "1" entre campos).
    assert "\nA " in detalle
    assert "\nB " in detalle
    # Campo A: superficie=150.0, ms_disponible=2500.0, ev_soportados=312.5
    assert "150.0" in resumen
    assert "2500.0" in resumen
    assert "312.5" in resumen
    # Campo B: superficie=200.0, ms_disponible=8000.0, ev_soportados=1000.0
    assert "200.0" in resumen
    assert "8000.0" in resumen
    assert "1000.0" in resumen
    # La fusión incorrecta previa producía superficie=300.0 (max entre 50/100/200 sumado mal)
    # y ev=875.0 para un único "Campo A" fusionado; no deben aparecer.
    assert "300.0" not in resumen
    assert "875.0" not in resumen


def test_soporte_animal_ms_disponible_y_ev_soportados_consistentes(soporte_campo_df):
    """ms_disponible == tasa_media × superficie y ev_soportados == ms_disponible / racion_kg_dia."""
    racion = 8.0
    _, resumen = soporte_animal(soporte_campo_df, group_by="Campo", racion_kg_dia=racion)
    # Campo A: tasa_media_pond = 2500/150 = 16.666..., superficie=150 -> ms=2500.0
    # ev_soportados = 2500/8 = 312.5
    assert "2500.0" in resumen
    assert "312.5" in resumen
    # Campo B: tasa_media=30.0, superficie=200 -> ms = 30*200 = 6000.0; ev = 6000/8 = 750.0
    assert "6000.0" in resumen
    assert "750.0" in resumen


def test_soporte_animal_n_ev_agrega_ha_requeridas_al_resumen(soporte_df):
    """n_ev produce ha_requeridas = n_ev × racion_kg_dia / tasa_media en el resumen."""
    _, resumen = soporte_animal(soporte_df, n_ev=200)
    assert "ha_requeridas" in resumen
    assert "Hectáreas requeridas para 200 EV" in resumen
    # L1: tasa_media=20 -> ha_requeridas = 200*8/20 = 80.0
    # L2: tasa_media=15 -> ha_requeridas = 200*8/15 = 106.67
    assert "80.0" in resumen


def test_soporte_animal_n_ev_no_cambia_el_grafico(soporte_df):
    """El gráfico generado con n_ev es idéntico (mismas barras de EV soportados) al que se
    genera sin n_ev: n_ev solo afecta el resumen de texto."""
    fig_con_n_ev, resumen_con_n_ev = soporte_animal(soporte_df, n_ev=200)
    fig_sin_n_ev, resumen_sin_n_ev = soporte_animal(soporte_df)

    alturas_con = [p.get_height() for p in fig_con_n_ev.axes[0].patches]
    alturas_sin = [p.get_height() for p in fig_sin_n_ev.axes[0].patches]
    assert alturas_con == alturas_sin

    assert "ha_requeridas" in resumen_con_n_ev
    assert "ha_requeridas" not in resumen_sin_n_ev


def test_soporte_animal_n_ev_cero_lanza_chart_error(soporte_df):
    """n_ev=0 debe lanzar ChartError."""
    with pytest.raises(ChartError, match="mayor que cero"):
        soporte_animal(soporte_df, n_ev=0)


def test_soporte_animal_group_by_invalido_lanza_chart_error(soporte_df):
    """group_by fuera de {'Lote', 'Campo', 'Recurso'} debe lanzar ChartError."""
    with pytest.raises(ChartError, match="group_by"):
        soporte_animal(soporte_df, group_by="Anio")


def test_soporte_animal_group_by_campo_sin_columna_campo_lanza_chart_error(soporte_df):
    """group_by='Campo' sobre un df sin columna 'Campo' lanza ChartError."""
    with pytest.raises(ChartError, match="Campo"):
        soporte_animal(soporte_df, group_by="Campo")
