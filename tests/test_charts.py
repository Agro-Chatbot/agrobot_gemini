import matplotlib
import pandas as pd
import pytest
from matplotlib.figure import Figure

from matplotlib.colors import to_hex

from chatbot.charts import (
    CHART_PALETTE,
    ChartError,
    bar_chart,
    histogram,
    line_chart,
    pie_chart,
    run_tool,
    scatter_plot,
    tool_schemas,
)
from chatbot.data import schema_summary

matplotlib.use("Agg")


def test_bar_chart(sample_df):
    fig, summary = bar_chart(sample_df, x="categoria", y="ventas", agg="sum")
    assert isinstance(fig, Figure)
    assert "Electrónica" in summary


def test_bar_chart_count_sin_y(sample_df):
    fig, summary = bar_chart(sample_df, x="region", agg="count")
    assert isinstance(fig, Figure)


def test_histogram(sample_df):
    fig, _ = histogram(sample_df, column="ventas", bins=10)
    assert isinstance(fig, Figure)


def test_scatter(sample_df):
    fig, summary = scatter_plot(sample_df, x="unidades", y="ventas")
    assert isinstance(fig, Figure)
    assert "correlación" in summary


def test_pie(sample_df):
    fig, _ = pie_chart(sample_df, category="categoria", value="ventas", agg="sum")
    assert isinstance(fig, Figure)


def test_columna_invalida(sample_df):
    with pytest.raises(ChartError):
        bar_chart(sample_df, x="no_existe", y="ventas", agg="sum")


def test_columna_no_numerica_en_scatter(sample_df):
    with pytest.raises(ChartError):
        scatter_plot(sample_df, x="categoria", y="ventas")


def test_bar_chart_agg_sum_sin_y_lanza_chart_error(sample_df):
    with pytest.raises(ChartError, match="y"):
        run_tool("bar_chart", sample_df, {"x": "categoria", "agg": "sum"})


def test_pie_chart_agg_sum_sin_value_lanza_chart_error(sample_df):
    with pytest.raises(ChartError, match="y"):
        run_tool("pie_chart", sample_df, {"category": "categoria", "agg": "sum"})


def test_line_chart_agg_sum_sin_y_lanza_chart_error(sample_df):
    with pytest.raises(ChartError, match="y"):
        run_tool("line_chart", sample_df, {"x": "categoria", "agg": "sum"})


def test_run_tool_dispatch(sample_df):
    fig, _ = run_tool("bar_chart", sample_df, {"x": "categoria", "y": "ventas", "agg": "sum"})
    assert isinstance(fig, Figure)


def test_tool_schemas_estructura():
    schemas = tool_schemas()
    assert len(schemas) == 6
    for s in schemas:
        assert "name" in s and "input_schema" in s


# --- Tests TECH-019: endurecer charts.py / data.py ---

def test_pie_chart_valores_negativos_lanza_chart_error():
    """Caso 1: pie_chart con valores que producen negativos debe lanzar ChartError."""
    df_neg = pd.DataFrame({"cat": ["A", "B"], "val": [-10, 5]})
    with pytest.raises(ChartError, match="no negativos"):
        pie_chart(df_neg, category="cat", value="val", agg="sum")


def test_scatter_varianza_cero_no_contiene_nan():
    """Caso 2: scatter_plot con columna de varianza cero no debe incluir 'nan' en el summary."""
    df_zero = pd.DataFrame({"x": [1, 1, 1], "y": [2, 3, 4]})
    _, summary = scatter_plot(df_zero, x="x", y="y")
    assert "nan" not in summary.lower()


def test_run_tool_clave_inesperada_lanza_chart_error(sample_df):
    """Caso 3: run_tool con clave inesperada en params debe lanzar ChartError, no TypeError."""
    with pytest.raises(ChartError):
        run_tool("bar_chart", sample_df, {"x": "categoria", "y": "ventas", "agg": "sum", "parametro_raro": True})


def test_schema_summary_columna_toda_nan_no_contiene_nan():
    """Caso 4: schema_summary con columna toda-NaN no debe producir 'nan' en el string."""
    df_nan = pd.DataFrame({"col_num": [float("nan"), float("nan")], "cat": ["A", "B"]})
    result = schema_summary(df_nan)
    assert "nan" not in result.lower()


# --- Tests TECH-110: paleta de gráficos accesible ---

def test_bar_chart_usa_paleta_propia(sample_df):
    """El primer patch de un bar_chart usa un color de CHART_PALETTE (no tab10)."""
    fig, _ = bar_chart(sample_df, x="categoria", y="ventas", agg="sum")
    ax = fig.axes[0]
    primer_color = to_hex(ax.patches[0].get_facecolor())
    assert primer_color in [c.lower() for c in CHART_PALETTE]


def test_bar_chart_facecolor_blanco(sample_df):
    """La figura y los ejes tienen fondo blanco explícito."""
    fig, _ = bar_chart(sample_df, x="categoria", y="ventas", agg="sum")
    ax = fig.axes[0]
    assert to_hex(fig.get_facecolor()) == "#ffffff"
    assert to_hex(ax.get_facecolor()) == "#ffffff"


def test_pie_chart_usa_paleta_propia(sample_df):
    """Los wedges del pie_chart usan colores de CHART_PALETTE, pasados explícitamente."""
    fig, _ = pie_chart(sample_df, category="categoria", value="ventas", agg="sum")
    ax = fig.axes[0]
    colores_paleta = {c.lower() for c in CHART_PALETTE}
    for wedge in ax.patches:
        assert to_hex(wedge.get_facecolor()) in colores_paleta


# --- Tests TECH-114: jerarquía tipográfica del título del gráfico ---

@pytest.mark.parametrize(
    "chart_fn, kwargs",
    [
        (bar_chart, {"x": "categoria", "y": "ventas", "agg": "sum"}),
        (line_chart, {"x": "categoria", "y": "ventas", "agg": "mean"}),
        (bar_chart, {"x": "categoria", "agg": "count"}),
        (pie_chart, {"category": "categoria", "value": "ventas", "agg": "sum"}),
    ],
)
def test_titulo_agregado_no_empieza_con_agg_crudo(sample_df, chart_fn, kwargs):
    """El título no debe empezar con el nombre crudo de la agregación (ej. 'sum de ...')."""
    fig, _ = chart_fn(sample_df, **kwargs)
    ax = fig.axes[0]
    titulo = ax.get_title()
    for agg_crudo in ("sum de", "mean de", "count de"):
        assert not titulo.lower().startswith(agg_crudo)


@pytest.mark.parametrize(
    "chart_fn, kwargs",
    [
        (bar_chart, {"x": "categoria", "y": "ventas", "agg": "sum"}),
        (line_chart, {"x": "categoria", "y": "ventas", "agg": "sum"}),
        (scatter_plot, {"x": "unidades", "y": "ventas"}),
        (histogram, {"column": "ventas", "bins": 10}),
    ],
)
def test_titulo_tiene_mayor_fontsize_que_labels(sample_df, chart_fn, kwargs):
    """El título del gráfico debe tener mayor fontsize que las etiquetas de los ejes."""
    fig, _ = chart_fn(sample_df, **kwargs)
    ax = fig.axes[0]
    title_fontsize = ax.title.get_fontsize()
    xlabel_fontsize = ax.xaxis.label.get_fontsize()
    ylabel_fontsize = ax.yaxis.label.get_fontsize()
    assert title_fontsize > xlabel_fontsize
    assert title_fontsize > ylabel_fontsize


# --- Tests TECH-153: respaldo muestral (n) por grupo en el summary de agg='mean' ---

def test_summary_incluye_n_por_grupo(sample_df):
    """El summary de agg='mean' trae n y n_no_nulo por grupo, sin romper count/sum."""
    fig, summary = bar_chart(sample_df, x="categoria", y="ventas", agg="mean")
    assert isinstance(fig, Figure)
    # Electrónica: ventas 1500 y 2200 -> n=2, n_no_nulo=2
    assert "Electrónica" in summary
    assert "n=2" in summary
    assert "n_no_nulo=2" in summary
    # Hogar: un solo registro -> n=1
    assert "Hogar" in summary
    assert "n=1" in summary


def test_summary_agg_sum_no_cambia_de_formato(sample_df):
    """agg='sum' sigue devolviendo el formato de summary anterior (sin n/n_no_nulo)."""
    _, summary = bar_chart(sample_df, x="categoria", y="ventas", agg="sum")
    assert "n=" not in summary
    assert "n_no_nulo" not in summary


def test_summary_agg_count_no_cambia_de_formato(sample_df):
    """agg='count' sigue devolviendo el formato de summary anterior (sin n/n_no_nulo)."""
    _, summary = bar_chart(sample_df, x="region", agg="count")
    assert "n_no_nulo" not in summary


def test_summary_categoria_sin_datos_en_periodo_aparece_con_n_cero(filterable_df):
    """Una categoría presente en el dataset pero sin filas en el subconjunto filtrado
    (ej. rango de fechas) aparece en el summary con n=0 en vez de desaparecer."""
    fig, summary = bar_chart(
        filterable_df,
        x="Recurso",
        y="valor",
        agg="mean",
        date_from="2022-01-01",
        date_to="2022-12-31",
    )
    assert isinstance(fig, Figure)
    # Solo hay filas de "Campo natural" en 2022; "Pradera" no tiene datos en el período.
    assert "Campo natural" in summary
    assert "Pradera" in summary
    pradera_linea = [linea for linea in summary.splitlines() if "Pradera" in linea][0]
    assert "n=0" in pradera_linea
    assert "n_no_nulo=0" in pradera_linea
    assert "sin datos" in pradera_linea


def test_pie_chart_categoria_sin_datos_no_rompe_el_grafico(filterable_df):
    """pie_chart con agg='mean' y una categoría sin datos en el período no debe fallar al
    dibujar el gráfico (esa categoría queda fuera de las porciones, pero en el summary)."""
    fig, summary = pie_chart(
        filterable_df,
        category="Recurso",
        value="valor",
        agg="mean",
        date_from="2022-01-01",
        date_to="2022-12-31",
    )
    assert isinstance(fig, Figure)
    assert "Pradera" in summary
    assert "n=0" in [linea for linea in summary.splitlines() if "Pradera" in linea][0]


def test_filtro_sobre_la_misma_columna_de_x_no_reintroduce_categorias_excluidas(filterable_df):
    """Un filtro explícito sobre la misma columna usada como x (ej. comparar solo un
    subconjunto de categorías) no debe reintroducir las categorías excluidas como n=0:
    eso anularía el filtro/comparación pedido por el usuario (TECH-153)."""
    fig, summary = bar_chart(
        filterable_df,
        x="Recurso",
        y="valor",
        agg="mean",
        filters=[{"col": "Recurso", "vals": ["Campo natural"]}],
    )
    assert isinstance(fig, Figure)
    assert "Campo natural" in summary
    assert "Pradera" not in summary


def test_filter_col_sobre_la_misma_columna_de_x_no_reintroduce_categorias_excluidas(filterable_df):
    """Mismo caso que el anterior pero usando el filtro legacy filter_col/filter_val."""
    _, summary = line_chart(
        filterable_df,
        x="Recurso",
        y="valor",
        agg="mean",
        filter_col="Recurso",
        filter_val="Campo natural",
    )
    assert "Campo natural" in summary
    assert "Pradera" not in summary


# --- Tests TECH-119: ranking top/bottom-N y reference_line ---

def test_top_n_asc_devuelve_las_n_categorias_de_menor_valor(sample_df):
    """top_n=3, order='asc' sobre una agregación por categoría devuelve exactamente las
    3 categorías de menor valor, ordenadas de menor a mayor."""
    fig, summary = bar_chart(sample_df, x="categoria", y="ventas", agg="sum", top_n=3, order="asc")
    ax = fig.axes[0]
    etiquetas = [t.get_text() for t in ax.get_xticklabels()]
    assert len(etiquetas) == 3
    # sum por categoría: Hogar=400, Ropa=1400, Electrónica=3700 -> asc: Hogar, Ropa, Electrónica
    assert etiquetas == ["Hogar", "Ropa", "Electrónica"]


def test_top_n_desc_devuelve_las_n_categorias_de_mayor_valor(sample_df):
    fig, summary = bar_chart(sample_df, x="categoria", y="ventas", agg="sum", top_n=1, order="desc")
    ax = fig.axes[0]
    etiquetas = [t.get_text() for t in ax.get_xticklabels()]
    assert etiquetas == ["Electrónica"]


def test_top_n_mayor_a_categorias_disponibles_no_rompe(sample_df):
    """top_n mayor que el número de categorías disponibles no rompe: devuelve todas."""
    fig, summary = bar_chart(sample_df, x="categoria", y="ventas", agg="sum", top_n=100, order="desc")
    ax = fig.axes[0]
    etiquetas = [t.get_text() for t in ax.get_xticklabels()]
    assert len(etiquetas) == 3  # Electrónica, Ropa, Hogar


def test_sin_top_n_comportamiento_identico_al_actual(sample_df):
    """Sin top_n, el resultado es idéntico al comportamiento previo (retrocompatible)."""
    fig_sin, summary_sin = bar_chart(sample_df, x="categoria", y="ventas", agg="sum")
    fig_con, summary_con = bar_chart(sample_df, x="categoria", y="ventas", agg="sum", top_n=None)
    assert summary_sin == summary_con
    ax_sin = fig_sin.axes[0]
    ax_con = fig_con.axes[0]
    etiquetas_sin = [t.get_text() for t in ax_sin.get_xticklabels()]
    etiquetas_con = [t.get_text() for t in ax_con.get_xticklabels()]
    assert etiquetas_sin == etiquetas_con


def test_top_n_invalido_lanza_chart_error(sample_df):
    with pytest.raises(ChartError):
        bar_chart(sample_df, x="categoria", y="ventas", agg="sum", top_n=0)


def test_order_invalido_con_top_n_lanza_chart_error(sample_df):
    with pytest.raises(ChartError):
        bar_chart(sample_df, x="categoria", y="ventas", agg="sum", top_n=2, order="raro")


def test_top_n_funciona_en_line_chart_y_pie_chart(sample_df):
    fig_line, _ = line_chart(sample_df, x="categoria", y="ventas", agg="sum", top_n=2, order="desc")
    assert isinstance(fig_line, Figure)
    fig_pie, summary_pie = pie_chart(sample_df, category="categoria", value="ventas", agg="sum", top_n=2, order="desc")
    assert isinstance(fig_pie, Figure)
    assert "Hogar" not in summary_pie  # Hogar es la de menor valor, top_n=2 desc la excluye


def test_top_n_con_agg_mean_reusa_format_summary_con_n_por_grupo(sample_df):
    """El summary de los extremos (top/bottom-N) incluye el n por grupo (TECH-153)."""
    _, summary = bar_chart(sample_df, x="categoria", y="ventas", agg="mean", top_n=1, order="desc")
    assert "n=" in summary
    assert "n_no_nulo=" in summary


def test_reference_line_mean_agrega_linea_al_axes(sample_df):
    """reference_line='mean' dibuja una línea en el Axes, verificable con ax.lines."""
    fig, summary = bar_chart(sample_df, x="categoria", y="ventas", agg="sum", reference_line="mean")
    ax = fig.axes[0]
    assert len(ax.lines) == 1
    assert "Línea de referencia" in summary
    assert "promedio" in summary.lower()


def test_reference_line_mean_incluye_categorias_por_encima_y_por_debajo(sample_df):
    _, summary = bar_chart(sample_df, x="categoria", y="ventas", agg="sum", reference_line="mean")
    # sum por categoría: Electrónica=3700, Ropa=1400, Hogar=400 -> promedio=1833.33
    assert "Electrónica" in summary.split("Por encima del promedio:")[1].split("\n")[0]
    assert "Hogar" in summary.split("Por debajo del promedio:")[1]


def test_reference_line_invalido_lanza_chart_error(sample_df):
    with pytest.raises(ChartError):
        bar_chart(sample_df, x="categoria", y="ventas", agg="sum", reference_line="mediana")


def test_reference_line_sin_especificar_no_agrega_lineas(sample_df):
    fig, summary = bar_chart(sample_df, x="categoria", y="ventas", agg="sum")
    ax = fig.axes[0]
    assert len(ax.lines) == 0
    assert "Línea de referencia" not in summary


# --- Tests TECH-122: group_by (comparación de N series en una sola tool call) ---

@pytest.fixture
def dos_campanas_df():
    """DataFrame con dos series (campañas) sobre el mismo eje x (mes), para group_by."""
    return pd.DataFrame(
        {
            "mes": ["Ene", "Feb", "Mar", "Ene", "Feb", "Mar"],
            "campana": ["2022", "2022", "2022", "2023", "2023", "2023"],
            "valor": [10.0, 20.0, 30.0, 15.0, 25.0, 35.0],
        }
    )


def test_bar_chart_group_by_produce_n_series(dos_campanas_df):
    """group_by produce un grupo de barras (una serie) por cada valor de group_by."""
    fig, summary = bar_chart(dos_campanas_df, x="mes", y="valor", agg="sum", group_by="campana")
    ax = fig.axes[0]
    assert len(ax.containers) == 2
    assert "2022" in summary and "2023" in summary


def test_line_chart_group_by_produce_n_series(dos_campanas_df):
    """group_by produce una línea por cada valor de group_by."""
    fig, summary = line_chart(dos_campanas_df, x="mes", y="valor", agg="sum", group_by="campana")
    ax = fig.axes[0]
    assert len(ax.lines) == 2
    assert "2022" in summary and "2023" in summary


def test_group_by_summary_incluye_n_por_serie(dos_campanas_df):
    """El summary con group_by lista, por serie, el n (cantidad de filas) de cada categoría
    (TECH-153 extendido a group_by)."""
    _, summary = bar_chart(dos_campanas_df, x="mes", y="valor", agg="sum", group_by="campana")
    # 3 meses x 2 campañas = 6 combinaciones, cada una con exactamente 1 fila.
    assert summary.count("(n=1, n_no_nulo=1)") == 6


def test_group_by_summary_lista_combinacion_sin_datos(dos_campanas_df):
    """Si una categoría de x existe para una serie de group_by pero no para otra (ej.
    "Abr" solo reportado en la campaña 2023), el summary debe listar esa combinación
    faltante como "sin datos"/n=0 en vez de omitirla en silencio (TECH-122, P1)."""
    df = pd.concat(
        [dos_campanas_df, pd.DataFrame({"mes": ["Abr"], "campana": ["2023"], "valor": [40.0]})],
        ignore_index=True,
    )
    _, summary = bar_chart(df, x="mes", y="valor", agg="sum", group_by="campana")
    secciones = summary.split("-- campana=")
    seccion_2022 = next(s for s in secciones if s.startswith("2022"))
    seccion_2023 = next(s for s in secciones if s.startswith("2023"))
    # "Abr" no tiene ninguna fila para la campaña 2022: debe listarse igual, como "sin datos".
    assert "Abr    sin datos  (n=0, n_no_nulo=0)" in seccion_2022
    # "Abr" sí tiene datos en la campaña 2023.
    assert "Abr    40  (n=1, n_no_nulo=1)" in seccion_2023


def test_bar_chart_sin_group_by_comportamiento_identico_al_actual(sample_df):
    """Sin group_by, bar_chart se comporta exactamente igual que antes (retrocompatible)."""
    fig_sin, summary_sin = bar_chart(sample_df, x="categoria", y="ventas", agg="sum")
    fig_con, summary_con = bar_chart(sample_df, x="categoria", y="ventas", agg="sum", group_by=None)
    assert summary_sin == summary_con
    ax_sin, ax_con = fig_sin.axes[0], fig_con.axes[0]
    etiquetas_sin = [t.get_text() for t in ax_sin.get_xticklabels()]
    etiquetas_con = [t.get_text() for t in ax_con.get_xticklabels()]
    assert etiquetas_sin == etiquetas_con


def test_line_chart_sin_group_by_comportamiento_identico_al_actual(sample_df):
    """Sin group_by, line_chart se comporta exactamente igual que antes (retrocompatible)."""
    fig_sin, summary_sin = line_chart(sample_df, x="categoria", y="ventas", agg="sum")
    fig_con, summary_con = line_chart(sample_df, x="categoria", y="ventas", agg="sum", group_by=None)
    assert summary_sin == summary_con
    assert len(fig_sin.axes[0].lines) == len(fig_con.axes[0].lines)


def test_bar_chart_group_by_igual_a_x_lanza_chart_error(dos_campanas_df):
    with pytest.raises(ChartError, match="group_by"):
        bar_chart(dos_campanas_df, x="mes", y="valor", agg="sum", group_by="mes")


def test_line_chart_group_by_igual_a_x_lanza_chart_error(dos_campanas_df):
    with pytest.raises(ChartError, match="group_by"):
        line_chart(dos_campanas_df, x="mes", y="valor", agg="sum", group_by="mes")


def test_group_by_con_top_n_lanza_chart_error(dos_campanas_df):
    with pytest.raises(ChartError):
        bar_chart(dos_campanas_df, x="mes", y="valor", agg="sum", group_by="campana", top_n=1)


def test_group_by_con_reference_line_lanza_chart_error(dos_campanas_df):
    with pytest.raises(ChartError):
        bar_chart(
            dos_campanas_df, x="mes", y="valor", agg="sum", group_by="campana", reference_line="mean"
        )


def test_date_from_date_to_no_se_bypasea_cuando_x_es_la_columna_fecha(filterable_df):
    """date_from/date_to filtran la columna Fecha; si x es la propia columna Fecha, las
    fechas fuera del rango pedido no deben reaparecer en el summary como n=0 (TECH-153)."""
    fig, summary = line_chart(
        filterable_df,
        x="Fecha",
        y="valor",
        agg="mean",
        date_from="2023-01-01",
        date_to="2023-12-31",
    )
    assert isinstance(fig, Figure)
    assert "n=0" not in summary
    assert "sin datos" not in summary
    assert "2022" not in summary
