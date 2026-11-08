"""Capture actual fixture outputs and unittest logs, validating before success."""

from datetime import datetime, timezone
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from public_validate import check


def main():
    cases = json.loads((HERE / 'cases.json').read_text(encoding='utf-8'))
    inputs = ''.join(json.dumps(c['input'], separators=(',', ':')) + '\n' for c in cases)
    expected = ''.join(json.dumps(c['expected'], separators=(',', ':')) + '\n' for c in cases)
    (HERE / 'inputs.jsonl').write_text(inputs, encoding='utf-8')
    (HERE / 'expected_outputs.jsonl').write_text(expected, encoding='utf-8')
    run = subprocess.run([sys.executable, str(ROOT / 'Python' / 'source' / 'main.py')],
                         input=inputs, capture_output=True, text=True, encoding='utf-8', timeout=20, check=True)
    (HERE / 'actual_outputs.jsonl').write_text(run.stdout, encoding='utf-8')
    answers = [json.loads(line) for line in run.stdout.splitlines()]
    if len(answers) != len(cases) or run.stderr:
        raise AssertionError('Incorrect output line count or nonempty stderr')
    for case, answer in zip(cases, answers):
        if not check(case['input'], answer, case['expected']):
            raise AssertionError(f"Fixture failed: {case['name']}: {answer}")
    stream = io.StringIO()
    stream.write(f'Captured UTC: {datetime.now(timezone.utc).isoformat()}\n')
    stream.write(f'Runtime: {platform.python_implementation()} {platform.python_version()}\n')
    stream.write(f'Platform: {platform.platform()}\n')
    stream.write('Command: python tests/student/capture_evidence.py\n')
    stream.write(f'Fixtures: {len(cases)}/{len(cases)} semantically valid.\n\n')
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern='test_algorithms.py')
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    (HERE / 'test_results.txt').write_text(stream.getvalue(), encoding='utf-8')
    print(stream.getvalue(), end='')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
