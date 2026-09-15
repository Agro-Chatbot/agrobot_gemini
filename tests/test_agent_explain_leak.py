"""Test que verifica que la figura se cierra cuando _explain lanza."""

from unittest.mock import MagicMock, patch

import matplotlib
import matplotlib.pyplot as plt
import pytest

matplotlib.use("Agg")


def _make_tool_use_block(tool_name="bar_chart"):
    """Construye un objeto que simula un bloque tool_use del SDK de Anthropic."""
    block = MagicMock()
    block.type = "tool_use"
    block.id = "tu_test_001"
    block.name = tool_name
    block.input = {"x": "categoria", "y": "ventas", "agg": "sum"}
    return block


def _make_sdk_response(content_blocks):
    """Construye un objeto que simula la respuesta de client.messages.create."""
    resp = MagicMock()
    resp.content = content_blocks
    return resp


def test_no_figure_leak_on_explain_error(monkeypatch):
    """Cuando _explain lanza, la figura creada por run_tool debe cerrarse."""
    import pandas as pd

    from chatbot.agent import answer

    df = pd.DataFrame({"categoria": ["A", "B"], "ventas": [10.0, 20.0]})
    schema = "categoria (object), ventas (float64)"

    tool_use_block = _make_tool_use_block()
    sdk_resp = _make_sdk_response([tool_use_block])

    # Mock del cliente Anthropic: primera llamada devuelve tool_use
    mock_client = MagicMock()
    mock_client.messages.create.return_value = sdk_resp

    # Mock de get_client para que devuelva nuestro cliente falso
    monkeypatch.setattr("chatbot.agent.get_client", lambda: mock_client)

    # Limpiar estado global de figuras antes de crear la figura de prueba
    plt.close("all")

    # Mock de run_tool para que devuelva una figura real (así hay algo que cerrar)
    real_fig = plt.figure()

    def fake_run_tool(name, df, params):
        return real_fig, "datos de prueba"

    monkeypatch.setattr("chatbot.agent.run_tool", fake_run_tool)

    # Mock de _explain para que lance
    def fake_explain(*args, **kwargs):
        raise RuntimeError("fallo simulado en _explain")

    monkeypatch.setattr("chatbot.agent._explain", fake_explain)

    # Antes del error, la figura existe
    assert real_fig.number in plt.get_fignums()

    with pytest.raises(RuntimeError, match="fallo simulado en _explain"):
        answer(query="mostrar ventas por categoria", df=df, schema=schema)

    # Después del error, la figura debe estar cerrada
    assert plt.get_fignums() == []
