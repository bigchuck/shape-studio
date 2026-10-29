"""
BATCH run log for Shape Studio
Appends one JSON line per (BATCH, executable) to runs.jsonl in the output folder,
recording the executable and templates as they were at run time plus each
image's seed, randomization draws and resolved template commands.
Read back with tools/runlog.py.
"""
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

LOG_NAME = 'runs.jsonl'
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def read_runs(log_path):
    """Return the list of run records in a log, skipping unreadable lines"""
    log_path = Path(log_path)
    if not log_path.exists():
        return []
    runs = []
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                runs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return runs


def next_run_id(log_path):
    """Next sequential id (r0001, r0002, ...) for this log"""
    highest = 0
    for run in read_runs(log_path):
        match = re.fullmatch(r'r(\d+)', str(run.get('run', '')))
        if match:
            highest = max(highest, int(match.group(1)))
    return f"r{highest + 1:04d}"


def git_info():
    """Short commit and dirty flag of the project repo, or None if git is unavailable"""
    try:
        commit = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'], cwd=PROJECT_ROOT,
            capture_output=True, text=True, timeout=5, check=True
        ).stdout.strip()
        status = subprocess.run(
            ['git', 'status', '--porcelain'], cwd=PROJECT_ROOT,
            capture_output=True, text=True, timeout=5, check=True
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return {'commit': commit, 'dirty': bool(status.strip())}


def set_note(log_path, run_id, note):
    """Set the note of run_id (or the last run if None); return (run id, previous note)"""
    log_path = Path(log_path)
    runs = read_runs(log_path)
    if not runs:
        raise ValueError(f"No runs in {log_path}")
    if run_id is None:
        target = runs[-1]
    else:
        number = int(re.fullmatch(r'r?0*(\d+)', run_id, re.IGNORECASE).group(1))
        matches = [r for r in runs if re.fullmatch(rf'r0*{number}', str(r.get('run', '')))]
        if not matches:
            raise ValueError(f"Run {run_id} not found in {log_path}")
        target = matches[-1]
    previous = target.get('note')
    target['note'] = note
    tmp_path = log_path.with_suffix('.tmp')
    with open(tmp_path, 'w', encoding='utf-8') as f:
        for run in runs:
            f.write(json.dumps(run, default=str) + '\n')
    tmp_path.replace(log_path)
    return target['run'], previous


def append_run(log_path, record):
    """Assign the next run id to record, append it to the log, return the id"""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    run_id = next_run_id(log_path)
    line = {
        'run': run_id,
        'time': datetime.now().isoformat(timespec='seconds'),
        **record,
    }
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(line, default=str) + '\n')
    return run_id
