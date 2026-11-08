"""Measure exact searches on shared, independently verified input pairs."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import random
from statistics import median
import subprocess
import sys
from time import perf_counter_ns

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Python" / "source"))
import algorithms


def reference_positions(text, pattern):
    """Independent test oracle; slicing equality is not used by the algorithms."""
    return [i for i in range(len(text) - len(pattern) + 1)
            if text[i:i + len(pattern)] == pattern]


def generate_pair(kind, n, m, seed):
    if kind == "repetitive":
        return "a" * n, "a" * m
    rng = random.Random(seed)
    text = "".join(chr(rng.randrange(32, 127)) for _ in range(n))
    start = n // 3
    return text, text[start:start + m]


def candidate_count(text, pattern):
    """Count equal-hash windows independently; excluded from all timing."""
    def fingerprint(value):
        result = 0
        for character in value:
            result = (31 * result + ord(character)) % 101
        return result
    target = fingerprint(pattern)
    return sum(fingerprint(text[i:i + len(pattern)]) == target
               for i in range(len(text) - len(pattern) + 1))


def environment():
    result = {"python": sys.version, "implementation": platform.python_implementation(),
              "platform": platform.platform(), "processor": platform.processor(),
              "logical_cpus": os.cpu_count()}
    if platform.system() == "Windows":
        command = (
            "$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1; "
            "$sysinfo = Get-CimInstance Win32_ComputerSystem; "
            "@{cpu=$cpu.Name; physical_cores=$cpu.NumberOfCores; "
            "ram_bytes=$sysinfo.TotalPhysicalMemory} | ConvertTo-Json -Compress"
        )
        try:
            result.update(json.loads(subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", command],
                text=True, timeout=20)))
        except (OSError, ValueError, subprocess.SubprocessError):
            result["hardware_note"] = "Detailed hardware query unavailable."
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "tests" / "student" / "benchmark_results.json")
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    if args.repeats < 3:
        parser.error("At least three timings per algorithm are required.")
    report = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "command": "python tests/student/benchmark_search.py",
        "environment": environment(),
        "timer": "time.perf_counter_ns; times converted to milliseconds",
        "warmup": "One untimed verified call per algorithm per pair; CPython has no JIT",
        "scope": "One direct algorithm call, including preprocessing and output allocation; excludes generation, oracle, hash-candidate counting, JSON parsing/serialization, validation, I/O, and compilation",
        "order": "Rotate naive,kmp,rk order by repetition index modulo 3",
        "generators": {
            "random": "random.Random(seed); n uniform printable ASCII characters (codes 32..126); pattern=text[n//3:n//3+m]",
            "repetitive": "text='a'*n, pattern='a'*m; all n-m+1 starts match",
        },
        "oracle": "For each start, compare independently sliced text window with pattern; check exact positions from all three algorithms before timing and after every timed call",
        "cases": [],
    }
    collision = {"text": "abdj", "pattern": "ab"}
    for name in ("naive", "kmp", "rk"):
        assert getattr(algorithms, name)(collision) == {"positions": [0]}
    report["collision_check"] = {
        "text": "abdj", "pattern": "ab", "expected_positions": [0],
        "hash_ab": 75, "hash_dj": 75, "all_three_passed": True,
    }
    names = ["naive", "kmp", "rk"]
    for kind in ("random", "repetitive"):
        for n, m, seed in ((500, 50, 43101), (1500, 150, 43102), (3000, 300, 43103)):
            text, pattern = generate_pair(kind, n, m, seed)
            expected = {"positions": reference_positions(text, pattern)}
            request = {"text": text, "pattern": pattern}
            encoded = json.dumps(request, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
            case = {"kind": kind, "n": n, "m": m,
                    "seed": seed if kind == "random" else None,
                    "input_sha256": hashlib.sha256(encoded).hexdigest(),
                    "occurrences": len(expected["positions"]),
                    "expected_positions": expected["positions"],
                    "equal_hash_candidates": candidate_count(text, pattern),
                    "methods": {}}
            for name in names:
                actual = getattr(algorithms, name)(request)
                assert actual == expected, (kind, n, name, actual, expected)
            samples = {name: [] for name in names}
            for repetition in range(args.repeats):
                offset = repetition % len(names)
                for name in names[offset:] + names[:offset]:
                    method = getattr(algorithms, name)
                    started = perf_counter_ns()
                    actual = method(request)
                    elapsed_ms = (perf_counter_ns() - started) / 1_000_000
                    assert actual == expected, (kind, n, name)
                    samples[name].append(elapsed_ms)
            for name, values in samples.items():
                case["methods"][name] = {"milliseconds": values, "median_ms": median(values)}
            case["verified"] = True
            report["cases"].append(case)
            print(json.dumps({key: value for key, value in case.items()
                              if key != "expected_positions"}), flush=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Saved measurements: {args.output}")


if __name__ == "__main__":
    main()
