"""Sanity checks for the cube model. Run: python test_cube.py"""
import random
from cube import *


def test_move_orders():
    for m in range(0, 9, 3):                     # quarter turns have order 4
        c = CubieCube()
        for _ in range(4):
            c = c.multiply(MOVES[m])
        assert c.is_solved(), MOVE_NAMES[m]
    # inverse pairs: X then X' is identity
    for m in range(0, 9, 3):
        assert CubieCube().multiply(MOVES[m]).multiply(MOVES[m + 2]).is_solved()


def test_sexy_move_order_6():
    seq = parse_moves("R U R' U'")
    c = CubieCube()
    for k in range(1, 7):
        for m in seq:
            c = c.multiply(MOVES[m])
        assert c.is_solved() == (k == 6)


def test_facelet_round_trip():
    rng = random.Random(1)
    for _ in range(500):
        c = CubieCube()
        for _ in range(20):
            c = c.multiply(MOVES[rng.randrange(9)])
        assert CubieCube.from_facelets(c.to_facelets()) == c
        assert decode(encode(c)) == c


def test_coordinate_moves_match_cubie_moves():
    rng = random.Random(2)
    for _ in range(500):
        c = CubieCube()
        for _ in range(15):
            c = c.multiply(MOVES[rng.randrange(9)])
        m = rng.randrange(9)
        assert apply_move(encode(c), m) == encode(c.multiply(MOVES[m]))


def test_R_moves_right_face_stickers():
    f = CubieCube().multiply(MOVES[3]).to_facelets()   # R
    assert f[4:8] == "RRRR"                             # R face still solid
    assert f[0:4] == "UFUF"                             # front stickers move up
    assert f[12:16] == "DBDB"


def test_normalize_colors_and_rejects_bad_input():
    scheme = dict(zip("URFDLB", "WRGYOB"))              # common color scheme
    scrambled = apply_sequence_facelets(SOLVED_FACELETS, parse_moves("R U F2 R'"))
    colored = "".join(scheme[c] for c in scrambled)
    norm, _ = normalize_colors(colored)
    assert norm == scrambled
    bad = list(colored); bad[0], bad[4] = bad[4], bad[0]
    for broken in ("W" * 24, colored[:20], "".join(bad)):
        try:
            CubieCube.from_facelets(normalize_colors(broken)[0])
            assert False, "should have failed"
        except ValueError:
            pass


def test_twisted_corner_rejected():
    c = CubieCube(co=[1, 0, 0, 0, 0, 0, 0, 0])
    try:
        CubieCube.from_facelets(c.to_facelets())
        assert False
    except ValueError as e:
        assert "twist" in str(e)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("pass", name)
    print("states:", N_STATES)
