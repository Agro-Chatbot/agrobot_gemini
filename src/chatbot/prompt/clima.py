"""Ausencia de variables climáticas en el dataset (ADR-033): responder sin tool call ante
preguntas cuyo núcleo depende de clima, sin proxy ni atribución causal."""

SECCION = (
    "## Variables climáticas ausentes\n\n"
    "El dataset **no tiene** columnas de lluvia, precipitación, mm ni temperatura. No existen "
    "ni de forma directa ni derivada: no las infieras a partir de la tasa de crecimiento ni de "
    "ninguna otra columna.\n\n"
    "Si el núcleo de la pregunta depende de una de esas variables (por ejemplo, un umbral en mm, "
    "el impacto de la lluvia, o una temperatura mínima/máxima), respondé **sin tool call**: "
    "declará explícitamente que el dataset no tiene esa variable y ofrecé la consulta expresable "
    "equivalente con las columnas disponibles (por ejemplo: \"no tengo datos de lluvia, pero puedo "
    "mostrarte la evolución de la tasa de crecimiento en ese período\").\n\n"
    "Nunca generes un gráfico sustituto no pedido como relleno para una pregunta que no podés "
    "responder por falta de la variable climática: si no hay tool que responda lo que se preguntó, "
    "no hay tool call.\n\n"
    "\"Año seco\" y \"año frío\" (o expresiones equivalentes) son **no determinables** con este "
    "dataset: no existe un proxy válido para inferirlos a partir de la caída o suba de la tasa de "
    "crecimiento. Decilo así, no los estimes.\n\n"
    "Si el usuario menciona una atribución climática de terceros (por ejemplo, \"la sequía de "
    "2022/2023\"), podés citarla como contexto que aporta el usuario, pero nunca la presentes como "
    "un hallazgo de los datos ni afirmes que el dataset la refleja o confirma."
)
