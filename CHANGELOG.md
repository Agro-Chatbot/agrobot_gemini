# Changelog

Todos los cambios relevantes de este proyecto se registran en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/), agrupado por
fecha (sin versionado semántico). Las decisiones de producto se citan por su ADR local en
`docs/decisiones/` (por ejemplo `ADR-021`); las referencias a tickets o ADR del coordinador
(`01-Coordinador-Charls_firstclass`) llevan el prefijo `molde-personal:`.

Versionado: este CHANGELOG se mantiene a mano. Propuesta pendiente de decisión del usuario:
trackear `CHANGELOG.md` en git (hoy está untracked y `.gitignore` no lo excluye), pero no el
tooling local de sanity (`.claude/`, `.locks/`, `SANITY.md`, `history/`, `monitoring/`,
`run-sanity.sh`, `scripts/`). No se ejecutó ningún `git add` ni `git commit`.

## [Sin publicar]

### Changed
- Python fijado en 3.11 (ADR-001): `requires-python` pasa a `>=3.11` y el proyecto usa un
  `.venv` local (ignorado por git); el sanity-auditor corre los tests con
  `.venv/bin/python -m pytest -q` (molde-personal: TECH-134).

- Renombre de la carpeta del proyecto (`molde-personal:TECH-103`, según
  `molde-personal:ADR-021`).
- Reescritura manual de `docs/api_src_chatbot.md` (`molde-personal:TECH-130`) leyendo el código
  de `src/chatbot/`: el doc quedó alineado con el código actual.

### Added
- Infraestructura local de sanity check del proyecto (S-21): `.claude/`, `run-sanity.sh`,
  `scripts/`, `monitoring/`, `history/`, `SANITY.md` y `.locks/`. Es una herramienta local de
  desarrollo: hoy está sin versionar (untracked) y no forma parte de la publicación.

## 2026-09-15

Publicación inicial de AgroBot-Hank (commit `721d9af`).

### Added
- Chatbot de análisis de datos forrajeros/ganaderos para usuario rural no técnico: recibe
  consultas en lenguaje natural sobre un CSV de tasas de crecimiento de pasturas y responde con
  un gráfico y un texto que lo explica.
- Flujo consulta -> Claude (Anthropic) elige una tool de graficado predefinida con parámetros
  validados vía tool use -> pandas + Matplotlib generan el gráfico -> Claude explica los datos
  agregados -> Streamlit muestra gráfico y texto. El modelo no ejecuta código generado
  (`ADR-002`, `ADR-004`).
- Tools predefinidas de graficado en `src/chatbot/charts/`: `bar_chart`, `line_chart`,
  `scatter_plot`, `histogram`, `pie_chart` y `soporte_animal`, con validación de parámetros,
  filtros compuestos multivalor (`ADR-034`) y comparación de series por `group_by` (`ADR-036`).
- Cálculo de soporte animal (`ADR-010`) y equivalencias EV por categoría (`ADR-038`).
- System prompt organizado como paquete de secciones en `src/chatbot/prompt/` (`ADR-032`),
  con buckets de recurso (`ADR-035`) y respuestas sin tool call (`ADR-037`).
- Interfaz Streamlit (`app.py`) con chat e historial de sesión (`ADR-003`), superficie visual
  (`ADR-021`) y estilo minimalista (`ADR-022`).
- Convenciones de dominio: campaña forrajera como año calendario (`ADR-006`), estaciones del
  hemisferio sur (`ADR-007`) y columnas derivadas con binning temporal (`ADR-008`).
- Dataset sintético `data/sample.csv` (semilla fija) con el esquema `Fecha, CREA, Campo, Lote,
  Recurso, Kg MS ha/día, Superficie ha`; `CSV_PATH` configurable vía `.env`.
- Tests con `pytest` para `data.py` y `charts/` (sin necesidad de API key).
- Documentación: README, referencia de la API interna, flujo de producto con
  diagrama, golden set de preguntas de ejemplo, consignas y propuesta del TP, y ADR de
  producto en `docs/decisiones/`.
- Entorno Python 3.11 con pyenv (`ADR-001`) y licencia MIT (`LICENSE`).
