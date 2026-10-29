"""
Run log analysis for Shape Studio BATCH runs (output/<dir>/runs.jsonl)

Usage (from the project root):
    python tools/runlog.py list    [--exec X] [--last N]
    python tools/runlog.py show    [RUN] [--image N]
    python tools/runlog.py diff    [RUN [RUN]]
    python tools/runlog.py varying [--exec X] [--last N]
    python tools/runlog.py report  [--exec X] [--last N] [-o FILE]

Common options:
    -d/--dir DIR   output folder (e.g. sa226) or runs.jsonl (default: newest log)
    --all          include keys disabled with a leading _
    --full         don't truncate long values

A run's settings are its merged template params (ops strings expanded to
ops[name] = weight), plus exec.* (executable fields), rand.* (randomization
specs) and tmpl.* (template fields). A param that differs between images of
one run was randomized and shows as "~ min..max". show marks where each param
came from: random, params, exec, global, template, ops_add or derived. diff
compares a run with the previous run of the same executable unless two runs
are given.
"""
import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.run_log import LOG_NAME, read_runs  # noqa: E402

# Executable / template fields that are documentation, not settings
META_FIELDS = {'description', 'author', 'created', 'comments'}
GROUP_ORDER = ('', 'exec.', 'rand.', 'tmpl.')
TRUNCATE = 60


class Random:
    """Marker for a param whose value varied between the images of one run"""

    def __init__(self, values):
        self.values = values

    def __str__(self):
        nums = [_as_float(v) for v in self.values]
        if all(n is not None for n in nums):
            low, high = min(nums), max(nums)
            if low == high:
                return f"~ {_fmt_num(low)}"
            return f"~ {_fmt_num(low)}..{_fmt_num(high)}"
        distinct = sorted({str(v) for v in self.values})
        return "~ {" + ", ".join(distinct) + "}"


def _as_float(value):
    if isinstance(value, bool):
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _fmt_num(n):
    return str(int(n)) if n == int(n) else f"{n:.4g}"


def canon(value):
    """Comparable form of a value: ".4", "0.4" and 0.4 are equal"""
    if isinstance(value, Random):
        return ('~random',)
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    number = _as_float(value)
    if number is not None:
        return ('num', number)
    text = str(value).strip()
    if text.lower() in ('true', 'false'):
        return text.lower()
    return re.sub(r'\s*,\s*', ',', text)


def display(value):
    if value is None:
        return '(unset)'
    if isinstance(value, (dict, list)):
        return json.dumps(value, separators=(',', ':'))
    return str(value)


def clip(text, full):
    return text if full or len(text) <= TRUNCATE else text[:TRUNCATE - 3] + '...'


def is_hidden(key):
    """True if any part of the key is disabled with a leading _"""
    return any(part.startswith('_') for part in re.split(r'[.\[\]:]', key) if part)


def _is_ops_key(key):
    return key.lstrip('_').endswith('ops')


def _parse_ops(value):
    """"a:1,b:2" -> {"a": "1", "b": "2"}, or None if not an ops string"""
    if not isinstance(value, str):
        return None
    ops = {}
    for token in value.split(','):
        token = token.strip()
        if not token:
            continue
        name, sep, weight = token.partition(':')
        if not sep:
            return None
        ops[name.strip()] = weight.strip()
    return ops


def _flatten_params(params):
    out = {}
    for key, value in params.items():
        ops = _parse_ops(value) if _is_ops_key(key) else None
        if ops is None:
            out[key] = value
        else:
            for name, weight in ops.items():
                out[f"{key}[{name}]"] = weight
    return out


def _good_images(run):
    with_steps = [img for img in run.get('images', []) if img.get('steps')]
    return [img for img in with_steps if 'error' not in img] or with_steps


def _step_prefix(steps, i):
    return f"{i + 1}:{steps[i]['template']}." if len(steps) > 1 else ''


def _param_sources(run):
    """{settings key: layer} for the param keys of a run

    Layers: random, params, exec (executable optional_params), global,
    template (template optional_params), ops_add, derived (set during the run).
    """
    images = _good_images(run)
    if not images:
        return {}
    steps = images[0]['steps']
    spec = run.get('exec_spec', {})
    commands = spec.get('commands', [])
    drawn = set().union(*[img.get('draws') or {} for img in images]) - set(overridden_draws(run))
    sources = {}
    for i, step in enumerate(steps):
        cmd = commands[i] if len(commands) == len(steps) and isinstance(commands[i], dict) else {}
        template = (run.get('templates') or {}).get(step['template']) or {}
        layers = [
            ('params', cmd.get('params', {})),
            ('exec', spec.get('optional_params', {})),
            ('global', run.get('global_params', {})),
            ('template', template.get('optional_params', {})),
        ]
        prefix = _step_prefix(steps, i)
        for key, value in step['params'].items():
            source = 'random' if key in drawn else next(
                (name for name, layer in layers if key in layer), 'derived')
            ops = _parse_ops(value) if _is_ops_key(key) else None
            if ops is None:
                sources[prefix + key] = source
                continue
            declared = dict(layers).get(source, {}).get(key)
            declared = _parse_ops(declared) or {}
            for op, weight in ops.items():
                from_layer = op in declared and canon(declared[op]) == canon(weight)
                sources[f"{prefix}{key}[{op}]"] = source if from_layer else 'ops_add'
    return sources


def settings(run):
    """Flat dict of everything that configured this run"""
    out = {}
    images = _good_images(run)
    if images:
        steps = images[0]['steps']
        random_keys = {key for key, source in _param_sources(run).items() if source == 'random'}
        values = {}
        for img in images:
            for i, step in enumerate(img['steps'][:len(steps)]):
                prefix = _step_prefix(steps, i)
                for key, value in _flatten_params(step['params']).items():
                    values.setdefault(prefix + key, []).append(value)
        for key, vals in values.items():
            constant = (key not in random_keys and len(vals) == len(images)
                        and len({canon(v) for v in vals}) == 1)
            out[key] = vals[0] if constant else Random(vals)

    spec = run.get('exec_spec', {})
    for field, value in spec.items():
        if field in META_FIELDS or field in ('commands', 'randomization', 'optional_params'):
            continue
        out[f"exec.{field}"] = value
    for i, cmd in enumerate(spec.get('commands', [])):
        if isinstance(cmd, dict):
            for field, value in cmd.items():
                if field != 'params':
                    out[f"exec.cmd{i + 1}.{field}"] = value
    for key, value in spec.get('randomization', {}).items():
        out[f"rand.{key}"] = value
    for name, template in (run.get('templates') or {}).items():
        for field, value in (template or {}).items():
            if field in META_FIELDS or field == 'optional_params':
                continue
            out[f"tmpl.{name}.{field}"] = value
    return out


def _sort_key(key):
    group = next((i for i, g in reversed(list(enumerate(GROUP_ORDER))) if key.startswith(g)), 0)
    return (group, key)


def overridden_draws(run):
    """Randomized keys whose draw was replaced by an explicit param: {key: value used}"""
    out = {}
    for img in _good_images(run):
        for key, drawn in (img.get('draws') or {}).items():
            for step in img['steps']:
                used = step['params'].get(key)
                if used is not None and canon(used) != canon(drawn):
                    out[key] = used
    return out


def changes(old, new, show_hidden=False):
    """[(key, old_value, new_value)] for keys whose settings differ"""
    a, b = settings(old), settings(new)
    out = []
    for key in sorted(set(a) | set(b), key=_sort_key):
        if not show_hidden and is_hidden(key):
            continue
        if key in a and key in b and canon(a[key]) == canon(b[key]):
            continue
        out.append((key, a.get(key), b.get(key)))
    return out


# --- run selection -----------------------------------------------------------

def find_log(path=None):
    """Resolve a folder or log path; default is the most recently written log"""
    if path:
        path = Path(path)
        if not path.is_absolute() and not path.exists():
            # Relative paths: project root, then the output folder (LOG SHOW -d sa226)
            candidates = [PROJECT_ROOT / path, PROJECT_ROOT / 'output' / path]
            path = next((p for p in candidates if p.exists()), candidates[-1])
        if path.is_dir():
            path = path / LOG_NAME
        if not path.exists():
            raise SystemExit(f"No run log at {path}")
        return path
    logs = sorted((PROJECT_ROOT / 'output').rglob(LOG_NAME), key=lambda p: p.stat().st_mtime)
    if not logs:
        raise SystemExit("No run logs found under output/")
    return logs[-1]


def _run_number(run_id):
    match = re.fullmatch(r'r?0*(\d+)', str(run_id).strip(), re.IGNORECASE)
    return int(match.group(1)) if match else None


def get_run(runs, run_id):
    number = _run_number(run_id)
    for run in runs:
        if _run_number(run['run']) == number:
            return run
    raise SystemExit(f"Run {run_id} not found")


def previous_run(runs, run):
    """Latest earlier run of the same script + executable, or None"""
    earlier = None
    for other in runs:
        if other is run:
            return earlier
        if (other.get('script'), other.get('executable')) == (run.get('script'), run.get('executable')):
            earlier = other
    return earlier


def select(runs, exec_name=None, last=None):
    if exec_name:
        runs = [r for r in runs if r.get('executable') == exec_name]
    return runs[-last:] if last else runs


# --- commands ----------------------------------------------------------------

def _image_range(run):
    indexes = [img['index'] for img in run.get('images', [])]
    if not indexes:
        return '-'
    return f"{min(indexes):04d}-{max(indexes):04d}"


def _git_label(run):
    git = run.get('git') or {}
    return f"{git.get('commit', '?')}{'*' if git.get('dirty') else ''}"


def _table(rows, header=None):
    rows = [header] + rows if header else rows
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    lines = ['  '.join(str(c).ljust(w) for c, w in zip(r, widths)).rstrip() for r in rows]
    if header:
        lines.insert(1, '  '.join('-' * w for w in widths))
    return lines


def cmd_list(runs, exec_name=None, last=None, show_hidden=False, **_):
    rows = []
    for run in select(runs, exec_name, last):
        prev = previous_run(runs, run)
        changed = len(changes(prev, run, show_hidden)) if prev else 'new'
        failed = sum(1 for img in run.get('images', []) if 'error' in img)
        images = f"{len(run.get('images', []))}" + (f" ({failed} failed)" if failed else '')
        flag = '!' if overridden_draws(run) else ''
        rows.append([run['run'], run.get('time', '').replace('T', ' '), run.get('executable', ''),
                     images, _image_range(run), f"{changed}{flag}", run.get('note') or ''])
    if not rows:
        return "No runs"
    lines = _table(rows, ['run', 'time', 'executable', 'images', 'range', 'changes', 'note'])
    if any(r[5].endswith('!') for r in rows):
        lines.append("! = a randomized param is overridden by params (see show)")
    return '\n'.join(lines)


def cmd_show(runs, run_id=None, image=None, show_hidden=False, full=False, **_):
    run = get_run(runs, run_id) if run_id else runs[-1]
    images = run.get('images', [])
    failed = sum(1 for img in images if 'error' in img)
    lines = [
        f"{run['run']}  {run.get('executable')}  ({run.get('script')})",
        f"  time     {run.get('time', '').replace('T', ' ')}",
        f"  command  {run.get('command')}",
        f"  git      {_git_label(run)}",
        f"  images   {len(images)} ({_image_range(run)})" + (f", {failed} failed" if failed else ''),
    ]
    if run.get('note'):
        lines.append(f"  note     {run['note']}")

    if image is not None:
        return '\n'.join(lines + [''] + _show_image(run, image))

    sources = _param_sources(run)
    rows = [[key, sources.get(key, ''), clip(display(value), full)]
            for key, value in sorted(settings(run).items(), key=lambda kv: _sort_key(kv[0]))
            if show_hidden or not is_hidden(key)]
    lines += ['', 'Settings:'] + ['  ' + line for line in _table(rows)]

    overridden = overridden_draws(run)
    if overridden:
        lines.append('')
        for key, used in overridden.items():
            lines.append(f"WARNING: '{key}' is randomized but params sets it to {display(used)}; the draw is ignored")
    errors = [img for img in images if 'error' in img]
    if errors:
        lines.append('')
        lines += [f"FAILED {img['index']:04d}: {img['error']}" for img in errors]
    return '\n'.join(lines)


def _show_image(run, image):
    wanted = str(image)
    for img in run.get('images', []):
        if wanted in (str(img['index']), f"{img['index']:04d}", img.get('png', '')):
            break
    else:
        raise SystemExit(f"Image {image} not in {run['run']} (images {_image_range(run)})")
    lines = [f"image {img['index']:04d}  {img.get('png') or 'FAILED: ' + img.get('error', '')}",
             f"  seed   {img['seed']}",
             f"  draws  {json.dumps(img.get('draws', {}))}"]
    for step in img.get('steps') or []:
        lines.append(f"  [{step['template']}]")
        lines += [f"    {display(c)}" for c in step['commands']]
    return lines


def cmd_diff(runs, run_a=None, run_b=None, show_hidden=False, full=False, **_):
    if run_a and run_b:
        old, new = get_run(runs, run_a), get_run(runs, run_b)
    else:
        new = get_run(runs, run_a) if run_a else runs[-1]
        old = previous_run(runs, new)
        if old is None:
            return f"{new['run']} is the first run of {new.get('executable')}; nothing to compare"
    header = (f"{old['run']} -> {new['run']}  {old.get('executable')}"
              + ('' if old.get('executable') == new.get('executable') else f" -> {new.get('executable')}"))
    lines = [header]
    if _git_label(old) != _git_label(new):
        lines.append(f"  git: {_git_label(old)} -> {_git_label(new)}")
    diff = changes(old, new, show_hidden)
    if not diff:
        lines.append("  no setting changes")
    rows = [[key, clip(display(a), full), '->', clip(display(b), full)] for key, a, b in diff]
    lines += ['  ' + line for line in _table(rows)] if rows else []
    return '\n'.join(lines)


def cmd_varying(runs, exec_name=None, last=10, show_hidden=False, full=False, **_):
    chosen = select(runs, exec_name, last)
    if len(chosen) < 2:
        return "Need at least two runs"
    per_run = [settings(run) for run in chosen]
    keys = set().union(*per_run)
    varying = [key for key in sorted(keys, key=_sort_key)
               if (show_hidden or not is_hidden(key))
               and len({canon(s[key]) if key in s else None for s in per_run}) > 1]
    if not varying:
        return f"No settings vary across {len(chosen)} runs"
    width = None if full else 24
    rows = [[key] + [clip(display(s.get(key)), True)[:width] for s in per_run] for key in varying]
    header = ['setting'] + [f"{run['run']}" for run in chosen]
    lines = _table(rows, header)
    execs = sorted({run.get('executable', '') for run in chosen})
    lines.insert(0, f"{len(varying)} varying settings across {len(chosen)} runs ({', '.join(execs)})")
    return '\n'.join(lines)


# --- HTML report ---------------------------------------------------------------

REPORT_NAME = 'runs_report.html'

REPORT_CSS = """
:root {
  --bg: #f7f7f5; --panel: #ffffff; --text: #1d1d1b; --muted: #6b6b66;
  --line: #e2e1dc; --accent: #2f6fb3; --changed: #fff2c2; --changed-text: #5a4500;
  --warn: #b5470b; --warn-bg: #fdebe0; --old: #9a3b3b; --new: #23703a; --thumb-bg: #ffffff;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #161614; --panel: #201f1d; --text: #e9e8e3; --muted: #9b9a93;
    --line: #34332f; --accent: #7fb0e6; --changed: #4a3d10; --changed-text: #ffe39a;
    --warn: #ffab7a; --warn-bg: #3d2415; --old: #f09a9a; --new: #8fd6a3; --thumb-bg: #ffffff;
  }
}
:root[data-theme="dark"] {
  --bg: #161614; --panel: #201f1d; --text: #e9e8e3; --muted: #9b9a93;
  --line: #34332f; --accent: #7fb0e6; --changed: #4a3d10; --changed-text: #ffe39a;
  --warn: #ffab7a; --warn-bg: #3d2415; --old: #f09a9a; --new: #8fd6a3; --thumb-bg: #ffffff;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
  font: 14px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 1200px; margin: 0 auto; padding: 24px 16px 64px; }
h1 { font-size: 22px; margin: 0 0 4px; }
h2 { font-size: 18px; margin: 40px 0 12px; padding-bottom: 6px; border-bottom: 2px solid var(--line); }
.meta, .muted { color: var(--muted); }
.controls { display: flex; flex-wrap: wrap; gap: 16px; align-items: center; margin: 16px 0; }
select, button { font: inherit; color: var(--text); background: var(--panel);
  border: 1px solid var(--line); border-radius: 6px; padding: 4px 8px; }
code, .mono, td.v { font-family: ui-monospace, "Cascadia Mono", Consolas, monospace; font-size: 12.5px; }
.scroll { overflow-x: auto; background: var(--panel); border: 1px solid var(--line); border-radius: 8px; }
table { border-collapse: collapse; width: 100%; }
th, td { text-align: left; padding: 4px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { font-weight: 600; color: var(--muted); white-space: nowrap; }
tr:last-child td { border-bottom: none; }
.varying td { white-space: nowrap; }
.varying td.chg { background: var(--changed); color: var(--changed-text); }
.varying a { color: var(--accent); text-decoration: none; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
  padding: 14px 16px; margin: 14px 0; scroll-margin-top: 16px; }
.card:target { outline: 2px solid var(--accent); }
.card-head { display: flex; flex-wrap: wrap; gap: 6px 16px; align-items: baseline; }
.run-id { font-size: 16px; font-weight: 700; }
.note { margin: 8px 0 0; font-style: italic; }
.warn { margin: 10px 0 0; padding: 6px 10px; border-radius: 6px; background: var(--warn-bg); color: var(--warn); }
.changes { margin-top: 10px; }
.changes .scroll { display: inline-block; max-width: 100%; }
.changes table { width: auto; }
a { color: var(--accent); }
.changes td.old { color: var(--old); }
.changes td.new { color: var(--new); }
.changes td.k, details td.k { font-family: ui-monospace, Consolas, monospace; font-size: 12.5px; white-space: nowrap; }
.thumbs { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.thumb { width: 112px; border: 1px solid var(--line); border-radius: 6px; background: var(--thumb-bg);
  padding: 0; cursor: pointer; overflow: hidden; }
.thumb img { width: 100%; aspect-ratio: 1; object-fit: contain; display: block; }
.thumb span { display: block; font-size: 11px; color: #555; background: #f0f0ec; padding: 1px 4px; }
.thumb.failed { display: flex; align-items: center; justify-content: center; aspect-ratio: 1;
  color: var(--warn); background: var(--warn-bg); font-size: 12px; cursor: default; }
details { margin-top: 12px; }
summary { cursor: pointer; color: var(--accent); }
details .scroll { margin-top: 8px; }
.src { color: var(--muted); font-size: 12px; }
body:not(.show-hidden) .hidden-key { display: none; }
.hidden-key td { opacity: .6; }
dialog { max-width: min(96vw, 1100px); width: 100%; border: 1px solid var(--line); border-radius: 10px;
  background: var(--panel); color: var(--text); padding: 16px; }
dialog::backdrop { background: rgba(0, 0, 0, .6); }
.viewer { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 16px; }
.viewer img { width: 100%; background: #fff; border-radius: 6px; }
.viewer pre { white-space: pre-wrap; word-break: break-all; margin: 8px 0 0; font-size: 12px;
  font-family: ui-monospace, Consolas, monospace; }
.viewer-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
@media (max-width: 720px) { .viewer { grid-template-columns: 1fr; } }
"""

REPORT_JS = """
const data = JSON.parse(document.getElementById('image-data').textContent);
const dlg = document.getElementById('viewer');
document.addEventListener('click', e => {
  const t = e.target.closest('.thumb[data-key]');
  if (!t) return;
  const d = data[t.dataset.key];
  dlg.querySelector('.v-title').textContent = d.title;
  dlg.querySelector('img').src = d.png;
  dlg.querySelector('.v-seed').textContent = d.seed;
  dlg.querySelector('.v-draws').textContent = d.draws;
  dlg.querySelector('.v-cmds').textContent = d.commands;
  dlg.showModal();
});
dlg.addEventListener('click', e => { if (e.target === dlg || e.target.matches('.close')) dlg.close(); });
const filter = document.getElementById('exec-filter');
filter.addEventListener('change', () => {
  document.querySelectorAll('section[data-exec]').forEach(s => {
    s.hidden = filter.value !== '' && s.dataset.exec !== filter.value;
  });
});
const hidden = document.getElementById('show-hidden');
const syncHidden = () => document.body.classList.toggle('show-hidden', hidden.checked);
hidden.addEventListener('change', syncHidden);
syncHidden();
"""


def _h(value):
    import html
    return html.escape(str(value), quote=True)


def _report_changes(old, new):
    rows = []
    for key, a, b in changes(old, new, show_hidden=True):
        cls = ' class="hidden-key"' if is_hidden(key) else ''
        rows.append(f'<tr{cls}><td class="k">{_h(key)}</td><td class="v old">{_h(display(a))}</td>'
                    f'<td class="muted">&rarr;</td><td class="v new">{_h(display(b))}</td></tr>')
    return rows


def _report_card(runs, run, image_data):
    rid = run['run']
    images = run.get('images', [])
    failed = sum(1 for img in images if 'error' in img)
    prev = previous_run(runs, run)
    parts = [f'<article class="card" id="{_h(rid)}">', '<div class="card-head">',
             f'<span class="run-id">{_h(rid)}</span>',
             f'<span class="muted">{_h(run.get("time", "").replace("T", " "))}</span>',
             f'<span class="muted">git <code>{_h(_git_label(run))}</code></span>',
             f'<span class="muted">{len(images)} images ({_h(_image_range(run))})'
             + (f', <span style="color:var(--warn)">{failed} failed</span>' if failed else '') + '</span>',
             '</div>']
    if run.get('note'):
        parts.append(f'<p class="note">{_h(run["note"])}</p>')
    for key, used in overridden_draws(run).items():
        parts.append(f'<p class="warn">&#9888; <code>{_h(key)}</code> is randomized but params sets it to '
                     f'<code>{_h(display(used))}</code>; the draw is ignored</p>')

    if prev is None:
        parts.append('<p class="muted changes">First run of this executable.</p>')
    else:
        rows = _report_changes(prev, run)
        label = f'Changed since <a href="#{_h(prev["run"])}">{_h(prev["run"])}</a>'
        if rows:
            parts.append(f'<div class="changes"><div class="muted">{label}</div><div class="scroll">'
                         f'<table>{"".join(rows)}</table></div></div>')
        else:
            parts.append(f'<p class="muted changes">{label}: no setting changes.</p>')

    parts.append('<div class="thumbs">')
    for img in images:
        if 'png' not in img:
            parts.append(f'<div class="thumb failed" title="{_h(img.get("error", ""))}">'
                         f'{img["index"]:04d} failed</div>')
            continue
        key = f"{rid}:{img['index']}"
        commands = [display(c) for step in img.get('steps') or [] for c in step['commands']]
        image_data[key] = {
            'title': f"{rid}  {img['png']}", 'png': img['png'], 'seed': str(img['seed']),
            'draws': json.dumps(img.get('draws', {})), 'commands': '\n\n'.join(commands),
        }
        parts.append(f'<button class="thumb" data-key="{_h(key)}" title="{_h(img["png"])}">'
                     f'<img loading="lazy" src="{_h(img["png"])}" alt="{_h(img["png"])}">'
                     f'<span>{img["index"]:04d}</span></button>')
    parts.append('</div>')

    sources = _param_sources(run)
    rows = []
    for key, value in sorted(settings(run).items(), key=lambda kv: _sort_key(kv[0])):
        cls = ' class="hidden-key"' if is_hidden(key) else ''
        rows.append(f'<tr{cls}><td class="k">{_h(key)}</td><td class="src">{_h(sources.get(key, ""))}</td>'
                    f'<td class="v">{_h(display(value))}</td></tr>')
    parts.append(f'<details><summary>All settings</summary><div class="scroll"><table>{"".join(rows)}'
                 f'</table></div></details>')
    parts.append(f'<p class="muted mono" style="margin:10px 0 0;font-size:11.5px">{_h(run.get("command"))}</p>')
    parts.append('</article>')
    return '\n'.join(parts)


def _report_varying(chosen):
    per_run = [settings(run) for run in chosen]
    keys = [key for key in sorted(set().union(*per_run), key=_sort_key)
            if len({canon(s[key]) if key in s else None for s in per_run}) > 1]
    if len(chosen) < 2 or not keys:
        return ''
    head = ''.join(f'<th class="{"hidden-key" if is_hidden(k) else ""}">{_h(k)}</th>' for k in keys)
    rows = []
    for i, (run, values) in enumerate(zip(chosen, per_run)):
        cells = []
        for key in keys:
            changed = i > 0 and canon(per_run[i - 1].get(key)) != canon(values.get(key))
            classes = ' '.join(c for c in ('chg' if changed else '', 'hidden-key' if is_hidden(key) else '') if c)
            text = display(values.get(key))
            short = text if len(text) <= 28 else text[:25] + '...'
            cells.append(f'<td class="v {classes}" title="{_h(text)}">{_h(short)}</td>')
        rows.append(f'<tr><td><a href="#{_h(run["run"])}">{_h(run["run"])}</a></td>{"".join(cells)}</tr>')
    return (f'<div class="muted" style="margin-bottom:6px">Settings that vary across these runs '
            f'(highlighted = changed from the run above)</div><div class="scroll"><table class="varying">'
            f'<tr><th>run</th>{head}</tr>{"".join(rows)}</table></div>')


def cmd_report(runs, exec_name=None, last=None, show_hidden=False, out=None, log=None, **_):
    from datetime import datetime
    chosen = select(runs, exec_name, last)
    if not chosen:
        return "No runs"
    out = Path(out) if out else Path(log).parent / REPORT_NAME

    by_exec = {}
    for run in chosen:
        by_exec.setdefault(run.get('executable', ''), []).append(run)
    # Most recently run executable first
    order = sorted(by_exec, key=lambda name: chosen.index(by_exec[name][-1]), reverse=True)

    image_data = {}
    sections = []
    for name in order:
        group = by_exec[name]
        cards = [_report_card(runs, run, image_data) for run in reversed(group)]
        sections.append(
            f'<section data-exec="{_h(name)}"><h2>{_h(name)} <span class="muted" style="font-weight:400;'
            f'font-size:14px">{len(group)} run{"s" if len(group) != 1 else ""} &middot; '
            f'{_h(group[0].get("script", ""))}</span></h2>{_report_varying(group)}{"".join(cards)}</section>')

    options = ''.join(f'<option value="{_h(n)}">{_h(n)}</option>' for n in order)
    rel_log = Path(log).resolve()
    try:
        rel_log = rel_log.relative_to(PROJECT_ROOT)
    except ValueError:
        pass
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Run Log Report</title>
<style>{REPORT_CSS}</style></head>
<body>
<main>
<h1>Run log</h1>
<div class="meta"><code>{_h(rel_log)}</code> &middot; {len(chosen)} runs &middot; generated {datetime.now():%Y-%m-%d %H:%M}</div>
<div class="controls">
  <label>Executable <select id="exec-filter"><option value="">All</option>{options}</select></label>
  <label><input type="checkbox" id="show-hidden"{' checked' if show_hidden else ''}> Show disabled (_) keys</label>
</div>
{''.join(sections)}
</main>
<dialog id="viewer"><div class="viewer-head"><strong class="v-title"></strong>
<button class="close" type="button">Close</button></div>
<div class="viewer"><img alt=""><div>
<div class="muted">seed</div><pre class="v-seed"></pre>
<div class="muted" style="margin-top:10px">draws</div><pre class="v-draws"></pre>
<div class="muted" style="margin-top:10px">commands</div><pre class="v-cmds"></pre>
</div></div></dialog>
<script type="application/json" id="image-data">{json.dumps(image_data).replace('</', '<\\/')}</script>
<script>{REPORT_JS}</script>
</body></html>
"""
    out.write_text(page, encoding='utf-8')
    return f"Report written to {out}"


COMMANDS = {'list': cmd_list, 'show': cmd_show, 'diff': cmd_diff, 'varying': cmd_varying,
            'report': cmd_report}


class _Parser(argparse.ArgumentParser):
    """Raise usage errors as SystemExit(message) so the app's LOG command can show them"""

    def error(self, message):
        raise SystemExit(f"{self.prog}: {message}")


def build_parser():
    common = _Parser(add_help=False)
    common.add_argument('-d', '--dir', help='output folder or runs.jsonl (default: newest log)')
    common.add_argument('--all', dest='show_hidden', action='store_true', help='include _disabled keys')
    common.add_argument('--full', action='store_true', help="don't truncate values")

    parser = _Parser(prog='runlog', description='Analyse BATCH run logs')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('list', parents=[common], help='one line per run')
    p.add_argument('--exec', dest='exec_name')
    p.add_argument('--last', type=int)
    p = sub.add_parser('show', parents=[common], help='all settings of a run')
    p.add_argument('run_id', nargs='?')
    p.add_argument('--image', help='image index or PNG name: seed, draws and resolved commands')
    p = sub.add_parser('diff', parents=[common], help='what changed between runs')
    p.add_argument('run_a', nargs='?')
    p.add_argument('run_b', nargs='?')
    p = sub.add_parser('varying', parents=[common], help='settings that changed across runs')
    p.add_argument('--exec', dest='exec_name')
    p.add_argument('--last', type=int, default=10)
    p = sub.add_parser('report', parents=[common], help='write an HTML report next to the log')
    p.add_argument('--exec', dest='exec_name')
    p.add_argument('--last', type=int)
    p.add_argument('-o', '--out', help=f'output file (default: {REPORT_NAME} next to the log)')
    return parser


def run_command(argv):
    """Run a runlog command line (list of args) and return its text output"""
    args = vars(build_parser().parse_args(argv))
    log = find_log(args.pop('dir'))
    runs = read_runs(log)
    if not runs:
        return f"No runs in {log}"
    return COMMANDS[args.pop('command')](runs, log=log, **args)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')
    print(run_command(sys.argv[1:]))


if __name__ == '__main__':
    main()
