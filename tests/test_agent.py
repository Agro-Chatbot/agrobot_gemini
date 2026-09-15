"""Tests para chatbot.agent.answer con mocks del SDK de Anthropic."""

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import pytest
from unittest.mock import MagicMock

matplotlib.use("Agg")


# ---------------------------------------------------------------------------
# Helpers para construir objetos falsos del SDK
# ---------------------------------------------------------------------------

def _make_tool_use_block(name="bar_chart", tool_id="tu_001"):
    b = MagicMock()
    b.type = "tool_use"
    b.id = tool_id
    b.name = name
    b.input = {"x": "categoria", "y": "ventas", "agg": "sum"}
    return b


def _make_text_block(text="Aquí el análisis."):
    b = MagicMock()
    b.type = "text"
    b.text = text
    return b


def _make_sdk_response(content_blocks):
    resp = MagicMock()
    resp.content = content_blocks
    return resp


# ---------------------------------------------------------------------------
# Fixtures compartidos
# ---------------------------------------------------------------------------

@pytest.fixture
def minimal_df():
    return pd.DataFrame({"categoria": ["A", "B"], "ventas": [10.0, 20.0]})


@pytest.fixture
def schema():
    return "categoria (object), ventas (float64)"


@pytest.fixture(autouse=True)
def close_all_figures():
    """Cierra todas las figuras antes y después de cada test."""
    plt.close("all")
    yield
    plt.close("all")


# ---------------------------------------------------------------------------
# Test 1: camino feliz — Claude elige tool válida → devuelve (fig, texto)
# ---------------------------------------------------------------------------

def test_answer_happy_path(monkeypatch, minimal_df, schema):
    """Claude elige una tool válida: answer debe devolver (fig, texto)."""
    from matplotlib.figure import Figure
    from chatbot.agent import answer

    tool_block = _make_tool_use_block()
    sdk_resp_tool = _make_sdk_response([tool_block])
    sdk_resp_explain = _make_sdk_response([_make_text_block("Análisis correcto.")])

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [sdk_resp_tool, sdk_resp_explain]

    monkeypatch.setattr("chatbot.agent.get_client", lambda: mock_client)

    fake_fig = plt.figure()

    def fake_run_tool(name, df, params):
        return fake_fig, "resumen de datos"

    monkeypatch.setattr("chatbot.agent.run_tool", fake_run_tool)

    fig, text = answer("mostrar ventas por categoria", minimal_df, schema)

    assert isinstance(fig, Figure)
    assert text == "Análisis correcto."
    plt.close(fig)


# ---------------------------------------------------------------------------
# Test 2: ChartError en primer intento + reintento exitoso → devuelve (fig, texto)
# ---------------------------------------------------------------------------

def test_answer_chart_error_then_retry_success(monkeypatch, minimal_df, schema):
    """ChartError en attempt 0, éxito en attempt 1 → devuelve (fig, texto)."""
    from matplotlib.figure import Figure
    from chatbot.charts import ChartError
    from chatbot.agent import answer

    tool_block_1 = _make_tool_use_block(tool_id="tu_001")
    tool_block_2 = _make_tool_use_block(tool_id="tu_002")
    sdk_resp_1 = _make_sdk_response([tool_block_1])
    sdk_resp_2 = _make_sdk_response([tool_block_2])
    sdk_resp_explain = _make_sdk_response([_make_text_block("Reintento exitoso.")])

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [sdk_resp_1, sdk_resp_2, sdk_resp_explain]

    monkeypatch.setattr("chatbot.agent.get_client", lambda: mock_client)

    call_count = {"n": 0}
    success_fig = plt.figure()

    def fake_run_tool(name, df, params):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise ChartError("columna inválida")
        return success_fig, "resumen ok"

    monkeypatch.setattr("chatbot.agent.run_tool", fake_run_tool)

    fig, text = answer("mostrar ventas por categoria", minimal_df, schema)

    assert isinstance(fig, Figure)
    assert text == "Reintento exitoso."
    assert call_count["n"] == 2
    plt.close(fig)


# ---------------------------------------------------------------------------
# Test 3: ChartError en ambos intentos → RuntimeError("No se pudo generar...")
# ---------------------------------------------------------------------------

def test_answer_chart_error_both_attempts(monkeypatch, minimal_df, schema):
    """ChartError en attempt 0 y 1 → RuntimeError con mensaje de reintentos agotados."""
    from chatbot.charts import ChartError
    from chatbot.agent import answer

    tool_block_1 = _make_tool_use_block(tool_id="tu_001")
    tool_block_2 = _make_tool_use_block(tool_id="tu_002")
    sdk_resp_1 = _make_sdk_response([tool_block_1])
    sdk_resp_2 = _make_sdk_response([tool_block_2])

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [sdk_resp_1, sdk_resp_2]

    monkeypatch.setattr("chatbot.agent.get_client", lambda: mock_client)

    def fake_run_tool(name, df, params):
        raise ChartError("error persistente")

    monkeypatch.setattr("chatbot.agent.run_tool", fake_run_tool)

    with pytest.raises(RuntimeError, match="No se pudo generar un gráfico válido"):
        answer("mostrar ventas por categoria", minimal_df, schema)


# ---------------------------------------------------------------------------
# Test 4a: respuesta sin tool_use pero con texto → (None, texto)
# ---------------------------------------------------------------------------

def test_answer_no_tool_use_devuelve_texto_sin_figura(monkeypatch, minimal_df, schema):
    """Claude responde sin elegir tool pero con texto → answer devuelve (None, texto)."""
    from chatbot.agent import answer

    text_block = _make_text_block("¿Podrías aclarar a qué lote te referís?")
    sdk_resp = _make_sdk_response([text_block])

    mock_client = MagicMock()
    mock_client.messages.create.return_value = sdk_resp

    monkeypatch.setattr("chatbot.agent.get_client", lambda: mock_client)

    # run_tool no debería llamarse; si se llama que falle con error claro
    monkeypatch.setattr("chatbot.agent.run_tool", lambda *a, **k: (_ for _ in ()).throw(AssertionError("run_tool no debe llamarse")))

    fig, text = answer("mostrar ventas por categoria", minimal_df, schema)

    assert fig is None
    assert text == "¿Podrías aclarar a qué lote te referís?"


# ---------------------------------------------------------------------------
# Test 4b: respuesta sin tool_use y sin texto → sigue lanzando RuntimeError
# ---------------------------------------------------------------------------

def test_answer_no_tool_use_sin_texto_raises(monkeypatch, minimal_df, schema):
    """Claude no elige tool y tampoco devuelve texto → RuntimeError (fallo real)."""
    from chatbot.agent import answer

    sdk_resp = _make_sdk_response([])

    mock_client = MagicMock()
    mock_client.messages.create.return_value = sdk_resp

    monkeypatch.setattr("chatbot.agent.get_client", lambda: mock_client)

    monkeypatch.setattr("chatbot.agent.run_tool", lambda *a, **k: (_ for _ in ()).throw(AssertionError("run_tool no debe llamarse")))

    with pytest.raises(RuntimeError):
        answer("mostrar ventas por categoria", minimal_df, schema)


# ---------------------------------------------------------------------------
# Test 4c: la primera llamada a messages.create usa tool_choice auto + disable_parallel
# ---------------------------------------------------------------------------

def test_answer_usa_tool_choice_auto_disable_parallel(monkeypatch, minimal_df, schema):
    """La primera llamada a client.messages.create debe usar
    tool_choice={"type": "auto", "disable_parallel_tool_use": True}."""
    from chatbot.agent import answer

    tool_block = _make_tool_use_block()
    sdk_resp_tool = _make_sdk_response([tool_block])
    sdk_resp_explain = _make_sdk_response([_make_text_block("Análisis correcto.")])

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [sdk_resp_tool, sdk_resp_explain]

    monkeypatch.setattr("chatbot.agent.get_client", lambda: mock_client)

    fake_fig = plt.figure()

    def fake_run_tool(name, df, params):
        return fake_fig, "resumen de datos"

    monkeypatch.setattr("chatbot.agent.run_tool", fake_run_tool)

    fig, text = answer("mostrar ventas por categoria", minimal_df, schema)
    plt.close(fig)

    first_call_kwargs = mock_client.messages.create.call_args_list[0].kwargs
    assert first_call_kwargs["tool_choice"] == {
        "type": "auto",
        "disable_parallel_tool_use": True,
    }


# ---------------------------------------------------------------------------
# Test 5: _explain devuelve texto vacío → RuntimeError("Claude no devolvió texto...")
# ---------------------------------------------------------------------------

def test_answer_explain_empty_text_raises(monkeypatch, minimal_df, schema):
    """Si _explain obtiene texto vacío de Claude → RuntimeError con mensaje específico."""
    from chatbot.agent import answer

    tool_block = _make_tool_use_block()
    sdk_resp_tool = _make_sdk_response([tool_block])
    # La segunda llamada (para _explain) devuelve bloque de texto vacío
    sdk_resp_explain = _make_sdk_response([_make_text_block("")])

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [sdk_resp_tool, sdk_resp_explain]

    monkeypatch.setattr("chatbot.agent.get_client", lambda: mock_client)

    fake_fig = plt.figure()

    def fake_run_tool(name, df, params):
        return fake_fig, "resumen de datos"

    monkeypatch.setattr("chatbot.agent.run_tool", fake_run_tool)

    with pytest.raises(RuntimeError, match="Claude no devolvió texto en la explicación"):
        answer("mostrar ventas por categoria", minimal_df, schema)

    assert plt.get_fignums() == [], "La figura debe haber sido cerrada por agent.answer() antes de relanzar la excepción"


# ---------------------------------------------------------------------------
# Test 6: answer_trace — _explain lanza → status "failed", sin propagación
# ---------------------------------------------------------------------------

def test_answer_trace_explain_raises_preserves_call(monkeypatch, minimal_df, schema):
    """Si _explain lanza, answer_trace no propaga ni descarta: conserva la tool call y los
    datos con status='ok_sin_texto', cierra la figura y deja una nota en explanation."""
    from unittest.mock import patch
    from chatbot.agent import answer_trace

    tool_block = _make_tool_use_block()
    sdk_resp_tool = _make_sdk_response([tool_block])

    mock_client = MagicMock()
    mock_client.messages.create.return_value = sdk_resp_tool

    monkeypatch.setattr("chatbot.agent.get_client", lambda: mock_client)

    fake_fig = plt.figure()

    def fake_run_tool(name, df, params):
        return fake_fig, "resumen de datos"

    monkeypatch.setattr("chatbot.agent.run_tool", fake_run_tool)

    with patch("chatbot.agent._explain", side_effect=RuntimeError("fallo en explain")):
        with patch("chatbot.agent.plt.close") as mock_close:
            result = answer_trace("mostrar ventas por categoria", minimal_df, schema)

    assert result["status"] == "ok_sin_texto"
    assert result["summary"] == "resumen de datos"
    assert len(result["calls"]) == 1
    assert "fallo en explain" in result["explanation"]
    assert result["query"] == "mostrar ventas por categoria"
    mock_close.assert_called_once_with(fake_fig)
