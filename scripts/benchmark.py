#!/usr/bin/env python3
"""Repeatable end-to-end packing benchmark; saves measurements and semantic fingerprints."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser()
parser.add_argument('--script', type=Path, default=Path(__file__).resolve().parents[1] / 'scent.kujo')
parser.add_argument('--runs', type=int, default=3)
parser.add_argument('--files', type=int, default=24)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if args.runs < 1 or args.files < 1:
    parser.error('runs and files must be positive')
kujo = shutil.which(os.environ.get('KUJO_BIN', 'kujo'))
if not kujo:
    parser.error('Set KUJO_BIN to an installed Kujo runtime')
kujo = str(Path(kujo).resolve())
results = {}
with tempfile.TemporaryDirectory(prefix='scent-bench-') as directory:
    root = Path(directory)
    repo = root / 'repo'
    repo.mkdir()
    subprocess.run(['git', 'init', '-q', str(repo)], check=True)
    for index in range(args.files):
        (repo / f'doc-{index:04}.md').write_text(f'# Document {index}\n' + 'Ordinary local context.\n' * 8)
    for mode in ('both', 'json', 'dry-run'):
        samples = []
        for run in range(args.runs):
            out = root / 'pack'
            argv = [kujo, 'run', str(args.script.resolve()), 'pack', '--task', 'review docs',
                    '--max-files', '10', '--out', str(out), '--json']
            argv += ['--dry-run'] if mode == 'dry-run' else ['--format', mode]
            start = time.perf_counter()
            completed = subprocess.run(argv, cwd=repo, capture_output=True, check=True, timeout=120)
            samples.append(time.perf_counter() - start)
        receipt = json.loads(completed.stdout)
        row = {'seconds': samples, 'median_seconds': statistics.median(samples),
               'stdout_bytes': len(completed.stdout), 'estimated_tokens': receipt['estimated_tokens'],
               'included_files': receipt['included_files']}
        if mode != 'dry-run':
            context = json.loads((out / 'context.json').read_text())
            semantic = {key: context[key] for key in ('selected_files', 'changed_files', 'redactions', 'excluded')}
            row['semantic_sha256'] = hashlib.sha256(json.dumps(semantic, sort_keys=True).encode()).hexdigest()
            row['context_json_bytes'] = (out / 'context.json').stat().st_size
        results[mode] = row
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps({'files': args.files, 'runs': args.runs, 'results': results}, indent=2) + '\n')
print(f'Benchmark evidence: {args.output}')
