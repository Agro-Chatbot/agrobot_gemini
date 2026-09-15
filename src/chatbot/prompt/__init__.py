"""System prompt del agente, ensamblado a partir de secciones por archivo (TECH-159).

Cada módulo de sección expone una constante `SECCION: str` (vacía si todavía no tiene
contenido), salvo `base`, que expone `seccion(schema)` porque necesita interpolar el
esquema del dataset. `system_prompt` concatena las secciones no vacías en orden fijo,
separadas por una línea en blanco.
"""

from . import (
    base,
    clima,
    filtros,
    ganaderia,
    graficos,
    limites,
    recursos,
    soporte,
    temporal,
    valores,
)

SECCIONES = (
    "base",
    "temporal",
    "valores",
    "filtros",
    "recursos",
    "graficos",
    "soporte",
    "ganaderia",
    "clima",
    "limites",
)


def system_prompt(schema: str) -> str:
    partes = [
        base.seccion(schema),
        temporal.SECCION,
        valores.SECCION,
        filtros.SECCION,
        recursos.SECCION,
        graficos.SECCION,
        soporte.SECCION,
        ganaderia.SECCION,
        clima.SECCION,
        limites.SECCION,
    ]
    return "\n\n".join(parte for parte in partes if parte)
