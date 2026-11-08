"""Generate full-domain cases, run real JSONL batches, save compact evidence."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import random
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
from public_validate import check
import oracles


def cases():
    yield 'lcs_million_cells', [
        ({'task': 'lcs', 'a': 'ab' * 500, 'b': 'ba' * 500}, {'length': 999}),
        ({'task': 'lcs', 'a': 'a' * 1000, 'b': 'b' * 1000}, {'length': 0}),
        ({'task': 'lcs', 'a': 'x' * 1000, 'b': 'x' * 1000}, {'length': 1000}),
    ], 'Shifted alternating strings lose one endpoint; disjoint alphabets give zero; equal strings give 1000.'
    # An optimal full binary tree with 200 equal leaves has 56 leaves at depth 7 and 144 at depth 8.
    yield 'merge_200_large_and_zero', [
        ({'task': 'merge', 'sizes': [10**9] * 200}, {'cost': 1544 * 10**9}),
        ({'task': 'merge', 'sizes': [0] * 200}, {'cost': 0}),
    ], 'Equal weights: minimum external path length 56*7 + 144*8 = 1544; ordered balanced splits attain it. Zeros cost zero.'
    n = 100000
    chain = [[i, i + 1] for i in range(n - 1)]
    yield 'tree_100000_chain_star_negative', [
        ({'task': 'tree', 'n': n, 'weights': [10**9] * n, 'edges': chain}, {'weight': (n // 2) * 10**9}),
        ({'task': 'tree', 'n': n, 'weights': [10**9] * n, 'edges': [[0, i] for i in range(1, n)]},
         {'weight': (n - 1) * 10**9}),
        ({'task': 'tree', 'n': n, 'weights': [-10**9] * n, 'edges': chain}, {'weight': 0}),
    ], 'Even chain permits exactly 50000 vertices; star optimum is all 99999 leaves; negative weights favour the empty set.'
    yield 'naive_3000_limits', [
        ({'task': 'naive', 'text': 'a' * 3000, 'pattern': 'a' * 1500}, {'positions': list(range(1501))}),
        ({'task': 'naive', 'text': 'a' * 3000, 'pattern': 'a' * 3000}, {'positions': [0]}),
        ({'task': 'naive', 'text': 'a' * 3000, 'pattern': ''}, {'positions': list(range(3001))}),
    ], 'All-a starts are exactly 0..n-m; empty pattern matches n+1 boundaries.'
    yield 'kmp_200000_100000_limits', [
        ({'task': 'kmp', 'text': 'a' * 200000, 'pattern': 'a' * 100000}, {'positions': list(range(100001))}),
        ({'task': 'kmp', 'text': 'a' * 200000, 'pattern': 'a' * 99999 + 'b'}, {'positions': []}),
        ({'task': 'kmp', 'text': 'a' * 200000, 'pattern': ''}, {'positions': list(range(200001))}),
    ], 'All-a overlap count n-m+1; absent b rejects long almost-matches; empty pattern emits every boundary.'
    yield 'rk_20million_product_and_10000_length', [
        ({'task': 'rk', 'text': 'a' * 10000, 'pattern': 'a' * 2000}, {'positions': list(range(8001))}),
        ({'task': 'rk', 'text': 'a' * 2000, 'pattern': 'a' * 10000}, {'positions': []}),
        ({'task': 'rk', 'text': 'dj' * 5000, 'pattern': 'ab'}, {'positions': []}),
    ], 'First two products equal 20000000. All-a windows match, longer pattern cannot fit; dj collides with ab but is unequal.'
    text = 'a' * 50000
    yield 'suffix_50000_repetitive', [
        ({'task': 'suffix', 'text': text}, {'sa': list(range(49999, -1, -1)),
                                         'lcp': list(range(50000)), 'repeated': text[:-1]}),
    ], 'All suffixes are a-runs: increasing length gives suffix order; adjacent common prefix lengths are 0..49999.'
    rng = random.Random(4201)
    text = ''.join(chr(rng.randrange(32, 127)) for _ in range(50000))
    yield 'suffix_50000_random_ascii', [
        ({'task': 'suffix', 'text': text}, oracles.suffix_result(text)),
    ], 'Seed 4201, uniform printable ASCII 32..126. Independent literal suffix comparator and direct adjacent prefix comparisons.'
    yield 'aho_10000_duplicates_dense_200000_text', [
        ({'task': 'aho', 'patterns': ['a' * 10] * 10000, 'texts': ['a' * 200000]},
         {'counts': [[199991] * 10000]}),
    ], 'Exactly 100000 total pattern characters. Each duplicate length-10 pattern has 200000-10+1 overlapping starts.'
    yield 'aho_100_text_rows_10000_columns', [
        ({'task': 'aho', 'patterns': ['a' * 10] * 10000, 'texts': ['a' * 2000] * 100},
         {'counts': [[1991] * 10000 for _ in range(100)]}),
    ], '100 independent texts total 200000 characters; every row/duplicate column has 2000-10+1 = 1991.'
    yield 'aho_100001_states_deep_failure_chain', [
        ({'task': 'aho', 'patterns': ['a' * 100000], 'texts': ['a' * 200000]}, {'counts': [[100001]]}),
    ], 'One 100000-character pattern creates 100001 trie states; overlapping starts total 100001.'
    suffix_lengths = list(range(1, 447)) + [319]
    yield 'aho_dense_suffix_patterns_L100000', [
        ({'task': 'aho', 'patterns': ['a' * length for length in suffix_lengths], 'texts': ['a' * 200000]},
         {'counts': [[200001 - length for length in suffix_lengths]]}),
    ], 'Pattern lengths 1..446 plus duplicate length 319 sum to 100000. Every pattern is a suffix of longer ones; each count is 200001-length.'
    # Force printable alphabet endpoints as well as 100000 total pattern characters.
    alphabet = ''.join(chr(i) for i in range(32, 127))
    rng = random.Random(4202)
    patterns = [''.join(rng.choices(alphabet, k=10)) for _ in range(10000)]
    patterns[0] = ' ' + '~' * 9
    patterns[1] = '~' + ' ' * 9
    texts = ['a' * 2000] * 100
    one_row = [1991 if pattern == 'a' * 10 else 0 for pattern in patterns]
    yield 'aho_wide_ascii_trie_100_texts', [
        ({'task': 'aho', 'patterns': patterns, 'texts': texts}, {'counts': [one_row[:] for _ in texts]}),
    ], 'Seed 4202, 10000 length-10 printable ASCII patterns (L=100000). An all-a text only matches the exact pattern a^10.'


def main():
    reports = []
    for name, batch, justification in cases():
        data = ''.join(json.dumps(request, separators=(',', ':')) + '\n' for request, _ in batch)
        started = perf_counter()
        result = subprocess.run([sys.executable, str(ROOT / 'Python' / 'source' / 'main.py')],
                                input=data, capture_output=True, text=True, encoding='utf-8', timeout=20, check=True)
        seconds = perf_counter() - started
        output_bytes = result.stdout.encode('utf-8')
        if len(output_bytes) > 8 * 1024 * 1024:
            raise AssertionError(f'{name}: exceeds 8 MiB output cap')
        lines = result.stdout.splitlines()
        if len(lines) != len(batch) or result.stderr:
            raise AssertionError(f'{name}: incorrect line count or stderr')
        for (request, expected), line in zip(batch, lines):
            if not check(request, json.loads(line), expected):
                raise AssertionError(f'{name}: invalid {request["task"]} answer/witness')
        entry = {
            'name': name, 'requests': len(batch), 'passed': True,
            'process_seconds': seconds, 'output_utf8_bytes': len(output_bytes),
            'input_sha256': hashlib.sha256(data.encode('utf-8')).hexdigest(),
            'actual_output_sha256': hashlib.sha256(output_bytes).hexdigest(),
            'expected_justification': justification,
        }
        reports.append(entry)
        print(f'PASS {name}: {len(batch)} requests; {seconds:.6f}s; {len(output_bytes)} output bytes', flush=True)
    report = {
        'captured_utc': datetime.now(timezone.utc).isoformat(),
        'runtime': f'{platform.python_implementation()} {platform.python_version()}',
        'platform': platform.platform(), 'command': 'python tests/student/scale_checks.py',
        'timeout_seconds_per_batch': 20, 'output_limit_bytes_per_batch': 8 * 1024 * 1024,
        'timing_scope': 'Real subprocess launch, JSONL input transfer/parsing, algorithms and output serialization/transfer; excludes parent generator/oracle/validation.',
        'limitations': 'Local Windows verification; no CPU affinity or memory-container cap was enforced. Times are observations, not worst-case guarantees.',
        'batches': reports,
    }
    (HERE / 'scale_results.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
