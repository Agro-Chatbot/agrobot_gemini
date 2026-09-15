"""Buckets de dominio sobre la columna `Recurso` (TECH-123, ADR-035).

No son columnas del dataset ni binning de `data.py` (ADR-008): son vocabulario de dominio
que el usuario nombra sin conocer los valores exactos del CSV. El agente traduce el bucket a
`filters` con los valores literales listados acá; nunca crea ni asume una columna
`GrupoRecurso`.
"""

SECCION = (
    "## Categorías agregadas de `Recurso` (\"pasturas implantadas\", \"verdeos\", etc.)\n\n"
    "El usuario puede pedir una categoría de dominio que agrupa varios valores de `Recurso` "
    "pero que no es, en sí misma, un valor de la columna. Estas categorías **no existen en el "
    "dataset**: traducilas a `filters` con la lista exacta de valores literales de abajo.\n\n"
    "- **\"pasturas implantadas\"** = estos 5 valores de `Recurso`: \"Pastura consociada\", "
    "\"Pastura de festuca\", \"Pastura de agropiro\", \"Pastura de agropiro y festuca\", "
    "\"Pastura base alfalfa\".\n"
    "- **\"verdeos\"** = estos 7 valores de `Recurso` (todos los \"Verdeo de *\"): "
    "\"Verdeo de invierno\", \"Verdeo de avena\", \"Verdeo de maiz\", \"Verdeo de triticale\", "
    "\"Verdeo de sorgo\", \"Verdeo de raigras\", \"Verdeo de verano\".\n"
    "- **\"promociones de raigrás\"** = \"Promocion de raigras\" y \"Promocion intensiva de "
    "raigras\". Es una categoría propia: **no forma parte de \"verdeos\"** aunque el nombre "
    "incluya \"raigrás\", ni de \"pasturas implantadas\".\n"
    "- **\"Silo de maiz\"** y **\"Campo natural\"** son, cada uno, su propia categoría: no "
    "pertenecen a ningún bucket de arriba.\n\n"
    "Al usar uno de estos buckets, armá `filters` con `col=\"Recurso\"` y `vals` igual a la "
    "lista completa de valores del bucket (no un subconjunto). En la explicación textual de la "
    "respuesta, **enumerá los valores concretos de `Recurso` que incluiste** — no te limites a "
    "nombrar el bucket."
)
