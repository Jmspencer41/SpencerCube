"""make_charts.py - figures for the Milestone 2 report (writes ../results/*.png)"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "..", "data")
OUT = os.path.join(HERE, "..", "results")

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SERIES = {"BFS": "#2a78d6", "A* (corners)": "#eb6834", "A* (pdb)": "#1baf7a"}
SEQ = "#2a78d6"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2,
    "ytick.color": INK2, "text.color": INK, "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
})


def depth_distribution():
    with open(os.path.join(DATA, "state_space_stats.json")) as f:
        s = json.load(f)
    counts = s["depth_counts"]
    depths = range(len(counts))
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    bars = ax.bar(depths, counts, color=SEQ, width=0.72)
    for d, c in zip(depths, counts):
        if c >= 600_000 or d in (0, 11):
            pct = 100 * c / s["total_states"]
            ax.text(d, c * 1.15, f"{c:,}\n({pct:.1f}%)" if pct >= 0.1 else f"{c:,}",
                    ha="center", va="bottom", fontsize=8, color=INK2)
    ax.set_yscale("log")
    ax.set_ylim(0.5, 2e7)
    ax.set_xticks(list(depths))
    ax.set_xlabel("Optimal solution length (moves, half turn metric)")
    ax.set_ylabel("Number of states (log scale)")
    ax.set_title("2x2 state space by distance from solved (3,674,160 states)",
                 loc="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig1_depth_distribution.png"), dpi=180)


def nodes_by_depth(metric, fname, ylabel, title):
    with open(os.path.join(OUT, "summary.json")) as f:
        s = json.load(f)
    fig, ax = plt.subplots(figsize=(7.5, 4))
    for alg, color in SERIES.items():
        bd = s[alg]["by_depth"]
        xs = [int(d) for d in bd]
        ys = [max(bd[d][metric], 0.01) for d in bd]
        ax.plot(xs, ys, color=color, lw=2, marker="o", ms=5, label=alg)
        ax.annotate(alg, (xs[-1], ys[-1]), xytext=(6, 0), textcoords="offset points",
                    va="center", fontsize=9, color=INK)
    ax.set_yscale("log")
    ax.set_xticks(range(1, 12))
    ax.set_xlim(0.6, 12.6)
    ax.set_xlabel("Optimal solution length of the test state (moves)")
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left", fontsize=11)
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), dpi=180)


if __name__ == "__main__":
    depth_distribution()
    nodes_by_depth("mean_expanded", "fig2_nodes_expanded.png",
                   "Mean nodes expanded (log scale)",
                   "Search effort by depth (10 test states per depth)")
    nodes_by_depth("mean_ms", "fig3_runtime.png", "Mean time per solve, ms (log scale)",
                   "Solve time by depth (pure Python, single thread)")
    print("charts written")
