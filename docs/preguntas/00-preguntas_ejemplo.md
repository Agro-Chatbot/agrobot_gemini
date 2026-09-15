# Preguntas de ejemplo — Dataset Tapalque II

Preguntas de ejemplo sobre el dataset `data/tapalqueii.csv`, organizadas por categoría
de caso de uso. La leyenda indica si la pregunta es respondible con las tools actuales.

**Leyenda:**
- ✅ Respondible hoy (tools actuales: `bar_chart`, `line_chart`, `scatter_plot`, `histogram`, `pie_chart`, `soporte_animal`)
- ⏳ Requiere capacidades futuras (ver tickets relacionados al pie)

> Ver `docs/preguntas/00-preguntas_respondidas.md` para el detalle de las llamadas (tool calls) reales
> que hace el agente ante cada pregunta ✅, generado con `scripts/demo_preguntas.py`.

---

## A. Tasas de crecimiento

1. ✅ ¿Cuál es la tasa de crecimiento promedio (Kg MS/ha/día) por tipo de recurso forrajero?
2. ✅ ¿Qué lotes tienen las mayores tasas de crecimiento promedio?
3. ✅ ¿Cómo evolucionó la tasa de crecimiento promedio a lo largo del tiempo?
4. ✅ ¿Cómo se distribuyen las tasas de crecimiento en todo el establecimiento?
5. ✅ ¿Qué campo tiene el mejor rendimiento forrajero promedio?

## B. Comparación entre campañas

6. ✅ ¿Cómo se comparan las tasas de crecimiento promedio entre campañas (2019–2026)?
7. ✅ ¿Qué campaña tuvo la mayor producción de materia seca acumulada?
8. ✅ ¿El campo natural rindió mejor en la campaña 2023 que en la 2024?
9. ✅ Comparar el rendimiento de las pasturas consociadas entre campañas.

## C. Impacto de sequía en el crecimiento del recurso

10. ⏳ ¿En qué períodos cayó marcadamente la tasa de crecimiento (posibles sequías)?
11. ✅ ¿Cómo impactó la sequía de 2022/2023 en el crecimiento del campo natural?
12. ✅ Comparar la tasa de crecimiento de un año seco contra un año normal.
13. ⏳ ¿Qué recursos fueron más resistentes a la caída de crecimiento en años secos?

## D. Soporte animal

14. ✅ ¿Cuántos animales puede soportar el lote X en este período?
15. ✅ ¿Cuántos animales soporta el conjunto de lotes de campo natural en un período dado?
16. ⏳ ¿Cuál es la carga animal soportable (EV/ha) promedio por campo?

## E. Demanda animal y raciones

17. ✅ ¿Cuánta materia seca produce por día el lote X para alimentar al rodeo? (Kg MS × Superficie)
18. ⏳ ¿Qué superficie de este recurso necesito para sostener N animales?

## F. Estacionalidad y composición del recurso

19. ✅ ¿Cómo varía la tasa de crecimiento según la estación del año?
20. ✅ ¿Qué proporción de la superficie total corresponde a cada tipo de recurso?

---

## Nota sobre el alcance actual de las tools

Hoy son respondibles las preguntas marcadas ✅ (14 de 20): las de una sola dimensión
(1–5, 20) más las que habilitaron las capacidades ya implementadas:

- **TECH-050** — Binning temporal por campaña/estación (`Anio`, `Estacion`): habilita B (6–9),
  parte de C (11, 12) y F (19).
- **TECH-051** — Filtros de fecha y categoría (`filter_col`/`filter_val`/`date_from`/`date_to`
  en todas las tools): habilita comparaciones acotadas a períodos.
- **TECH-052** — Tool `soporte_animal` (carga animal / EV soportados): habilita D (14, 15) y
  la producción de MS de E (17).

Las 6 preguntas que siguen marcadas ⏳ dependen de capacidades aún no implementadas:

- **10, 13** — detección de anomalías/tendencia (identificar automáticamente períodos de
  caída o comparar resiliencia entre recursos), más allá de un `groupby` de una dimensión.
- **16** — carga animal soportable promedio *por campo* (requiere agregación por campo, no
  por lote como hace hoy `soporte_animal`).
- **18** — demanda inversa (superficie necesaria para N animales): hoy solo se resuelve como
  cálculo en texto a partir del resumen, sin tool dedicada.
