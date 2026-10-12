"""Independent check of the NEW topics. Re-derives each answer from the question text by brute force / numerics,
without using the generator's own formulas. Usage: python verify2.py [seeds]"""
import os, sys, re, math, itertools
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "tools"))
import gen
from sympy import Symbol, lambdify, Rational, sympify, parse_expr
from sympy.parsing.sympy_parser import standard_transformations, implicit_multiplication_application, convert_xor
TR = standard_transformations + (implicit_multiplication_application, convert_xor)
X, Y, TT = Symbol("x"), Symbol("y"), Symbol("t")

def P(s):
    s = s.replace("|", "|")
    s = re.sub(r"\|([^|]*)\|", r" Abs(\1) ", s)
    return parse_expr(s, transformations=TR, local_dict={"e": gen.E, "ln": gen.log, "lg": lambda a: gen.log(a, 10)})

def F(s, var=X): return lambdify(var, P(s), "numpy")
def fl(v): return float(gen.N(v))
bad = []
def fail(q, why): bad.append((q["id"], q["question"], gen.ans_str(q), why))

def roots_numeric(g, lo=-60, hi=60, n=240001):
    xs = np.linspace(lo, hi, n); ys = g(xs); r = []
    for i in range(n - 1):
        if ys[i] == 0: r.append(xs[i])
        elif ys[i] * ys[i + 1] < 0:
            a, b = xs[i], xs[i + 1]
            for _ in range(60):
                m = (a + b) / 2
                if g(a) * g(m) <= 0: b = m
                else: a = m
            r.append((a + b) / 2)
    # touching roots
    ay = np.abs(ys)
    for i in range(1, n - 1):
        if ay[i] < ay[i - 1] and ay[i] <= ay[i + 1] and ay[i] < 1e-6 and ys[i - 1] * ys[i + 1] >= 0: r.append(xs[i])
    out = []
    for v in sorted(r):
        if not out or abs(v - out[-1]) > 1e-3: out.append(v)
    return out

def nums(s): return [int(v) for v in re.findall(r"-?\d+", s)]
def vecs(s):  # "3i - 4j" -> (3,-4)
    s = s.replace(" ", "").replace("-", "+-")
    a = b = 0
    for term in s.split("+"):
        if not term: continue
        if term.endswith("i"): c = term[:-1]; a += -1 if c == "-" else (1 if c == "" else int(c))
        elif term.endswith("j"): c = term[:-1]; b += -1 if c == "-" else (1 if c == "" else int(c))
    return (a, b)

def tup(a): return tuple(fl(c) for c in a)
def match_pairs(q, got):
    t = sorted(tup(p) for p in q["answer"]); g = sorted(got)
    return len(t) == len(g) and all(all(abs(u - v) < 1e-5 * max(1, abs(u)) for u, v in zip(a, b)) for a, b in zip(t, g))

def verify(q):
    t, lv, txt, ans = q["topic"], q["level"], q["question"], q["answer"]
    if t == "mod":
        eq = re.match(r"Solve (.*)\.$", txt).group(1); l, r = eq.split(" = ")
        fl_, fr = F(l), F(r); g = lambda z: fl_(z) - fr(z)
        got = roots_numeric(g)
        got = [v for v in got if abs(g(v)) < 1e-6]
        exp = sorted(fl(v) for v in ans)
        if len(got) != len(exp) or any(abs(a - b) > 1e-5 for a, b in zip(got, exp)): fail(q, f"roots {got}")
    elif t == "ineq":
        body = re.match(r"Solve (.*)\.$", txt).group(1); m = re.search(r"(<=|>=|<|>)", body)
        l, r = body[:m.start()], body[m.end():]; op = m.group(1)
        fl_, fr = F(l), F(r); xs = np.linspace(-40, 40, 80001) + 1e-7
        lhs, rhs = fl_(xs) * np.ones_like(xs), fr(xs) * np.ones_like(xs)
        truth = {"<": lhs < rhs, "<=": lhs <= rhs, ">": lhs > rhs, ">=": lhs >= rhs}[op]
        ivs = gen.interval_parts(ans); mine = np.zeros_like(truth)
        for iv in ivs:
            lo = -np.inf if iv.start == -gen.oo else fl(iv.start); hi = np.inf if iv.end == gen.oo else fl(iv.end)
            mine |= (xs > lo) & (xs < hi)
        if (mine != truth).any(): fail(q, f"grid mismatch at {xs[mine != truth][:3]}")
        # boundary membership with exact rationals
        for iv in ivs:
            for e, closed in ((iv.start, not iv.left_open), (iv.end, not iv.right_open)):
                if e in (gen.oo, -gen.oo): continue
                v = fl(e); a_, b_ = (fl_(np.array([v])) * np.ones(1))[0], (fr(np.array([v])) * np.ones(1))[0]
                holds = {"<": a_ < b_ - 1e-9, "<=": a_ <= b_ + 1e-9, ">": a_ > b_ + 1e-9, ">=": a_ >= b_ - 1e-9}[op]
                if holds != closed: fail(q, f"boundary {v} closed={closed}")
        if abs(float(gen.N(0)) ) > 1: pass
    elif t == "prog":
        if "common difference" in txt and "Find the" in txt and "term." in txt and "first term" in txt and "arithmetic" in txt and "sum" not in txt:
            a, d, n = nums(re.search(r"first term (-?\d+) and common difference (-?\d+)\. Find the (\d+)", txt).group(0)); u = a
            for _ in range(n - 1): u += d
            if u != fl(ans): fail(q, f"got {u}")
        elif "sum of the first" in txt:
            a, d = nums(re.search(r"first term (-?\d+) and common difference (-?\d+)", txt).group(0)); n = int(re.search(r"first (\d+) terms", txt).group(1))
            tot = 0; u = a
            for _ in range(n): tot += u; u += d
            if tot != fl(ans): fail(q, f"got {tot}")
        elif txt.startswith("A geometric progression has first term") and "nth" not in txt and re.search(r"Find the \d+\w\w term", txt):
            m = re.search(r"first term (-?\d+) and common ratio (\S+)\. Find the (\d+)", txt); a = Rational(m.group(1)); r = Rational(m.group(2)); n = int(m.group(3))
            u = a
            for _ in range(n - 1): u *= r
            if u != ans: fail(q, f"got {u}")
        elif txt.startswith("The ") and "arithmetic" in txt:
            m = re.match(r"The (\d+)\w\w term of an arithmetic progression is (-?\d+) and the (\d+)\w\w term is (-?\d+)", txt); mm, U, nn, V = map(int, m.groups())
            sols = [(a, d) for a in range(-150, 150) for d in range(-60, 60) if a + (mm - 1) * d == U and a + (nn - 1) * d == V]
            if sols != [tuple(int(c) for c in ans[0])]: fail(q, f"sols {sols}")
        elif txt.startswith("The ") and "geometric" in txt and "sum to infinity" not in txt:
            m = re.match(r"The (\d+)\w\w term of a geometric progression is (-?\d+) and the (\d+)\w\w term is (-?\d+)", txt); mm, U, nn, V = map(int, m.groups())
            sols = [(a, r) for a in range(-300, 300) for r in range(-12, 13) if a != 0 and a * r**(mm - 1) == U and a * r**(nn - 1) == V]
            if sols != [tuple(int(c) for c in ans[0])]: fail(q, f"sols {sols}")
        elif "sum to infinity" in txt and "Find the common ratio" in txt:
            m = re.search(r"first term (-?\d+) and sum to infinity (\S+)\.", txt); a = Rational(m.group(1)); S = Rational(m.group(2))
            sols = sorted({Rational(p, qq) for qq in range(1, 13) for p in range(-qq + 1, qq) if a / (1 - Rational(p, qq)) == S})
            if sols != [ans]: fail(q, f"sols {sols}")
        elif "Find the sum to infinity" in txt:
            m = re.search(r"first term (-?\d+) and common ratio (-?\d+)/(\d+)", txt); a, p, qq = map(int, m.groups())
            tot = 0.0; u = float(a)
            for _ in range(3000): tot += u; u *= p / qq
            if abs(tot - fl(ans)) > 1e-6: fail(q, f"got {tot}")
        elif "second term" in txt:
            m = re.search(r"second term of a geometric progression is (-?\d+) and its sum to infinity is (-?\d+)", txt); u, S = map(int, m.groups())
            sols = []
            for qq in range(1, 20):
                for p in range(-qq + 1, qq):
                    r = Rational(p, qq)
                    if p == 0: continue
                    a = Rational(u) / r
                    if a / (1 - r) == S and (a, r) not in sols: sols.append((a, r))
            if not match_pairs(q, sorted(tup(s_) for s_ in sols)): fail(q, f"sols {sols}")
        elif "least number of terms" in txt and "arithmetic" in txt:
            m = re.search(r"first term (-?\d+) and common difference (-?\d+)\. .* exceed (\d+)", txt); a, d, K = map(int, m.groups())
            n = 0; tot = 0; u = a
            while tot <= K: tot += u; u += d; n += 1
            if n != fl(ans): fail(q, f"got {n}")
        elif "least number of terms" in txt:
            m = re.search(r"first term (-?\d+) and common ratio (-?\d+)\. .* exceed (\d+)", txt); a, r, K = map(int, m.groups())
            n = 0; tot = 0; u = a
            while tot <= K: tot += u; u *= r; n += 1
            if n != fl(ans): fail(q, f"got {n}")
        else: fail(q, "no verifier branch")
    elif t == "vec":
        if txt.startswith("The position vectors of A and B, relative"):
            m = re.search(r"are (.*) and (.*)\. Find", txt); p, qq = vecs(m.group(1)), vecs(m.group(2))
            if (qq[0] - p[0], qq[1] - p[1]) != tuple(int(c) for c in ans): fail(q, "AB")
        elif "magnitude" in txt:
            v = vecs(re.search(r"vector (.*)\. Give", txt).group(1))
            if abs(math.hypot(*v) - fl(ans)) > 1e-9: fail(q, "mag")
        elif "unit vector" in txt:
            v = vecs(re.search(r"direction of (.*)\.", txt).group(1)); h = math.hypot(*v)
            if abs(v[0] / h - fl(ans[0])) > 1e-9 or abs(v[1] / h - fl(ans[1])) > 1e-9: fail(q, "unit")
        elif "parallel" in txt:
            m = re.search(r"vectors (.*) and (-?\d*i) \+ kj are|vectors (.*) and (.*) are parallel", txt)
            a_, b_ = vecs(re.search(r"The vectors (.*?) and ", txt).group(1)); c_ = vecs(re.search(r" and (.*?)j are parallel", txt).group(1).replace("k", "1") + "j")[0]
            lam = c_ / a_
            if abs(lam * b_ - fl(ans[0])) > 1e-9: fail(q, "par")
        elif "AP:PB" in txt:
            m = re.search(r"are (.*) and (.*)\. The point P.*AP:PB = (\d+):(\d+)", txt); A, B = vecs(m.group(1)), vecs(m.group(2)); a1, b1 = int(m.group(3)), int(m.group(4))
            Pp = [A[i] + (B[i] - A[i]) * a1 / (a1 + b1) for i in (0, 1)]
            if any(abs(Pp[i] - fl(ans[i])) > 1e-9 for i in (0, 1)): fail(q, "div")
        elif txt.startswith("Given that m("):
            m = re.match(r"Given that m\((.*?)\) \+ n\((.*?)\) = (.*?), find", txt); u, v, w = map(vecs, m.groups())
            sols = [(a, b) for a in range(-12, 13) for b in range(-12, 13) if a * u[0] + b * v[0] == w[0] and a * u[1] + b * v[1] == w[1]]
            if sols != [tuple(int(c) for c in ans[0])]: fail(q, f"sols {sols}")
        elif "collide" in txt:
            m = re.search(r"position vector \((.*?)\) m and particle Q has position vector \((.*?)\) m\. P moves with constant velocity \((.*?)\) m/s and Q with constant velocity \((.*?)\) m/s", txt)
            p0, q0, vp, vq = map(vecs, m.groups()); sols = []
            for tt in np.arange(0, 20.001, 0.5):
                if all(abs(p0[i] + vp[i] * tt - q0[i] - vq[i] * tt) < 1e-9 for i in (0, 1)): sols.append((tt, p0[0] + vp[0] * tt, p0[1] + vp[1] * tt))
            if not match_pairs(q, sols): fail(q, f"sols {sols}")
        elif "distance between P and Q when" in txt:
            m = re.search(r"position vector \((.*?)\) m and particle Q has position vector \((.*?)\) m\. P has constant velocity \((.*?)\) m/s and Q has constant velocity \((.*?)\) m/s\. Find the distance between P and Q when t = (\d+)", txt)
            p0, q0, vp, vq = map(vecs, m.groups()[:4]); T_ = int(m.group(5))
            d = math.hypot(q0[0] + vq[0] * T_ - p0[0] - vp[0] * T_, q0[1] + vq[1] * T_ - p0[1] - vp[1] * T_)
            if abs(d - fl(ans)) > 1e-9: fail(q, f"dist {d}")
        else: fail(q, "no verifier branch")
    elif t == "kin":
        if "expression for its displacement" in txt:
            vtxt = re.search(r"v = (.*?)\. When", txt).group(1).replace("t", "x"); s0 = int(re.search(r"is (-?\d+) m\.", txt).group(1)); v = F(vtxt)
            for p in (1.3, 2.9):
                xs = np.linspace(0, p, 200001); val = s0 + np.trapezoid(v(xs), xs)
                if abs(val - fl(ans.subs(TT, p))) > 1e-4: fail(q, f"s({p}) {val}")
        elif "displacement" in txt and "velocity v" in txt or "acceleration a" in txt:
            s_ = P(re.search(r"s = (.*?)\. Find", txt).group(1).replace("t", "x")); f = lambdify(X, s_, "numpy")
            for p in (0.7, 1.9, 3.3):
                h = 1e-4
                if "velocity v" in txt: val = (f(p + h) - f(p - h)) / (2 * h)
                else: h = 1e-3; val = (f(p + h) - 2 * f(p) + f(p - h)) / h**2
                if abs(val - fl(ans.subs(TT, p))) > 1e-3: fail(q, f"num deriv {val}")
        elif "instantaneous rest" in txt:
            v = F(re.search(r"v = (.*?)\. Find", txt).group(1).replace("t", "x")); got = [r for r in roots_numeric(v, 0, 30, 30001) if r >= 0]
            if len(got) != len(ans) or any(abs(a - fl(b)) > 1e-5 for a, b in zip(got, sorted(ans))): fail(q, f"{got}")
        elif "expression for its displacement" in txt:
            vtxt = re.search(r"v = (.*?)\. When", txt).group(1).replace("t", "x"); s0 = int(re.search(r"is (-?\d+) m\.", txt).group(1)); v = F(vtxt)
            for p in (1.3, 2.9):
                xs = np.linspace(0, p, 200001); val = s0 + np.trapezoid(v(xs), xs)
                if abs(val - fl(ans.subs(TT, p))) > 1e-4: fail(q, f"s({p}) {val}")
        elif "total distance" in txt:
            v = F(re.search(r"v = (.*?)\. Find", txt).group(1).replace("t", "x")); T_ = int(re.search(r"first (\d+) seconds", txt).group(1))
            xs = np.linspace(0, T_, 2000001); val = np.trapezoid(np.abs(v(xs)), xs)
            if abs(val - fl(ans)) > 1e-4: fail(q, f"{val}")
        else: fail(q, "no verifier branch")
    elif t == "rates":
        if "approximate change" in txt:
            m = re.search(r"y = (.*?), use .* from (\d+) to (\d+(?:\.\d+)?)", txt); f = F(m.group(1)); x0 = float(m.group(2)); dx = float(m.group(3)) - x0
            h = 1e-6; dy = (f(x0 + h) - f(x0 - h)) / (2 * h) * dx
            if abs(dy - fl(ans)) > 1e-5: fail(q, f"{dy}")
        elif "circle is increasing" in txt and "radius" in txt.split("increasing")[0]:
            m = re.search(r"at (\S+) cm/s.*radius is (\d+) cm", txt); rho = float(Rational(m.group(1))); r0 = int(m.group(2))
            A = lambda tt: math.pi * (r0 + rho * tt)**2; h = 1e-5
            if abs((A(h) - A(-h)) / (2 * h) - fl(ans)) > 1e-5: fail(q, "circle")
        elif "sphere" in txt:
            m = re.search(r"at (\S+) cm/s.*radius is (\d+) cm", txt); rho = float(Rational(m.group(1))); r0 = int(m.group(2))
            V = lambda tt: 4 / 3 * math.pi * (r0 + rho * tt)**3; h = 1e-5
            if abs((V(h) - V(-h)) / (2 * h) - fl(ans)) > 1e-4: fail(q, "sphere")
        elif "cube" in txt:
            m = re.search(r"at (\d+) cm/s.*edge is (\d+) cm", txt); rho, x0 = int(m.group(1)), int(m.group(2)); V = lambda tt: (x0 + rho * tt)**3; h = 1e-5
            if abs((V(h) - V(-h)) / (2 * h) - fl(ans)) > 1e-4: fail(q, "cube")
        elif "point moves along the curve" in txt:
            m = re.search(r"curve y = (.*?) so that x is increasing at (\d+) units.*when x = (\d+)", txt); f = F(m.group(1)); c = int(m.group(2)); x0 = int(m.group(3)); h = 1e-5
            if abs((f(x0 + c * h) - f(x0 - c * h)) / (2 * h) - fl(ans)) > 1e-3: fail(q, "func")
        elif "area of a circle is increasing" in txt:
            m = re.search(r"at (\d+) pi cm.*radius is (\d+) cm", txt); Ap, r0 = int(m.group(1)), int(m.group(2))
            if abs(Ap * math.pi / (2 * math.pi * r0) - fl(ans)) > 1e-9: fail(q, "rev")
        elif "square sheet" in txt:
            L = int(re.search(r"sides of (\d+) cm", txt).group(1)); xs = np.linspace(0.0001, L / 2 - 0.0001, 2000001); V = xs * (L - 2 * xs)**2; i = V.argmax()
            if abs(xs[i] - fl(ans[0][0])) > 1e-3 or abs(V[i] - fl(ans[0][1])) > 1e-3: fail(q, f"{xs[i]},{V[i]}")
        elif "farmer" in txt:
            F_ = int(re.search(r"has (\d+) m", txt).group(1)); xs = np.linspace(0.0001, F_ / 2 - 0.0001, 2000001); A = xs * (F_ - 2 * xs); i = A.argmax()
            if abs(xs[i] - fl(ans[0][0])) > 1e-3 or abs(A[i] - fl(ans[0][1])) > 1e-3: fail(q, f"{xs[i]},{A[i]}")
        elif "cuboid" in txt:
            V0 = int(re.search(r"volume (\d+) cm", txt).group(1)); xs = np.linspace(0.5, 30, 2000001); S_ = 2 * xs**2 + 4 * V0 / xs; i = S_.argmin()
            if abs(xs[i] - fl(ans[0][0])) > 1e-3 or abs(S_[i] - fl(ans[0][1])) > 1e-3: fail(q, f"{xs[i]},{S_[i]}")
        else: fail(q, "no verifier branch")
    elif t == "area":
        import mpmath
        if "bounded by the curve y = " in txt and "x-axis and the lines" in txt:
            m = re.search(r"curve y = (.*?), the x-axis and the lines x = (\d+) and x = (\d+)", txt); f = F(m.group(1)); lo, hi = int(m.group(2)), int(m.group(3))
            if abs(float(mpmath.quad(lambda z: abs(f(z)), [lo, hi])) - fl(ans)) > 1e-8: fail(q, "easy")
        elif "crosses the x-axis at two points" in txt:
            f = F(re.search(r"y = (.*?) crosses", txt).group(1)); r = roots_numeric(f, -20, 20)
            if abs(float(mpmath.quad(lambda z: abs(f(z)), [r[0], r[1]])) - fl(ans)) > 1e-6: fail(q, "quad")
        elif "The line y = " in txt:
            m = re.search(r"The line y = (.*?) meets the curve y = (.*?) at two", txt); g_, f_ = F(m.group(1)), F(m.group(2))
            r = roots_numeric(lambda z: g_(z) - f_(z) + 0 * z, -20, 20)
            if len(r) != 2 or abs(float(mpmath.quad(lambda z: abs(g_(z) - f_(z)), [r[0], r[1]])) - fl(ans)) > 1e-6: fail(q, "line-curve")
        elif "three points" in txt:
            f = F(re.search(r"y = (.*?) crosses", txt).group(1)); r = roots_numeric(f, -20, 20)
            tot = sum(float(mpmath.quad(lambda z: abs(f(z)), [r[i], r[i + 1]])) for i in range(len(r) - 1))
            if len(r) != 3 or abs(tot - fl(ans)) > 1e-6: fail(q, "cubic")
        elif "e^(" in txt:
            a = int(re.search(r"e\^\((\d+)x\)", txt).group(1))
            if abs(float(mpmath.quad(lambda z: math.exp(a * z), [0, 1])) - fl(ans)) > 1e-8: fail(q, "exp")
        else:
            m = re.search(r"y = 1/\((.*?)\), .* x = (\d+)\.", txt); f = F(m.group(1)); h = int(m.group(2))
            if abs(float(mpmath.quad(lambda z: 1 / f(z), [0, h])) - fl(ans)) > 1e-8: fail(q, "inv")
    elif t == "lin":
        pts = re.findall(r"\((-?\d+), (-?\d+)\)", txt.split("straight line")[1]) if "straight line" in txt else []
        if "y = ax^2 + b" in txt or "y = a/x + b" in txt or "y = ax + b/x" in txt or "y/x against x" in txt:
            (X1, Y1), (X2, Y2) = [(int(a), int(b)) for a, b in pts]
            m = Rational(Y2 - Y1, X2 - X1); c = Y1 - m * X1
            exp = (m, c) if "y/x against" not in txt else (c, m)
            if (fl(exp[0]), fl(exp[1])) != (fl(ans[0][0]), fl(ans[0][1])): fail(q, f"{exp}")
            # plug back: reconstruct original function and check the plotted points
            a_, b_ = fl(ans[0][0]), fl(ans[0][1])
            ok = True
            for (Xv, Yv) in [(int(a), int(b)) for a, b in pts]:
                if "y = ax^2 + b" in txt: ok &= abs(a_ * Xv + b_ - Yv) < 1e-9
                elif "y = a/x + b" in txt: ok &= abs(a_ * Xv + b_ - Yv) < 1e-9
                elif "y = ax + b/x" in txt: ok &= abs(a_ * Xv + b_ - Yv) < 1e-9
                else: ok &= abs(b_ * Xv + a_ - Yv) < 1e-9
            if not ok: fail(q, "points")
        elif "lg y against lg x" in txt:
            m = re.search(r"gradient (\S+) that meets the vertical axis at \(0, (\d+)\)", txt); gr = float(Rational(m.group(1))); c = int(m.group(2))
            A, n = fl(ans[0][0]), fl(ans[0][1])
            ys = [(math.log10(A * xx**n), math.log10(xx)) for xx in (2.0, 5.0)]
            slope = (ys[1][0] - ys[0][0]) / (ys[1][1] - ys[0][1]); icpt = ys[0][0] - slope * ys[0][1]
            if abs(slope - gr) > 1e-9 or abs(icpt - c) > 1e-9: fail(q, f"{slope},{icpt}")
        elif "lg y against x" in txt:
            m = re.search(r"gradient (\d+) that meets the vertical axis at \(0, (\d+)\)", txt); gr, c = int(m.group(1)), int(m.group(2)); A, b = fl(ans[0][0]), fl(ans[0][1])
            y0, y1 = math.log10(A), math.log10(A * b**3)
            if abs((y1 - y0) / 3 - gr) > 1e-9 or abs(y0 - c) > 1e-9: fail(q, "Ab^x")
        elif "y^2 against x^3" in txt:
            m = re.search(r"gradient (\d+) and intercept (-?\d+)", txt); gr, c = int(m.group(1)), int(m.group(2))
            yv = fl(ans)
            if abs(yv**2 - (gr * 8 + c)) > 1e-9 or yv <= 0: fail(q, "y2x3")
        else: fail(q, "no verifier branch")
    elif t == "line":
        if "midpoint" in txt:
            a, b, c, d = nums(txt.split("Find")[0]); got = ((a + c) / 2, (b + d) / 2)
            if tup(ans[0]) != got: fail(q, "mid")
        elif "length of AB" in txt:
            a, b, c, d = nums(txt.split("Find")[0])
            if abs(math.hypot(a - c, b - d) - fl(ans)) > 1e-9: fail(q, "len")
        elif "through the points" in txt:
            a, b, c, d = nums(txt); f = lambdify(X, ans, "numpy")
            if abs(f(a) - b) > 1e-9 or abs(f(c) - d) > 1e-9: fail(q, "thru")
        elif "perpendicular to the line" in txt:
            m = re.search(r"point \((-?\d+), (-?\d+)\) that is perpendicular to the line y = (.*)\.", txt); px, py = int(m.group(1)), int(m.group(2))
            g = F(m.group(3)); f = lambdify(X, ans, "numpy"); sl1 = g(1.0) - g(0.0); sl2 = f(1.0) - f(0.0)
            if abs(sl1 * sl2 + 1) > 1e-9 or abs(f(px) - py) > 1e-9: fail(q, "perp")
        elif "perpendicular bisector" in txt:
            a, b, c, d = nums(txt.split("Find")[0]); f = lambdify(X, ans, "numpy")
            for xv in (-3.0, 0.7, 4.2):
                if abs(math.hypot(xv - a, f(xv) - b) - math.hypot(xv - c, f(xv) - d)) > 1e-8: fail(q, "bis")
        elif "foot of the perpendicular" in txt:
            m = re.search(r"equation y = (.*?)\. .*P\((-?\d+), (-?\d+)\)", txt); g = F(m.group(1)); px, py = int(m.group(2)), int(m.group(3))
            fx, fy = tup(ans[0]); slope = g(1.0) - g(0.0)
            if abs(g(fx) - fy) > 1e-9 or abs((fx - px) + slope * (fy - py)) > 1e-9: fail(q, "foot")
        else: fail(q, "no verifier branch")
    elif t == "cgeo":
        th = np.linspace(0, 2 * np.pi, 13)
        if "write down the coordinates" in txt.lower() or "Write down the coordinates" in txt:
            e = re.search(r"circle is (.*)\. Write", txt).group(1); l, r = e.split(" = "); f = lambdify((X, Y), P(l) - P(r), "numpy")
            a, b, rr = tup(ans[0])
            if np.abs(f(a + rr * np.cos(th), b + rr * np.sin(th))).max() > 1e-8: fail(q, "easy centre")
        elif txt.startswith("A circle has equation"):
            e = re.search(r"equation (.*) = 0\.", txt).group(1); f = lambdify((X, Y), P(e), "numpy"); a, b, rr = tup(ans[0])
            if np.abs(f(a + rr * np.cos(th), b + rr * np.sin(th))).max() > 1e-8: fail(q, "expanded")
        elif txt.startswith("Find the equation of the circle with centre"):
            a, b, rr = nums(txt)[:3]; f = lambdify((X, Y), ans, "numpy")
            if np.abs(f(a + rr * np.cos(th), b + rr * np.sin(th))).max() > 1e-8: fail(q, "eqn")
        elif "end points of a diameter" in txt:
            a1, b1, a2, b2 = nums(txt.split("Find")[0]); cx, cy, rr = (a1 + a2) / 2, (b1 + b2) / 2, math.hypot(a1 - a2, b1 - b2) / 2; f = lambdify((X, Y), ans, "numpy")
            if np.abs(f(cx + rr * np.cos(th), cy + rr * np.sin(th))).max() > 1e-8: fail(q, "diam")
        elif "tangent to the circle at P" in txt:
            m = re.search(r"The circle (.*?) = (\d+) passes through the point P\((-?\d+), (-?\d+)\)", txt); circ = P(m.group(1)) - int(m.group(2)); px, py = int(m.group(3)), int(m.group(4))
            cf = lambdify((X, Y), circ, "numpy"); f = lambdify(X, ans, "numpy")
            if abs(cf(px, py)) > 1e-9 or abs(f(px) - py) > 1e-9: fail(q, "P")
            # tangent: circle value along line has a double root -> min of cf(x, f(x)) is ~0
            xs = np.linspace(px - 3, px + 3, 600001); vals = cf(xs, f(xs))
            if vals.min() < -1e-6: fail(q, "line enters circle")
        elif "passes through the point" in txt:
            a, b, c, d = nums(txt.split("Find")[0]); rr = math.hypot(a - c, b - d); f = lambdify((X, Y), ans, "numpy")
            if np.abs(f(a + rr * np.cos(th), b + rr * np.sin(th))).max() > 1e-8: fail(q, "thru")
        elif "meets the circle" in txt:
            m = re.search(r"line y = (.*?) meets the circle (.*?) = (\d+)\.", txt); g = F(m.group(1)); circ = P(m.group(2)) - int(m.group(3))
            cf = lambdify((X, Y), circ, "numpy")
            r = roots_numeric(lambda z: cf(z, g(z)), -40, 40)
            got = sorted((v, float(g(v))) for v in r)
            if not match_pairs(q, got): fail(q, f"{got}")
        elif "is a tangent to the circle" in txt:
            m = re.search(r"The line (\d+)y = (\d+)x \+ k is a tangent to the circle (.*?) = (\d+)\.", txt); q_, p_ = int(m.group(1)), int(m.group(2)); circ = P(m.group(3)); rr = math.sqrt(int(m.group(4)))
            cx = fl(gen.solve(gen.diff(circ, X), X)[0]); cy = fl(gen.solve(gen.diff(circ, Y), Y)[0])
            for k in ans:
                k = fl(k); dist = abs(p_ * cx - q_ * cy + k) / math.hypot(p_, q_)
                if abs(dist - rr) > 1e-9: fail(q, f"k={k}")
        else: fail(q, "no verifier branch")
    elif t == "tgraph":
        xs = np.linspace(0, 360, 360001)
        if txt.startswith("State the amplitude"):
            e = re.search(r"y = (.*?)\. Give", txt).group(1).replace("sin(", "sin((").replace("cos(", "cos((")
            e = re.sub(r"(sin|cos)\(\((\d*)x\)", lambda mm: f"{mm.group(1)}(({mm.group(2) or 1})*x*pi/180)", e)
            f = lambdify(X, P(e), "numpy"); v = f(xs); amp = (v.max() - v.min()) / 2
            per = next(p for p in range(1, 361) if np.abs(f(xs[:2000] + p) - v[:2000]).max() < 1e-7 and np.abs(f(xs[:2000] + 2 * p) - v[:2000]).max() < 1e-7)
            if abs(amp - fl(ans[0][0])) > 1e-6 or per != fl(ans[0][1]): fail(q, f"{amp},{per}")
        elif txt.startswith("Find the greatest and least"):
            e = re.search(r"y = (.*?)\. Give", txt)
            e = re.sub(r"(sin|cos)\((\d*)x\)", lambda mm: f"{mm.group(1)}(({mm.group(2) or 1})*x*pi/180)", e.group(1))
            f = lambdify(X, P(e), "numpy"); v = f(xs)
            if abs(v.max() - fl(ans[0][0])) > 1e-6 or abs(v.min() - fl(ans[0][1])) > 1e-6: fail(q, f"{v.max()},{v.min()}")
        else:
            m = re.search(r"y = a (sin|cos)\(bx\) \+ c.*greatest value (-?\d+), least value (-?\d+) and period (\d+)", txt); fn = m.group(1); hi, lo, per = int(m.group(2)), int(m.group(3)), int(m.group(4))
            a, b, c = tup(ans[0]); f = (lambda z: a * np.sin(np.radians(b * z)) + c) if fn == "sin" else (lambda z: a * np.cos(np.radians(b * z)) + c)
            v = f(xs)
            if abs(v.max() - hi) > 1e-6 or abs(v.min() - lo) > 1e-6 or abs(360 / b - per) > 1e-9 or a <= 0 or b <= 0: fail(q, "hard")

if __name__ == "__main__":
    seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    topics = sys.argv[2].split(",") if len(sys.argv) > 2 else ["mod", "ineq", "prog", "vec", "kin", "rates", "area", "lin", "line", "cgeo", "tgraph"]
    n = 0
    for t in topics:
        for lv in gen.LEVELS:
            for seed in range(1, seeds + 1):
                try: q = gen.build(f"{t}-{lv}-{seed}")
                except Exception as ex: bad.append((f"{t}-{lv}-{seed}", "", "", f"BUILD {ex!r}")); continue
                try: verify(q)
                except Exception as ex: bad.append((q["id"], q["question"], gen.ans_str(q), f"VERIFIER ERROR {ex!r}"))
                n += 1
    print(f"checked {n} questions, {len(bad)} problems")
    seen = set()
    for b in bad:
        key = (b[0].split('-')[0], b[0].split('-')[1], b[3][:25])
        if key in seen: continue
        seen.add(key); print(b)
