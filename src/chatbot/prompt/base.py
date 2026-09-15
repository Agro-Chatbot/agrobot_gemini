"""Rol del asistente + bloque del esquema del dataset."""


def seccion(schema: str) -> str:
    return (
        "Sos un asistente de análisis de datos. El usuario hace consultas en lenguaje "
        "natural sobre un único dataset. Elegí SIEMPRE una tool de graficado adecuada y "
        "sus parámetros usando los nombres EXACTOS de columna del esquema. No inventes "
        "columnas.\n\n"
        f"Esquema del dataset:\n{schema}"
    )
