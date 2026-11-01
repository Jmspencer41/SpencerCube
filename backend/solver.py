"""
solver.py - search algorithms for the 2x2 cube.

    bfs(start)                  baseline, uninformed, optimal
    astar(start, "corners")     A* with a simple admissible heuristic
    astar(start, "pdb")         A* with pattern database heuristic (Korf style)

All three return the same SearchResult so they can be compared directly.
Every solver is optimal in the half turn metric (each of the 9 moves = 1).
"""
import heapq
import time
from collections import deque
from dataclasses import dataclass, field

from cube import (N_MOVES, MOVE_NAMES, MOVE_FACE, N_ORI, N_PERM, PERM_MOVE, ORI_MOVE,
                  SOLVED_STATE, PERMS, index_to_ori, apply_move)


@dataclass
class SearchResult:
    algorithm: str
    moves: list                      # list of move indices
    expanded: int                    # nodes taken off the frontier and expanded
    generated: int                   # child states created
    max_frontier: int
    seconds: float
    solved: bool = True

    @property
    def length(self):
        return len(self.moves)

    @property
    def move_string(self):
        return " ".join(MOVE_NAMES[m] for m in self.moves) or "(already solved)"


def _children(state, last_face):
    """Yield (move, child). Skips turning the same face twice in a row,
    since U then U2 is just U' and adds nothing new."""
    p, o = divmod(state, N_ORI)
    prow, orow = PERM_MOVE[p], ORI_MOVE[o]
    for m in range(N_MOVES):
        if MOVE_FACE[m] == last_face:
            continue
        yield m, prow[m] * N_ORI + orow[m]


def _rebuild(parent, state):
    path = []
    while True:
        prev, m = parent[state]
        if prev is None:
            break
        path.append(m)
        state = prev
    return path[::-1]


# ---------------------------------------------------------------------------
# Baseline: breadth first search
# ---------------------------------------------------------------------------
def bfs(start):
    t0 = time.perf_counter()
    if start == SOLVED_STATE:
        return SearchResult("BFS", [], 0, 0, 1, time.perf_counter() - t0)
    parent = {start: (None, None)}
    last = {start: -1}
    frontier = deque([start])
    expanded = generated = max_frontier = 0
    while frontier:
        max_frontier = max(max_frontier, len(frontier))
        s = frontier.popleft()
        expanded += 1
        for m, child in _children(s, last[s]):
            generated += 1
            if child in parent:
                continue
            parent[child] = (s, m)
            last[child] = MOVE_FACE[m]
            if child == SOLVED_STATE:                 # goal test on generation
                return SearchResult("BFS", _rebuild(parent, child), expanded,
                                    generated, max_frontier, time.perf_counter() - t0)
            frontier.append(child)
    return SearchResult("BFS", [], expanded, generated, max_frontier,
                        time.perf_counter() - t0, solved=False)


# ---------------------------------------------------------------------------
# Heuristics
# ---------------------------------------------------------------------------
def h_corners(state):
    """Count corners that are out of place or twisted. One move touches at most
    4 corners, so ceil(wrong / 4) never overestimates. Admissible but weak."""
    p, o = divmod(state, N_ORI)
    cp, co = PERMS[p], index_to_ori(o)
    wrong = sum(1 for i in range(8) if cp[i] != i or co[i] != 0)
    return (wrong + 3) // 4


def _pattern_db(size, table, goal):
    """BFS over one abstraction (just permutation or just orientation)."""
    dist = [-1] * size
    dist[goal] = 0
    q = deque([goal])
    while q:
        x = q.popleft()
        for m in range(N_MOVES):
            y = table[x][m]
            if dist[y] < 0:
                dist[y] = dist[x] + 1
                q.append(y)
    return dist


_SOLVED_P, _SOLVED_O = divmod(SOLVED_STATE, N_ORI)
PERM_DB = _pattern_db(N_PERM, PERM_MOVE, _SOLVED_P)    # 5,040 entries
ORI_DB = _pattern_db(N_ORI, ORI_MOVE, _SOLVED_O)       # 729 entries


def h_pdb(state):
    """Max of two pattern databases: moves needed to fix only the corner
    positions, and moves needed to fix only the twists. Each is a lower bound
    on the real distance, so the max is too (Korf 1997)."""
    p, o = divmod(state, N_ORI)
    return max(PERM_DB[p], ORI_DB[o])


HEURISTICS = {"corners": h_corners, "pdb": h_pdb}


# ---------------------------------------------------------------------------
# A* search
# ---------------------------------------------------------------------------
def astar(start, heuristic="pdb"):
    h = HEURISTICS[heuristic]
    name = f"A* ({heuristic})"
    t0 = time.perf_counter()
    g = {start: 0}
    parent = {start: (None, None)}
    last = {start: -1}
    counter = 0
    # (f, -g, tiebreak, state): on equal f prefer deeper nodes
    heap = [(h(start), 0, counter, start)]
    closed = set()
    expanded = generated = max_frontier = 0
    while heap:
        max_frontier = max(max_frontier, len(heap))
        f, neg_g, _, s = heapq.heappop(heap)
        if s in closed:
            continue
        if s == SOLVED_STATE:
            return SearchResult(name, _rebuild(parent, s), expanded, generated,
                                max_frontier, time.perf_counter() - t0)
        closed.add(s)
        expanded += 1
        gs = g[s] + 1
        for m, child in _children(s, last[s]):
            generated += 1
            if child in closed or gs >= g.get(child, 1 << 30):
                continue
            g[child] = gs
            parent[child] = (s, m)
            last[child] = MOVE_FACE[m]
            counter += 1
            heapq.heappush(heap, (gs + h(child), -gs, counter, child))
    return SearchResult(name, [], expanded, generated, max_frontier,
                        time.perf_counter() - t0, solved=False)


SOLVERS = {
    "bfs": bfs,
    "astar-corners": lambda s: astar(s, "corners"),
    "astar-pdb": lambda s: astar(s, "pdb"),
}


def verify(start, moves):
    s = start
    for m in moves:
        s = apply_move(s, m)
    return s == SOLVED_STATE
