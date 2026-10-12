"""Students write the same answer in many ways. All reasonable forms must be accepted; near misses must not."""
import pytest
from sympy import expand
import gen

SEEDS = range(1, 40)
LV = list(gen.LEVELS)


def ok(q, s, want):
    v = gen.verdict(q, s)
    assert (v == "CORRECT") == want, (q["id"], s, v, gen.ans_str(q))


@pytest.mark.parametrize("lv", LV)
def test_vector_forms(lv):
    for seed in SEEDS:
        q = gen.build(f"vec-{lv}-{seed}")
        if q["kind"] != "vec":
            continue
        a, b = q["answer"]; fa, fb = gen.fmt(a), gen.fmt(b)
        for s in (f"({fa}, {fb})", f"({fa},{fb})", f"[{fa}, {fb}]", f"({fa})i + ({fb})j", f"({fa})i+({fb})j"):
            ok(q, s, True)
        ok(q, f"({fa}, {gen.fmt(b + 1)})", False)
        ok(q, f"{gen.fmt(b + 1)}i + {fb}j", gen.fmt(b + 1) == fa)   # swapping parts is only right if they match


@pytest.mark.parametrize("lv", LV)
def test_circle_equation_forms(lv):
    for seed in SEEDS:
        q = gen.build(f"cgeo-{lv}-{seed}")
        if q["kind"] != "eqn":
            continue
        F = q["answer"]
        for s in (f"{gen.fmt(F)} = 0", f"{gen.fmt(expand(2 * F))} = 0", f"{gen.fmt(expand(F + 3))} = 3"):
            ok(q, s, True)
        ok(q, f"{gen.fmt(F + 1)} = 0", False)
        ok(q, f"{gen.fmt(expand(F + gen.x))} = 0", False)


@pytest.mark.parametrize("lv", LV)
def test_inequality_forms(lv):
    for seed in SEEDS:
        q = gen.build(f"ineq-{lv}-{seed}")
        t = q["ans_text"]
        ok(q, t, True)
        ok(q, t.replace(" or ", ", "), True)
        ok(q, t.replace(" or ", " ; "), True)
        ok(q, t.replace("<=", "≤").replace(">=", "≥"), True)
        if "<=" in t or ">=" in t:
            ok(q, t.replace("<=", "<").replace(">=", ">"), False)      # closed vs open boundary
        elif " < " in t or " > " in t:
            ok(q, t.replace("<", "<=").replace(">", ">="), False)


@pytest.mark.parametrize("lv", LV)
def test_named_pairs(lv):
    for seed in SEEDS:
        q = gen.build(f"lin-{lv}-{seed}")
        if not (q.get("names") and q["kind"] == "pairs"):
            continue
        a = q["answer"][0]; n = q["names"]
        ok(q, f"{n[0]} = {gen.fmt(a[0])}, {n[1]} = {gen.fmt(a[1])}", True)
        ok(q, f"{n[0]}={gen.fmt(a[0])} and {n[1]}={gen.fmt(a[1])}", True)
        ok(q, f"({gen.fmt(a[0])}, {gen.fmt(a[1])})", True)
        ok(q, f"({gen.fmt(a[1])}, {gen.fmt(a[0])})", a[0] == a[1])


def test_exact_answers_reject_decimals():
    q = gen.build("line-easy-1")
    for seed in range(1, 40):
        q = gen.build(f"line-easy-{seed}")
        if q.get("exact") and not q["answer"].is_rational:
            assert gen.verdict(q, str(float(q["answer"]))).startswith("NOT EXACT")
            assert gen.verdict(q, gen.ans_str(q)) == "CORRECT"
            return
    pytest.skip("no irrational exact question in these seeds")


def test_ambiguous_division_is_flagged():
    q = {"kind": "expr", "answer": 1 / (2 * gen.x), "id": "fake-easy-1", "topic": "diff", "level": "easy"}
    assert gen.verdict(q, "1/(2x)") == "CORRECT"
    assert gen.verdict(q, "1/2x").startswith("AMBIGUOUS")          # could mean (1/2)x
    assert gen.verdict(q, "(1/2)x") == "INCORRECT"


def test_unreadable_input_is_reported():
    q = gen.build("diff-easy-1")
    for junk in ("", "???", "the answer is blue", "x ^ ^ 2"):
        assert gen.verdict(q, junk).startswith("COULD NOT READ"), junk
