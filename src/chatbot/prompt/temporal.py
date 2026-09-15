"""Columnas derivadas disponibles: Anio, Estacion. Reglas de resolución de expresiones
temporales relativas ("hoy", "este mes", "últimos N años", "salida del invierno") contra la
última fecha con datos del dataset (TECH-148).
"""

SECCION = (
    "Columnas derivadas disponibles:\n"
    "- `Anio` (año como texto, ej: '2023'): año calendario (ene–dic). Usala como 'campaña' cuando el usuario pregunte por campañas o años.\n"
    "- `Estacion` (texto): estación del año. Valores posibles: Verano, Otoño, Invierno, Primavera (hemisferio sur).\n\n"
    "## Resolución de expresiones temporales relativas\n\n"
    "1. Expresiones relativas como \"hoy\", \"este mes\", \"este año\" o \"esta primavera\" se "
    "resuelven SIEMPRE contra la última fecha con datos del dataset (el máximo de `Fecha` que "
    "figura en el rango min → max del esquema) — NUNCA contra la fecha real del sistema, que "
    "puede no tener datos cargados todavía.\n"
    "2. Cuando resuelvas una expresión relativa a un rango concreto, declará en la explicación "
    "el `date_from`/`date_to` efectivamente usado, para que el usuario sepa a qué período "
    "concreto correspondió \"este mes\" o \"este año\".\n"
    "3. Si el período consultado cae en una campaña parcial, nombrala como parcial en la "
    "explicación — el esquema ya indica qué campañas son parciales en la línea \"Cobertura: "
    "...\"; leé ese dato de ahí, no lo inventes.\n"
    "4. \"últimos N años\" se traduce a un rango explícito `date_from`/`date_to` que termina en "
    "la última fecha con datos del esquema (no en la fecha del sistema ni en un valor fijo) y "
    "empieza N años calendario antes de esa fecha.\n"
    "5. \"salida del invierno\" es una expresión de dominio agronómico específica de este "
    "negocio: se traduce al rango `date_from=\"<año>-08-01\"` a `date_to=\"<año>-09-30\"`. "
    "Esto NO es lo mismo que `Estacion=Primavera` (que por definición del dataset corresponde a "
    "septiembre–noviembre) — no las uses como sinónimos."
)
