"""Call the unmodified generated role through OpenCode's native agent loader."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time

import run_live_evaluation as live
from skill_events import assistant_text


def actual_agents(state):
    path = state / 'data/opencode/opencode.db'
    if not path.is_file():
        return []
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as con:
        records = [json.loads(row[0]) for row in con.execute('select data from message')]
    return [{'agent': r.get('agent'), 'mode': r.get('mode')} for r in records if r.get('role') == 'assistant']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--attempt', type=Path, required=True)
    args = ap.parse_args()
    attempt = args.attempt.resolve()
    target = attempt / 'runtime'
    if target.exists():
        raise SystemExit('Refusing to overwrite runtime evidence')
    spec = live.load(live.HERE / 'runtime.json')
    frozen = live.load(live.HERE / 'frozen-inputs.json')
    assert live.digest(live.HERE / 'runtime.json') == frozen['protocol']['runtime.json']
    assert live.hashes(live.HERE / 'fixtures') == frozen['fixtures']
    assert live.hashes(live.PRODUCT) == frozen['product']
    provider = live.selected_provider()
    target.mkdir(parents=True)
    live.save(target / 'protocol.json', spec)

    def one(variant):
        run = target / variant / 'run-1'
        run.mkdir(parents=True)
        source = attempt / 'iteration-1/eval-creation' / variant / 'run-1' / spec['artifact_relative_path']
        state, env, public = live.environment(provider, spec['max_steps'])
        config = json.loads(env['OPENCODE_CONFIG_CONTENT'])
        config['agent'][spec['agent_name']] = {'steps': spec['max_steps']}
        public['agent'][spec['agent_name']] = {'steps': spec['max_steps']}
        env['OPENCODE_CONFIG_CONTENT'] = json.dumps(config)
        workspace = state / 'runtime-workspace'
        workspace.mkdir()
        inputs = workspace / 'inputs'
        inputs.mkdir()
        for fixture in (live.HERE / spec['fixture_dir']).iterdir():
            if fixture.name != 'sentinel.txt':
                shutil.copy2(fixture, inputs / fixture.name)
        sentinel = workspace / spec['sentinel_workspace_path']
        shutil.copy2(live.HERE / spec['sentinel_source'], sentinel)
        before = {'inputs': live.hashes(inputs), 'sentinel': live.digest(sentinel)}
        live.save(run / 'client-environment.json', {**live.runtime_metadata(state, public),
                  'workspace': str(workspace), 'source': str(source)})
        result = {'variant': variant, 'status': 'error', 'model_called': False,
                  'error': None, 'native_discovery_passed': False}
        stdout, stderr = '', ''
        try:
            if not source.is_file():
                raise ValueError('Generation did not deliver the required role')
            live.save(run / 'source.json', {'path': str(source), 'sha256': live.digest(source)})
            installed = workspace / '.opencode/agents' / (spec['agent_name'] + '.md')
            adapt = subprocess.run([sys.executable, str(live.PRODUCT / 'scripts/agent_adapt.py'),
                str(source), '--client', 'opencode', '--out', str(installed)],
                capture_output=True, encoding='utf-8', errors='replace')
            live.write(run / 'adapt.stdout.txt', adapt.stdout)
            live.write(run / 'adapt.stderr.txt', adapt.stderr)
            result['adapt_returncode'] = adapt.returncode
            if adapt.returncode:
                raise ValueError('Generated role failed OpenCode adaptation')
            shutil.copy2(installed, run / 'installed-agent.md')
            live.discovery(workspace, env, run / 'skill-discovery', None)
            debug = [str(live.EXE), '--pure', 'debug', 'agent', spec['agent_name']]
            rc, text, err = live.run_client(debug, timeout=40, cwd=str(workspace), env=env)
            live.write(run / 'native-agent.stdout.json', text)
            live.write(run / 'native-agent.stderr.txt', err)
            resolved = json.loads(text) if rc == 0 else {}
            result['native_discovery_passed'] = (resolved.get('name') == spec['agent_name']
                and resolved.get('mode') == 'primary' and bool(resolved.get('prompt')))
            if not result['native_discovery_passed']:
                raise ValueError('Native loader did not resolve the generated primary role')
            command = [str(live.EXE), '--pure', 'run', '--format', 'json', '-m', live.MODEL,
                       '--agent', spec['agent_name'], spec['prompt']]
            live.command_evidence(run / 'invocation.json', command, workspace, spec['timeout_seconds'])
            result['model_called'] = True
            started = time.monotonic()
            try:
                rc, stdout, stderr = live.run_client(command, timeout=spec['timeout_seconds'],
                                                     cwd=str(workspace), env=env)
                result.update(returncode=rc, timed_out=False)
                error = live.execution_error(stdout + stderr, 'opencode')
                if rc or error:
                    raise ValueError(error or f'client exited {rc}')
                result['status'] = 'completed'
            except subprocess.TimeoutExpired as error:
                result.update(returncode=None, timed_out=True)
                stdout, stderr = error.stdout or '', error.stderr or ''
                raise ValueError('Runtime call timed out') from error
            finally:
                result['duration_seconds'] = round(time.monotonic() - started, 3)
        except Exception as error:
            result['error'] = f'{type(error).__name__}: {error}'
        finally:
            if isinstance(stdout, bytes): stdout = stdout.decode('utf-8', 'replace')
            if isinstance(stderr, bytes): stderr = stderr.decode('utf-8', 'replace')
            live.write(run / 'stdout.jsonl', stdout)
            live.write(run / 'stderr.txt', stderr)
            live.write(run / 'response.txt', assistant_text(stdout))
            result.update(live.stream_metrics(stdout + stderr, 'opencode'))
            observed = live.observed_models(state, run / 'observed-models.json')
            result['observed_models'] = observed['models']
            result['actual_agents'] = actual_agents(state)
            after = {'inputs': live.hashes(inputs), 'sentinel': live.digest(sentinel) if sentinel.exists() else None}
            live.save(run / 'input-integrity.json', {'before': before, 'after': after, 'unchanged': before == after})
            calls = live.tool_calls(stdout + stderr, 'opencode')
            violations = [c for c in calls if c['tool'] not in ('read', 'grep', 'glob')]
            live.save(run / 'tool-audit.json', {'calls': calls, 'non_readonly_attempts': violations})
            live.save(run / 'execution.json', result)
            print(f"runtime {variant}: {result['status']}; {result['error']}", flush=True)
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(one, spec['variants']))
    live.save(target / 'summary.json', results)
    return 0 if all(r['status'] == 'completed' for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
