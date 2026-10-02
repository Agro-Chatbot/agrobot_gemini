#!/usr/bin/env python3
"""
sanity_report.py — registro y render del sanity-check de ingeniería del proyecto.

Fuente de verdad: monitoring/sanity/sanity.json (machine-readable; acumula la última
corrida por check + snapshot del backlog + mejoras propuestas). Render legible:
SANITY.md en la raíz del proyecto.

Subcomandos:
  snapshot                 imprime el conteo del backlog (ready/pending/blocked/done) como JSON.
  update --check C --status S [--findings N] [--summary T]
                           actualiza un check en sanity.json y sella su last_run.
  propose --title T --priority P [--source C] [--rationale R]
                           agrega una mejora a proposed_tickets.
  clear-proposals          vacía proposed_tickets (tras convertirlas en tickets del backlog).
  render [--stale-days N]  refresca snapshot del backlog + check `trazabilidad` + last_run global y
                           regenera SANITY.md.
  check-stale [--days N]   exit != 0 si la última corrida es más vieja que N días (o nunca corrió).

El agente `sanity-auditor` usa update/propose/render; run-sanity.sh / cron usan check-stale.
Autocontenido: no depende de placeholders de plantilla ni de librerías externas.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SANITY_JSON = REPO_ROOT / 'monitoring' / 'sanity' / 'sanity.json'
SANITY_MD = REPO_ROOT / 'SANITY.md'

# Orden y metadatos de los checks del tablero.
CHECKS = [
    ('architecture',  'Arquitectura',        'architect'),
    ('security',      'Seguridad',           'security-reviewer'),
    ('code_sanity',   'Code sanity',         'code-reviewer'),
    ('tests',         'Tests',               '—'),
    ('changelog_docs','Changelog/docs drift','architect'),
    ('trazabilidad',  'Trazabilidad',        'sanity_report.py'),
]
CHECK_LABEL = {k: label for k, label, _ in CHECKS}
DEFAULT_STALE_DAYS = 7
TIME_FMT = '%Y-%m-%d %H:%M'


def now_str():
    return datetime.now().strftime(TIME_FMT)


def find_registry():
    """Ubica el registro de tickets: layout del template (02-System/) o del propio toolkit (backlog/)."""
    for rel in ('02-System/tickets.json', 'backlog/tickets.json'):
        p = REPO_ROOT / rel
        if p.exists():
            return p
    return REPO_ROOT / '02-System' / 'tickets.json'


def backlog_snapshot():
    """Cuenta tickets por bucket. pending = pending + not_ready; cancelled se ignora."""
    snap = {'ready': 0, 'pending': 0, 'blocked': 0, 'done': 0}
    reg = find_registry()
    if not reg.exists():
        return snap
    try:
        tickets = json.loads(reg.read_text(encoding='utf-8')).get('tickets', [])
    except (json.JSONDecodeError, OSError):
        return snap
    for t in tickets:
        st = t.get('status', 'pending')
        if st == 'ready':
            snap['ready'] += 1
        elif st in ('pending', 'not_ready'):
            snap['pending'] += 1
        elif st == 'blocked':
            snap['blocked'] += 1
        elif st == 'done':
            snap['done'] += 1
    return snap


def default_doc():
    return {
        'version': '1.0',
        'last_run': None,
        'checks': [
            {'check': k, 'status': 'pending', 'findings': None, 'summary': '',
             'agent': agent, 'last_run': None}
            for k, _, agent in CHECKS
        ],
        'backlog': {'ready': 0, 'pending': 0, 'blocked': 0, 'done': 0},
        'proposed_tickets': [],
    }


def load_doc():
    if SANITY_JSON.exists():
        try:
            return json.loads(SANITY_JSON.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            sys.exit(f'Error: {SANITY_JSON} no es JSON válido.')
    return default_doc()


def save_doc(doc):
    SANITY_JSON.parent.mkdir(parents=True, exist_ok=True)
    SANITY_JSON.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def get_check(doc, name):
    return next((c for c in doc['checks'] if c['check'] == name), None)


def staleness(last_run, days):
    """Devuelve (is_stale, edad_en_dias|None). Nunca corrió → stale."""
    if not last_run:
        return True, None
    try:
        age = (datetime.now() - datetime.strptime(last_run, TIME_FMT)).days
    except ValueError:
        return True, None
    return age > days, age


def render_md(doc, stale_days=DEFAULT_STALE_DAYS):
    last = doc.get('last_run')
    is_stale, age = staleness(last, stale_days)
    if not last:
        fresh = 'nunca corrió'
    elif is_stale:
        fresh = f'VENCIDO (última corrida hace {age} días, umbral {stale_days})'
    else:
        fresh = f'fresco (hace {age} días)'

    lines = [
        '# Sanity check del proyecto',
        '',
        f'- **Última corrida:** {last or "—"}',
        f'- **Frescura:** {fresh}',
        '',
        '| Check | Estado | Hallazgos | Última corrida | Resumen |',
        '|---|---|---|---|---|',
    ]
    for c in doc['checks']:
        findings = '—' if c.get('findings') is None else c['findings']
        summary = (c.get('summary') or '').replace('|', '\\|').replace('\n', ' ')
        lines.append(
            f"| {CHECK_LABEL.get(c['check'], c['check'])} | {c.get('status', 'pending')} "
            f"| {findings} | {c.get('last_run') or '—'} | {summary} |"
        )

    b = doc.get('backlog', {})
    lines.append(
        f"| Tickets (ready / pending / blocked) | — "
        f"| {b.get('ready', 0)} / {b.get('pending', 0)} / {b.get('blocked', 0)} "
        f"| {last or '—'} | done: {b.get('done', 0)} |"
    )

    props = doc.get('proposed_tickets', [])
    lines += ['', '## Mejoras propuestas', '']
    if not props:
        lines.append('_Sin mejoras propuestas en la última corrida._')
    else:
        lines.append('| Título | Prioridad | Check origen | Motivo |')
        lines.append('|---|---|---|---|')
        for p in props:
            title = (p.get('title') or '').replace('|', '\\|')
            rationale = (p.get('rationale') or '').replace('|', '\\|').replace('\n', ' ')
            lines.append(
                f"| {title} | {p.get('priority', '')} "
                f"| {CHECK_LABEL.get(p.get('source_check', ''), p.get('source_check', '—'))} "
                f"| {rationale} |"
            )
    lines += ['', '> Generado por `scripts/sanity_report.py`. Fuente de verdad: '
              '`monitoring/sanity/sanity.json`. Las mejoras propuestas NO se crean como tickets '
              'automáticamente (regla de backlog).', '']
    SANITY_MD.write_text('\n'.join(lines), encoding='utf-8')


def trazabilidad_check(doc):
    """Check determinista de trazabilidad (TECH-061, molde-personal:ADR-017). Lo calcula `render`.

    Invoca scripts/trazabilidad.py check (no reimplementa la validación). Sin ese script el
    check queda `n/a`. Umbrales: colgantes > 0 -> fail; sin `origen` por encima de la línea de
    base (fijada la primera vez), sesiones bloqueadas sin motivo o vista vieja -> warn.
    """
    script = REPO_ROOT / 'scripts' / 'trazabilidad.py'
    prev = get_check(doc, 'trazabilidad') or {}
    if not script.exists():
        return {'status': 'n/a', 'findings': None,
                'summary': 'no disponible (sin scripts/trazabilidad.py)', 'metrics': None}

    r = subprocess.run([sys.executable, str(script), 'check'], cwd=REPO_ROOT,
                       capture_output=True, text=True)
    colgantes = ([l.strip('- ').strip() for l in r.stderr.splitlines()
                  if l.strip().startswith('-')] or [r.stderr.strip() or 'error'])\
        if r.returncode != 0 else []

    registry = find_registry()
    try:
        tickets = json.loads(registry.read_text(encoding='utf-8')).get('tickets', [])
    except (OSError, json.JSONDecodeError):
        tickets = []
    sin_origen = sum(1 for t in tickets if not t.get('origen'))
    base = (prev.get('metrics') or {}).get('sin_origen_base')
    if base is None:
        base = sin_origen

    sesiones_path = REPO_ROOT / '03-Sesiones' / 'sesiones.json'
    bloqueadas = []
    if sesiones_path.exists():
        try:
            ses = json.loads(sesiones_path.read_text(encoding='utf-8')).get('sesiones', [])
            bloqueadas = [x['sesion_id'] for x in ses
                          if x.get('estado') == 'bloqueada' and not x.get('motivo_bloqueo')]
        except (OSError, json.JSONDecodeError):
            pass

    vista = REPO_ROOT / 'docs' / 'trazabilidad.md'
    fuentes = [p for p in (registry, sesiones_path) if p.exists()]
    vieja = (not vista.exists()) or any(p.stat().st_mtime > vista.stat().st_mtime for p in fuentes)

    exceso = max(0, sin_origen - base)
    findings = len(colgantes) + exceso + len(bloqueadas) + (1 if vieja else 0)
    status = 'fail' if colgantes else ('warn' if findings else 'ok')
    partes = [f'colgantes {len(colgantes)}' + (f" ({'; '.join(colgantes[:3])})" if colgantes else ''),
              f'sin origen {sin_origen}/{len(tickets)} (base {base})',
              f'bloqueadas sin motivo {len(bloqueadas)}',
              f"vista {'DESACTUALIZADO' if vieja else 'al día'}"]
    return {'status': status, 'findings': findings, 'summary': ' · '.join(partes),
            'metrics': {'colgantes': colgantes, 'sin_origen': sin_origen, 'sin_origen_base': base,
                        'tickets': len(tickets), 'bloqueadas_sin_motivo': bloqueadas,
                        'vista_desactualizada': vieja}}


# --- subcomandos ------------------------------------------------------------

def cmd_snapshot(args):
    print(json.dumps(backlog_snapshot(), ensure_ascii=False))


def cmd_update(args):
    if args.check not in CHECK_LABEL:
        sys.exit(f"Error: check desconocido '{args.check}'. Válidos: {', '.join(CHECK_LABEL)}")
    doc = load_doc()
    c = get_check(doc, args.check)
    if c is None:
        c = {'check': args.check, 'agent': next((a for k, _, a in CHECKS if k == args.check), '—')}
        doc['checks'].append(c)
    c['status'] = args.status
    if args.findings is not None:
        c['findings'] = args.findings
    if args.summary is not None:
        c['summary'] = args.summary
    c['last_run'] = now_str()
    save_doc(doc)
    print(f"check '{args.check}' → {args.status}")


def cmd_propose(args):
    doc = load_doc()
    doc.setdefault('proposed_tickets', []).append({
        'title': args.title,
        'priority': args.priority,
        'source_check': args.source or '',
        'rationale': args.rationale or '',
    })
    save_doc(doc)
    print(f"propuesta agregada: {args.title}")


def cmd_clear_proposals(args):
    doc = load_doc()
    n = len(doc.get('proposed_tickets', []))
    doc['proposed_tickets'] = []
    save_doc(doc)
    print(f"proposed_tickets vaciado ({n} eliminadas)")


def cmd_render(args):
    doc = load_doc()
    doc['backlog'] = backlog_snapshot()
    c = get_check(doc, 'trazabilidad')
    if c is None:
        c = {'check': 'trazabilidad', 'agent': 'sanity_report.py'}
        doc['checks'].append(c)
    c.update(trazabilidad_check(doc))
    c['last_run'] = now_str()
    doc['last_run'] = now_str()
    save_doc(doc)
    render_md(doc, args.stale_days)
    print(f"SANITY.md regenerado (last_run {doc['last_run']})")


def cmd_check_stale(args):
    doc = load_doc()
    is_stale, age = staleness(doc.get('last_run'), args.days)
    if is_stale:
        when = f'hace {age} días' if age is not None else 'nunca corrió'
        print(f"VENCIDO: el sanity-check {when} (umbral {args.days}). Corré ./run-sanity.sh")
        sys.exit(1)
    print(f"fresco: última corrida hace {age} días (umbral {args.days})")


def main():
    p = argparse.ArgumentParser(description='Registro y render del sanity-check del proyecto.')
    sub = p.add_subparsers(dest='cmd', required=True)

    sub.add_parser('snapshot', help='Conteo del backlog como JSON.').set_defaults(func=cmd_snapshot)

    up = sub.add_parser('update', help='Actualiza un check y sella su last_run.')
    up.add_argument('--check', required=True)
    up.add_argument('--status', required=True, choices=['ok', 'warn', 'fail', 'pending'])
    up.add_argument('--findings', type=int, default=None)
    up.add_argument('--summary', default=None)
    up.set_defaults(func=cmd_update)

    pr = sub.add_parser('propose', help='Agrega una mejora a proposed_tickets.')
    pr.add_argument('--title', required=True)
    pr.add_argument('--priority', required=True)
    pr.add_argument('--source', default=None)
    pr.add_argument('--rationale', default=None)
    pr.set_defaults(func=cmd_propose)

    sub.add_parser('clear-proposals', help='Vacía proposed_tickets.').set_defaults(func=cmd_clear_proposals)

    rn = sub.add_parser('render', help='Regenera SANITY.md desde sanity.json.')
    rn.add_argument('--stale-days', type=int, default=DEFAULT_STALE_DAYS)
    rn.set_defaults(func=cmd_render)

    cs = sub.add_parser('check-stale', help='Exit != 0 si el reporte venció.')
    cs.add_argument('--days', type=int, default=DEFAULT_STALE_DAYS)
    cs.set_defaults(func=cmd_check_stale)

    args = p.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
