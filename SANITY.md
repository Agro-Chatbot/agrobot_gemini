# Sanity check del proyecto

- **Última corrida:** 2026-10-01 21:57
- **Frescura:** fresco (hace 0 días)

| Check | Estado | Hallazgos | Última corrida | Resumen |
|---|---|---|---|---|
| Arquitectura | warn | 5 | 2026-10-01 21:57 | Capas sanas; duplicacion en agent.py y charts/basic.py, except Exception amplio, decisiones sin ADR |
| Seguridad | warn | 2 | 2026-10-01 21:57 | Sin secretos ni exec dinamico; P3: sin auth/limite de costo en Streamlit, artefactos locales sin ignorar |
| Code sanity | warn | 5 | 2026-10-01 21:57 | Loop duplicado answer/answer_trace, guarda faltante en soporte.py (tasa<=0), duplicacion en aggregate.py |
| Tests | ok | 0 | 2026-10-01 21:57 | 146 passed, 1 skipped |
| Changelog/docs drift | warn | 3 | 2026-10-01 21:57 | ADR citan 02-System/decisions.json inexistente; README/flujo_producto sin entrada en CHANGELOG; huecos de numeracion ADR |
| Trazabilidad | n/a | — | 2026-10-01 21:57 | no disponible (sin scripts/trazabilidad.py) |
| Tickets (ready / pending / blocked) | — | 0 / 0 / 0 | 2026-10-01 21:57 | done: 0 |

## Mejoras propuestas

| Título | Prioridad | Check origen | Motivo |
|---|---|---|---|
| Extraer loop comun de answer/answer_trace en agent.py | P2 | Code sanity | Duplicacion; cambios de flujo deben hacerse dos veces |
| Guardar ha_requeridas contra tasa_media<=0 y validar tipos en soporte.py (+tests) | P2 | Code sanity | Puede producir inf/negativos explicados como dato valido |
| Corregir referencias a 02-System/decisions.json en ADR y documentar huecos de numeracion | P2 | Changelog/docs drift | Referencia rota en ADR-001/009/021/037 |
| Ignorar en .gitignore history/, .locks/, *.egg-info/ y decidir versionado del tooling sanity | P2 | Seguridad | Artefactos con consultas/salidas LLM podrian commitearse |
| Registrar en CHANGELOG cambios de README y flujo_producto.md | P3 | Changelog/docs drift | Cambios sin entrada |
| Auth y tope de consultas/gasto si se expone la app Streamlit | P3 | Seguridad | ANTHROPIC_API_KEY consumible sin limite |
| Documentar como ADR: manejo de errores ChartError vs Exception | P3 | Arquitectura | Documentar como ADR; decision estructural sin ADR |
| Documentar como ADR: answer/answer_trace y singleton del cliente LLM | P3 | Arquitectura | Documentar como ADR; decision estructural sin ADR |

> Generado por `scripts/sanity_report.py`. Fuente de verdad: `monitoring/sanity/sanity.json`. Las mejoras propuestas NO se crean como tickets automáticamente (regla de backlog).
