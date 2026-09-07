#!/usr/bin/env python3
"""Offline CLI regressions. Run from any directory; KUJO_BIN selects the runtime."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(os.environ.get('SCENT_SCRIPT', ROOT / 'scent.kujo')).resolve()
KUJO = shutil.which(os.environ.get('KUJO_BIN', 'kujo'))
if not KUJO:
    raise SystemExit('Set KUJO_BIN to an installed Kujo runtime.')
KUJO = str(Path(KUJO).resolve())


class Hardening(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='scent-hardening-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.out = self.root / 'pack'
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)

    def pack(self, *args, code=0):
        result = subprocess.run([KUJO, 'run', str(SCRIPT), 'pack', '--task', 'audit',
                                 '--out', str(self.out), '--json', *args],
                                cwd=self.repo, text=True, capture_output=True, timeout=120)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result

    def context(self):
        return json.loads((self.out / 'context.json').read_text())

    def test_mixed_tokens(self):
        jwt = 'abcdefghij.klmnopqrst.uvwxyzABCD'
        provider = 'sk-ABCDEFGHIJKLMNOPQRSTUVWXYZ123456'
        (self.repo / 'mixed.txt').write_text(f'{provider} {jwt}\n{jwt} {provider}\n')
        self.pack('--include', 'mixed.txt', '--task', f'{provider} {jwt}')
        for artifact in self.out.iterdir():
            text = artifact.read_text()
            self.assertNotIn(jwt, text, artifact.name)
            self.assertNotIn(provider, text, artifact.name)
        types = [r['redaction_type'] for r in self.context()['redactions']]
        self.assertEqual(types.count('jwt'), 3)

    def test_private_key_provenance(self):
        (self.repo / 'keys.txt').write_text('-----BEGIN PRIVATE KEY-----\nprivate\n'
            '-----END PRIVATE KEY-----\npassword=example\n')
        self.pack('--include', 'keys.txt')
        records = self.context()['redactions']
        self.assertEqual([(r['line'], r['redaction_type']) for r in records],
                         [(1, 'private_key'), (4, 'password')])
        self.assertEqual(self.context()['selected_files'][0]['content'],
                         '[REDACTED:PRIVATE_KEY]\npassword=[REDACTED:PASSWORD]\n')

    def test_normalized_exclusions(self):
        (self.repo / 'docs').mkdir()
        (self.repo / 'docs' / 'private.txt').write_text('EXCLUDED_MARKER')
        (self.repo / 'safe.txt').write_text('safe')
        self.pack('--include', '.', '--exclude', 'docs//./private.txt')
        self.assertEqual([f['path'] for f in self.context()['selected_files']], ['safe.txt'])

    def test_symlink_command_discovery(self):
        outside = self.root / 'package.json'
        outside.write_text('{"scripts":{"test":"echo outside"}}')
        (self.repo / 'package.json').symlink_to(outside)
        (self.repo / 'safe.txt').write_text('safe')
        self.pack('--include', 'safe.txt')
        self.assertEqual(self.context()['commands'], [])

    def test_excluded_tree_does_not_consume_candidate_cap(self):
        bulk = self.repo / 'a_bulk'
        bulk.mkdir()
        for i in range(2001):
            (bulk / f'{i:04}.txt').touch()
        (self.repo / 'z_wanted.txt').write_text('wanted')
        self.pack('--exclude', 'a_bulk')
        self.assertEqual([f['path'] for f in self.context()['selected_files']], ['z_wanted.txt'])

    def test_output_failure_exit(self):
        (self.repo / 'safe.txt').write_text('safe')
        self.out.write_text('not a directory')
        result = self.pack('--include', 'safe.txt', code=4)
        self.assertIn('error:', result.stdout)
        self.assertEqual(self.out.read_text(), 'not a directory')

    def test_atomic_hardlink_replacement(self):
        (self.repo / 'safe.txt').write_text('safe')
        self.out.mkdir()
        victim = self.root / 'victim'
        victim.write_text('sentinel')
        os.link(victim, self.out / 'context.json')
        self.pack('--include', 'safe.txt', '--format', 'json')
        self.assertEqual(victim.read_text(), 'sentinel')
        self.assertNotEqual(victim.stat().st_ino, (self.out / 'context.json').stat().st_ino)

    def test_failed_atomic_publish_preserves_destination(self):
        (self.repo / 'safe.txt').write_text('safe')
        self.out.mkdir()
        destination = self.out / 'context.json'
        destination.mkdir()
        (destination / 'sentinel').write_text('unchanged')
        self.pack('--include', 'safe.txt', '--format', 'json', code=4)
        self.assertEqual((destination / 'sentinel').read_text(), 'unchanged')
        self.assertEqual(list(self.out.iterdir()), [destination])

    def test_concurrent_default_outputs_are_distinct(self):
        (self.repo / 'safe.txt').write_text('safe')
        def run(task):
            result = subprocess.run([KUJO, 'run', str(SCRIPT), 'pack', '--task', task,
                                     '--include', 'safe.txt', '--json'], cwd=self.repo,
                                    capture_output=True, text=True, check=True, timeout=120)
            return json.loads(result.stdout)
        with ThreadPoolExecutor(max_workers=2) as executor:
            receipts = list(executor.map(run, ['first audit', 'second audit']))
        self.assertNotEqual(receipts[0]['output_dir'], receipts[1]['output_dir'])
        for receipt, task in zip(receipts, ['first audit', 'second audit']):
            self.assertEqual(json.loads(Path(receipt['context_json']).read_text())['task'], task)

    def test_artifact_permissions(self):
        (self.repo / 'safe.txt').write_text('safe')
        self.pack('--include', 'safe.txt')
        self.assertTrue(all(path.stat().st_mode & 0o777 == 0o600 for path in self.out.iterdir()))
        (self.out / 'context.json').chmod(0o640)
        self.pack('--include', 'safe.txt')
        self.assertEqual((self.out / 'context.json').stat().st_mode & 0o777, 0o640)

    def test_atomic_write_byte_limit(self):
        destination = self.root / 'bounded.txt'
        destination.write_text('sentinel')
        probe = self.root / 'bounded.kujo'
        prefix = SCRIPT.read_text().split('func main()')[0]
        probe.write_text(prefix + '\ncontent := repeat("é", 4194304)\n' +
                         'print(to_json(write_text(' + json.dumps(str(destination)) +
                         ', content + "x")))\n')
        result = subprocess.run([KUJO, 'run', str(probe)], check=True, capture_output=True,
                                text=True, timeout=120)
        error = json.loads(result.stdout)
        self.assertFalse(error['ok'])
        self.assertEqual(error['exit_code'], 4)
        self.assertEqual(destination.read_text(), 'sentinel')
        self.assertFalse(list(self.root.glob('*.scent-*.tmp')))
        probe.write_text(prefix + '\nprint(to_json(write_text(' + json.dumps(str(destination)) +
                         ', repeat("é", 4194304))))\n')
        result = subprocess.run([KUJO, 'run', str(probe)], check=True, capture_output=True,
                                text=True, timeout=120)
        self.assertTrue(json.loads(result.stdout)['ok'])
        self.assertEqual(destination.stat().st_size, 8388608)

    def test_score_order_equivalence(self):
        # Execute the real private helper without the CLI; oracle is Python's
        # lexicographic score/path ordering, including ties and unusual names.
        items = [{'score': (i * 17) % 11,
                  'candidate': {'rel_path': f'{63-i:03}-é\n.md'}, 'reason': str(i)}
                 for i in range(64)]
        probe = self.root / 'sort.kujo'
        prefix = SCRIPT.read_text().split('func main()')[0]
        probe.write_text(prefix + '\nprint(to_json(sort_scored(parse_json(' +
                         json.dumps(json.dumps(items)) + '))))\n')
        result = subprocess.run([KUJO, 'run', str(probe)], check=True, capture_output=True,
                                text=True, timeout=120)
        self.assertEqual(json.loads(result.stdout),
                         sorted(items, key=lambda row: (-row['score'], row['candidate']['rel_path'])))

    def test_dry_run_receipt_and_formats(self):
        (self.repo / 'safe.txt').write_text('safe\n')
        receipt = json.loads(self.pack('--include', 'safe.txt', '--dry-run').stdout)
        self.assertFalse(self.out.exists())
        self.assertIsNone(receipt['context_json'])
        self.assertLess(len(json.dumps(receipt)), 1024)
        self.pack('--include', 'safe.txt')
        context = self.context()
        self.assertEqual(receipt['estimated_tokens'], context['estimated_tokens'])
        self.assertEqual(receipt['included_files'], len(context['selected_files']))
        self.pack('--include', 'safe.txt', '--format', 'md')
        self.assertFalse((self.out / 'context.json').exists())
        self.pack('--include', 'safe.txt', '--format', 'json')
        self.assertFalse((self.out / 'context.md').exists())


if __name__ == '__main__':
    unittest.main()
