"""Audit saved live evidence without invoking a model or rewriting executor metrics."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parent


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def main():
    artifact_errors = []
    observations = []
    for manifest_path in ROOT.glob('attempt-*/iteration-1/*/*/run-1/artifacts.json'):
        run = manifest_path.parent
        for record in load(manifest_path)['files']:
            path = run / record['path']
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
                artifact_errors.append(str(path.relative_to(ROOT)))
    # The actual selected provider/model is read from the local client's own
    # session metadata. This does not attest a provider's underlying model weights.
    markers = list(ROOT.glob('attempt-*/trigger/raw/*/execution.json'))
    markers += list(ROOT.glob('attempt-*/iteration-1/*/*/run-1/client-environment.json'))
    for marker in sorted(markers):
        meta = load(marker)
        db = Path(meta['state_root']) / 'data/opencode/opencode.db'
        if not db.is_file():
            continue
        with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True) as connection:
            rows = connection.execute('select id, session_id, data from message').fetchall()
        messages = []
        for mid, sid, data in rows:
            message = json.loads(data)
            if message.get('role') != 'assistant':
                continue
            messages.append({'message_id': mid, 'session_id': sid,
                             'provider': message.get('providerID'), 'model': message.get('modelID'),
                             'finish': message.get('finish')})
        models = sorted({f"{m['provider']}/{m['model']}" for m in messages
                         if m['provider'] and m['model']})
        evidence = {'source': 'opencode_local_session_metadata', 'models': models,
                    'messages': messages, 'billing': 'unknown; client cost=0 is not a billing statement'}
        save(marker.parent / 'observed-models.json', evidence)
        observations.append({'run': str(marker.parent.relative_to(ROOT)), 'models': models,
                             'assistant_messages': len(messages)})

    # Check only exact configured secret values, never print the values or copy
    # the user's configuration. Avoid credential/account database tables entirely.
    config = load(Path(os.environ['USERPROFILE']) / '.config/opencode/opencode.json')
    secrets = []
    for provider in config.get('provider', {}).values():
        options = provider.get('options', {})
        value = options.get('apiKey')
        if isinstance(value, str) and len(value) > 12 and not value.startswith('{'):
            secrets.append(value.encode('utf-8'))
    leaks = []
    for path in ROOT.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            if any(secret in path.read_bytes() for secret in secrets):
                leaks.append(str(path.relative_to(ROOT)))
    save(ROOT / 'evidence-audit.json', {'artifact_hash_errors': artifact_errors,
          'configured_secret_matches': leaks, 'observed_models': observations})
    print(json.dumps({'artifact_hash_errors': len(artifact_errors), 'configured_secret_matches': len(leaks),
                      'observed_runs': len(observations)}, ensure_ascii=False))
    if artifact_errors or leaks:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
