#!/usr/bin/env bash
# run-sanity.sh — corre el sanity-check de ingeniería del proyecto de forma headless.
#
# Uso:
#   ./run-sanity.sh
#
# Entrypoint: el coordinator (agente top-level durable) delega el chequeo en el sanity-auditor
# y sostiene el loop hasta consolidar. Se arranca desde el coordinator —y no desde el
# sanity-auditor directo— porque el auditor spawnea sus revisores de forma concurrente y cierra
# su turno tras el primer resultado (end_turn); en modo headless `-p` eso hacía salir el proceso
# antes de las Fases 2/3, dejando sanity.json sin consolidar. El coordinator mantiene el proceso
# vivo hasta que el sanity-check termina.
#
# El sanity-auditor recolecta arquitectura, seguridad, code sanity, tests y el snapshot del
# backlog; consolida monitoring/sanity/sanity.json, regenera SANITY.md y propone mejoras como
# tickets (sin crearlas).
#
# Programarlo (recurrente) — no lo instala este script, es acción del usuario:
#   # Linux/macOS con cron:  crontab -e  → todos los lunes 09:00
#   0 9 * * 1  cd /ruta/al/proyecto && ./run-sanity.sh >> monitoring/sanity/cron.log 2>&1
#   # macOS: alternativamente un LaunchAgent (~/Library/LaunchAgents) con StartCalendarInterval.
#
# Chequear si el reporte quedó viejo SIN re-correrlo (exit != 0 si venció):
#   python3 scripts/sanity_report.py check-stale --days 7

set -euo pipefail
# Sin esto, el harness mata los subagentes en background a los 600 s (TECH-051).
export CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS="${CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS:-0}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

HISTORY_DIR="$REPO_ROOT/history/sanity"
mkdir -p "$HISTORY_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
HISTORY_FILE="$HISTORY_DIR/sanity_${STAMP}.json"

# Modo de corrida para el manifiesto (history/runs.jsonl — schema documentado en la cabecera de
# run-ticket.sh). Una corrida de sanity no tiene ticket ni ola asociados.
export CLAUDE_RUN_MODE="sanity"
export CLAUDE_RUN_ID="$STAMP"
STARTED_AT="$(date +%Y-%m-%dT%H:%M:%S%z)"

# Marca de inicio (precisión de minuto, igual al TIME_FMT de sanity_report.py) para la
# verificación post-run: confirma que esta corrida —no una previa del mismo día— consolidó.
START_TS="$(date '+%Y-%m-%d %H:%M')"

PROMPT="Tu única tarea en esta corrida es orquestar el SANITY-CHECK de ingeniería del proyecto. \
NO es un ticket de código: no implementes, refactorices ni escribas código, y no crees tickets \
en el backlog. La única escritura permitida es la del reporte de sanity vía \
scripts/sanity_report.py (la hace el sanity-auditor).

Delegá el trabajo en el subagente \`sanity-auditor\` con esta instrucción y esperá (bloqueante) \
a que termine:

  \"Corré el sanity-check completo siguiendo tus instrucciones. IMPORTANTE: invocá a architect, \
security-reviewer y code-reviewer como llamadas Agent BLOQUEANTES en una sola tanda (foreground, \
en un mismo mensaje) y esperá a que los TRES devuelvan su resultado antes de consolidar — no los \
lances en background ni cierres tu turno mientras haya revisores pendientes. Después consolidá \
sanity.json (update de los 5 checks + render) y terminá proponiendo mejoras (propose) sin crearlas.\"

Mantené el loop vivo hasta que el sanity-check esté CONSOLIDADO. Consolidado significa: \
monitoring/sanity/sanity.json tiene last_run de hoy, los 5 checks (architecture, security, \
code_sanity, tests, changelog_docs) ya no están en 'pending', y SANITY.md quedó regenerado. Si el \
sanity-auditor devuelve un resultado parcial (p. ej. \"esperando architect y security-reviewer…\") \
sin haber consolidado, volvé a delegar / continuá hasta cerrar las 3 fases. No cierres tu turno \
con el sanity-check a medias.

Al final imprimí una línea de estado: \"SANITY: consolidado\" si sanity.json quedó con last_run de \
hoy y sin checks en pending, o \"SANITY: incompleto — <motivo>\" si no."

echo "Iniciando sanity-check (coordinator → sanity-auditor)..."
echo ""

# Arrancar desde el coordinator (mismo agente que usa run-ticket.sh) para sostener el loop.
# --name etiqueta la sesión — aparece en /resume y en la telemetría de tokens.
# El output crudo (--output-format json) queda persistido en history/ además de imprimirse.
claude \
  --agent coordinator \
  --name "sanity:${STAMP}" \
  --output-format json \
  -p "$PROMPT" \
  | tee "$HISTORY_FILE" || true

ENDED_AT="$(date +%Y-%m-%dT%H:%M:%S%z)"

echo ""
echo "Output crudo: $HISTORY_FILE"

# Verificación post-run (read-only): ¿esta corrida consolidó el tablero?
CONSOLIDATED=$(python3 -c "
import json, sys
from datetime import datetime
fmt = '%Y-%m-%d %H:%M'
try:
    d = json.load(open('monitoring/sanity/sanity.json'))
    lr = d.get('last_run')
    ok = bool(lr) and datetime.strptime(lr, fmt) >= datetime.strptime(sys.argv[1], fmt) \
         and all(c.get('status') != 'pending' for c in d['checks'])
    print('consolidado' if ok else 'incompleto')
except Exception:
    print('incompleto')
" "$START_TS" 2>/dev/null || echo "incompleto")

if [[ "$CONSOLIDATED" == "consolidado" ]]; then
  echo "Sanity-check consolidado. Reporte legible: SANITY.md    Registro: monitoring/sanity/sanity.json"
  RUN_STATUS="done"
else
  echo "ADVERTENCIA: el sanity-check NO quedó consolidado (sanity.json sin last_run fresco o con checks en pending)."
  echo "Revisá el output crudo: $HISTORY_FILE"
  RUN_STATUS="unknown"
fi

# is_error del JSON crudo pesa más que el chequeo de consolidación: un corte de API deja el
# sanity-check a medias sin importar qué diga sanity.json.
if [[ -f "$HISTORY_FILE" ]] && python3 -c "
import json, sys
try:
    sys.exit(0 if json.load(open(sys.argv[1])).get('is_error') else 1)
except Exception:
    sys.exit(1)
" "$HISTORY_FILE"; then
  RUN_STATUS="blocked"
fi

# Manifiesto de corridas (history/runs.jsonl) — sin ticket ni ola asociados.
python3 "$REPO_ROOT/scripts/append_run_manifest.py" \
  --repo-root "$REPO_ROOT" \
  --history-file "$HISTORY_FILE" \
  --run-id "$STAMP" \
  --mode "sanity" \
  --started-at "$STARTED_AT" \
  --ended-at "$ENDED_AT" \
  --status "$RUN_STATUS" \
  || echo "Advertencia: no se pudo actualizar el manifiesto de corridas (history/runs.jsonl)."
