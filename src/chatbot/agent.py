"""Orquestación: consulta NL -> Gemini elige tool -> gráfico -> explicación."""

import matplotlib.pyplot as plt
from google.genai import types

from . import config, prompt
from .charts import ChartError, run_tool, tool_schemas
from .llm import get_client

# Gemini cuenta los tokens de "thinking" dentro de este límite: con 1024 puede
# devolver respuestas vacías o cortadas.
MAX_TOKENS = 4096
MAX_RETRIES = 2  # reintentos si Gemini pasa params inválidos


def _system_prompt(schema: str) -> str:
    return prompt.system_prompt(schema)


# --- Helpers específicos de Gemini -------------------------------------------------


def _gemini_tools() -> list[types.Tool]:
    """Convierte los schemas de las tools (formato Anthropic: name, description,
    input_schema) al formato de function calling de Gemini."""
    declarations = [
        types.FunctionDeclaration(
            name=s["name"],
            description=s.get("description", ""),
            parameters_json_schema=s["input_schema"],
        )
        for s in tool_schemas()
    ]
    return [types.Tool(function_declarations=declarations)]


def _generate(client, system: str, contents: list, allow_tools: bool = True):
    """Llama al modelo y devuelve el `Content` de la respuesta (rol "model").

    allow_tools=False declara las tools pero prohíbe llamarlas (modo NONE); se usa
    en la explicación final, donde el historial ya contiene llamadas a funciones.
    """
    gen_config = types.GenerateContentConfig(
        system_instruction=system,
        max_output_tokens=MAX_TOKENS,
        tools=_gemini_tools(),
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode="AUTO" if allow_tools else "NONE"
            )
        ),
        # El loop de tools lo manejamos nosotros, no el SDK.
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    resp = client.models.generate_content(
        model=config.LLM_MODEL, contents=contents, config=gen_config
    )
    candidate = resp.candidates[0] if resp.candidates else None
    if candidate is None or candidate.content is None:
        reason = candidate.finish_reason if candidate else resp.prompt_feedback
        raise RuntimeError(f"Gemini no devolvió contenido (motivo: {reason}).")
    return candidate.content


def _function_calls(content) -> list:
    return [p.function_call for p in (content.parts or []) if p.function_call]


def _text(content) -> str:
    return "".join(
        p.text for p in (content.parts or []) if p.text and not p.thought
    ).strip()


def _clean_args(value):
    """Gemini devuelve los números como float (5 -> 5.0). Los enteros exactos se
    convierten a int para que la validación de params de las tools no falle."""
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, dict):
        return {k: _clean_args(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean_args(v) for v in value]
    return value


def _tool_response(fcs: list, first_response: dict) -> types.Content:
    """Arma la respuesta a las llamadas de función. Gemini exige una respuesta por
    cada llamada del turno anterior: la primera lleva el resultado real y las
    demás (si el modelo emitió varias en paralelo) se marcan como no ejecutadas."""
    parts = [
        types.Part.from_function_response(name=fcs[0].name, response=first_response)
    ]
    for fc in fcs[1:]:
        parts.append(
            types.Part.from_function_response(
                name=fc.name,
                response={"error": "No ejecutada: se procesa una sola herramienta por turno."},
            )
        )
    return types.Content(role="user", parts=parts)


# --- Loop agéntico -----------------------------------------------------------------


def answer(query: str, df, schema: str):
    """Devuelve (fig, texto). `fig` es `None` si Gemini responde sin elegir una tool
    (p.ej. pide una aclaración o indica que el dato no existe). Lanza `RuntimeError`
    solo ante fallos reales (ni tool ni texto, o reintentos de `ChartError` agotados).
    """
    client = get_client()
    contents = [types.Content(role="user", parts=[types.Part(text=query)])]
    system = _system_prompt(schema)

    for attempt in range(MAX_RETRIES + 1):
        model_content = _generate(client, system, contents)

        fcs = _function_calls(model_content)
        if not fcs:
            # Gemini respondió sin elegir tool (caso distinto de params inválidos).
            text = _text(model_content)
            if text:
                return None, text
            raise RuntimeError(
                "Gemini no eligió ninguna tool y tampoco devolvió texto."
            )

        fc = fcs[0]
        args = _clean_args(dict(fc.args or {}))

        try:
            fig, summary = run_tool(fc.name, df, args)
        except ChartError as e:
            # Devolver el error a Gemini para que corrija los parámetros
            contents.append(model_content)
            contents.append(_tool_response(fcs, {"error": str(e)}))
            continue

        try:
            explanation = _explain(client, system, contents, model_content, fcs, summary)
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
    contents = [types.Content(role="user", parts=[types.Part(text=query)])]
    system = _system_prompt(schema)
    calls: list[dict] = []

    # Solo se procesa una tool por turno: si Gemini emite varias en paralelo, se
    # ejecuta la primera y las demás se devuelven como "no ejecutadas".
    for attempt in range(MAX_RETRIES + 1):
        model_content = _generate(client, system, contents)

        fcs = _function_calls(model_content)
        if not fcs:
            return {
                "query": query,
                "calls": calls,
                "summary": None,
                "explanation": _text(model_content),
                "status": "no_tool",
            }

        fc = fcs[0]
        args = _clean_args(dict(fc.args or {}))
        call = {"name": fc.name, "input": args}
        calls.append(call)

        try:
            fig, summary = run_tool(fc.name, df, args)
        except ChartError as e:
            call["error"] = str(e)
            contents.append(model_content)
            contents.append(_tool_response(fcs, {"error": str(e)}))
            continue

        # La tool call ya se resolvió (es lo que el doc quiere mostrar). Si el paso de
        # explicación falla —p. ej. el LLM no devuelve texto en esta corrida— igual
        # conservamos la llamada y los datos, con una nota en vez de abortar la pregunta.
        try:
            explanation = _explain(client, system, contents, model_content, fcs, summary)
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


def _explain(client, system, contents, model_content, fcs, summary):
    contents = contents + [
        model_content,
        _tool_response(
            fcs,
            {
                "result": (
                    f"Gráfico '{fcs[0].name}' generado. Datos:\n{summary}\n\n"
                    "Explicá en 2-4 frases qué muestra el gráfico y el insight principal."
                )
            },
        ),
    ]
    content = _generate(client, system, contents, allow_tools=False)
    text = _text(content)
    if not text:
        raise RuntimeError("Gemini no devolvió texto en la explicación.")
    return text