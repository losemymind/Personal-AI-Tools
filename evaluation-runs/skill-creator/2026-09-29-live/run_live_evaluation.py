"""Dev-only live evaluation. Calls the real local OpenCode binary; no stub responses.

Replays must use a NEW output root. Provider secrets stay in child environment only.
The committed HEAD product is extracted outside the repository as the old baseline.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PRODUCT = REPO / 'skill-creator/skills/skill-creator'
sys.path.insert(0, str(PRODUCT / 'scripts'))
import skill_eval
from skill_utils import run_client, parse_skill_md
from skill_events import stream_metrics

MODEL = 'deepseek/deepseek-flash'
EXE = Path(os.environ['LOCALAPPDATA']) / 'Programs/@openworkdesktop/resources/sidecars/opencode.exe'
ISOLATE_HOME = False


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def hashes(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()
            and '__pycache__' not in p.parts and p.suffix != '.pyc'}


def environment():
    root = Path(tempfile.mkdtemp(prefix='skill-live-env-'))
    env = os.environ.copy()
    for key, part in [('XDG_CONFIG_HOME', 'config'), ('XDG_DATA_HOME', 'data'),
                      ('XDG_STATE_HOME', 'state'), ('XDG_CACHE_HOME', 'cache')]:
        (root / part).mkdir()
        env[key] = str(root / part)
    # Read only the selected provider. Do not serialize its credentials to artifacts.
    config = json.loads((Path.home() / '.config/opencode/opencode.json').read_text(encoding='utf-8-sig'))
    public_config = {
        'model': MODEL, 'small_model': MODEL, 'share': 'disabled', 'autoupdate': False,
        'permission': {'*': 'allow', 'webfetch': 'deny', 'websearch': 'deny',
                       'question': 'deny', 'task': 'deny', 'external_directory': 'deny',
                       'skill': {'*': 'deny', 'skill-creator': 'allow', 'customize-opencode': 'allow'}},
        'mcp': {}, 'plugin': [], 'agent': {'build': {'steps': 24}},
    }
    env['OPENCODE_CONFIG_CONTENT'] = json.dumps({**public_config, 'provider': {'deepseek': config['provider']['deepseek']}})
    # Avoid inheriting custom roots/configuration that could reintroduce global skills.
    env.pop('OPENCODE_CONFIG', None)
    env.pop('OPENCODE_CONFIG_DIR', None)
    env['PYTHONUTF8'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PATH'] = str(EXE.parent) + os.pathsep + env.get('PATH', '')
    if ISOLATE_HOME:
        # Process-local user-directory isolation, verified by transcript audit.
        # This changes discovery and shell defaults; it is NOT an OS sandbox.
        for key, part in [('USERPROFILE', 'home'), ('APPDATA', 'home/AppData/Roaming'),
                          ('LOCALAPPDATA', 'home/AppData/Local')]:
            target = root / part
            target.mkdir(parents=True, exist_ok=True)
            env[key] = str(target)
    return root, env, public_config


def discovery(cwd, env):
    result = subprocess.run([str(EXE), '--pure', 'debug', 'skill'], cwd=cwd, env=env,
                            capture_output=True, encoding='utf-8', timeout=40, check=True)
    return [{k: item.get(k) for k in ('name', 'description', 'location')}
            for item in json.loads(result.stdout)]


def trigger(out, env):
    queries = json.loads((HERE / 'queries.json').read_text(encoding='utf-8'))
    name, desc, _ = parse_skill_md(PRODUCT)
    query_ids = {item['query']: item['id'] for item in queries}

    def capture(cmd, **kwargs):
        run = out / 'trigger/raw' / f"query-{query_ids[cmd[-1]]:02d}"
        run.mkdir(parents=True, exist_ok=False)
        state_root, child_env, _ = environment()
        try:
            found = discovery(kwargs['cwd'], child_env)
        except subprocess.CalledProcessError as error:
            (run / 'discovery-error.txt').write_text(error.stderr or '', encoding='utf-8')
            raise RuntimeError(f'discovery preflight exited {error.returncode}') from error
        save(run / 'discovery.json', found)
        installed = [s for s in found if s['name'] == name]
        if len(installed) != 1 or not Path(installed[0]['location']).resolve().is_relative_to(Path(kwargs['cwd']).resolve()):
            raise RuntimeError('Target discovery is not isolated')
        started = time.monotonic()
        timed_out = False
        rc = None
        stdout = stderr = ''
        try:
            rc, stdout, stderr = run_client([str(EXE), '--pure', *cmd[1:]], **{**kwargs, 'env': child_env})
            return rc, stdout, stderr
        except subprocess.TimeoutExpired as error:
            timed_out = True
            stdout, stderr = error.stdout or '', error.stderr or ''
            raise
        finally:
            (run / 'stdout.jsonl').write_text(stdout, encoding='utf-8')
            (run / 'stderr.txt').write_text(stderr, encoding='utf-8')
            save(run / 'execution.json', {'returncode': rc, 'timed_out': timed_out,
                 'state_root': str(state_root),
                 'duration_seconds': round(time.monotonic() - started, 3),
                 **stream_metrics(stdout + stderr, 'opencode')})
            print(f'trigger query {query_ids[cmd[-1]]}: rc={rc}, timeout={timed_out}', flush=True)

    # Observation wrapper around the unchanged real runner: only selects the
    # installed executable, --pure mode, isolated environment, and raw log capture.
    skill_eval.run_client = capture
    results = skill_eval.run_cli_batch(queries, name, desc, 'opencode', 120, MODEL,
                                      1, 0.5, concurrency=2, skill_dir=PRODUCT)
    report = {'skill_name': name, 'description': desc, 'mode': 'cli', 'client': 'opencode',
              'model': MODEL, 'model_source': 'requested', 'runs_per_query': 1,
              'threshold': 0.5, 'results': results, 'summary': skill_eval.summarize(results)}
    save(out / 'trigger/evaluation.json', report)
    print('TRIGGER_SUMMARY', json.dumps(report['summary']), flush=True)


def old_snapshot(root):
    prefix = 'skill-creator/skills/skill-creator/'
    archive = subprocess.run(['git', 'archive', '--format=zip', 'HEAD', prefix],
                             cwd=REPO, capture_output=True, check=True).stdout
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        z.extractall(root / 'old')
    return root / 'old' / prefix


def scenarios(out, env, root):
    items = json.loads((HERE / 'scenarios.json').read_text(encoding='utf-8'))
    old = old_snapshot(root)
    save(out / 'old-product-hashes.json', hashes(old))
    versions = {'with_skill': PRODUCT, 'old_skill': old, 'without_skill': None}
    jobs = []
    for item in items:
        eval_dir = out / 'iteration-1' / f"eval-{item['name']}"
        save(eval_dir / 'eval_metadata.json', {'eval_id': item['id'], 'eval_name': item['name'],
             'prompt': item['prompt'], 'assertions': item['assertions'], 'fixture_is_synthetic': True})
        for variant, skill in versions.items():
            jobs.append((item, variant, skill, eval_dir / variant / 'run-1'))
    # Alternate groups to avoid always assigning one group the same temporal order.
    jobs.sort(key=lambda j: (j[0]['id'], {'old_skill': 0, 'without_skill': 1, 'with_skill': 2}[j[1]]
                            if j[0]['id'] % 2 else {'with_skill': 0, 'old_skill': 1, 'without_skill': 2}[j[1]]))

    def one(job):
        item, variant, skill, run_dir = job
        state_root, child_env, _ = environment()
        args = [sys.executable, '-X', 'utf8', str(PRODUCT / 'scripts/skill_scenario.py'),
                '--client', 'opencode', '--model', MODEL, '--prompt', item['prompt'],
                '--input-dir', str(HERE / item['input_dir']), '--output-dir', 'outputs',
                '--run-dir', str(run_dir), '--timeout', '240', '--keep',
                '--client-cmd', f'"{EXE}" --pure run --format json -m {{model}} {{prompt}}']
        if skill:
            args += ['--skill-dir', str(skill)]
        started = time.monotonic()
        p = subprocess.run(args, cwd=root, env=child_env, capture_output=True, encoding='utf-8', errors='replace')
        save(run_dir / 'client-environment.json', {'state_root': str(state_root), 'isolated_user_directories': ISOLATE_HOME,
             'public_config': public_config_without_secrets(child_env)})
        (run_dir / 'executor.stdout.txt').write_text(p.stdout, encoding='utf-8')
        (run_dir / 'executor.stderr.txt').write_text(p.stderr, encoding='utf-8')
        # --keep allows independent verification that copied inputs stayed unchanged.
        kept = next((line.split('kept workspace: ', 1)[1] for line in p.stderr.splitlines()
                     if line.startswith('kept workspace: ')), None)
        if kept:
            save(run_dir / 'input-integrity.json', {
                'source': hashes(HERE / item['input_dir']), 'after': hashes(Path(kept) / 'inputs'),
                'unchanged': hashes(HERE / item['input_dir']) == hashes(Path(kept) / 'inputs')})
            save(run_dir / 'discovery.json', discovery(kept, child_env))
        print(f"scenario {item['name']} / {variant}: rc={p.returncode}, {time.monotonic()-started:.1f}s", flush=True)
        return {'eval_id': item['id'], 'config': variant, 'returncode': p.returncode}

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(one, jobs))
    save(out / 'scenario-execution.json', results)


def public_config_without_secrets(env):
    config = json.loads(env['OPENCODE_CONFIG_CONTENT'])
    config.pop('provider', None)
    return config


def main():
    global ISOLATE_HOME
    ap = argparse.ArgumentParser()
    ap.add_argument('phase', choices=['trigger', 'scenarios'])
    ap.add_argument('--out', type=Path, default=HERE)
    ap.add_argument('--isolate-home', action='store_true', help='Use per-run empty USERPROFILE/APPDATA/LOCALAPPDATA in the child only')
    args = ap.parse_args()
    ISOLATE_HOME = args.isolate_home
    out = args.out.resolve()
    target = out / ('trigger' if args.phase == 'trigger' else 'iteration-1')
    if target.exists():
        raise SystemExit(f'Refusing to reuse existing attempt folder: {target}')
    root, env, public_config = environment()
    version = subprocess.run([str(EXE), '--version'], capture_output=True, encoding='utf-8', check=True).stdout.strip()
    initial = discovery(root, env)
    if any(s['name'] == 'skill-creator' for s in initial):
        raise SystemExit('Global skill-creator still visible; stop before model invocation')
    save(out / f'{args.phase}-environment.json', {
        'started_at': datetime.now(timezone.utc).isoformat(), 'exe': str(EXE), 'client_version': version,
        'model': MODEL, 'model_source': 'requested', 'public_config': public_config,
        'isolated_user_directories': ISOLATE_HOME,
        'baseline_discovery': initial, 'state_root': str(root),
        'head': subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip(),
        'query_sha256': hashlib.sha256((HERE / 'queries.json').read_bytes()).hexdigest(),
        'fixtures_sha256': hashes(HERE / 'fixtures') if (HERE / 'fixtures').exists() else None,
        'scenario_sha256': hashlib.sha256((HERE / 'scenarios.json').read_bytes()).hexdigest() if (HERE / 'scenarios.json').exists() else None,
        'limits': 'One run per query/task, single model; no task-quality claim from trigger signal. XDG isolation is not a security sandbox.',
    })
    save(out / f'{args.phase}-product-hashes.json', hashes(PRODUCT))
    if args.phase == 'trigger':
        trigger(out, env)
    else:
        scenarios(out, env, root)


if __name__ == '__main__':
    main()
