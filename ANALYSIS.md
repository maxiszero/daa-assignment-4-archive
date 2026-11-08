# Assignment 4 — analysis

## Environment and reproducibility

Selected language: **Python**, using CPython **3.12.6**, 64-bit, on Windows 10
build 19045. Hardware reported by Windows: Intel Core i5-13450HX, 10 physical
cores / 16 logical processors, 16,873,545,728 bytes RAM (about 15.71 GiB).
All algorithms use only the Python standard library. No compilation or package
installation is needed. The supplied launcher and UTF-8 JSON Lines adapter are
preserved. Each request creates its own algorithm state; stdout contains only
one JSON result per request. Printable ASCII is the specified string domain.
Python integers preserve the required exact costs and counts beyond 32 bits.

Run from the repository root:

```sh
python --version
python tools/run.py --setup
python tools/run.py --check
python tools/run.py --input examples/lcs.jsonl
python -m unittest discover -s tests/student -p "test_*.py" -v
python tests/student/capture_evidence.py
python tests/student/scale_checks.py
python tests/student/benchmark_search.py
```

The selected source is `Python/source/algorithms.py`. Tests, input generators,
expected answers, actual answers and measured logs are in `tests/student/`.
Submit the exact assessed commit and corresponding GitHub Actions run in
Moodle. The practical submission is separate from the individual defence quiz.

## Algorithm explanations

### 1. LCS: prefix DP and reconstruction

Let `dp[i][j]` be the maximum common subsequence length of `a[:i]` and `b[:j]`.
The zero row and column are zero: an empty prefix has no nonempty subsequence.
If `a[i-1] == b[j-1]`, append that character to an optimum for the shorter
prefixes: `dp[i][j] = dp[i-1][j-1] + 1`. An optimal common subsequence can use
the equal final characters; deleting them leaves the shorter-prefix problem.
Otherwise at least one of the two unequal final characters is unused, so
`dp[i][j] = max(dp[i-1][j], dp[i][j-1])`. Increasing rows and columns compute
every dependency before it is read. Induction on the prefix lengths proves
that every cell is optimal.

Starting at `(len(a), len(b))`, equal characters are recorded and both indices
decrease. On a mismatch, move to a neighbour with the same optimum, preferring
the upper neighbour on a tie. Reverse the recorded characters. Each move
preserves an optimal remaining solution, so the result is a subsequence of
both inputs with the required length. Either empty input returns zero and an
empty sequence immediately.

Time and auxiliary memory are O((n+1)(m+1)); reconstruction takes O(n+m) time
and O(min(n,m)+1) additional/output storage. Input storage is O(n+m+1).
`tea_time` versus `team` must return length 4: this catches confusing a
subsequence with a contiguous substring. `ab`/`ba` checks tied optima.

### 2. Ordered merging: interval DP and chronological plan

Let `dp[l][r]` be the minimum cost of combining original blocks `l..r` into
one block. A singleton costs zero. Prefix sums give the size of any interval
in O(1). In the final merge, the two children must be adjacent intervals
`[l,k]` and `[k+1,r]`, for some `l <= k < r`. Therefore

```
dp[l][r] = min_k(dp[l][k] + dp[k+1][r] + prefix[r+1] - prefix[l])
```

Every valid plan has such a last split. Conversely, two optimal child plans
followed by their merge form a valid plan. This proves the recurrence by
induction on interval length. Intervals are processed from short to long.
The first minimizing split is saved; ties keep it.

An explicit stack emits both child plans before `[l,k,r]`. Consequently the
required two blocks already exist when each operation executes. Original
indices are retained, and a binary merge tree with n leaves emits exactly
n-1 operations. No blocks or one block returns cost zero and an empty plan.

For n>=1, time is O(n^3), DP/split storage O(n^2), and reconstruction stack
and output O(n). The empty case is O(1). Input storage is O(n+1).
`[1,100,1]` has ordered optimum 203: unrestricted merging would wrongly merge
the nonadjacent ones first and obtain 104. Zero sizes test tied splits;
large sizes test arithmetic beyond 32 bits.

### 3. Tree independent set: take/skip DP

Root the valid input tree at vertex 0 and build an iterative parent/order
traversal. Each child is discovered after its parent, so reversing the order
places every child before its parent. Define `take[v]` as the best subtree
weight when v is selected, and `skip[v]` when it is excluded:

```
take[v] = weights[v] + sum(skip[child])
skip[v] = sum(max(take[child], skip[child]))
```

A selected parent excludes each child; an excluded parent leaves independent
choices in separate child subtrees. Subtrees have no cross edges because the
input is a tree. These facts establish the recurrence and its optimum by
postorder induction. Leaves start with their own weight and skip value zero.
The answer is `max(take[0],skip[0])`; root choice affects only the computation.

Reconstruction carries the parent's decision on an explicit stack. Select v
only when its parent was excluded and `take[v] > skip[v]`; ties prefer skip.
Children then receive the chosen decision. This creates an independent set
with optimal weight and no repeated vertices. Empty and all-negative trees
return the empty set with weight zero. Both traversals avoid recursion limits.

Time, auxiliary storage and maximum output storage are O(n+1); input adjacency
data is also O(n+1). A 100,000-vertex chain checks depth safety, a large star
checks summation and reconstruction, and `[4,9,6]` on a path checks the optimum
`[0,2]` of weight 10 rather than the locally largest vertex.

### 4a. Naive exact search

For a nonempty pattern, try every start from 0 through n-m inclusive. Compare
characters from left to right; at comparison j, the first j characters match.
Report a start only after all m comparisons succeed. Every possible occurrence
has exactly one such start, so none is missed or invented. Incrementing the
start by one preserves overlaps. If m>n the loop is empty. An empty pattern
returns all n+1 boundaries before any pattern access.

Time is O(n*m+n+1), O(1) auxiliary memory, and O(z+1) output memory for z
positions. Input storage is O(n+m+1). `aaaaa`/`aaa` must give `[0,1,2]`;
`abc`/empty must include the final boundary 3.

### 4b. KMP

`pi[i]` is the length of the longest proper prefix of the pattern that is also
a suffix of `pattern[:i+1]`. Prefix preprocessing extends the current border
on equality and otherwise follows `pi[matched-1]` until an extendable border
or zero is found. All shorter candidate borders are represented by that chain.

During the text scan, `matched` is the length of a pattern prefix matching a
suffix of the text processed so far. A mismatch uses the same fallback chain,
without moving the text cursor backwards. When `matched == m`, report the
start and fall back to `pi[m-1]`, preserving a possible overlapping occurrence.
The invariant proves exactness and completeness. Empty patterns return every
boundary before preprocessing; longer-than-text patterns return no starts.

Each forward character step increases `matched` by at most one, and every
fallback decreases it. Thus preprocessing and scanning have linear total
fallback work: O(n+m+z+1) time, O(m+1) auxiliary memory and O(z+1) output
memory. Input storage is O(n+m+1). `abababa`/`aba` gives `[0,2,4]`; long
almost-matching repetitive patterns exercise fallback rather than restarting.

### 4c. Exact Rabin–Karp

Use ASCII codes, base B=31 and modulus M=101, with the leftmost character at
the highest power. Hash the pattern and first length-m window by repeated
`h = (B*h + ord(character)) % M`. With `high = B^(m-1) mod M`, update by

```
next_hash = ((hash - ord(outgoing)*high)*B + ord(incoming)) % M
```

Removing the first term and shifting the remaining powers gives precisely
the polynomial hash of the next window. Python's remainder with positive M
normalizes the result into 0..100. Unequal hashes reject a window, but equal
hashes trigger individual character comparisons. Equal strings necessarily
have equal hashes; verification rejects collisions. This proves exactness.
All starts, including overlaps, are considered. Handle m=0 and m>n before
forming the initial window.

For 1<=m<=n, time is O(n+m+c*m), where c is the number of equal-hash candidate
windows. The modular exponentiation costs O(log m), absorbed by preprocessing.
A bound covering empty/longer patterns is O(n*m+n+m+1); deterministic linear
worst-case time is not claimed. Rolling state uses O(1) auxiliary storage,
excluding O(z+1) output and O(n+m+1) input storage. `ab` and `dj` both hash to
75, so `abdj`/`ab` must return only `[0]`.

### 5. Prefix-doubling suffix array and Kasai LCP

Initially each suffix rank is its first ASCII character. At width w, sorting
indices by `(rank[i], rank[i+w])` orders prefixes of length 2w. A missing
second half has rank -1, smaller than every character/rank. Assign new equal
ranks exactly to equal pairs, and double w. Inductively ranks describe the
prefixes they cover. Stop when all ranks are distinct or the width covers the
whole text. The resulting array orders all and only the n nonempty suffixes.
Only indices and ranks are stored; no list of materialized suffix strings is
built. Empty text returns three empty outputs; one character needs no rounds.

For Kasai, build inverse suffix positions and visit text starts in increasing
order. Compare a suffix with its preceding suffix in SA, storing the length
in `lcp[inverse[start]]`. After advancing the text start, reuse at least the
previous common length minus one: deleting the first common character retains
that shared prefix, and the new immediate predecessor shares at least as much
as the shifted previous candidate. Reset at SA position zero. Each successful
extension increases the reused length and each step decreases it by at most
one, so total extension work is O(n). `lcp[0]` is zero.

Suffixes sharing a prefix form a contiguous interval in lexicographic order.
Any repeated substring therefore appears in an adjacent pair's common prefix,
and every adjacent common prefix is a repeat at two distinct starts. Taking
the maximum LCP and slicing that substring yields a longest repeat; overlaps
are allowed. Ties keep the first maximum encountered during text-order scanning.

Python comparison sorting of rank pairs gives O(n log^2(n+1)) worst-case time
for doubling; Kasai adds O(n). Auxiliary and output storage are O(n+1), including
sort keys/workspace, rank arrays and the returned repeat. Input storage is
O(n+1). `banana` gives SA `[5,3,1,0,4,2]`, LCP `[0,1,3,0,0,2]`, repeat `ana`.
All-equal text checks overlapping repeats and missing-suffix ordering.

### 6. Aho–Corasick dictionary counts

Insert all patterns into one trie. Keep a terminal state for each original
dictionary position: duplicate strings share a state while retaining separate
output columns. Each state has 95 compact signed-integer transition entries
(`array('i')`) indexed by ASCII code minus 32. Zero initially means a missing
trie edge and denotes root in the completed automaton.

Process real trie children in breadth-first order. A child's failure state is
the transition for its edge character from the parent's failure state. Missing
transitions inherit the corresponding completed failure transition. Failure
states are strictly shallower, so their rows are ready before use. Consequently
the scan state is always the longest suffix of consumed text that is a trie
prefix. Root's missing transitions stay at root.

For each independent text, reset state and a visit counter per state. Count
the state reached after every character, then traverse the BFS order backwards
and add each state's visits to its failure state. A terminal pattern matches
exactly when it is the current state or lies on that state's failure chain.
Propagation therefore counts every overlapping and suffix-pattern occurrence
without enumerating individual matches. Reading terminal counters in original
dictionary order gives correct duplicate columns. No inherited output lists
are copied. An empty text produces an all-zero count row; an empty dictionary gives one empty
row per text; no texts gives an empty result immediately.

Let L include duplicate pattern lengths, p be dictionary size, S the number
of trie states including root, and q the number of texts. Construction is
O(L+95*S+p), and each text costs O(|text|+S+p). Auxiliary memory is
O(95*S+p), including failure links, BFS order and one visit array. Output
memory is O(q*(p+1)+1), separately from input O(L+sum|text|+p+q+1).
The alphabet is fixed, and all counters use exact Python integers. Patterns
`he,she,he` on `sheshe,sheshe,empty` must give `[[2,2,2],[2,2,2],[0,0,0]]`.
Dense nested patterns and 10,000 duplicate dictionary entries check aggregation.

## Tests and observed results

The initial template's Python algorithm checks failed with TODO results; setup
alone passed. After implementation, all **44 public cases** and the repeated
88-request public batch passed. The public validator and workflow were not
changed. Independent review found no additional correctness issue.

Student evidence contains **21 unittest methods**, **25 explicit fixtures**,
a **75-request mixed JSONL batch**, and **13 scale batches / 24 requests**.
Small reference models enumerate subsequences, adjacent-merge schedules and
vertex subsets. Search uses built-in matching only in the test oracle; suffix
tests use literal suffix comparisons and direct LCP comparisons. Production
algorithms do not use those shortcuts. Semantic witness validation accepts
alternative optima and rejects impossible subsequences, premature/nonadjacent
merges, duplicate/adjacent selected vertices, and incorrect suffix results.

Every fixture's full input, expected result, actual result and intended defect
are available in [cases.json](tests/student/cases.json),
[expected_outputs.jsonl](tests/student/expected_outputs.jsonl) and
[actual_outputs.jsonl](tests/student/actual_outputs.jsonl). The test log is
[test_results.txt](tests/student/test_results.txt); all 25 fixtures and all
21 methods passed (observed unittest duration 0.103 seconds).

|Command|Representative input|Expected|Observed|Defect detected|
|---|---|---|---|---|
|LCS|`tea_time`, `team`|length 4 and a valid subsequence|length 4, `team`|Substring/subsequence confusion|
|merge|`[1,100,1]`|203, chronological adjacent plan|203, valid plan|Illegal nonadjacent greedy merges|
|tree|weights `[4,9,6]`, path 0–1–2|10, vertices 0 and 2|10, valid set|Locally greedy selection|
|naive/KMP/RK|`aaaaa`, `aaa`|`[0,1,2]`|All three agree|Lost overlaps|
|KMP|`abc`, empty pattern|`[0,1,2,3]`|All boundaries returned|Missing final empty-pattern start|
|RK|`abdjababdj`, `ab`|`[0,4,6]`|`[0,4,6]`|Hash collision reported as match|
|suffix|`banana`|SA/LCP above; repeat `ana`|Matches expected|Sentinel/indexing/Kasai errors|
|Aho|Repeated texts and duplicate/suffix patterns|Independent rows, equal duplicate columns|Oracle agreement|Leaked state or missed suffix matches|

Scale tests use actual subprocess JSONL transport and validate results, not
only successful termination. Each batch has a 20-second timeout and an 8 MiB
output check. The generator, independent expected-value justification, input
and output hashes, runtime and measured times are recorded in
[scale_results.json](tests/student/scale_results.json).
These were local Windows runs; CPU affinity and the official container memory
limit were not enforced. Passing these samples is evidence of domain coverage,
not a guarantee about all hidden tests or a promised mark.

|Scale batch|Requests|Observed seconds|UTF-8 output bytes|Result|
|---|---:|---:|---:|---|
|lcs_million_cells|3|0.301402|2085|PASS|
|merge_200_large_and_zero|2|0.192251|5074|PASS|
|tree_100000_chain_star_negative|3|0.331623|883438|PASS|
|naive_3000_limits|3|0.147899|20340|PASS|
|kmp_200000_100000_limits|3|0.120510|1877843|PASS|
|rk_20million_product_and_10000_length|3|0.791224|38945|PASS|
|suffix_50000_repetitive|1|0.275261|627810|PASS|
|suffix_50000_random_ascii|1|0.145941|388925|PASS|
|aho_10000_duplicates_dense_200000_text|1|0.056310|70015|PASS|
|aho_100_text_rows_10000_columns|1|0.149727|5000213|PASS|
|aho_100001_states_deep_failure_chain|1|0.633510|22|PASS|
|aho_dense_suffix_patterns_L100000|1|0.057461|3144|PASS|
|aho_wide_ascii_trie_100_texts|1|1.126621|2000213|PASS|

## Reproducible search comparison

Command: `python tests/student/benchmark_search.py`. Raw results, full input
hashes, seeds, expected occurrence lists and environment are in
[benchmark_results.json](tests/student/benchmark_results.json). Measurements
were made on 8 November 2026. All three methods use the exact same text/pattern
pair at each size, within the common domain (both lengths at most 3000).

Random cases use `random.Random(seed)` and independent uniform printable ASCII
characters (codes 32..126). The pattern is a slice beginning at `n//3`, ensuring
at least one occurrence. Seeds are 43101, 43102, 43103 for `(n,m)=(500,50), (1500,150),
(3000,300)`. Repetitive cases use text `a*n` and pattern `a*m`, with n-m+1
overlapping matches. They deliberately exercise expensive exact verification.

Before timing, an independent sliced-window equality oracle verifies all three
outputs. Each method gets one untimed verified warm-up call per pair. CPython
3.12 has no JIT. Each of the five measurements times one direct function call
using `perf_counter_ns`, including its preprocessing and output allocation.
Generation, oracle work, hash-candidate counting, JSON parsing/serialization,
I/O, validation and compilation are excluded. The same boundary applies to all
methods. Method order rotates each repetition; timed outputs are checked after
the timer stops. All checks passed. Times below are milliseconds; medians are
computed from the unrounded saved samples.

|Case|n|m|Method|Run 1|Run 2|Run 3|Run 4|Run 5|Median|
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
|random|500|50|naive|0.028500|0.026300|0.025700|0.026500|0.025800|0.026300|
|random|500|50|kmp|0.026200|0.025600|0.025000|0.025200|0.025100|0.025200|
|random|500|50|rk|0.064600|0.063600|0.063400|0.064500|0.063700|0.063700|
|random|1500|150|naive|0.085100|0.082700|0.084600|0.083400|0.085100|0.084600|
|random|1500|150|kmp|0.076300|0.075700|0.076000|0.077700|0.081300|0.076300|
|random|1500|150|rk|0.194200|0.199000|0.194700|0.197200|0.197600|0.197200|
|random|3000|300|naive|0.179000|0.172000|0.172600|0.168100|0.167200|0.172000|
|random|3000|300|kmp|0.148400|0.156100|0.150400|0.150200|0.149400|0.150200|
|random|3000|300|rk|0.400300|0.394000|0.398600|0.389500|0.394900|0.394900|
|repetitive|500|50|naive|0.960300|0.970400|0.972000|0.978800|0.972700|0.972000|
|repetitive|500|50|kmp|0.055000|0.054100|0.053000|0.052300|0.053900|0.053900|
|repetitive|500|50|rk|1.052400|1.052500|1.033800|1.080100|1.042700|1.052400|
|repetitive|1500|150|naive|9.129600|9.273600|9.197500|9.486100|9.061100|9.197500|
|repetitive|1500|150|kmp|0.171100|0.174800|0.172200|0.171100|0.170000|0.171100|
|repetitive|1500|150|rk|9.471400|9.245100|9.240400|9.320400|9.329800|9.320400|
|repetitive|3000|300|naive|37.421100|36.563500|37.744300|37.834200|36.295100|37.421100|
|repetitive|3000|300|kmp|0.376900|0.382300|0.372200|0.411600|0.365800|0.376900|
|repetitive|3000|300|rk|39.984600|37.190300|37.548700|37.706200|38.082200|37.706200|

On random inputs, most naive windows fail at their first character; KMP is
also fast, while this RK implementation pays rolling-hash arithmetic overhead.
At n=3000, their observed medians were about 0.172, 0.150 and 0.395 ms.
The equal-hash candidate counts for the three random sizes were 4, 25 and 23,
although each input had only one exact occurrence.

On repetitive inputs every candidate is a real match: c is 451, 1351 and 2701.
Naive and exact RK repeatedly compare m characters per window. At n=3000,
their medians were about 37.421 and 37.706 ms, versus 0.377 ms for KMP.
This is consistent with the stated candidate-sensitive and linear bounds,
but six measured cases and noisy wall-clock timings do not prove asymptotic
complexity or establish a ranking across all machines and distributions.

The mandated modulus 101 is a collision laboratory. Hash-equal windows must
always be verified; the supplied `ab`/`dj` example is checked separately and
correctly returns only the true occurrence. These collision rates do not
represent every production hash design using different moduli, multiple hashes
or randomized parameters. Even fewer accidental collisions would not remove
the cost of verifying numerous genuine matches in this exact implementation.

## Sources, AI assistance and verification responsibility

The sources used were the official [assignment specification](docs/Assignment_4_EN.md),
[contracts](docs/guide/CONTRACTS.md), [algorithm notes](docs/LECTURE_CLARIFICATIONS_EN_RU.md),
[testing guide](docs/guide/TESTING.md), [rubric](docs/guide/RUBRIC.md), and the
starter repository from [RZhaniya/daa-assignment-4-archive](https://github.com/RZhaniya/daa-assignment-4-archive).
The template supplied the JSONL adapter, launcher, public cases and validator.
No external implementation or algorithm library was copied.

OpenAI Codex assisted with implementing all eight Python algorithms, designing
student tests and independent small-case reference models, running checks and
benchmarks, writing this analysis, and reviewing the code. Actual automated
verification performed in this workspace is recorded in the linked evidence;
timings were measured, not estimated. The student's personal review or quiz
performance is not asserted here. The student remains responsible for reviewing
and understanding the submitted code, verifying its suitability and following
the course's attribution and independent-defence requirements.
