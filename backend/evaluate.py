"""
evaluate.py - Step 3: run every solver on the test sets and check results
against the ground truth distances from prepare_data.py.

Writes ../results/results.csv and ../results/summary.json
"""
import csv
import json
import os
import statistics as st
from collections import defaultdict

from cube import CubieCube, encode
from solver import SOLVERS, verify

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(HERE, "..", "results")
os.makedirs(OUT, exist_ok=True)


def main():
    with open(os.path.join(DATA, "test_sets.json")) as f:
        sets = json.load(f)

    rows = []
    for set_name in ("stratified", "uniform", "scrambles"):
        for case in sets[set_name]:
            start = encode(CubieCube.from_facelets(case["facelets"]))
            assert start == case["state"]
            for alg, fn in SOLVERS.items():
                r = fn(start)
                rows.append({
                    "set": set_name, "algorithm": r.algorithm, "optimal": case["optimal"],
                    "length": r.length, "is_optimal": r.length == case["optimal"],
                    "solves_cube": verify(start, r.moves),
                    "expanded": r.expanded, "generated": r.generated,
                    "max_frontier": r.max_frontier, "ms": round(r.seconds * 1000, 3),
                    "solution": r.move_string,
                })
        print("done", set_name)

    with open(os.path.join(OUT, "results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    summary = {}
    by_alg = defaultdict(list)
    for r in rows:
        by_alg[r["algorithm"]].append(r)
    for alg, rs in by_alg.items():
        per_depth = defaultdict(list)
        for r in rs:
            if r["set"] == "stratified":
                per_depth[r["optimal"]].append(r)
        uni = [r for r in rs if r["set"] == "uniform"]
        summary[alg] = {
            "cases": len(rs),
            "solved": sum(r["solves_cube"] for r in rs),
            "optimal": sum(r["is_optimal"] for r in rs),
            "uniform_mean_expanded": round(st.mean(r["expanded"] for r in uni)),
            "uniform_mean_ms": round(st.mean(r["ms"] for r in uni), 1),
            "uniform_max_ms": round(max(r["ms"] for r in uni), 1),
            "by_depth": {d: {"mean_expanded": round(st.mean(x["expanded"] for x in v)),
                             "mean_ms": round(st.mean(x["ms"] for x in v), 2)}
                         for d, v in sorted(per_depth.items())},
        }
    with open(os.path.join(OUT, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    for alg, s in summary.items():
        print(f"\n{alg}: solved {s['solved']}/{s['cases']}, optimal {s['optimal']}/{s['cases']}, "
              f"uniform: {s['uniform_mean_expanded']:,} nodes avg, "
              f"{s['uniform_mean_ms']} ms avg, {s['uniform_max_ms']} ms max")
        for d, v in s["by_depth"].items():
            print(f"   depth {d:>2}: {v['mean_expanded']:>10,} nodes  {v['mean_ms']:>10} ms")


if __name__ == "__main__":
    main()
