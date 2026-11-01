"""
cube.py - 2x2 Rubik's cube model for SpencerCube.

How the cube is represented
---------------------------
* Sticker (facelet) string: 24 characters, 4 per face, in the face order
  U R F D L B. This is the format the front end will send.

      Face layout (each face read left to right, top to bottom):

                  U0 U1
                  U2 U3
            L0 L1 F0 F1 R0 R1 B0 B1
            L2 L3 F2 F3 R2 R3 B2 B3
                  D0 D1
                  D2 D3

* Cubie model: corner permutation (cp) + corner orientation (co), the
  standard Kociemba style model. The down back left corner (DBL) is held
  fixed, so only U, R and F turns are needed. That gives 9 moves:
  U U2 U' R R2 R' F F2 F'.

* Coordinate (integer) model used by the search:
      state = perm_index * 729 + orient_index
  7! = 5040 permutations of the 7 free corners, 3^6 = 729 orientations
  (the 7th twist is forced by the others). 5040 * 729 = 3,674,160 states.
"""

from itertools import permutations
from collections import Counter

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FACES = "URFDLB"
SOLVED_FACELETS = "UUUURRRRFFFFDDDDLLLLBBBB"

URF, UFL, ULB, UBR, DFR, DLF, DBL, DRB = range(8)
CORNER_NAMES = ["URF", "UFL", "ULB", "UBR", "DFR", "DLF", "DBL", "DRB"]

# Sticker indices for each corner slot, listed U/D sticker first, then clockwise.
CORNER_FACELETS = [
    (3, 4, 9),     # URF
    (2, 8, 17),    # UFL
    (0, 16, 21),   # ULB
    (1, 20, 5),    # UBR
    (13, 11, 6),   # DFR
    (12, 19, 10),  # DLF
    (14, 23, 18),  # DBL
    (15, 7, 22),   # DRB
]
CORNER_COLORS = [tuple(name) for name in CORNER_NAMES]

# Basic quarter turns in "replaced by" form: corner at slot i comes from cp[i].
_BASIC = {
    "U": ([UBR, URF, UFL, ULB, DFR, DLF, DBL, DRB], [0, 0, 0, 0, 0, 0, 0, 0]),
    "R": ([DFR, UFL, ULB, URF, DRB, DLF, DBL, UBR], [2, 0, 0, 1, 1, 0, 0, 2]),
    "F": ([UFL, DLF, ULB, UBR, URF, DFR, DBL, DRB], [1, 2, 0, 0, 2, 1, 0, 0]),
}

MOVE_NAMES = ["U", "U2", "U'", "R", "R2", "R'", "F", "F2", "F'"]
MOVE_FACE = [0, 0, 0, 1, 1, 1, 2, 2, 2]          # which face each move turns
N_MOVES = len(MOVE_NAMES)


# ---------------------------------------------------------------------------
# Cubie level cube
# ---------------------------------------------------------------------------
class CubieCube:
    def __init__(self, cp=None, co=None):
        self.cp = list(cp) if cp is not None else list(range(8))
        self.co = list(co) if co is not None else [0] * 8

    def multiply(self, other):
        """Return self followed by other."""
        cp = [self.cp[other.cp[i]] for i in range(8)]
        co = [(self.co[other.cp[i]] + other.co[i]) % 3 for i in range(8)]
        return CubieCube(cp, co)

    def __eq__(self, other):
        return self.cp == other.cp and self.co == other.co

    def is_solved(self):
        return self.cp == list(range(8)) and self.co == [0] * 8

    # ---- facelets ----------------------------------------------------------
    def to_facelets(self):
        f = list(SOLVED_FACELETS)
        for i in range(8):
            j, ori = self.cp[i], self.co[i]
            for n in range(3):
                f[CORNER_FACELETS[i][(n + ori) % 3]] = CORNER_COLORS[j][n]
        return "".join(f)

    @staticmethod
    def from_facelets(f):
        """Facelet string (face letters URFDLB) -> CubieCube. Raises ValueError."""
        cp, co = [None] * 8, [0] * 8
        for i in range(8):
            stickers = [f[k] for k in CORNER_FACELETS[i]]
            ori = next((o for o in range(3) if stickers[o] in "UD"), None)
            if ori is None:
                raise ValueError(f"corner slot {CORNER_NAMES[i]} has no U or D sticker")
            c1, c2 = stickers[(ori + 1) % 3], stickers[(ori + 2) % 3]
            for j in range(8):
                if CORNER_COLORS[j][1] == c1 and CORNER_COLORS[j][2] == c2 \
                        and CORNER_COLORS[j][0] == stickers[ori]:
                    cp[i], co[i] = j, ori
                    break
            else:
                raise ValueError(f"corner slot {CORNER_NAMES[i]} shows colors "
                                 f"{''.join(stickers)}, which is not a real corner")
        if sorted(cp) != list(range(8)):
            raise ValueError("a corner piece appears twice")
        if sum(co) % 3 != 0:
            raise ValueError("one corner is twisted (twist sum is not a multiple of 3), "
                             "this cube cannot be solved")
        return CubieCube(cp, co)


def _build_moves():
    moves = []
    for face in "URF":
        q = CubieCube(*_BASIC[face])
        h = q.multiply(q)
        p = h.multiply(q)
        moves += [q, h, p]
    return moves


MOVES = _build_moves()          # CubieCube for each of the 9 moves


# ---------------------------------------------------------------------------
# Input preprocessing: any 6 colors -> face letters, with the cube rotated
# so the DBL corner defines the color scheme.
# ---------------------------------------------------------------------------
def normalize_colors(stickers):
    """
    Take 24 sticker colors in any alphabet (W Y G B R O, or whatever the UI
    uses) and convert them to face letters URFDLB.

    The DBL corner is treated as fixed, so its three stickers decide which
    color is D, B and L. The other three faces are the colors that never
    share a corner with D, B and L (their opposites).
    """
    s = [c.upper() for c in stickers if not c.isspace()]
    if len(s) != 24:
        raise ValueError(f"expected 24 stickers, got {len(s)}")
    counts = Counter(s)
    if len(counts) != 6 or any(v != 4 for v in counts.values()):
        raise ValueError(f"need 6 colors with 4 stickers each, got {dict(counts)}")

    corner_sets = [{s[k] for k in trip} for trip in CORNER_FACELETS]
    if any(len(cs) != 3 for cs in corner_sets):
        raise ValueError("a corner has the same color on two of its stickers")

    def opposite(color):
        partners = set().union(*(cs for cs in corner_sets if color in cs))
        opp = set(counts) - partners
        if len(opp) != 1:
            raise ValueError(f"cannot find a single opposite color for {color}")
        return opp.pop()

    d, b, l = s[14], s[23], s[18]
    mapping = {d: "D", b: "B", l: "L", opposite(d): "U", opposite(b): "F", opposite(l): "R"}
    if len(set(mapping.values())) != 6 or len(mapping) != 6:
        raise ValueError("color scheme is inconsistent")
    return "".join(mapping[c] for c in s), {v: k for k, v in mapping.items()}


# ---------------------------------------------------------------------------
# Integer coordinates and move tables
# ---------------------------------------------------------------------------
_FREE = [0, 1, 2, 3, 4, 5, 7]                    # every slot except DBL
PERMS = []
for p in permutations(_FREE):
    cp = list(p[:6]) + [DBL] + [p[6]]
    PERMS.append(tuple(cp))
PERMS.sort()
PERM_INDEX = {p: i for i, p in enumerate(PERMS)}
N_PERM, N_ORI = len(PERMS), 3 ** 6               # 5040, 729
N_STATES = N_PERM * N_ORI                        # 3,674,160


def ori_to_index(co):
    idx = 0
    for i in range(6):
        idx = idx * 3 + co[i]
    return idx


def index_to_ori(idx):
    co = [0] * 8
    for i in range(5, -1, -1):
        co[i] = idx % 3
        idx //= 3
    co[7] = (-sum(co[:6])) % 3                   # co[6] (DBL) is always 0
    return co


def encode(cube):
    if cube.cp[DBL] != DBL or cube.co[DBL] != 0:
        raise ValueError("DBL corner must be in place (normalize the input first)")
    return PERM_INDEX[tuple(cube.cp)] * N_ORI + ori_to_index(cube.co)


def decode(state):
    p, o = divmod(state, N_ORI)
    return CubieCube(PERMS[p], index_to_ori(o))


def _build_tables():
    ptab = [[0] * N_MOVES for _ in range(N_PERM)]
    otab = [[0] * N_MOVES for _ in range(N_ORI)]
    for p in range(N_PERM):
        c = CubieCube(PERMS[p], [0] * 8)
        for m, mv in enumerate(MOVES):
            ptab[p][m] = PERM_INDEX[tuple(c.multiply(mv).cp)]
    for o in range(N_ORI):
        c = CubieCube(list(range(8)), index_to_ori(o))
        for m, mv in enumerate(MOVES):
            otab[o][m] = ori_to_index(c.multiply(mv).co)
    return ptab, otab


PERM_MOVE, ORI_MOVE = _build_tables()
SOLVED_STATE = encode(CubieCube())


def apply_move(state, m):
    p, o = divmod(state, N_ORI)
    return PERM_MOVE[p][m] * N_ORI + ORI_MOVE[o][m]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def parse_moves(text):
    out = []
    for tok in text.replace(",", " ").split():
        if tok not in MOVE_NAMES:
            raise ValueError(f"unknown move {tok!r}; allowed: {' '.join(MOVE_NAMES)}")
        out.append(MOVE_NAMES.index(tok))
    return out


def apply_sequence_facelets(facelets, moves):
    c = CubieCube.from_facelets(facelets)
    for m in moves:
        c = c.multiply(MOVES[m])
    return c.to_facelets()


def net(facelets, colors=None):
    """ASCII net of the cube for terminal output."""
    f = [colors[c] if colors else c for c in facelets]
    U, R, F, D, L, B = (f[i:i + 4] for i in range(0, 24, 4))
    pad = " " * 6
    rows = [
        pad + f"{U[0]} {U[1]}",
        pad + f"{U[2]} {U[3]}",
        f"{L[0]} {L[1]} | {F[0]} {F[1]} | {R[0]} {R[1]} | {B[0]} {B[1]}",
        f"{L[2]} {L[3]} | {F[2]} {F[3]} | {R[2]} {R[3]} | {B[2]} {B[3]}",
        pad + f"{D[0]} {D[1]}",
        pad + f"{D[2]} {D[3]}",
    ]
    return "\n".join(rows)
