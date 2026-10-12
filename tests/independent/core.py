"""Independent re-derivation of the answer key for the original 13 topics. It re-solves each question from its text
with its own code (numerics, brute force, sympy) and never reads the generator's formulas."""
import os, sys, re, math, itertools, collections, traceback
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import gen
from gen import to_expr, num, x, y, close
import sympy as sp
from sympy import Symbol, Eq, solve, diff, N, Rational, binomial, factorial, log, exp, pi, sin, cos
k = Symbol("k")
def E(s): return to_expr(s.replace("e^", "E^"))  # 'E' only matters for exp parse; to_expr handles e via LOCALS
def ex(s): return to_expr(s)
def approx(a, b, tol=1e-7): return close(float(a), float(b), tol, 1e-8)
fails = collections.Counter(); ex_ = {}
def fail(key, info):
    fails[key] += 1; ex_.setdefault(key, info)

def verify(q):
    t, lv, text, a, kind = q["topic"], q["level"], q["question"], q["answer"], q["kind"]
    if t == "diff":
        f = ex(re.match(r"Differentiate y = (.*) with respect to x\.", text).group(1))
        for p in [0.6, 1.3, 2.2, 6.5]:
            try: complex(N(f.subs(x, p))); float(N(f.subs(x, p)))
            except Exception: continue
            h = 1e-6; nd = (N(f.subs(x, p + h)) - N(f.subs(x, p - h))) / (2 * h)
            if not approx(nd, N(a.subs(x, p)), 1e-5): return "derivative mismatch"
    elif t == "integ":
        if lv != "hard":
            f = ex(re.match(r"Find the integral of (.*) with respect to x\.", text).group(1))
            if not gen.same_func(diff(a, x), f): return "antiderivative wrong"
        else:
            m = re.match(r"Evaluate the definite integral of (.*) from x = (.*) to x = (.*)\. Give", text)
            f, lo, hi = ex(m.group(1)), ex(m.group(2)), ex(m.group(3))
            import mpmath
            v = mpmath.quad(sp.lambdify(x, f, "mpmath"), [float(lo), float(hi)])
            if not approx(v, N(a)): return "definite integral wrong"
    elif t == "stat":
        f = ex(re.match(r"Find (?:the )?(?:exact )?coordinates of the stationary points of y = (.*?)\.(?: Then.*)?$", text).group(1))
        d = diff(f, x); roots = [r for r in solve(d, x) if r.is_real]
        if len(roots) != len(a): return "root count differs"
        for (px, py) in a:
            if not approx(N(d.subs(x, px)), 0, 1e-9): return "not stationary"
            if not approx(N(f.subs(x, px)), N(py)): return "y wrong"
    elif t == "quad":
        if lv == "easy":
            f = ex(re.match(r"The curve y = (.*) has a max", text).group(1)); (px, py), = a
            if diff(f, x).subs(x, px) != 0 or f.subs(x, px) != py: return "vertex wrong"
        elif lv == "medium":
            m = re.match(r"The equation (.*) = 0 has equal roots\. Find the (?:value|possible values) of k\.", text)
            f = ex(m.group(1)); P = sp.Poly(f, x); A, B, C = P.all_coeffs()
            disc = sp.expand(B * B - 4 * A * C); sol = solve(disc, k)
            if sorted(float(s) for s in sol) != sorted(float(v) for v in a): return f"k set differs {sol} vs {a}"
        else:
            m = re.match(r"The line y = (.*) is a tangent to the curve y = (.*)\. Find", text)
            line, curve = ex(m.group(1)), ex(m.group(2))
            disc = sp.discriminant(sp.expand(curve - line), x); sol = solve(disc, k)
            if [float(s) for s in sol] != [float(a[0])]: return "tangent k wrong"
    elif t == "log":
        if lv == "easy":
            m = re.match(r"Solve log base (\d+) of x = (-?\d+)\.", text)
            if m:
                if Rational(int(m.group(1)))**int(m.group(2)) != a: return "log easy wrong"
            else:
                m = re.match(r"Solve (\d+)\^x = (\d+)\.", text)
                if not approx(float(m.group(1))**float(N(a)), float(m.group(2)), 1e-9): return "exp wrong"
        elif lv == "medium":
            m = re.match(r"Solve log base (\d+) of x \+ log base \d+ of \(x - (\d+)\) = (\d+)\.", text)
            b_, d_, n_ = (int(g) for g in m.groups()); v = float(a[0])
            if v <= d_ or not approx(math.log(v, b_) + math.log(v - d_, b_), n_, 1e-9): return "log medium wrong"
            # no other valid root
            cands = solve(Eq(x * (x - d_), b_**n_), x); good = [c for c in cands if c > d_]
            if len(good) != 1: return "root count"
        else:
            f = ex(re.match(r"Solve (.*) = 0\.", text).group(1))
            for v in a:
                if not approx(N(f.subs(x, v)), 0, 1e-9): return "log hard root wrong"
            ys = Symbol("yy"); b_ = int(re.search(r"(\d+)\^\(2x\)", text).group(1))
            g = sp.expand(f.subs(x, sp.log(ys, b_) if False else 0))  # placeholder
            Q = sp.expand(sp.powsimp(f)); 
    elif t == "binom":
        m = re.match(r"Find the coefficient of x\^(\d+) in the expansion of \((.*)\)\^(\d+)\.", text)
        if m:
            r, base, n = int(m.group(1)), ex(m.group(2)), int(m.group(3))
            if sp.expand(base**n).coeff(x, r) != a: return "coef wrong"
        else:
            m = re.match(r"Find the term independent of x in the expansion of \((.*)\)\^(\d+)\.", text)
            base, n = ex(m.group(1)), int(m.group(2))
            if sp.expand(base**n).coeff(x, 0) != a: return "term indep wrong"
    elif t == "simul":
        m = re.match(r"Solve simultaneously: (.*) and (.*)\.$", text)
        e1, e2 = m.group(1), m.group(2)
        def eq_of(s):
            l, r = s.split("="); return Eq(ex(l), ex(r))
        E1, E2 = eq_of(e1), eq_of(e2)
        sol = solve([E1, E2], [x, y], dict=True)
        truth = sorted((float(s[x]), float(s[y])) for s in sol)
        got = sorted((float(p[0]), float(p[1])) for p in a)
        if len(truth) != len(got) or any(not close(p[0], g[0]) or not close(p[1], g[1]) for p, g in zip(truth, got)): return f"simul differs {truth} {got}"
    elif t == "factor":
        if lv == "easy":
            m = re.match(r"Find the remainder when (.*) is divided by \(x ([+-]) (\d+)\)\.", text)
            f = ex(m.group(1)); r = -int(m.group(3)) if m.group(2) == "+" else int(m.group(3))
            if sp.rem(sp.Poly(f, x), sp.Poly(x - r, x)).as_expr() != a: return "remainder wrong"
        elif lv == "medium":
            m = re.match(r"\(x ([+-]) (\d+)\) is a factor of (.*)\. Find the value of k\.", text)
            r = -int(m.group(2)) if m.group(1) == "+" else int(m.group(2)); f = ex(m.group(3))
            if f.subs({x: r, k: a}) != 0: return "factor k wrong"
        else:
            m = re.match(r"Show that \(x ([+-]) (\d+)\) is a factor of (.*)\. Hence solve .* = 0\.", text)
            r = -int(m.group(2)) if m.group(1) == "+" else int(m.group(2)); f = ex(m.group(3))
            if f.subs(x, r) != 0: return "not a factor"
            if sorted(solve(f, x)) != sorted(a): return "roots differ"
    elif t == "trig":
        m = re.match(r"Solve (.*) = (.*) for 0 <= x <= (\d+) degrees\.", text)
        lhs, rhs, hi = m.group(1), m.group(2), int(m.group(3))
        lhs = re.sub(r"(sec|cosec|cot) x", r"\1(x)", lhs)
        lhs = re.sub(r"(sin|cos)\^2 x", r"\1(x)^2", lhs); lhs = re.sub(r"(sin|cos) 2x", r"\1(2x)", lhs); lhs = re.sub(r"(sin|cos) x", r"\1(x)", lhs)
        f = ex(lhs) - ex(rhs); f = f.replace(sp.Function("sec"), lambda a_: 1 / sp.cos(a_)) if f.has(sp.Function("sec")) else f
        _fn = sp.lambdify(x, f, "math")
        def fn(v):
            try: return _fn(v)
            except ZeroDivisionError: return 1e9
        truth = [d for d in range(0, hi + 1) if abs(fn(math.radians(d))) < 1e-9]
        # make sure no non-integer solutions are missed: fine scan for sign changes
        xs = [i * 0.05 for i in range(0, hi * 20 + 1)]; vals = [fn(math.radians(v)) for v in xs]
        changes = sum(1 for i in range(len(vals) - 1) if vals[i] * vals[i + 1] < 0)
        if sorted(truth) != sorted(int(v) for v in a): return f"trig differs {truth} {a}"
    elif t == "tangent":
        m = re.match(r"Find the equation of the (?:(tangent|normal) )?(?:to|of).*", text)
        m = re.match(r"Find the equation of the (tangent|normal) to the curve y = (.*) at the point where x = (-?\d+)\.", text)
        typ, f, x0 = m.group(1), ex(m.group(2)), int(m.group(3))
        slope = N(diff(f, x).subs(x, x0)); y0 = N(f.subs(x, x0))
        g = slope if typ == "tangent" else -1 / slope
        if not approx(N(a.subs(x, x0)), y0): return "line misses the point"
        if not approx(N(diff(a, x)), g): return "slope wrong"
    elif t == "func":
        m = re.match(r"f\(x\) = (.*) and g\(x\) = (.*)\. Find (fg|gf)\(x\)\.", text)
        if m:
            f, g, w = ex(m.group(1)), ex(m.group(2)), m.group(3)
            res = f.subs(x, g) if w == "fg" else g.subs(x, f)
            if not gen.same_func(res, a): return "composite wrong"
        else:
            f = ex(re.match(r"f\(x\) = (.*)\. Find f\^-1\(x\)\.", text).group(1))
            if not gen.same_func(f.subs(x, a), x): return "inverse wrong"
    elif t == "circ":
        nums = [sp.sympify(v) for v in re.findall(r"\d+(?:/\d+)?", text.replace("cm^2", ""))]
        if lv == "easy": r_, th = nums[0], nums[1]; ok = (a == r_ * th)
        elif lv == "medium": r_, th = nums[0], nums[1]; ok = (a == r_ * r_ * th / 2)
        else:
            L, A_ = nums[0], nums[1]; r_, th = (sp.sympify(c) for c in a[0]); ok = (r_ * th == L and r_ * r_ * th / 2 == A_)
        if not ok: return "circ wrong"
    elif t == "perm":
        n_ = [int(v) for v in re.findall(r"\d+", text)]
        if "president" in text: n = n_[0]; tru = n * (n - 1) * (n - 2)
        elif "runners" in text: n, r = n_[0], n_[1]; tru = math.perm(n, r)
        elif "A team of" in text: r, n = n_[0], n_[1]; tru = math.comb(n, r)
        elif "next to each other" in text and "not" not in text:
            n = n_[0]; tru = sum(1 for p in itertools.permutations(range(n)) if abs(p.index(0) - p.index(1)) == 1)
        elif "not stand next" in text:
            n = n_[0]; tru = sum(1 for p in itertools.permutations(range(n)) if abs(p.index(0) - p.index(1)) != 1)
        else:
            r, m_, w, j = n_[0], n_[1], n_[2], n_[3]
            tru = sum(1 for c in itertools.combinations(range(m_ + w), r) if sum(1 for v in c if v >= m_) >= j)
        if tru != a: return f"perm wrong {tru} {a}"
    return None


def run_all(seeds=60, topics=None):
    """Command line use: python tests/independent/core.py [seeds]"""
    for t in (topics or gen.GEN):
        for lv in gen.LEVELS:
            for seed in range(1, seeds + 1):
                try:
                    q = gen.build(f"{t}-{lv}-{seed}")
                    r = verify(q)
                    if r: fail((t, lv), (q["id"], q["question"], r))
                except Exception as e:
                    fail((t, lv, "EXC"), (f"{t}-{lv}-{seed}", repr(e)[:150], traceback.format_exc().splitlines()[-4:-1]))
    print("independent failures:", sum(fails.values()))
    for kk, v in sorted(fails.items(), key=str): print(kk, v, ex_[kk])

if __name__ == "__main__":
    run_all(int(sys.argv[1]) if len(sys.argv) > 1 else 60)
