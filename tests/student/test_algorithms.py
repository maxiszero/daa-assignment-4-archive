"""Independent optima, semantic witnesses, boundaries, and state-reset tests."""

import json
from pathlib import Path
import random
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Python" / "source"))
sys.path.insert(0, str(ROOT / "tools"))
import algorithms
from public_validate import check
import oracles


class AlgorithmsTests(unittest.TestCase):
    def valid(self, request, expected):
        actual = getattr(algorithms, request["task"])(request)
        self.assertTrue(check(request, actual, expected), (request, actual, expected))
        return actual

    def test_lcs_empty_disjoint_and_subsequence_not_substring(self):
        for a, b, length in [("", "abc", 0), ("abc", "", 0), ("abc", "XYZ", 0),
                             ("tea_time", "team", 4), ("ab", "ba", 1)]:
            self.valid({"task": "lcs", "a": a, "b": b}, {"length": length})

    def test_lcs_random_against_enumerated_subsequences(self):
        rng = random.Random(4101)
        for _ in range(100):
            a = ''.join(rng.choices('ab C!', k=rng.randrange(10)))
            b = ''.join(rng.choices('ab C!', k=rng.randrange(10)))
            self.valid({"task": "lcs", "a": a, "b": b}, {"length": oracles.lcs_length(a, b)})

    def test_merge_empty_single_zero_and_large_cost(self):
        for sizes, cost in [([], 0), ([10**9], 0), ([0, 0, 0, 0], 0),
                            ([2, 3, 4], 14), ([10**9] * 4, 8 * 10**9)]:
            self.valid({"task": "merge", "sizes": sizes}, {"cost": cost})

    def test_merge_random_against_all_adjacent_merge_schedules(self):
        rng = random.Random(4102)
        for _ in range(90):
            sizes = tuple(rng.randrange(8) for _ in range(rng.randrange(8)))
            self.valid({"task": "merge", "sizes": list(sizes)}, {"cost": oracles.merge_cost(sizes)})

    def test_merge_nonadjacent_greedy_counterexample(self):
        # Unrestricted Huffman merges two nonadjacent 1s first for 104; ordered optimum is 203.
        self.valid({"task": "merge", "sizes": [1, 100, 1]}, {"cost": 203})

    def test_tree_empty_negative_ties_and_large_total(self):
        cases = [([], [], 0), ([-5], [], 0), ([0, 0], [[0, 1]], 0),
                 ([4, 9, 6], [[0, 1], [1, 2]], 10),
                 ([10**9] * 5, [[0, i] for i in range(1, 5)], 4 * 10**9)]
        for weights, edges, expected in cases:
            self.valid({"task": "tree", "n": len(weights), "weights": weights, "edges": edges},
                       {"weight": expected})

    def test_tree_random_against_all_vertex_subsets_and_relabeling(self):
        rng = random.Random(4103)
        for _ in range(80):
            n = rng.randrange(1, 12)
            weights = [rng.randrange(-8, 9) for _ in range(n)]
            edges = [[i, rng.randrange(i)] for i in range(1, n)]
            expected = oracles.tree_weight(weights, edges)
            self.valid({"task": "tree", "n": n, "weights": weights, "edges": edges}, {"weight": expected})
            labels = list(range(n))
            rng.shuffle(labels)
            renamed_weights = [0] * n
            for old, new in enumerate(labels):
                renamed_weights[new] = weights[old]
            renamed_edges = [[labels[v], labels[u]] for u, v in reversed(edges)]
            self.valid({"task": "tree", "n": n, "weights": renamed_weights, "edges": renamed_edges},
                       {"weight": expected})

    def test_search_empty_overlapping_last_start_long_pattern_and_ascii(self):
        cases = [("", ""), ("", "a"), ("abc", ""), ("ab", "abc"),
                 ("aaaaa", "aaa"), ("abababa", "aba"), ("xxend", "end"),
                 (' !~A !~a !~A', ' !~A'), ('"\\"\\', '"\\')]
        for text, pattern in cases:
            for task in ("naive", "kmp", "rk"):
                self.valid({"task": task, "text": text, "pattern": pattern},
                           {"positions": oracles.positions(text, pattern)})

    def test_search_random_crosscheck_three_methods_and_builtin_oracle(self):
        rng = random.Random(4104)
        for _ in range(180):
            text = ''.join(rng.choices('abc A!~', k=rng.randrange(80)))
            pattern = ''.join(rng.choices('abc A!~', k=rng.randrange(15)))
            expected = {"positions": oracles.positions(text, pattern)}
            for task in ("naive", "kmp", "rk"):
                self.valid({"task": task, "text": text, "pattern": pattern}, expected)

    def test_kmp_nested_prefix_fallback_and_overlap(self):
        for text, pattern in [('abababacabababacaba', 'ababaca'),
                              ('aaaabaaaabaaaaab', 'aaaab'), ('abcabcabcabc', 'abcabc')]:
            self.valid({"task": "kmp", "text": text, "pattern": pattern},
                       {"positions": oracles.positions(text, pattern)})

    def test_rk_actual_hash_collision_is_rejected(self):
        hash_value = lambda s: sum(ord(c) * 31**(len(s) - i - 1) for i, c in enumerate(s)) % 101
        self.assertEqual(hash_value('ab'), hash_value('dj'))
        self.valid({"task": "rk", "text": "abdjababdj", "pattern": "ab"}, {"positions": [0, 4, 6]})

    def test_suffix_empty_single_unique_periodic_and_ascii(self):
        for text in ('', 'x', 'abcdef', 'banana', 'aaaaaa', 'abababab', ' ~! A~! '):
            self.valid({"task": "suffix", "text": text}, oracles.suffix_result(text))

    def test_suffix_random_against_literal_suffix_comparison(self):
        rng = random.Random(4105)
        for _ in range(120):
            text = ''.join(rng.choices('abcA !~', k=rng.randrange(65)))
            self.valid({"task": "suffix", "text": text}, oracles.suffix_result(text))

    def test_aho_empty_dictionary_empty_texts_and_empty_text(self):
        for patterns, texts in [([], []), ([], ['x', '', 'x']), (['a'], []), (['a', 'a', 'aa'], [''])]:
            self.valid({"task": "aho", "patterns": patterns, "texts": texts},
                       {"counts": oracles.aho_counts(patterns, texts)})

    def test_aho_duplicates_suffix_matches_overlap_and_state_reset(self):
        patterns = ['a', 'aa', 'aaa', 'aa', 'he', 'she', 'hers', 'his', 'he']
        texts = ['aaaa', 'ushershishe', 'aaaa', '', 's', 'he', 'she']
        self.valid({"task": "aho", "patterns": patterns, "texts": texts},
                   {"counts": oracles.aho_counts(patterns, texts)})

    def test_aho_random_against_independent_pattern_searches(self):
        rng = random.Random(4106)
        for _ in range(100):
            patterns = [''.join(rng.choices('ab !', k=rng.randrange(1, 8))) for _ in range(rng.randrange(12))]
            if patterns:
                patterns.append(patterns[0])
            texts = [''.join(rng.choices('ab !', k=rng.randrange(60))) for _ in range(rng.randrange(6))]
            self.valid({"task": "aho", "patterns": patterns, "texts": texts},
                       {"counts": oracles.aho_counts(patterns, texts)})

    def test_mixed_jsonl_requests_three_batches_in_one_process(self):
        cases = json.loads((ROOT / 'tests' / 'student' / 'cases.json').read_text(encoding='utf-8'))
        data = ''.join(json.dumps(c['input']) + '\n' for c in cases * 3)
        result = subprocess.run([sys.executable, str(ROOT / 'Python' / 'source' / 'main.py')],
                                input=data, capture_output=True, text=True, encoding='utf-8', timeout=20, check=True)
        self.assertEqual(result.stderr, '')
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 3 * len(cases))
        for case, line in zip(cases * 3, lines):
            self.assertTrue(check(case['input'], json.loads(line), case['expected']), case['name'])


class WitnessValidationTests(unittest.TestCase):
    def test_lcs_alternative_optima_and_invalid_sequence(self):
        request = {"task": "lcs", "a": "ab", "b": "ba"}
        expected = {"length": 1}
        for sequence in ('a', 'b'):
            self.assertTrue(check(request, {"length": 1, "sequence": sequence}, expected))
        for answer in ({"length": 2, "sequence": 'ab'}, {"length": 1, "sequence": 'x'},
                       {"length": True, "sequence": 'a'}):
            self.assertFalse(check(request, answer, expected))

    def test_merge_alternative_plans_and_invalid_chronology_or_adjacency(self):
        request = {"task": "merge", "sizes": [1, 1, 1]}
        expected = {"cost": 5}
        for plan in ([[0, 0, 1], [0, 1, 2]], [[1, 1, 2], [0, 0, 2]]):
            self.assertTrue(check(request, {"cost": 5, "plan": plan}, expected))
        for plan in ([[0, 1, 2], [0, 0, 1]], [[0, 0, 2]], [[0, 0, 1], [0, 0, 1]]):
            self.assertFalse(check(request, {"cost": 5, "plan": plan}, expected))

    def test_tree_alternative_sets_and_invalid_adjacent_or_duplicate_vertices(self):
        request = {"task": "tree", "n": 2, "weights": [1, 1], "edges": [[0, 1]]}
        expected = {"weight": 1}
        for selected in ([0], [1]):
            self.assertTrue(check(request, {"weight": 1, "selected": selected}, expected))
        for selected in ([0, 1], [0, 0], [2]):
            self.assertFalse(check(request, {"weight": 1, "selected": selected}, expected))

    def test_suffix_alternative_longest_repeats_and_invalid_sa_lcp_repeat(self):
        request = {"task": "suffix", "text": "ababcdcd"}
        expected = oracles.suffix_result(request['text'])
        self.assertEqual(len(expected['repeated']), 2)
        for repeated in ('ab', 'cd'):
            self.assertTrue(check(request, dict(expected, repeated=repeated), expected))
        self.assertFalse(check(request, dict(expected, repeated='xy'), expected))
        self.assertFalse(check(request, dict(expected, sa=list(reversed(expected['sa']))), expected))
        self.assertFalse(check(request, dict(expected, lcp=[0] * 8), expected))


if __name__ == '__main__':
    unittest.main(verbosity=2)
