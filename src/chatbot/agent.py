"""Orquestación: consulta NL -> Claude elige tool -> gráfico -> explicación."""

import matplotlib.pyplot as plt

from . import config, prompt
from .charts import ChartError, run_tool, tool_schemas
from .llm import get_client

MAX_TOKENS = 1024
MAX_RETRIES = 1  # reintentos si Claude pasa params inválidos


def _system_prompt(schema: str) -> str:
    return prompt.system_prompt(schema)


def answer(query: str, df, schema: str):
    """Devuelve (fig, texto). `fig` es `None` si Claude responde sin elegir una tool
    (p.ej. pide una aclaración o indica que el dato no existe). Lanza `RuntimeError`
    solo ante fallos reales (ni tool ni texto, o reintentos de `ChartError` agotados).
    """
    client = get_client()
    messages = [{"role": "user", "content": query}]
    system = _system_prompt(schema)

    for attempt in range(MAX_RETRIES + 1):
        resp = client.messages.create(
            model=config.LLM_MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            tools=tool_schemas(),
            tool_choice={"type": "auto", "disable_parallel_tool_use": True},
            messages=messages,
        )

        tool_use = next((b for b in resp.content if b.type == "tool_use"), None)
        if tool_use is None:
            # Claude respondió sin elegir tool (caso distinto de params inválidos).
            text = "".join(b.text for b in resp.content if b.type == "text").strip()
            if text:
                return None, text
            raise RuntimeError(
                "Claude no eligió ninguna tool y tampoco devolvió texto."
            )

        try:
            fig, summary = run_tool(tool_use.name, df, dict(tool_use.input))
        except ChartError as e:
            # Devolver el error a Claude para que corrija los parámetros
            messages.append({"role": "assistant", "content": resp.content})
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": f"Error: {e}",
                            "is_error": True,
                        }
                    ],
                }
            )
            continue

        try:
            explanation = _explain(client, system, messages, resp.content, tool_use, summary)
        except Exception:
            plt.close(fig)
            raise
        return fig, explanation

    raise RuntimeError("No se pudo generar un gráfico válido tras varios intentos.")


def answer_trace(query: str, df, schema: str) -> dict:
    """Ejecuta el mismo loop agéntico que `answer` pero, en vez de devolver la figura,
    captura las tool calls que hace el agente (name + input, incluidos reintentos) y el
    texto de explicación. No renderiza ni guarda el gráfico.

    Devuelve {query, calls, summary, explanation, status} con
    status en {"ok", "no_tool", "failed"}. No lanza en los casos borde para no abortar un
    batch por una sola pregunta.
    """
    client = get_client()
    messages = [{"role": "user", "content": query}]
    system = _system_prompt(schema)
    calls: list[dict] = []

    # Forzamos una sola tool por turno (disable_parallel_tool_use): el diseño elige un
    # gráfico, y sin esto el agente a veces emite varios tool_use en paralelo y rompe el loop.
    for attempt in range(MAX_RETRIES + 1):
        resp = client.messages.create(
            model=config.LLM_MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            tools=tool_schemas(),
            tool_choice={"type": "auto", "disable_parallel_tool_use": True},
            messages=messages,
        )

        tool_use = next((b for b in resp.content if b.type == "tool_use"), None)
        if tool_use is None:
            text = "".join(b.text for b in resp.content if b.type == "text").strip()
            return {
                "query": query,
                "calls": calls,
                "summary": None,
                "explanation": text,
                "status": "no_tool",
            }

        call = {"name": tool_use.name, "input": dict(tool_use.input)}
        calls.append(call)

        try:
            fig, summary = run_tool(tool_use.name, df, dict(tool_use.input))
        except ChartError as e:
            call["error"] = str(e)
            messages.append({"role": "assistant", "content": resp.content})
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": f"Error: {e}",
                            "is_error": True,
                        }
                    ],
                }
            )
            continue

        # La tool call ya se resolvió (es lo que el doc quiere mostrar). Si el paso de
        # explicación falla —p. ej. el LLM no devuelve texto en esta corrida— igual
        # conservamos la llamada y los datos, con una nota en vez de abortar la pregunta.
        try:
            explanation = _explain(client, system, messages, resp.content, tool_use, summary)
            status = "ok"
        except Exception as e:  # noqa: BLE001
            explanation = f"_(El agente generó el gráfico; no devolvió texto explicativo: {e})_"
            status = "ok_sin_texto"
        finally:
            if fig is not None:
                plt.close(fig)
        return {
            "query": query,
            "calls": calls,
            "summary": summary,
            "explanation": explanation,
            "status": status,
        }

    return {
        "query": query,
        "calls": calls,
        "summary": None,
        "explanation": "",
        "status": "failed",
    }


def _explain(client, system, messages, assistant_content, tool_use, summary):
    messages = messages + [
        {"role": "assistant", "content": assistant_content},
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": (
                        f"Gráfico '{tool_use.name}' generado. Datos:\n{summary}\n\n"
                        "Explicá en 2-4 frases qué muestra el gráfico y el insight principal."
                    ),
                }
            ],
        },
    ]
    resp = client.messages.create(
        model=config.LLM_MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=messages,
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    if not text:
        raise RuntimeError("Claude no devolvió texto en la explicación.")
    return text
