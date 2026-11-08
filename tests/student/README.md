# Student verification

Run from the repository root using Python 3.12+; no third-party packages are required.

```sh
python tools/run.py --language Python --setup
python tools/run.py --language Python --check
python -m unittest discover -s tests/student -p "test_algorithms.py" -v
python tests/student/capture_evidence.py
python tests/student/scale_checks.py
python tools/run.py --language Python --input tests/student/inputs.jsonl
python tests/student/benchmark_search.py
```

Recorded results: **21 unittest methods**, **25 fixtures** and **13 scale batches
containing 24 requests** passed. The mixed transport test sends all 25 fixtures
three times, giving 75 requests in a single persistent process. Actual results
are preserved in the files below; timings are observations from the local
Windows environment, not a guarantee about other machines.

| File | Purpose |
|---|---|
| `test_algorithms.py` | Small deterministic oracle comparisons, boundary cases, semantic witnesses, and mixed-request state reset. |
| `oracles.py` | Independent reference models used only by tests. |
| `cases.json` | 25 inputs, justified example expected outputs, and the defect each case detects. |
| `inputs.jsonl`, `expected_outputs.jsonl` | The same cases in JSON Lines form. |
| `actual_outputs.jsonl` | Actual output captured from the supplied Python entry point. |
| `capture_evidence.py`, `test_results.txt` | Reproduce fixture checks and save actual unittest results and runtime metadata. |
| `scale_checks.py`, `scale_results.json` | Full-domain generators and actual subprocess timings, validation status, output sizes, and input/output SHA-256 hashes. |
| `benchmark_search.py`, `benchmark_results.json` | Reproducible naive/KMP/RK comparison and its actual measurements; see `ANALYSIS.md`. |

`tools/run.py --input` prints answers without comparing them. The evidence
capture script performs semantic comparison against the expected answers.

## Independent expected answers

The oracles deliberately use different methods from the required implementations:

- LCS enumerates subsequences of the shorter input and checks membership in the
  other string, instead of using prefix DP.
- Merge enumerates legal adjacent merge schedules with memoization of the
  current block-size tuple, instead of using interval DP and split reconstruction.
- Tree selection enumerates all vertex subsets and filters adjacent vertices;
  random relabeling also checks that changing the root identity preserves value.
- Exact-search and dictionary expected counts use Python's built-in `find` in
  tests only, advancing by one position so overlaps count. Implementation code
  must implement the assigned algorithms itself.
- Suffix order uses literal character-by-character suffix comparison, followed
  by direct adjacent common-prefix comparisons. It uses neither rank doubling
  nor Kasai's reused prefix length and does not materialize all suffix strings.
- Seeds `4101` through `4106` make randomized small tests reproducible.

The supplied semantic validator checks reconstructed sequences, chronological
adjacent merge plans, independent vertex sets, and suffix/LCP/repeat witnesses
against these independently derived optimal values. Witness-checker tests
accept alternate valid LCSs, merge plans, selected sets and longest repeats;
they reject incorrect sequences, merge chronology, duplicate/adjacent selected
vertices, suffix order, LCP and repeated strings. Numeric Booleans are rejected.

The fixed fixtures cover empty cases, noncontiguous subsequences, ties, illegal
nonadjacent merge greediness, totals beyond 32 bits, negative weights, overlaps,
the final search boundary, longer patterns, the actual `ab`/`dj` base-31/mod-101
collision, suffix indexing, duplicate dictionary entries, suffix matches and
independent text state. Every fixture's `defect` field explains its expected
answer and the mistake it detects.

## Scale and transport

`scale_checks.py` runs each named batch through the real JSONL entry point with
a 20-second subprocess timeout and checks that output is at most 8 MiB. It checks
every answer semantically, not only program completion. Large input/output data
are transient; their deterministic generators, expected-value justifications,
actual byte counts and SHA-256 hashes are recorded instead of committing large
files.

The 13 batches cover:

- LCS: three pairs with 1000-by-1000 character dimensions.
- Merge: 200 blocks, including weights of `10^9` and zero costs. For equal
  weights the optimal external path length is `56*7 + 144*8 = 1544`, so the
  expected cost is `1544*10^9`.
- Tree: 100000-vertex chain, star and all-negative chain. Expected optimums
  follow from alternating chain vertices, all star leaves, and the empty set.
- Naive: length 3000 boundaries and dense overlapping matches.
- KMP: text length 200000, pattern length 100000, long prefix failures and empty
  pattern output of 200001 boundaries.
- RK: length product 20000000, maximum text/pattern lengths where permitted,
  dense true matches, longer patterns and many deliberate hash collisions.
- Suffix: length 50000, both all-equal and seeded printable-ASCII text. The
  repetitive case has closed-form suffix/LCP arrays; the random case uses the
  independent literal comparator. Seed: `4201`.
- Aho: 10000 duplicate patterns and 200000 text characters; a 100-by-10000 dense
  output matrix; one length-100000 pattern producing 100001 trie states; dense
  suffix patterns of lengths 1 through 446 plus duplicate length 319 (total
  pattern length 100000); and a wide printable-ASCII trie queried by 100 texts.
  The wide-trie generator uses seed `4202` and includes ASCII codes 32 and 126.

Each scale timing includes process launch, JSON parsing, algorithms and pipe
input/output, while excluding parent-side input generation, reference oracles
and validation. This differs intentionally from the algorithm-only comparison
benchmark. No container memory cap or CPU affinity was enforced on the local
Windows runs; the report does not claim measurements it did not perform.
