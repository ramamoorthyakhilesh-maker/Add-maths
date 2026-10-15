"""Mistake diagnosis (tools/slips.py).

The idea: when an answer is INCORRECT, Edith can say which usual slip it looks like. The slip answers are computed, not guessed,
so these tests check three things: every slip answer is something a student could type and the checker reads back,
the right slip is named for hand-made cases, and nothing in the advice can give the answer away.
"""
import collections, json, os, re, subprocess, sys
import pytest
from sympy import Rational, Symbol, exp, expand, integrate, diff, log, Interval, Union, oo
import gen, slips
from conftest import SEEDS, ROOT

x, y, t = gen.x, gen.y, gen.t_
CELLS = [(tp, lv) for tp in gen.GEN for lv in gen.LEVELS]


def mkq(topic, level, text, kind, answer, **kw):
    q = gen.mk(text, kind, answer, ["step"], **kw)
    q.update(id=f"{topic}-{level}-0", topic=topic, level=level)
    return q


def code(q, s):
    assert gen.verdict(q, s).startswith("INCORRECT"), (s, gen.verdict(q, s))
    d = slips.diagnose(q, s, gen)
    return d[0] if d else None


# ---------- every slip answer is typable, readable and different from the right answer ----------
@pytest.mark.parametrize("topic,level", CELLS)
def test_slip_answers_round_trip(topic, level):
    for seed in range(1, SEEDS + 1):
        q = gen.build(f"{topic}-{level}-{seed}")
        for sl in slips.candidates(gen, q):
            text = slips.cand_text(gen, q, sl.cand)
            if gen.check(q, text) is True:
                continue                                    # this slip happens to equal the right answer here, so it is not a slip
            assert gen.check(slips.cand_q(q, sl), text) is True, (q["id"], sl.code, text)
            assert gen.verdict(q, text) != "CORRECT", (q["id"], sl.code, text)
            d = slips.diagnose(q, text, gen)
            assert d is not None, (q["id"], sl.code, text)
            hit = {s2.code for s2 in slips.candidates(gen, q) if gen.check(slips.cand_q(q, s2), text) is True}
            assert d[0] in hit | {"incomplete", "extra", "onlyx", "onlyy", "offset", "factor"}, (q["id"], text, d[0], hit)


@pytest.mark.parametrize("topic,level", CELLS)
def test_unrelated_wrong_answers_get_no_diagnosis(topic, level):
    junk = {"expr": "x^7 + 3x^5 + 98765x", "antider": "x^7 + 3x^5 + 98765x", "int": "98765", "value": "98765.4321", "num3sf": "98765.4321",
            "set": "98765", "pairs": "(98765, 98766)", "interval": "x > 98765", "vec": "98765i + 98766j", "eqn": "x^2 + y^2 + 98765 = 0"}
    for seed in range(1, 5):
        q = gen.build(f"{topic}-{level}-{seed}")
        if q.get("var"):
            continue
        s = junk[q["kind"]]
        if gen.verdict(q, s) == "INCORRECT":
            assert slips.diagnose(q, s, gen) is None, (q["id"], s)


# ---------- the advice never gives the answer away ----------
def test_advice_text_is_clean():
    for c, a in list(slips.ADV.items()) + [(k, v) for k, v in slips.TOPIC_ADV.items()]:
        assert a.endswith(".") and "—" not in a and "  " not in a, (c, a)
        assert len(a) < 330, (c, len(a))


@pytest.mark.parametrize("topic,level", CELLS)
def test_advice_never_contains_the_answer(topic, level):
    texts = list(slips.ADV.values()) + list(slips.TOPIC_ADV.values())
    for seed in range(1, SEEDS + 1):
        q = gen.build(f"{topic}-{level}-{seed}")
        a = gen.ans_str(q)
        if len(a) < 4:
            continue
        for tx in texts:
            assert a not in tx, (q["id"], a, tx)


def test_every_code_has_advice_and_every_advice_is_used():
    used = {"incomplete", "extra", "onlyx", "onlyy", "offset", "factor"}
    for tp in gen.GEN:
        for lv in gen.LEVELS:
            for seed in range(1, 41):
                q = gen.build(f"{tp}-{lv}-{seed}")
                for sl in slips.candidates(gen, q):
                    assert sl.code in slips.ADV, (q["id"], sl.code)
                    used.add(sl.code)
    assert not (set(slips.ADV) - used), sorted(set(slips.ADV) - used)
    for (tp, c) in slips.TOPIC_ADV:
        assert tp in gen.GEN and c in slips.ADV, (tp, c)


# ---------- hand-made cases: what a student writes, and which slip it is ----------
def f_chain():
    return mkq("diff", "medium", "Differentiate y = (3x + 2)^4 with respect to x.", "expr", diff((3 * x + 2) ** 4, x))


@pytest.mark.parametrize("ans,want", [
    ("4(3x+2)^3", "chain"), ("-12(3x+2)^3", "sign"), ("24(3x+2)^3", "double"), ("6(3x+2)^3", "half"),
    ("12(3x+2)^3 + 5", "offset"), ("36(3x+2)^3", "factor"),
])
def test_chain_rule_cases(ans, want):
    assert code(f_chain(), ans) == want


def test_product_and_quotient_cases():
    q = mkq("diff", "hard", "Differentiate y = x^2*e^(3*x) with respect to x.", "expr", diff(x**2 * exp(3 * x), x))
    assert code(q, "2x * 3*e^(3x)") == "prod_sep"
    q = mkq("diff", "hard", "Differentiate y = (2x + 1)/(x^2 + 3) with respect to x.", "expr", diff((2 * x + 1) / (x**2 + 3), x))
    assert code(q, "(2x(2x+1) - 2(x^2+3))/(x^2+3)^2") == "quot_order"
    assert code(q, "(2(x^2+3) - 2x(2x+1))/(x^2+3)") == "quot_sq"
    assert code(q, "2/(2x)") == "quot_sep"


def test_integration_cases():
    q = mkq("integ", "medium", "Find the integral of (5x + 1)^4 with respect to x.", "antider", integrate((5 * x + 1) ** 4, x))
    assert code(q, "(5x+1)^5/5") == "nodivide"
    assert code(q, "20(5x+1)^3") == "differentiated"
    q = mkq("integ", "hard", "Evaluate the definite integral of 2x from x = 1 to x = 3. Give an exact answer.", "value", 8)
    assert code(q, "9") == "upper_only"
    assert code(q, "-8") == "sign"


def test_missing_constant_is_noted_only_on_correct_antiderivatives():
    q = mkq("integ", "medium", "Find the integral of (5x + 1)^4 with respect to x.", "antider", integrate((5 * x + 1) ** 4, x))
    assert slips.note(q, "(5x+1)^5/25") and "+ c" in slips.note(q, "(5x+1)^5/25")
    assert slips.note(q, "(5x+1)^5/25 + c") is None
    assert slips.note(q, "(5x+1)^5/25 + C") is None
    assert slips.note(mkq("diff", "easy", "Differentiate y = x^2 with respect to x.", "expr", 2 * x), "2x") is None


def test_solution_sets_and_points():
    q = mkq("trig", "easy", "Solve sin x = 1/2 for 0 <= x <= 360 degrees.", "set", [30, 150], tol=1e-6)
    assert code(q, "30") == "incomplete"
    assert code(q, "30, 150, 210") == "extra"
    assert code(q, "-30, -150") == "sign"
    assert code(q, "0.5236, 2.618") == "radians"
    q = mkq("trig", "medium", "Solve sin 2x = 1/2 for 0 <= x <= 180 degrees.", "set", [15, 75], tol=1e-6)
    assert code(q, "30, 150") == "double"
    q = mkq("simul", "easy", "Solve simultaneously: x + y = 5 and xy = 6.", "pairs", [(2, 3), (3, 2)])
    assert code(q, "(2, 3)") == "incomplete"
    assert code(q, "x = 2, x = 3") == "onlyx"
    q = mkq("stat", "easy", "Find the coordinates of the stationary points of y = x^2 - 4x + 7.", "pairs", [(2, 3)])
    assert code(q, "(3, 2)") == "swap"
    assert code(q, "x = 2") == "onlyx"
    assert code(q, "(-2, 3)") == "sign1"


def test_tangent_function_and_circle_cases():
    f = x**2
    q = mkq("tangent", "medium", "Find the equation of the normal to the curve y = x^2 at the point where x = 1.", "expr", expand(-(x - 1) / 2 + 1))
    assert code(q, "y = 2x - 1") == "tn_swap"
    assert code(q, "y = x/2 + 1/2") == "gradflip"
    assert code(q, "y = -2x + 3") == "gradflip"
    assert code(q, "y = -x/2 + 3") == "offset"
    q = mkq("func", "easy", "f(x) = 2x + 3. Find f^-1(x).", "expr", (x - 3) / 2)
    assert code(q, "1/(2x+3)") == "recip"
    assert code(q, "(x+3)/2") == "invsign"
    assert code(q, "x/2 - 3") == "invorder"
    q = mkq("func", "medium", "f(x) = 2x + 1 and g(x) = x^2 - 3. Find fg(x).", "expr", expand(2 * (x**2 - 3) + 1))
    assert code(q, "(2x+1)^2 - 3") == "compswap"
    assert code(q, "(2x+1)(x^2-3)") == "compmul"
    q = mkq("cgeo", "easy", "Find the equation of the circle with centre (3, -2) and radius 4.", "eqn", expand((x - 3)**2 + (y + 2)**2 - 16))
    assert code(q, "(x+3)^2 + (y-2)^2 = 16") == "cg_sign"
    assert code(q, "(x-3)^2 + (y+2)^2 = 4") == "cg_r2"
    q = mkq("cgeo", "easy", "The equation of a circle is (x - 3)^2 + (y + 2)^2 = 25. Write down the coordinates of the centre and the radius. Give your answer as (a, b, r), where (a, b) is the centre and r is the radius.",
            "pairs", [(3, -2, 5)])
    assert code(q, "(-3, 2, 5)") == "cg_sign"
    assert code(q, "(3, -2, 25)") == "cg_r2"


def test_counting_progressions_vectors_and_mechanics_cases():
    q = mkq("perm", "easy", "A team of 3 is chosen from 8 people. How many different teams are possible?", "int", 56)
    assert code(q, "336") == "comb_order"
    q = mkq("perm", "easy", "8 runners take part in a race. In how many ways can the first 3 places be filled?", "int", 336)
    assert code(q, "56") == "perm_order"
    q = mkq("perm", "hard", "A committee of 4 is chosen from 5 men and 4 women. It must contain at least 2 women. In how many ways can this be done?", "int", 81)
    assert code(q, "60") == "perm_atleast"
    assert code(q, "6*21") == "perm_double"
    q = mkq("prog", "easy", "An arithmetic progression has first term 3 and common difference 4. Find the 5th term.", "int", 19)
    assert code(q, "23") == "prog_ap"
    q = mkq("vec", "easy", "Find the magnitude of the vector 3i - 4j. Give an exact answer.", "value", 5)
    assert code(q, "25") == "vec_sqrt"
    assert code(q, "7") == "vec_add"
    q = mkq("vec", "easy", "The position vectors of A and B, relative to an origin O, are 2i + j and 5i + 3j. Find the vector AB. Write it in the form ai + bj.", "vec", (3, 2))
    assert code(q, "-3i - 2j") == "vec_ab"
    q = mkq("kin", "easy", "A particle moves in a straight line. Its displacement s metres from a fixed point after t seconds is s = t^3 - 6t^2 + 9t. Find an expression for its velocity v in terms of t.",
            "expr", diff(t**3 - 6 * t**2 + 9 * t, t), var="t")
    assert code(q, "6t - 12") == "kin_order"
    q = mkq("kin", "hard", "A particle moves in a straight line, starting from O. Its velocity v m/s at time t seconds is v = t^2 - 4t + 3. Find the total distance the particle travels in the first 4 seconds.", "value", 4)
    # the signed integral of t^2 - 4t + 3 over 0 to 4 is 4/3; the distance counts the stretch where v < 0 as positive, giving 4
    assert code(q, "4/3") == "kin_dist"
    q = mkq("rates", "easy", "Given y = x^3 + 2x, use differentiation to find the approximate change in y when x increases from 2 to 2.01.", "value", Rational(14, 100))
    assert code(q, "0.140601") == "rate_exact"
    assert code(q, "14") == "rate_nochain"
    q = mkq("area", "hard", "Find the exact area of the region bounded by the curve y = e^(2x), the x-axis, the y-axis and the line x = 1.", "value", (exp(2) - 1) / 2)
    assert code(q, "e^2 - 1") == "area_nodiv"
    q = mkq("circ", "medium", "A sector of a circle has radius 5 cm and angle 3/2 radians. Find its area.", "value", Rational(75, 4))
    assert code(q, "7.5") == "circ_formula"
    assert code(q, "37.5") == "double"
    q = mkq("line", "easy", "A is the point (1, 2) and B is the point (5, 8). Find the midpoint of AB.", "pairs", [(3, 5)])
    assert code(q, "(6, 10)") == "mid_sum"
    q = mkq("line", "easy", "A is the point (1, 2) and B is the point (4, 6). Find the length of AB. Give an exact answer.", "value", 5)
    assert code(q, "25") == "len_sqrt"
    assert code(q, "7") == "len_add"


def test_logs_binomial_factor_and_inequalities():
    q = mkq("log", "easy", "Solve log base 2 of x = 5.", "value", 32)
    assert code(q, "10") == "logmul"
    assert code(q, "25") == "logswap"
    q = mkq("log", "easy", "Solve 3^x = 20. Give your answer correct to 3 significant figures.", "num3sf", log(20) / log(3))
    assert code(q, "6.67") == "logdivide"
    q = mkq("binom", "easy", "Find the coefficient of x^2 in the expansion of (1 + 3x)^5.", "int", 90)
    assert code(q, "10") == "bin_b"
    q = mkq("factor", "easy", "Find the remainder when x^3 + 2x - 5 is divided by (x - 2).", "int", 7)
    assert code(q, "-17") == "wrongroot"
    q = mkq("ineq", "easy", "Solve x^2 - 5x + 6 < 0.", "interval", Interval.open(2, 3), ans_text="2 < x < 3")
    assert code(q, "x < 2 or x > 3") == "ineq_side"
    assert code(q, "2 <= x <= 3") == "ineq_strict"


# ---------- through the command line ----------
def run_cli(args, log):
    env = dict(os.environ, EDITH_LOG=str(log), PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, os.path.join(ROOT, "tools", "gen.py"), *args], capture_output=True, text=True, env=env, timeout=120).stdout


def test_check_prints_diagnosis_after_incorrect_only(tmp_path):
    lg = tmp_path / "log.jsonl"; qid = "diff-medium-100"; q = gen.build(qid)
    wrong = run_cli(["check", qid, "-sin(4x-6)"], lg).splitlines()
    assert wrong[0] == "INCORRECT" and wrong[1].startswith("DIAGNOSIS (chain): ") and len(wrong) == 2
    assert gen.ans_str(q) not in "\n".join(wrong)
    assert run_cli(["check", qid, "-4 sin(4x-6)"], lg).splitlines() == ["CORRECT"]
    assert run_cli(["check", qid, "banana"], lg).startswith("COULD NOT READ")
    rows = [json.loads(l) for l in lg.read_text().splitlines()]
    assert rows[0]["result"] == "INCORRECT" and rows[0]["diag"] == "chain"
    assert "diag" not in rows[1] and "diag" not in rows[2]


def test_a_failing_diagnosis_never_breaks_the_check(monkeypatch, capsys):
    monkeypatch.setattr(slips, "diagnose", lambda *a, **k: 1 / 0)
    gen.main(["check", "diff-medium-100", "-sin(4x-6)"])
    assert capsys.readouterr().out.strip() == "INCORRECT"


def test_antiderivative_note_appears_after_correct(capsys):
    qid = "integ-medium-100"; q = gen.build(qid); ans = gen.ans_str(q)
    gen.main(["check", qid, ans]); out = capsys.readouterr().out.splitlines()
    assert out[0] == "CORRECT" and out[1].startswith("NOTE: Add + c")
    gen.main(["check", qid, ans + " + c"]); assert capsys.readouterr().out.splitlines() == ["CORRECT"]


def test_progress_lists_recurring_slips(tmp_path, monkeypatch, capsys):
    import datetime, importlib
    now = datetime.datetime.now()
    rows = [{"ts": (now - datetime.timedelta(days=d)).isoformat(timespec="seconds"), "args": ["check", f"diff-medium-{d}", "x"], "result": "INCORRECT", "diag": "chain"} for d in (1, 2, 3)]
    rows.append({"ts": now.isoformat(timespec="seconds"), "args": ["check", "integ-easy-1", "x"], "result": "INCORRECT", "diag": "sign"})
    rows.append({"ts": (now - datetime.timedelta(days=90)).isoformat(timespec="seconds"), "args": ["check", "log-easy-1", "x"], "result": "INCORRECT", "diag": "logmul"})
    p = tmp_path / "log.jsonl"; p.write_text("\n".join(json.dumps(r) for r in rows) + "\nnot json\n")
    monkeypatch.setenv("EDITH_LOG", str(p))
    import progress; importlib.reload(progress)
    progress.main(["mistakes"]); out = capsys.readouterr().out.splitlines()
    assert out[0].startswith("chain: 3 times (diff 3)") and out[0].endswith("RECURRING")
    assert out[1].startswith("sign: 1 time (integ 1)") and "RECURRING" not in out[1]
    assert len(out) == 2                                   # the 90-day-old slip is outside the window
    p.write_text(""); progress.main(["mistakes"]); assert "No slips logged yet" in capsys.readouterr().out
    importlib.reload(progress)
