"""
prepare_data.py - Step 1 of Milestone 2.

There is no outside dataset, so "preparing the data" means:
  1. Enumerate the whole 2x2 state space with one breadth first sweep from
     the solved cube. This gives the true optimal distance for all 3,674,160
     states ("God's table"), which is the ground truth used to check the
     solvers.
  2. Look at the distribution of distances (the cube version of class
     imbalance).
  3. Build test sets: a stratified set with the same number of states at
     every depth, plus a uniform random set that matches what a real
     scramble looks like.

Outputs go to ../data/
"""
import json
import os
import random
import time

import numpy as np

from cube import (N_STATES, N_ORI, PERM_MOVE, ORI_MOVE, SOLVED_STATE, N_MOVES,
                  decode, MOVE_NAMES, MOVE_FACE)

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA, exist_ok=True)
SEED = 425


def enumerate_states():
    ptab = np.array(PERM_MOVE, dtype=np.int32)
    otab = np.array(ORI_MOVE, dtype=np.int32)
    dist = np.full(N_STATES, 255, dtype=np.uint8)
    dist[SOLVED_STATE] = 0
    frontier = np.array([SOLVED_STATE], dtype=np.int64)
    depth = 0
    while frontier.size:
        p, o = frontier // N_ORI, frontier % N_ORI
        nxt = (ptab[p] * N_ORI + otab[o]).ravel()      # all 9 children at once
        nxt = np.unique(nxt)
        nxt = nxt[dist[nxt] == 255]
        depth += 1
        dist[nxt] = depth
        frontier = nxt
    return dist


def random_scramble(rng, n):
    moves, last = [], -1
    while len(moves) < n:
        m = rng.randrange(N_MOVES)
        if MOVE_FACE[m] != last:
            moves.append(m)
            last = MOVE_FACE[m]
    return moves


def main():
    t0 = time.perf_counter()
    dist = enumerate_states()
    secs = time.perf_counter() - t0
    assert (dist != 255).all(), "some states were never reached"
    np.save(os.path.join(DATA, "gods_table.npy"), dist)

    counts = np.bincount(dist)
    total = int(counts.sum())
    print(f"Enumerated {total:,} states in {secs:.1f}s; max depth {len(counts) - 1}")
    print(f"{'depth':>5} {'states':>10} {'percent':>8}")
    for d, c in enumerate(counts):
        print(f"{d:>5} {c:>10,} {100 * c / total:>7.3f}%")
    mean = (np.arange(len(counts)) * counts).sum() / total
    print(f"mean optimal distance {mean:.3f}")

    stats = {"total_states": total, "enumeration_seconds": round(secs, 2),
             "max_depth": len(counts) - 1, "mean_depth": round(float(mean), 4),
             "depth_counts": counts.tolist()}
    with open(os.path.join(DATA, "state_space_stats.json"), "w") as f:
        json.dump(stats, f, indent=2)

    rng = random.Random(SEED)
    # Stratified test set: 10 states at every depth 1..11 (depth 11 has
    # only 2,644 states, so random sampling alone would almost never hit it).
    stratified = []
    for d in range(1, len(counts)):
        idx = np.flatnonzero(dist == d)
        pick = rng.sample(idx.tolist(), min(10, idx.size))
        stratified += [{"state": int(s), "optimal": d,
                        "facelets": decode(int(s)).to_facelets()} for s in pick]

    # Uniform random states: what a "real" fully random cube looks like.
    uniform = []
    for s in rng.sample(range(N_STATES), 50):
        uniform.append({"state": s, "optimal": int(dist[s]),
                        "facelets": decode(s).to_facelets()})

    # Move scrambles of length 1..15, the way a person mixes the cube in the UI.
    scrambles = []
    for n in range(1, 16):
        for _ in range(3):
            ms = random_scramble(rng, n)
            s = SOLVED_STATE
            for m in ms:
                p, o = divmod(s, N_ORI)
                s = PERM_MOVE[p][m] * N_ORI + ORI_MOVE[o][m]
            scrambles.append({"scramble": " ".join(MOVE_NAMES[m] for m in ms),
                              "scramble_length": n, "state": s,
                              "optimal": int(dist[s]),
                              "facelets": decode(s).to_facelets()})

    with open(os.path.join(DATA, "test_sets.json"), "w") as f:
        json.dump({"seed": SEED, "stratified": stratified, "uniform": uniform,
                   "scrambles": scrambles}, f, indent=1)
    print(f"test sets: stratified={len(stratified)} uniform={len(uniform)} "
          f"scrambles={len(scrambles)}")


if __name__ == "__main__":
    main()
