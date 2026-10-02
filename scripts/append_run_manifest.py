#!/usr/bin/env python3
"""
Append one line to the run manifest (history/runs.jsonl) after a headless run
(run-ticket.sh / run-parallel.sh / run-sanity.sh) and print a human-readable
cost summary line to stdout.

Usage:
  python3 scripts/append_run_manifest.py \
    --repo-root <path> --history-file <path> --run-id <id> \
    --mode ticket|parallel|sanity --wave-id <id-or-empty> \
    --started-at <iso8601> --ended-at <iso8601> --status done|blocked|unknown \
    [--ticket-id <TID>]

`--ticket-id` omitted (or empty) → ticket_id is recorded as null (used by
run-sanity.sh, which has no associated ticket).

Reads the raw `claude --output-format json` payload from --history-file (if
present and valid) to pull total_cost_usd, modelUsage, num_turns,
duration_ms, duration_api_ms, subagent_stats, session_id, is_error and
terminal_reason. Missing/invalid payload degrades gracefully (fields stay
null) rather than failing the run.

Concurrency: multiple runs may finish at the same time (parallel waves), so
the append is serialized with flock on .locks/runs.lock — same pattern as
scripts/update_ticket_status.py's registry lock.
"""
import argparse
import fcntl
import json
import sys
from pathlib import Path


def read_project_slug(repo_root: Path) -> str:
    settings = repo_root / '.claude/settings.json'
    try:
        data = json.loads(settings.read_text(encoding='utf-8'))
        return data.get('env', {}).get('PROJECT_SLUG', '') or repo_root.name
    except Exception:
        return repo_root.name


def read_history_payload(history_file: Path) -> dict:
    try:
        return json.loads(history_file.read_text(encoding='utf-8'))
    except Exception:
        return {}


def build_model_usage(raw_model_usage: dict) -> dict:
    model_usage = {}
    for model, u in (raw_model_usage or {}).items():
        model_usage[model] = {
            'input': u.get('inputTokens'),
            'output': u.get('outputTokens'),
            'cache_read': u.get('cacheReadInputTokens'),
            'cache_write': u.get('cacheCreationInputTokens'),
            'cost_usd': u.get('costUSD'),
        }
    return model_usage


def build_summary_line(entry: dict) -> str:
    cost = entry['total_cost_usd']
    cost_str = f'USD {cost:.4f}' if isinstance(cost, (int, float)) else 'USD ?'

    turns = entry['num_turns']
    turns_str = f'{turns} turnos' if isinstance(turns, int) else '? turnos'

    dur_ms = entry['duration_ms']
    if isinstance(dur_ms, (int, float)):
        total_s = int(dur_ms / 1000)
        m, s = divmod(total_s, 60)
        dur_str = f'{m}m{s}s' if m else f'{s}s'
    else:
        dur_str = '?'

    by_type = (entry['subagent_stats'] or {}).get('by_type') or {}
    sub_str = ', '.join(f'{k}×{v}' for k, v in by_type.items()) if by_type else 'ninguno'

    return f'Costo: {cost_str} · {turns_str} · {dur_str} · subagentes: {sub_str}'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', required=True)
    parser.add_argument('--history-file', required=True)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--ticket-id', default='')
    parser.add_argument('--mode', required=True)
    parser.add_argument('--wave-id', default='')
    parser.add_argument('--started-at', required=True)
    parser.add_argument('--ended-at', required=True)
    parser.add_argument('--status', required=True)
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    history_file = Path(args.history_file)

    payload = read_history_payload(history_file)
    subagent_stats_raw = payload.get('subagent_stats') or {}

    try:
        history_rel = str(history_file.relative_to(repo_root))
    except ValueError:
        history_rel = str(history_file)

    entry = {
        'run_id': args.run_id,
        'ticket_id': args.ticket_id or None,
        'session_id': payload.get('session_id'),
        'mode': args.mode,
        'wave_id': args.wave_id,
        'project': read_project_slug(repo_root),
        'project_root': str(repo_root),
        'started_at': args.started_at,
        'ended_at': args.ended_at,
        'status': args.status,
        'is_error': payload.get('is_error'),
        'terminal_reason': payload.get('terminal_reason'),
        'total_cost_usd': payload.get('total_cost_usd'),
        'num_turns': payload.get('num_turns'),
        'duration_ms': payload.get('duration_ms'),
        'duration_api_ms': payload.get('duration_api_ms'),
        'model_usage': build_model_usage(payload.get('modelUsage')),
        'subagent_stats': {
            'spawned': subagent_stats_raw.get('spawned'),
            'completed': subagent_stats_raw.get('completed'),
            'failed': subagent_stats_raw.get('failed'),
            'by_type': subagent_stats_raw.get('by_type'),
        },
        'history_file': history_rel,
    }

    manifest_dir = repo_root / 'history'
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / 'runs.jsonl'
    lock_path = repo_root / '.locks' / 'runs.lock'
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    lock_fd = open(lock_path, 'a')
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        with open(manifest_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()

    print(build_summary_line(entry))


if __name__ == '__main__':
    main()
