"""Deterministic post-run checks; never edits model artifacts or calls a model."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PRODUCT = REPO / 'agent-creator/skills/agent-creator'
sys.path.insert(0, str(PRODUCT / 'scripts'))
import agent_adapt


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def metadata(path):
    if not path.is_file():
        return {'exists': False}
    try:
        text = path.read_text(encoding='utf-8-sig')
        fm, body = agent_adapt.split_frontmatter(text)
        parsed = agent_adapt.parse_frontmatter(fm, str(path)) if fm is not None else None
        return {'exists': True, 'frontmatter': parsed, 'body_chars': len(body),
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    except Exception as error:
        return {'exists': True, 'error': str(error)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--attempt', type=Path, required=True)
    args = ap.parse_args()
    if (args.attempt / 'objective-verification.json').exists():
        raise SystemExit('Refusing to overwrite objective verification')
    records = []
    for task, relative in [('creation', 'agents/release-evidence-auditor.md'),
                           ('repair', 'bug-triager/AGENT.md')]:
        for variant in ('with_skill', 'old_skill', 'without_skill'):
            run = args.attempt / 'iteration-1' / f'eval-{task}' / variant / 'run-1'
            output = run / 'outputs/artifacts/outputs'
            entry = output / relative
            record = {'task': task, 'variant': variant, 'entry': metadata(entry),
                      'source_exists': entry.is_file(), 'packages': {}}
            if entry.is_file():
                result = subprocess.run([sys.executable, str(PRODUCT / 'scripts/agent_validate.py'),
                                         '--strict', '--dir', str(entry.parent.resolve())],
                                        capture_output=True, encoding='utf-8', errors='replace')
                (run / 'strict.stdout.txt').write_text(result.stdout, encoding='utf-8')
                (run / 'strict.stderr.txt').write_text(result.stderr, encoding='utf-8')
                record['strict_returncode'] = result.returncode
            else:
                record['strict_returncode'] = None
            verification = output / 'verification.json'
            try:
                record['self_report'] = json.loads(verification.read_text(encoding='utf-8-sig'))
            except (ValueError, OSError) as error:
                record['self_report_error'] = str(error)
            if task == 'repair':
                for client in ('opencode', 'claude'):
                    package = output / 'packages' / client / 'bug-triager'
                    meta = metadata(package / 'AGENT.md')
                    meta['reference_exists'] = (package / 'references/report-format.md').is_file()
                    if meta.get('frontmatter'):
                        try:
                            check = getattr(agent_adapt, f'check_{client}_frontmatter')
                            check(meta['frontmatter'], str(package))
                            meta['post_check_passed'] = True
                        except Exception as error:
                            meta['post_check_passed'] = False
                            meta['post_check_error'] = str(error)
                    record['packages'][client] = meta
            files = []
            manifest = run / 'artifacts.json'
            if manifest.is_file():
                for item in json.loads(manifest.read_text(encoding='utf-8'))['files']:
                    artifact = run / item['path']
                    files.append({'path': item['path'], 'hash_ok': artifact.is_file() and
                        hashlib.sha256(artifact.read_bytes()).hexdigest() == item['sha256']})
            record['artifacts'] = files
            records.append(record)
    save(args.attempt / 'objective-verification.json', {'records': records,
         'scope': 'Current fixed validator/adaptor used equally on all outputs; not client runtime evidence.'})
    print(json.dumps([{'task': r['task'], 'variant': r['variant'],
                      'exists': r['source_exists'], 'strict': r['strict_returncode']} for r in records]))


if __name__ == '__main__':
    main()
