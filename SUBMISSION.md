# Assignment 4 submission

Selected language: **Python 3.12+** (`submission.json`).

The implementation is in `Python/source/algorithms.py`; the template's JSON
Lines transport and public validator are preserved. Each request is independent.
No third-party Python packages or compilation step are required.

Run from the repository root:

```sh
python --version
python tools/run.py --setup
python tools/run.py --check
python tools/run.py --input examples/lcs.jsonl
python -m unittest discover -s tests/student -p "test_*.py" -v
python tests/student/scale_checks.py
python tests/student/capture_evidence.py
python tests/student/benchmark_search.py
```

See `ANALYSIS.md` for correctness arguments, reconstruction, time and memory
bounds, test evidence, measured search comparisons, and source/AI attribution.
Student tests and reproducible generators are under `tests/student`.

For Moodle, submit the exact GitHub commit URL (full 40-character SHA), the
language **Python 3.12**, and optionally the successful Public checks run URL
for that same commit. The separately assessed individual defence is not part
of this code submission.
