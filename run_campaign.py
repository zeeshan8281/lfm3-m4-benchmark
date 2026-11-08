from pathlib import Path
import json, os, subprocess, time
root = Path(__file__).resolve().parent
jobs = [('campaign', 'campaign')] + [('cold', f'cold-{i}') for i in range(1, 4)]
env = dict(os.environ, HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false')
for mode, name in jobs:
    output = root / 'runs' / f'{name}.jsonl'
    assert not output.exists(), f'Preserve existing results: {output}'
    cmd = [str(root / 'runtime/venv/bin/python'), str(root / 'harness.py'), '--mode', mode, '--output', str(output)]
    started = time.perf_counter()
    with (root / 'runs' / f'{name}.log').open('x') as log:
        result = subprocess.run(cmd, cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
    record = {'command': cmd, 'returncode': result.returncode, 'process_wall_seconds': time.perf_counter() - started}
    (root / 'runs' / f'{name}-process.json').write_text(json.dumps(record, indent=2))
    print(json.dumps(record), flush=True)
    assert result.returncode == 0, f'Failed {name}; inspect preserved log'
