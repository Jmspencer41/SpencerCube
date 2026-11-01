"""
main.py - terminal version of the full pipeline: Input -> Processing -> Output.

Examples
    python main.py --scramble "R U2 F' R U F2 R'"
    python main.py --stickers "GWWO RRYB ..."  (24 colors, order U R F D L B)
    python main.py --scramble "R U F" --algorithm bfs
"""
import argparse

from cube import (SOLVED_FACELETS, MOVES, CubieCube, normalize_colors, encode, decode,
                  parse_moves, apply_sequence_facelets, net)
from solver import SOLVERS, verify

DEFAULT_COLORS = dict(zip("URFDLB", "WRGYOB"))   # white top, green front


def solve(stickers, algorithm="astar-pdb"):
    # 1. Input preprocessing: colors -> face letters -> cubie model -> integer state
    facelets, colors = normalize_colors(stickers)
    cube = CubieCube.from_facelets(facelets)      # validates the cube
    start = encode(cube)
    # 2. AI search
    result = SOLVERS[algorithm](start)
    # 3. Output: move list, plus check it really solves the cube
    final = decode(start)
    for m in result.moves:
        final = final.multiply(MOVES[m])
    assert verify(start, result.moves) and final.is_solved()
    return facelets, colors, result, final.to_facelets()


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--scramble", help="moves applied to a solved cube, e.g. \"R U F2\"")
    g.add_argument("--stickers", help="24 sticker colors in U R F D L B order")
    ap.add_argument("--algorithm", default="astar-pdb", choices=SOLVERS)
    a = ap.parse_args()

    if a.scramble:
        f = apply_sequence_facelets(SOLVED_FACELETS, parse_moves(a.scramble))
        stickers = "".join(DEFAULT_COLORS[c] for c in f)
    else:
        stickers = a.stickers

    facelets, colors, r, final = solve(stickers, a.algorithm)
    print("INPUT (scrambled cube):")
    print(net(facelets, colors))
    print(f"\nSEARCH: {r.algorithm}")
    print(f"  solution ({r.length} moves): {r.move_string}")
    print(f"  nodes expanded: {r.expanded:,}   generated: {r.generated:,}   "
          f"time: {r.seconds * 1000:.1f} ms")
    print("\nOUTPUT (after applying solution):")
    print(net(final, colors))


if __name__ == "__main__":
    main()
