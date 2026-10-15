"""Edith question generator. Every answer is computed with sympy, so answer keys are correct by construction.

Commands (write answers in plain text; ^ for powers):
  python gen.py list                              topics and levels
  python gen.py new <topic> [level] [seed]        one new question (level: easy, medium, hard; default medium)
  python gen.py followup <topic> [seed]           three questions: easy, medium, hard
  python gen.py check <id> "<student answer>"     CORRECT, INCORRECT or AMBIGUOUS (never prints the answer).
                                                  After INCORRECT it may add a DIAGNOSIS line naming the usual slip that matches.
  python gen.py hint <id> <n>                     the n-th hint (1, 2, 3 ...) for that question
  python gen.py reveal <id>                       full worked steps and the answer (use only after the student has solved it, or has used all hints)
  python gen.py dump <id>                         JSON with question and answer, for the benchmark script
<id> is printed with every question, for example  diff-medium-48213
"""
import sys, os, re, json, random, math, ast
from sympy import (Symbol, Rational, Integer, sqrt, exp, log, sin, cos, tan, pi, E, diff, integrate,
                   solve, expand, factor, simplify, N, binomial, factorial, Eq, S, sympify, cancel,
                   sec, Abs, Lt, Le, Gt, Ge, Interval, Union, FiniteSet, EmptySet, oo)
from sympy.parsing.sympy_parser import (parse_expr, stringify_expr, eval_expr, standard_transformations,
                                        implicit_multiplication_application, convert_xor)

x = Symbol("x"); y = Symbol("y"); k_ = Symbol("k")
T = standard_transformations + (implicit_multiplication_application, convert_xor)
LOCALS = {"ln": log, "e": E, "cosec": lambda a: 1 / sin(a), "sec": lambda a: 1 / cos(a),
          "cot": lambda a: 1 / tan(a), "lg": lambda a: log(a, 10)}

# ---------- formatting ----------
def fmt(e):
    s = str(e).replace("**", "^").replace("exp(", "e^(").replace("log(", "ln(")
    s = re.sub(r"(?<![\^\w.])(\d+(?:\.\d+)?)\*(?=[a-zA-Z(])", r"\1", s)
    return s

def pstr(terms):
    """Build 'ax^2 + bx - c' text. terms = [(coef, 'x^2'), ...]; coef is an int or a name like 'k'."""
    out = ""
    for c, p in terms:
        if not isinstance(c, str) and c == 0: continue
        if isinstance(c, str): neg, mag = False, c
        else:
            neg = c < 0; a_ = abs(c); mag = "" if (a_ == 1 and p) else str(a_)
        body = mag + p
        out += (("-" if neg else "") + body) if not out else ((" - " if neg else " + ") + body)
    return out or "0"

def eqn(l, r): return f"{fmt(l)} = {fmt(r)}"

def ri(rng, a, b, nz=False):
    while True:
        v = rng.randint(a, b)
        if not nz or v != 0: return v

def pair_str(p): return f"({fmt(p[0])}, {fmt(p[1])})"

def ans_str(q):
    a, kind = q["answer"], q["kind"]
    if q.get("ans_text"): return q["ans_text"]
    if kind in ("expr", "antider", "value", "num3sf", "int"): return fmt(a)
    if kind == "set": return ", ".join(fmt(v) for v in a)
    if kind == "pairs": return ", ".join("(" + ", ".join(fmt(c) for c in p) + ")" for p in a)
    if kind == "vec": return f"({fmt(a[0])}, {fmt(a[1])})"
    if kind == "eqn": return f"{fmt(a)} = 0"
    return str(a)

# ---------- parsing student answers ----------
def clean(s):
    s = re.sub(r"\|([^|]*)\|", r" Abs(\1) ", s).replace("[", "(").replace("]", ")")
    for a, b in (("×", "*"), ("·", "*"), ("−", "-"), ("–", "-"), ("√", "sqrt"), ("π", "pi"), ("÷", "/"),
                 ("²", "^2"), ("³", "^3"), ("°", ""), ("degrees", ""), ("degree", ""), ("rad", "")):
        s = s.replace(a, b)
    return s.strip()

ALLOWED = {"x", "y", "t", "k", "e", "pi", "sqrt", "ln", "lg", "sin", "cos", "tan", "sec", "cosec", "cot",
           "exp", "abs", "Abs", "U", "V"}

def sanitise(s):
    """Student text goes into sympy's parser, so reject anything that is not plain maths."""
    if len(s) > 300 or "__" in s: raise ValueError("unsafe input")
    if re.search(r"[^0-9A-Za-z_+\-*/^().,=<>\s]", s) or re.search(r"\.[A-Za-z_]", s): raise ValueError("unsafe input")
    if s.count("^") > 8 or re.search(r"\^\s*\(?\s*-?\d{3,}", s): raise ValueError("power too large")
    for w in re.findall(r"[A-Za-z_]+", s):
        if w in ALLOWED: continue
        if w == "log" or len(w) > 3: raise ValueError("unknown word " + w)
    return s

_GLOB = {}
exec("from sympy import *", _GLOB)

def _small(n):
    if isinstance(n, ast.Constant):
        try: return abs(float(n.value)) <= 99
        except (TypeError, ValueError): return False
    if isinstance(n, ast.Name): return n.id in ("pi", "e", "E")
    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("Integer", "Float", "Rational"):
        return all(_small(a) for a in n.args)
    if isinstance(n, ast.UnaryOp): return _small(n.operand)
    if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Div, ast.Add, ast.Sub)): return _small(n.left) and _small(n.right)
    return False

def guard(code):
    """Refuse anything that could run for ages (a tower of powers) or reach Python internals."""
    tree = ast.parse(code, mode="eval")
    for n in ast.walk(tree):
        if isinstance(n, (ast.Attribute, ast.Subscript, ast.Lambda, ast.ListComp, ast.GeneratorExp, ast.Dict, ast.Set, ast.Starred)):
            raise ValueError("unsafe input")
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Pow):
            e = n.right
            has_sym = any(isinstance(m, ast.Call) and isinstance(m.func, ast.Name) and m.func.id == "Symbol" for m in ast.walk(e))
            if not (has_sym or _small(e)): raise ValueError("power too large")

def to_expr(s):
    s = sanitise(clean(s))
    s = re.sub(r"\+\s*[cC]\s*$", "", s)
    code = stringify_expr(s, dict(LOCALS), _GLOB, T)
    guard(code)
    return eval_expr(code, dict(LOCALS), _GLOB)

LHS = re.compile(r"\s*(y|v|s|a|v\(t\)|s\(t\)|a\(t\)|ds/dt|dv/dt|dy/dx|y'|f\(x\)|f'\(x\)|g\(x\)|fg\(x\)|gf\(x\)|f\^-1\(x\)|f\^\(-1\)\(x\)|f-1\(x\))\s*", re.I)

def student_func(s, var=x):
    s = clean(s)
    if "=" in s:
        parts = s.split("=")
        if len(parts) == 2:
            if LHS.fullmatch(parts[0]): s = parts[1]
            else:
                sol = solve(Eq(to_expr(parts[0]), to_expr(parts[1])), y)
                if len(sol) == 1: return sol[0]
                raise ValueError("cannot read equation")
    f = to_expr(s)
    if var != x and x in f.free_symbols and var not in f.free_symbols: f = f.subs(x, var)
    return f

def num(e):
    v = complex(N(e, 30))
    if abs(v.imag) > 1e-9: raise ValueError("complex")
    if not math.isfinite(v.real): raise ValueError("not finite")
    return v.real

def close(a, b, rel=1e-7, ab=1e-9): return abs(a - b) <= max(ab, rel * max(abs(a), abs(b)))

SAMPLES = [0.37, 1.61, -0.83, 2.77, 3.9, -2.3, 0.11, 5.2, 7.3, 11.9, 25.5, -7.7, -15.2]

def same_func(f, g, var=x):
    ok = 0
    for p in SAMPLES:
        try:
            a = num(f.subs(var, p)); b = num(g.subs(var, p))
        except Exception:
            continue
        if not close(a, b): return False
        ok += 1
    return ok >= 3

def split_top(s, sep=","):
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([": depth += 1
        if ch in ")]": depth -= 1
        if ch == sep and depth == 0: out.append(cur); cur = ""
        else: cur += ch
    out.append(cur); return out

def tuples(s):
    res, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(":
            if depth == 0: cur = ""
            else: cur += ch
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                parts = split_top(cur)
                if len(parts) >= 2: res.append(tuple(to_expr(p_) for p_ in parts))
            elif depth > 0: cur += ch
        elif depth > 0: cur += ch
    return res

def xy_pairs(s):
    m = re.findall(r"x\s*=\s*([^,;]+?)\s*(?:,|;|and)?\s*y\s*=\s*([^,;]+?)(?=\s*(?:,|;|and|or|$))", clean(s))
    return [(to_expr(a), to_expr(b)) for a, b in m]

def values(s):
    s = clean(s)
    s = re.sub(r"\b[a-zA-Z]\s*=\s*", "", s)
    out = []
    for piece in re.split(r",|;|\bor\b|\band\b|\n", s):
        piece = piece.strip()
        if not piece: continue
        if piece.startswith("±") or piece.startswith("+-"):
            v = num(to_expr(piece.lstrip("±+-").strip())); out += [v, -v]
        else: out.append(num(to_expr(piece)))
    return out

def sig3(v):
    if v == 0: return 0.0
    return round(v, 2 - int(math.floor(math.log10(abs(v)))))

def named_tuple(s, names):
    s = clean(s); out = []
    for n in names:
        m = re.search(r"(?<![A-Za-z])" + re.escape(n) + r"\s*=\s*([^,;]+?)(?=\s*(?:,|;|\band\b|$))", s)
        if not m: return []
        out.append(to_expr(m.group(1)))
    return [tuple(out)]

REL = re.compile(r"(<=|>=|<|>)")
RELF = {"<": Lt, "<=": Le, ">": Gt, ">=": Ge}

def chain_pred(piece):
    parts = REL.split(clean(piece).replace("\u2264", "<=").replace("\u2265", ">="))
    if len(parts) < 3 or len(parts) % 2 == 0: raise ValueError("not an inequality")
    exprs = [to_expr(p_) for p_ in parts[0::2]]; ops = parts[1::2]
    def pred(v):
        for i, o in enumerate(ops):
            r = RELF[o](exprs[i].subs(x, v), exprs[i + 1].subs(x, v))
            if r not in (S.true, S.false): raise ValueError("cannot decide")
            if r == S.false: return False
        return True
    return pred

def interval_parts(st):
    return [st] if st.is_Interval else list(st.args)

def interval_ok(ans, s):
    s = clean(s).replace("\u222a", ";")
    groups = []
    for p_ in re.split(r"\bor\b|;|,|\bU\b", s):
        if p_.strip(): groups.append([chain_pred(z) for z in re.split(r"\band\b", p_) if z.strip()])
    if not groups: return False
    bs = set()
    for iv in interval_parts(ans):
        for e in (iv.start, iv.end):
            if e not in (oo, -oo): bs.add(e)
    bs = sorted(bs, key=lambda r: float(r))
    pts = list(bs) + [(a_ + b_) / 2 for a_, b_ in zip(bs, bs[1:])] + [bs[0] - 1, bs[-1] + 1, bs[0] - 100, bs[-1] + 100]
    pts += [b_ + d_ for b_ in bs for d_ in (Rational(1, 1000), -Rational(1, 1000))]
    for v in pts:
        mine = any(all(f(v) for f in g) for g in groups)
        if mine != bool(ans.contains(v)): return False
    return True

def vec_parse(s):
    s = clean(s)
    if re.search(r"(?<![A-Za-z])[ij](?![A-Za-z(])", s):
        t2 = re.sub(r"(?<![A-Za-z])i(?![A-Za-z(])", " U ", s)
        t2 = re.sub(r"(?<![A-Za-z])j(?![A-Za-z(])", " V ", t2)
        e = expand(to_expr(t2)); ui, uj = Symbol("U"), Symbol("V")
        ci, cj = e.coeff(ui), e.coeff(uj)
        if expand(e - ci * ui - cj * uj) != 0: raise ValueError("bad vector")
        return (ci, cj)
    tp = tuples(s)
    if len(tp) == 1 and len(tp[0]) == 2: return tp[0]
    m = re.fullmatch(r"\(?\s*(-?[\d./]+)\s+(-?[\d./]+)\s*\)?", s)
    if m: return (to_expr(m.group(1)), to_expr(m.group(2)))
    raise ValueError("no vector")

EQPTS = [(1.3, 0.7), (-2.1, 3.4), (4.2, -1.9), (0.5, -3.3), (6.1, 2.2), (-5.5, -4.1), (2.9, 5.3)]

def check(q, s):
    kind, a = q["kind"], q["answer"]
    v = Symbol(q["var"]) if q.get("var") else x
    try:
        if kind == "expr":
            return same_func(student_func(s, v), a, v)
        if kind == "antider":
            f = student_func(s, v)
            f = f.replace(lambda e: e.func == log and isinstance(e.args[0], Abs), lambda e: log(e.args[0].args[0]))
            if f.free_symbols - {v}: return False
            return same_func(diff(f, v), diff(a, v), v)
        if kind == "int":
            return close(num(to_expr(clean(s))), num(a), 1e-12, 1e-12)
        if kind == "value":
            u = num(to_expr(clean(s))); t = num(a)
            if close(u, t, 1e-7): return True
            return not a.is_rational and sig3(u) == sig3(t)
        if kind == "num3sf":
            return sig3(num(to_expr(clean(s)))) == sig3(num(a))
        if kind == "set":
            vs = sorted(values(s)); t = sorted(num(e) for e in a)
            tol = q.get("tol", 1e-6)
            if len(set(round(u, 6) for u in vs)) != len(set(round(u, 6) for u in t)): return False
            return all(any(abs(u - w) <= tol * max(1, abs(w)) for u in vs) for w in t) and \
                   all(any(abs(u - w) <= tol * max(1, abs(w)) for w in t) for u in vs)
        if kind == "pairs":
            got = tuples(clean(s)) or xy_pairs(s)
            if not got and q.get("names"): got = named_tuple(s, q["names"])
            gv = [tuple(num(c) for c in p_) for p_ in got]
            tv = [tuple(num(c) for c in p_) for p_ in a]
            if len(gv) != len(tv) or any(len(g) != len(tv[0]) for g in gv): return False
            same = lambda g, t: all(close(c1, c2, 1e-6) for c1, c2 in zip(g, t))
            return all(any(same(g, t) for g in gv) for t in tv) and all(any(same(g, t) for t in tv) for g in gv)
        if kind == "interval":
            return interval_ok(a, s)
        if kind == "vec":
            g = vec_parse(s)
            return all(close(num(c1), num(c2), 1e-7) for c1, c2 in zip(g, a))
        if kind == "eqn":
            sides = clean(s).split("=")
            if len(sides) != 2: return False
            F = to_expr(sides[0]) - to_expr(sides[1]); ratios = []
            for px, py in EQPTS:
                fa = num(a.subs({x: px, y: py}))
                if abs(fa) < 1e-9: continue
                ratios.append(num(F.subs({x: px, y: py})) / fa)
            return len(ratios) >= 4 and abs(ratios[0]) > 1e-9 and all(close(r, ratios[0], 1e-6) for r in ratios)
    except Exception:
        return None
    return False


AMB = re.compile(r"/\s*(\d+(?:\.\d+)?\s*(?:\([^()]*\)|(?:[a-zA-Z_]+(?:\([^()]*\))?(?:\^-?\d+)?)+))")

def ambiguous_alts(s):
    """Readings of a/2x as a/(2x). Returns every combination of bracketing the ambiguous divisions."""
    ms = list(AMB.finditer(s))[:5]
    out = []
    for mask in range(1, 2 ** len(ms)):
        t, last = "", 0
        for i, m in enumerate(ms):
            t += s[last:m.start()]
            t += "/(" + m.group(1) + ")" if mask >> i & 1 else s[m.start():m.end()]
            last = m.end()
        out.append(t + s[last:])
    return out

def verdict(q, s):
    r = check(q, s)
    if r is True and q.get("exact") and q["kind"] == "value" and not q["answer"].is_rational \
            and re.search(r"\d\.\d", clean(s)):
        return ("NOT EXACT: the value is right but the question asks for an exact answer. "
                "Ask the student to write it with surds, pi, e or ln instead of a decimal.")
    if r is True: return "CORRECT"
    if any(check(q, alt) is True for alt in ambiguous_alts(s)):
        return ("AMBIGUOUS: this can be read two ways, for example a/2x means (a/2)x, not a/(2x). "
                "Ask the student to rewrite it with brackets around every denominator, then check again.")
    if r is None: return "COULD NOT READ THE ANSWER: ask the student to rewrite it in plain text"
    return "INCORRECT"

# ---------- generators ----------
GEN = {}
def topic(name, desc):
    def deco(f): GEN[name] = (f, desc); return f
    return deco

def mk(text, kind, answer, steps, **kw):
    if kind in ("int", "value", "num3sf"): answer = sympify(answer)
    d = {"question": text, "kind": kind, "answer": answer, "steps": steps}
    if kind == "value" and re.search(r"exact|in terms of", text, re.I): d["exact"] = True
    d.update(kw); return d

@topic("diff", "Differentiation: term by term, chain, product, quotient")
def g_diff(rng, lv):
    if lv == "easy":
        if rng.random() < 0.6:
            ts = rng.sample([x**2, x**3, x**4, x**5, 1 / x, sqrt(x), x**-2, x**Rational(3, 2)], 2)
            f = ri(rng, -6, 6, True) * ts[0] + ri(rng, -6, 6, True) * ts[1] + ri(rng, -9, 9, True) * x + ri(rng, -9, 9, True)
            steps = ["Differentiate term by term using d/dx(a x^n) = a n x^(n-1).",
                     "Rewrite roots and fractions as powers of x first: sqrt(x) = x^(1/2) and 1/x = x^(-1).",
                     "A constant differentiates to 0."]
        else:
            kk = ri(rng, -4, 5, True)
            f = ri(rng, 1, 5) * exp(kk * x) + ri(rng, -6, 6, True) * x**ri(rng, 2, 4) + ri(rng, -9, 9)
            steps = ["Differentiate term by term.", f"The derivative of e^(kx) is k e^(kx). Here k = {kk}.",
                     "For a x^n use a n x^(n-1). A constant differentiates to 0."]
        return mk(f"Differentiate y = {fmt(f)} with respect to x.", "expr", diff(f, x), steps)
    if lv == "medium":
        t = rng.choice(["pow", "exp", "ln", "sin", "cos"])
        a, b = ri(rng, 1, 5), ri(rng, -6, 6, True)
        if t == "pow":
            n = rng.choice([3, 4, 5, -1, -2, Rational(1, 2)]); inner = a * x + b; f = inner**n
        elif t == "exp":
            inner = a * x**2 + ri(rng, -3, 3, True) * x; f = exp(inner)
        elif t == "ln":
            inner = a * x**2 + abs(b); f = log(inner)
        elif t == "sin":
            inner = a * x + b; f = sin(inner)
        else:
            inner = a * x + b; f = cos(inner)
        c = ri(rng, 1, 4); f = c * f
        steps = ["This is a function of a function, so use the chain rule: dy/dx = dy/du * du/dx.",
                 f"Let u = {fmt(inner)}. Write y in terms of u.", f"du/dx = {fmt(diff(inner, x))}. Now find dy/du.",
                 "Multiply the two derivatives and put u back in terms of x."]
        return mk(f"Differentiate y = {fmt(f)} with respect to x.", "expr", diff(f, x), steps)
    t = rng.choice(["prod", "prod", "quot"])
    if t == "prod":
        n = ri(rng, 2, 4); kk = ri(rng, 2, 4); a, b = ri(rng, 1, 4), ri(rng, -5, 5, True)
        u, v = rng.choice([(x**n, exp(kk * x)), (x**n, log(x)), (x**n, sin(kk * x)), (x**n, cos(kk * x)),
                           ((a * x + b)**n, exp(kk * x)), ((a * x + b)**n, sin(kk * x)), (x, (a * x + abs(b))**Rational(1, 2))])
        f = u * v
        steps = ["This is a product of two functions of x, so use the product rule: d/dx(uv) = u v' + v u'.",
                 f"Take u = {fmt(u)} and v = {fmt(v)}.", f"Find u' and v'. One of them needs the chain rule.",
                 "Substitute into u v' + v u' and simplify."]
    else:
        a, b, c = ri(rng, 1, 4), ri(rng, -5, 5, True), ri(rng, 1, 5)
        u, v = rng.choice([(a * x + b, x**2 + c), (exp(a * x), x + c), (sin(a * x), x), (x**2, a * x + c), (log(x), x**2), (x**2 + b, exp(x))])
        f = u / v
        steps = ["This is a quotient, so use the quotient rule: d/dx(u/v) = (v u' - u v') / v^2.",
                 f"Take u = {fmt(u)} and v = {fmt(v)}.", "Find u' and v'.", "Substitute carefully, keeping the order v u' - u v', then simplify."]
    return mk(f"Differentiate y = {fmt(f)} with respect to x.", "expr", diff(f, x), steps)

@topic("integ", "Integration: indefinite, reverse chain rule, definite integrals")
def g_integ(rng, lv):
    if lv == "easy":
        ns = rng.sample([2, 3, 4, 5], 2)
        f = sum(ri(rng, -4, 4, True) * (n + 1) * x**n for n in ns) + ri(rng, -9, 9, True)
        return mk(f"Find the integral of {fmt(f)} with respect to x.", "antider", integrate(f, x),
                  ["Integrate term by term: the integral of a x^n is a x^(n+1) / (n+1).", "A constant c integrates to c x.", "Add the constant of integration."])
    if lv == "medium":
        t = rng.choice(["pow", "exp", "sin", "cos", "inv", "sec2"]); a, b = ri(rng, 2, 5), ri(rng, -5, 5, True)
        if t == "inv":
            b = abs(b) + 1; f = ri(rng, 1, 4) / (a * x + b)
            return mk(f"Find the integral of {fmt(f)} with respect to x.", "antider", integrate(f, x),
                      ["The integral of 1/x is ln x, so the integral of 1/(ax + b) is (1/a) ln(ax + b).", "Keep the constant multiplier and divide by the coefficient of x.", "Add the constant of integration."])
        if t == "sec2":
            f = ri(rng, 1, 4) * sec(a * x + b)**2
            return mk(f"Find the integral of {fmt(f)} with respect to x.", "antider", f.args[0] * 0 + (f / sec(a * x + b)**2) * tan(a * x + b) / a,
                      ["Recall that the derivative of tan x is sec^2 x, so the integral of sec^2 x is tan x.", "The inside is linear, so divide by the coefficient of x.", "Add the constant of integration."])
        if t == "pow": f = (a * x + b)**rng.choice([2, 3, 4, 5])
        elif t == "exp": f = ri(rng, 1, 4) * exp(a * x + b)
        elif t == "sin": f = ri(rng, 1, 4) * sin(a * x + b)
        else: f = ri(rng, 1, 4) * cos(a * x + b)
        return mk(f"Find the integral of {fmt(f)} with respect to x.", "antider", integrate(f, x),
                  ["The inside of the bracket is linear, so reverse the chain rule.",
                   "Integrate as if the inside were just x, then divide by the coefficient of x.", "Add the constant of integration."])
    t = rng.choice(["poly", "pow", "exp", "trig"])
    if t == "poly":
        p, q = ri(rng, -2, 1), ri(rng, 2, 4); f = ri(rng, 1, 4) * x**2 + ri(rng, -6, 6, True) * x + ri(rng, -4, 4, True); lo, hi = p, q
    elif t == "pow":
        a, b = ri(rng, 2, 4), ri(rng, -3, 3, True); f = (a * x + b)**rng.choice([2, 3]); lo, hi = 0, ri(rng, 1, 3)
    elif t == "exp":
        kk = ri(rng, 2, 4); f = ri(rng, 1, 4) * exp(kk * x); lo, hi = 0, rng.choice([1, 2])
    else:
        kk = ri(rng, 1, 3); f = ri(rng, 1, 4) * rng.choice([sin(kk * x), cos(kk * x)]); lo, hi = 0, pi / (2 * kk)
    val = simplify(integrate(f, (x, lo, hi)))
    return mk(f"Evaluate the definite integral of {fmt(f)} from x = {fmt(lo)} to x = {fmt(hi)}. Give an exact answer.", "value", val,
              ["Find the indefinite integral first (no constant needed for a definite integral).", f"Substitute x = {fmt(hi)} and x = {fmt(lo)} into it.", "Subtract: upper value minus lower value."])

@topic("stat", "Stationary points and their nature")
def g_stat(rng, lv):
    if lv != "hard":
        while True:
            p, q = ri(rng, -3, 3), ri(rng, -3, 3)
            if p != q: break
        a = rng.choice([1, 2])
        if a == 1 and (p + q) % 2: q += 1
        if p == q: q += 2
        c = ri(rng, -6, 6)
        f = expand(a * x**3 - Rational(3 * a, 2) * (p + q) * x**2 + 3 * a * p * q * x + c)
        pts = [(p, f.subs(x, p)), (q, f.subs(x, q))]
        d2 = diff(f, x, 2)
        nat = ", ".join(f"({p_}, {fmt(f.subs(x, p_))}) is a {'minimum' if d2.subs(x, p_) > 0 else 'maximum'}" for p_, _ in sorted(pts))
        return mk(f"Find the coordinates of the stationary points of y = {fmt(f)}. Then decide whether each is a maximum or a minimum.",
                  "pairs", pts, ["Differentiate to get dy/dx.", "Set dy/dx = 0 and solve for x.", "Substitute each x value into y to get the coordinates.",
                                 "Find d2y/dx2 and test the sign at each point: positive means minimum, negative means maximum."], note=nat)
    kk = rng.choice([1, 2]); f = x**2 * exp(-kk * x); xs = [0, Rational(2, kk)]
    pts = [(v, simplify(f.subs(x, v))) for v in xs]
    return mk(f"Find the exact coordinates of the stationary points of y = {fmt(f)}.", "pairs", pts,
              ["Use the product rule on x^2 and e^(-kx) to get dy/dx.", "Factorise dy/dx. The factor e^(-kx) is never zero.",
               "Solve for x, then substitute back into y."])

@topic("quad", "Quadratics: turning points, discriminant, tangency")
def g_quad(rng, lv):
    if lv == "easy":
        a = rng.choice([1, 2, -1, -2, 3, -3]); p, q = ri(rng, -4, 4, True), ri(rng, -9, 9)
        f = expand(a * (x - p)**2 + q); word = "minimum" if a > 0 else "maximum"
        return mk(f"The curve y = {fmt(f)} has a maximum or minimum point. Find its coordinates.", "pairs", [(p, q)],
                  ["Complete the square: write the quadratic as a(x + h)^2 + k.", "The squared bracket is zero at the turning point.", "Read off the coordinates (-h, k)."],
                  note=f"It is a {word}.")
    if lv == "medium":
        if rng.random() < 0.5:
            m = ri(rng, 1, 6); d = rng.choice([dd for dd in range(1, m * m + 1) if (m * m) % dd == 0]); sgn = rng.choice([1, -1])
            c = sgn * d; kv = sgn * (m * m) // d; b = 2 * m * rng.choice([1, -1])
            if d == 0 or c == 0: c, kv = 1, m * m
            eq = pstr([("k", "x^2"), (b, "x"), (c, "")])
            return mk(f"The equation {eq} = 0 has equal roots. Find the value of k.", "set", [Rational(b * b, 4 * c)],
                      ["Equal roots means the discriminant b^2 - 4ac = 0.", "Identify a, b and c. Here a contains k.", "Solve the resulting equation for k."])
        c = rng.choice([4, 9, 16, 25, 36, 8, 12, 18, 5, 7])
        return mk(f"The equation {pstr([(1, 'x^2'), ('k', 'x'), (c, '')])} = 0 has equal roots. Find the possible values of k.", "set", [2 * sqrt(c), -2 * sqrt(c)],
                  ["Equal roots means the discriminant b^2 - 4ac = 0.", "Here a = 1, b = k and c is the constant.", "You get k^2 = something. Remember there are two square roots."])
    mm, b = ri(rng, -4, 4), 2 * ri(rng, -3, 3) + ri(rng, -4, 4) * 0
    c = ri(rng, -5, 5)
    t = ri(rng, -3, 3, True); b = mm + 2 * t; kv = c - t * t
    return mk(f"The line y = {pstr([(mm, 'x'), ('k', '')])} is a tangent to the curve y = {pstr([(1, 'x^2'), (b, 'x'), (c, '')])}. Find the value of k.", "set", [kv],
              ["Set the line equal to the curve to get a quadratic in x.", "A tangent touches the curve once, so the discriminant is 0.", "Write the discriminant in terms of k and solve."])

@topic("log", "Logarithms and exponentials")
def g_log(rng, lv):
    if lv == "easy":
        if rng.random() < 0.5:
            bs, n = rng.choice([2, 3, 5, 10]), ri(rng, -3, 4, True)
            return mk(f"Solve log base {bs} of x = {n}.", "value", Rational(bs)**n, ["Rewrite the logarithm as a power: log_b(x) = n means x = b^n."])
        a, b = rng.choice([2, 3, 5, 7]), rng.choice([11, 13, 17, 19, 20, 30, 50, 100])
        return mk(f"Solve {a}^x = {b}. Give your answer correct to 3 significant figures.", "num3sf", log(b) / log(a),
                  ["Take logarithms of both sides.", "Bring the power x down in front using the power law.", "Divide by log a and use a calculator."])
    if lv == "medium":
        b = rng.choice([2, 3, 5]); n = ri(rng, 1, 4)
        pairs = [(u, v) for v in range(1, b**n) for u in range(v + 1, b**n + 1) if u * v == b**n]
        u, v = rng.choice(pairs); d = u - v
        return mk(f"Solve log base {b} of x + log base {b} of (x - {d}) = {n}.", "set", [u],
                  ["Combine the two logarithms into one using the product law.", f"Rewrite as a power of {b} to remove the logarithm, giving a quadratic in x.",
                   "Solve the quadratic, then reject any value that makes a logarithm undefined."])
    b = rng.choice([2, 3, 4]); m, n = rng.sample(range(0, 4), 2)
    f = b**(2 * x) - (b**m + b**n) * b**x + b**(m + n)
    return mk(f"Solve {fmt(f)} = 0.", "set", [m, n],
              [f"Notice b^(2x) = (b^x)^2. Let y = {b}^x.", "Solve the quadratic in y.", f"Convert back: {b}^x = each value of y, then solve for x."])

@topic("binom", "Binomial expansion")
def g_binom(rng, lv):
    if lv == "easy":
        n, r = ri(rng, 4, 7), ri(rng, 2, 3); c = ri(rng, 1, 3)
        e = expand((1 + c * x)**n).coeff(x, r)
        return mk(f"Find the coefficient of x^{r} in the expansion of ({pstr([(1, ''), (c, 'x')])})^{n}.", "int", e,
                  ["The general term is nCr * a^(n-r) * b^r.", "Here the x part comes from b^r, so choose r to match the power of x you want.", "Multiply the binomial coefficient by the numbers raised to powers."])
    if lv == "medium":
        n, r = ri(rng, 5, 8), ri(rng, 2, 4); a, b = ri(rng, 1, 3), ri(rng, -3, 3, True)
        e = expand((a + b * x)**n).coeff(x, r)
        return mk(f"Find the coefficient of x^{r} in the expansion of ({pstr([(a, ''), (b, 'x')])})^{n}.", "int", e,
                  ["The general term is nCr * a^(n-r) * b^r where the second term supplies the x.", "Pick r so the power of x is right.", "Be careful with the sign of b when it is negative."])
    n = rng.choice([3, 6, 6, 9]); a, c = ri(rng, 1, 2), ri(rng, 1, 3) * rng.choice([1, -1])
    e = expand((a * x**2 + c / x)**n).coeff(x, 0)
    first = ("" if a == 1 else str(a)) + "x^2"; second = ("" if abs(c) == 1 else str(abs(c))) + "/x" if abs(c) != 1 else "1/x"
    second = f"{abs(c)}/x"
    return mk(f"Find the term independent of x in the expansion of ({first} {'-' if c < 0 else '+'} {second})^{n}.", "int", e,
              ["Write the general term. Collect the power of x from both brackets.", "The term independent of x has power 0. Solve for r.", "Substitute that r into the general term."])

@topic("simul", "Simultaneous equations (one linear, one non-linear)")
def g_simul(rng, lv):
    if lv == "easy":
        while True:
            p, q = ri(rng, -6, 6, True), ri(rng, -6, 6, True)
            if p != q: break
        return mk(f"Solve simultaneously: x + y = {p + q} and xy = {p * q}.", "pairs", [(p, q), (q, p)],
                  ["Make y the subject of the linear equation.", "Substitute into the other equation to get a quadratic in x.", "Solve it, then find y for each x."])
    if lv == "medium":
        while True:
            x1, x2 = ri(rng, -4, 4), ri(rng, -4, 4)
            if x1 != x2: break
        b, c = ri(rng, -4, 4), ri(rng, -6, 6)
        q = lambda t: t * t + b * t + c
        m = x1 + x2 + b; kk = q(x1) - m * x1
        return mk(f"Solve simultaneously: y = {pstr([(1, 'x^2'), (b, 'x'), (c, '')])} and {pstr([(-m, 'x'), (1, 'y')])} = {kk}.", "pairs", [(x1, q(x1)), (x2, q(x2))],
                  ["Make y the subject of the linear equation.", "Set the two expressions for y equal to get a quadratic in x.", "Solve it, then find y for each x using the linear equation."])
    pts = []
    for c in (5, 10, 13, 15, 17, 25):
        pts += [(c, (u, v)) for u in range(-c, c + 1) for v in range(-c, c + 1) if u * u + v * v == c * c]
    opts = []
    for c, p1 in pts:
        for c2, p2 in pts:
            if c == c2 and p1[0] < p2[0]:
                m = Rational(p2[1] - p1[1], p2[0] - p1[0]); kk = p1[1] - m * p1[0]
                if m.is_integer and kk.is_integer: opts.append((c, p1, p2, int(m), int(kk)))
    c, p1, p2, m, kk = rng.choice(opts)
    return mk(f"Solve simultaneously: x^2 + y^2 = {c * c} and y = {pstr([(m, 'x'), (kk, '')])}.", "pairs", [p1, p2],
              ["Substitute the expression for y into the circle equation.", "Expand and collect to get a quadratic in x.", "Solve it, then find y for each x using the line."])

@topic("factor", "Remainder theorem, factor theorem, cubics")
def g_factor(rng, lv):
    if lv == "easy":
        lc = rng.choice([1, 2, 3]); a, b, c = ri(rng, -5, 5), ri(rng, -6, 6), ri(rng, -9, 9, True); r = ri(rng, -3, 3, True)
        f = lc * x**3 + a * x**2 + b * x + c
        return mk(f"Find the remainder when {fmt(f)} is divided by ({fmt(x - r)}).", "int", f.subs(x, r),
                  ["Use the remainder theorem: the remainder when f(x) is divided by (x - r) is f(r).", f"Find the value that makes the bracket zero, then substitute it into f(x)."])
    if lv == "medium":
        while True:
            r, a, c = rng.choice([-2, -1, 1, 2, 3]), ri(rng, -4, 4), ri(rng, -8, 8, True)
            num_ = -(r**3 + a * r**2 + c)
            if num_ % r == 0: kv = num_ // r; break
        f = pstr([(1, "x^3"), (a, "x^2"), ("k", "x"), (c, "")])
        return mk(f"({fmt(x - r)}) is a factor of {f}. Find the value of k.", "int", kv,
                  ["Use the factor theorem: if (x - r) is a factor then f(r) = 0.", "Substitute x = r into f(x) and set it equal to 0.", "Solve the resulting equation for k."])
    while True:
        rts = rng.sample(range(-4, 5), 3)
        if rts[0] != 0: break
    lc = rng.choice([1, 1, 2]); f = expand(lc * (x - rts[0]) * (x - rts[1]) * (x - rts[2]))
    return mk(f"Show that ({fmt(x - rts[0])}) is a factor of {fmt(f)}. Hence solve {fmt(f)} = 0.", "set", rts,
              ["Substitute the value that makes the bracket zero into f(x) and show you get 0.", "Divide f(x) by the factor to get a quadratic.", "Factorise or solve the quadratic, then list all three roots."])

@topic("trig", "Trigonometric equations (degrees)")
def g_trig(rng, lv):
    vals = [("0", 0), ("1/2", 0.5), ("-1/2", -0.5), ("sqrt(3)/2", math.sqrt(3) / 2), ("-sqrt(3)/2", -math.sqrt(3) / 2),
            ("sqrt(2)/2", math.sqrt(2) / 2), ("-sqrt(2)/2", -math.sqrt(2) / 2), ("1", 1), ("-1", -1)]
    def sols(fn, lo, hi, tgt, scale=1):
        return [d for d in range(lo, hi + 1) if abs(fn(math.radians(scale * d)) - tgt) < 1e-9]
    if lv == "easy":
        name, fn = rng.choice([("sin", math.sin), ("cos", math.cos)]); s, v = rng.choice(vals)
        ans = sols(fn, 0, 360, v)
        return mk(f"Solve {name} x = {s} for 0 <= x <= 360 degrees.", "set", ans,
                  ["Find the acute angle using the inverse function on the positive value.", "Use the shape of the graph (or the CAST diagram) to find every angle in the range.", "Check each answer lies in 0 to 360."], tol=1e-6)
    if lv == "medium":
        if rng.random() < 0.35:
            cases = [("sec x = 2", [60, 300]), ("sec x = -2", [120, 240]), ("cosec x = 2", [30, 150]), ("cosec x = -2", [210, 330]),
                     ("cot x = 1", [45, 225]), ("cot x = -1", [135, 315]), ("cot x = sqrt(3)", [30, 210]), ("cot x = 1/sqrt(3)", [60, 240]),
                     ("sec x = -sqrt(2)", [135, 225]), ("cosec x = sqrt(2)", [45, 135])]
            txt, ans = rng.choice(cases)
            return mk(f"Solve {txt} for 0 <= x <= 360 degrees.", "set", ans,
                      ["Rewrite using the reciprocal: sec x = 1/cos x, cosec x = 1/sin x, cot x = 1/tan x.", "Turn the equation into one for cos x, sin x or tan x.",
                       "Solve it for 0 to 360 degrees using the graph or CAST diagram."])
        name, fn = rng.choice([("sin", math.sin), ("cos", math.cos)]); s, v = rng.choice(vals[:7])
        ans = sols(fn, 0, 180, v, 2)
        if not ans: return g_trig(rng, lv)
        return mk(f"Solve {name} 2x = {s} for 0 <= x <= 180 degrees.", "set", ans,
                  ["Let u = 2x. The range for u is 0 to 360 degrees.", "Solve for u using the graph or CAST diagram.", "Divide each u value by 2 to get x."])
    c1, c2 = rng.choice([(Rational(1, 2), -1), (Rational(-1, 2), 1), (Rational(1, 2), Rational(-1, 1))])
    c2 = rng.choice([-1, 1]) if c1 == Rational(1, 2) else 1
    fq = expand(2 * (x - c1) * (x - c2))
    name = rng.choice(["cos", "sin"]); fn = math.cos if name == "cos" else math.sin
    t = {"cos": cos, "sin": sin}[name]; polyx = fq.subs(x, Symbol("c"))
    text = fmt(polyx).replace("c", f"{name} x").replace(f"{name} x^2", f"{name}^2 x")
    ans = sorted(set(sols(fn, 0, 360, float(c1)) + sols(fn, 0, 360, float(c2))))
    return mk(f"Solve {text} = 0 for 0 <= x <= 360 degrees.", "set", ans,
              [f"This is a quadratic in {name} x. Let u = {name} x.", "Factorise or use the formula to find u.", f"Solve {name} x = each value of u, within the range. Reject any value outside -1 to 1."], tol=1e-6)

@topic("tangent", "Tangents and normals")
def g_tangent(rng, lv):
    if lv == "easy":
        while True:
            a, b, c, x0 = ri(rng, -3, 3, True), ri(rng, -5, 5), ri(rng, -6, 6), ri(rng, -3, 3)
            f = a * x**2 + b * x + c; m = diff(f, x).subs(x, x0)
            if m != 0: break
        line = m * (x - x0) + f.subs(x, x0)
        return mk(f"Find the equation of the tangent to the curve y = {fmt(f)} at the point where x = {x0}.", "expr", expand(line),
                  ["Differentiate to find the gradient function.", f"Substitute x = {x0} for the gradient and for the y coordinate.", "Use y - y1 = m(x - x1)."])
    if lv == "medium":
        while True:
            a, b, c, x0 = ri(rng, -2, 2, True), ri(rng, -4, 4), ri(rng, -5, 5), ri(rng, -2, 2)
            f = x**3 + a * x**2 + b * x + c; m = diff(f, x).subs(x, x0)
            if m != 0: break
        line = -(x - x0) / m + f.subs(x, x0)
        return mk(f"Find the equation of the normal to the curve y = {fmt(f)} at the point where x = {x0}.", "expr", line,
                  ["Differentiate to find the gradient of the tangent at the point.", "The normal is perpendicular to the tangent: its gradient is -1 divided by the tangent gradient.", f"Find the y coordinate at x = {x0}, then use y - y1 = m(x - x1)."])
    while True:
        a, b, n, x0 = ri(rng, 1, 3), ri(rng, -3, 3), rng.choice([2, 3, 4]), rng.choice([0, 1])
        f = rng.choice([(a * x + b)**n, x * exp(x), x**2 * log(x + 1) + x, exp(a * x) / (x + 2)]); m = diff(f, x).subs(x, x0)
        if m != 0 and f.subs(x, x0).is_finite: break
    typ = rng.choice(["tangent", "normal"])
    g = m if typ == "tangent" else -1 / m
    line = simplify(g * (x - x0) + f.subs(x, x0))
    return mk(f"Find the equation of the {typ} to the curve y = {fmt(f)} at the point where x = {x0}. Give exact values.", "expr", line,
              ["Differentiate (decide which rule you need) and substitute the x value for the gradient.", f"For a normal, take -1 divided by that gradient." if typ == "normal" else "That value is the tangent gradient.", "Find the y coordinate, then use y - y1 = m(x - x1)."])

@topic("func", "Functions: composite and inverse")
def g_func(rng, lv):
    a, b, c, d = ri(rng, 1, 4), ri(rng, -5, 5, True), ri(rng, -4, 4, True), ri(rng, -4, 4, True)
    if lv == "easy":
        a = rng.choice([-3, -2, 2, 3, 4]); f = a * x + b
        return mk(f"f(x) = {pstr([(a, 'x'), (b, '')])}. Find f^-1(x).", "expr", solve(Eq(y, f), x)[0].subs(y, x),
                  ["Write y = f(x).", "Rearrange to make x the subject.", "Swap x and y (or replace y by x) to write the inverse function."])
    if lv == "medium":
        f = a * x + b; g = x**2 + c; which = rng.choice(["fg", "gf"])
        res = f.subs(x, g) if which == "fg" else g.subs(x, f)
        return mk(f"f(x) = {pstr([(a, 'x'), (b, '')])} and g(x) = {pstr([(1, 'x^2'), (c, '')])}. Find {which}(x).", "expr", expand(res),
                  [f"{which}(x) means apply the right-hand function first, then the left-hand one.", "Replace every x in the outer function by the whole inner function.", "Expand and simplify."])
    while b == a * (abs(c) + 1): b = ri(rng, -5, 5, True)
    f = (a * x + b) / (x + abs(c) + 1)
    inv = solve(Eq(y, f), x)[0].subs(y, x)
    return mk(f"f(x) = {fmt(f)}. Find f^-1(x).", "expr", inv,
              ["Write y = f(x) and multiply both sides by the denominator.", "Collect all the x terms on one side and factorise out x.", "Divide to make x the subject, then swap x and y."])

@topic("circ", "Circular measure: arc length and sector area (radians)")
def g_circ(rng, lv):
    r = ri(rng, 3, 12); th = rng.choice([Rational(1, 2), Rational(3, 4), Rational(6, 5), Rational(3, 2), Rational(9, 5), 2, Rational(5, 2)])
    if lv == "easy":
        return mk(f"A sector of a circle has radius {r} cm and angle {fmt(th)} radians. Find the arc length.", "value", r * th,
                  ["Use arc length s = r * theta, with theta in radians.", "Substitute r and theta."])
    if lv == "medium":
        return mk(f"A sector of a circle has radius {r} cm and angle {fmt(th)} radians. Find its area.", "value", Rational(1, 2) * r * r * th,
                  ["Use area A = (1/2) r^2 theta, with theta in radians.", "Substitute r and theta."])
    L, A = r * th, Rational(1, 2) * r * r * th
    return mk(f"A sector of a circle has arc length {fmt(L)} cm and area {fmt(A)} cm^2. Find the radius and the angle of the sector in radians. Give your answer as (radius, angle).",
              "pairs", [(r, th)], ["Write both formulas: s = r theta and A = (1/2) r^2 theta.", "Divide the area equation by the arc length equation to find r.", "Use s = r theta to find theta."])

@topic("perm", "Permutations and combinations")
def g_perm(rng, lv):
    if lv == "easy":
        n, r = ri(rng, 6, 12), ri(rng, 2, 4)
        if rng.random() < 0.5:
            return mk(f"A club has {n} members. A president, a secretary and a treasurer are chosen, one person for each job. How many ways can this be done?" if r == 3 else
                      f"{n} runners take part in a race. In how many ways can the first {r} places be filled?", "int", factorial(n) / factorial(n - (3 if r == 3 else r)),
                      ["Order matters, so this is a permutation.", "Use nPr = n! / (n - r)!."])
        return mk(f"A team of {r} is chosen from {n} people. How many different teams are possible?", "int", binomial(n, r),
                  ["Order does not matter, so this is a combination.", "Use nCr = n! / (r!(n - r)!)."])
    if lv == "medium":
        n = ri(rng, 5, 8)
        if rng.random() < 0.5:
            return mk(f"{n} people stand in a row. Two particular people must stand next to each other. How many arrangements are there?", "int", 2 * factorial(n - 1),
                      ["Treat the two people as one block.", "Arrange the block with the other people, then multiply by the ways to order the pair inside the block."])
        return mk(f"{n} people stand in a row. Two particular people must not stand next to each other. How many arrangements are there?", "int", factorial(n) - 2 * factorial(n - 1),
                  ["Count all arrangements with no restriction.", "Count the arrangements where the two are together (treat them as a block).", "Subtract."])
    m, w, r = ri(rng, 4, 6), ri(rng, 3, 5), ri(rng, 4, 5); j = 2
    tot = sum(binomial(w, i) * binomial(m, r - i) for i in range(j, min(w, r) + 1))
    return mk(f"A committee of {r} is chosen from {m} men and {w} women. It must contain at least {j} women. In how many ways can this be done?", "int", tot,
              ["List the possible numbers of women: from the minimum up to the largest possible.", "For each case, multiply the ways to choose the women by the ways to choose the men.", "Add the cases."])

# ---------- more topics (v3) ----------
t_ = Symbol("t")
OPS = {"<": Lt, "<=": Le, ">": Gt, ">=": Ge}
FLIP = {"<": ">", "<=": ">=", ">": "<", ">=": "<="}

def ordn(n):
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"

def lin(a, b): return pstr([(a, "x"), (b, "")])

def set_text(st):
    parts = sorted(interval_parts(st), key=lambda i: float(i.start))
    out = []
    for iv in parts:
        lo, hi = iv.start, iv.end
        if lo == -oo: out.append(("x < " if iv.right_open else "x <= ") + fmt(hi))
        elif hi == oo: out.append(("x > " if iv.left_open else "x >= ") + fmt(lo))
        else: out.append(f"{fmt(lo)} {'<' if iv.left_open else '<='} x {'<' if iv.right_open else '<='} {fmt(hi)}")
    return " or ".join(out)

def only_intervals(st):
    if st.is_Interval: return True
    return st.is_Union and all(i.is_Interval for i in st.args)

def region_set(lhs, op, rhs, branches):
    """Solution set of lhs op rhs, found by splitting at every root of each branch = 0 and testing exactly."""
    pts = set()
    for e in branches:
        for r in solve(e, x):
            r = sympify(r)
            if r.is_real: pts.add(r)
    pts = sorted(pts, key=lambda r: float(r))
    f = OPS[op]
    tv = lambda v: bool(f(lhs.subs(x, v), rhs.subs(x, v)))
    edges = [-oo] + pts + [oo]; parts = []
    for lo, hi in zip(edges, edges[1:]):
        if lo == -oo and hi == oo: mid = 0
        elif lo == -oo: mid = hi - 1
        elif hi == oo: mid = lo + 1
        else: mid = (lo + hi) / 2
        if tv(mid): parts.append(Interval(lo, hi, True, True))
    for p_ in pts:
        if tv(p_): parts.append(FiniteSet(p_))
    return Union(*parts) if parts else EmptySet, pts

@topic("mod", "Modulus equations")
def g_mod(rng, lv):
    if lv == "easy":
        a, b, c = ri(rng, 1, 4), ri(rng, -8, 8), ri(rng, 1, 9)
        return mk(f"Solve |{lin(a, b)}| = {c}.", "set", sorted({Rational(c - b, a), Rational(-c - b, a)}),
                  ["The modulus means the inside can equal c or -c.", "Write the two equations: inside = c and inside = -c.", "Solve both. Both are valid because the right side is positive."])
    if lv == "medium":
        form = rng.choice(["lin", "lin", "mod"])
        for _ in range(4000):
            a, b, c, d = ri(rng, 1, 4), ri(rng, -8, 8), ri(rng, -4, 4, True), ri(rng, -8, 8)
            if abs(a) == abs(c): continue
            cands = {Rational(d - b, a - c), Rational(-(b + d), a + c)}
            if len(cands) < 2 or any(r.q != 1 for r in cands): continue
            if form == "mod": ans = sorted(cands); break
            ans = sorted(r for r in cands if Abs(a * r + b) == c * r + d)
            if ans: break
        if form == "mod":
            return mk(f"Solve |{lin(a, b)}| = |{lin(c, d)}|.", "set", ans,
                      ["Two moduli are equal when the insides are equal or are negatives of each other.", "Solve inside1 = inside2, then inside1 = -(inside2).", "Both answers are valid here."])
        return mk(f"Solve |{lin(a, b)}| = {lin(c, d)}.", "set", ans,
                  ["Write the two cases: inside = right side, and inside = -(right side).", "Solve both. This can create a false answer.", "Substitute each answer back into the original equation. The modulus can never equal a negative number."])
    for _ in range(6000):
        a, b, c, d = rng.choice([1, 1, 2]), ri(rng, -6, 6), ri(rng, -9, 9), ri(rng, 1, 10)
        roots, ok = set(), True
        for dd in (d, -d):
            disc = b * b - 4 * a * (c - dd)
            if disc < 0: continue
            sq = math.isqrt(disc)
            if sq * sq != disc: ok = False; break
            roots |= {Rational(-b + sq, 2 * a), Rational(-b - sq, 2 * a)}
        if ok and len(roots) >= 3: break
    return mk(f"Solve |{pstr([(a, 'x^2'), (b, 'x'), (c, '')])}| = {d}.", "set", sorted(roots),
              ["Write two equations: quadratic = d and quadratic = -d.", "Rearrange each to the form ax^2 + bx + c = 0 and solve.", "Check how many real roots each one gives, then list all the answers."])

@topic("ineq", "Quadratic and modulus inequalities")
def g_ineq(rng, lv):
    op = rng.choice(["<", "<=", ">", ">="])
    def quad_set(A, p, q, op):
        if A < 0: op = FLIP[op]
        closed = "=" in op
        if op.startswith(">"): return Union(Interval(-oo, p, True, not closed), Interval(q, oo, not closed, True))
        return Interval(p, q, not closed, not closed)
    steps_q = ["Move everything to one side and factorise to find the critical values (the roots).",
               "Sketch the quadratic. Mark the roots on the x axis.", "Read off where the graph is above or below the axis, as the inequality asks.",
               "Write the answer as inequalities. Use < or > for strict, <= or >= when equality is allowed."]
    if lv == "easy":
        while True:
            p, q = ri(rng, -6, 6), ri(rng, -6, 6)
            if p < q: break
        e = expand((x - p) * (x - q)); st = quad_set(1, p, q, op)
        return mk(f"Solve {fmt(e)} {op} 0.", "interval", st, steps_q, ans_text=set_text(st))
    if lv == "medium":
        while True:
            m1, m2, n1, n2 = ri(rng, 1, 3), ri(rng, 1, 3), ri(rng, -6, 6, True), ri(rng, -6, 6, True)
            p, q = Rational(n1, m1), Rational(n2, m2)
            if p != q: break
        sg = rng.choice([1, 1, -1]); e = expand(sg * (m1 * x - n1) * (m2 * x - n2)); lo, hi = sorted([p, q])
        st = quad_set(sg, lo, hi, op)
        if sg > 0 and rng.random() < 0.4:
            rhs = -e.coeff(x, 0)
            return mk(f"Solve {pstr([(e.coeff(x, 2), 'x^2'), (e.coeff(x, 1), 'x')])} {op} {rhs}.", "interval", st, steps_q, ans_text=set_text(st))
        return mk(f"Solve {fmt(e)} {op} 0.", "interval", st, steps_q, ans_text=set_text(st))
    for _ in range(3000):
        form = rng.choice(["a", "b", "c", "d"])
        a, b, c, d = ri(rng, 1, 4), ri(rng, -6, 6), ri(rng, -4, 4, True), ri(rng, -8, 8)
        if form == "a":
            cc = ri(rng, 1, 9); lhs, rhs = Abs(a * x + b), Integer(cc); br = [a * x + b - cc, a * x + b + cc]
            text = f"|{lin(a, b)}| {op} {cc}"
        elif form == "b":
            lhs, rhs = Abs(a * x + b), c * x + d; br = [a * x + b - rhs, a * x + b + rhs]
            if abs(a) == abs(c): continue
            text = f"|{lin(a, b)}| {op} {lin(c, d)}"
        elif form == "c":
            kk = ri(rng, 1, 3)
            if abs(kk * a) == abs(c): continue
            lhs, rhs = kk * Abs(a * x + b), Abs(c * x + d); br = [kk * (a * x + b) - (c * x + d), kk * (a * x + b) + (c * x + d)]
            text = f"{kk if kk > 1 else ''}|{lin(a, b)}| {op} |{lin(c, d)}|"
        else:
            e = x**2 + b * x + ri(rng, -9, 9); dd = ri(rng, 1, 10); lhs, rhs = Abs(e), Integer(dd); br = [e - dd, e + dd]
            text = f"|{fmt(e)}| {op} {dd}"
        try:
            st, pts = region_set(lhs, op, rhs, br)
        except Exception:
            continue
        if not pts or not all(r.is_rational for r in pts): continue
        if st is EmptySet or not only_intervals(st) or st == S.Reals: continue
        return mk(f"Solve {text}.", "interval", st,
                  ["Find the critical values: solve the equation, using both signs inside the modulus.",
                   "Check the critical values in the original, they can be false.", "Test a value in each region to see which regions satisfy the inequality.",
                   "Write the answer in terms of x."], ans_text=set_text(st))
    raise RuntimeError("ineq: no question found")

@topic("prog", "Arithmetic and geometric progressions")
def g_prog(rng, lv):
    if lv == "easy":
        t = rng.choice(["apn", "aps", "gpn"])
        if t == "apn":
            a, d, n = ri(rng, -10, 20), ri(rng, -6, 8, True), ri(rng, 10, 40)
            return mk(f"An arithmetic progression has first term {a} and common difference {d}. Find the {ordn(n)} term.", "int", a + (n - 1) * d,
                      ["Use the nth term: u_n = a + (n - 1)d.", "Substitute a, d and n."])
        if t == "aps":
            a, d, n = ri(rng, -10, 20), ri(rng, -6, 8, True), ri(rng, 8, 30)
            return mk(f"An arithmetic progression has first term {a} and common difference {d}. Find the sum of the first {n} terms.", "int", Rational(n, 2) * (2 * a + (n - 1) * d),
                      ["Use S_n = n/2 (2a + (n - 1)d).", "Substitute a, d and n."])
        a, r, n = ri(rng, 1, 6), rng.choice([2, 3, -2, Rational(1, 2), -3]), ri(rng, 5, 8)
        return mk(f"A geometric progression has first term {a} and common ratio {fmt(r)}. Find the {ordn(n)} term.", "value", a * r**(n - 1),
                  ["Use the nth term: u_n = a r^(n - 1).", "Substitute a, r and n. Be careful with a negative or fractional r."])
    if lv == "medium":
        if rng.random() < 0.5:
            a, d = ri(rng, -8, 15), ri(rng, -5, 7, True); m, n = rng.choice([(3, 8), (2, 7), (4, 10), (5, 9), (3, 12)])
            return mk(f"The {ordn(m)} term of an arithmetic progression is {a + (m - 1) * d} and the {ordn(n)} term is {a + (n - 1) * d}. Find the first term and the common difference. Give your answer as (a, d).",
                      "pairs", [(a, d)], ["Write each term using u_n = a + (n - 1)d. This gives two equations in a and d.", "Subtract one from the other to find d.", "Substitute d back to find a."], names=["a", "d"])
        a, r = ri(rng, 1, 5) * rng.choice([1, -1]), rng.choice([2, 3, -2, -3]); m, n = rng.choice([(2, 5), (1, 4), (3, 6), (2, 3)])
        return mk(f"The {ordn(m)} term of a geometric progression is {a * r**(m - 1)} and the {ordn(n)} term is {a * r**(n - 1)}. Find the first term and the common ratio. Give your answer as (a, r).",
                  "pairs", [(a, r)], ["Write each term using u_n = a r^(n - 1).", "Divide the larger-numbered term by the smaller to eliminate a. You get r to a power.", "Solve for r (check the power is odd, so there is one real answer), then find a."], names=["a", "r"])
    t = rng.choice(["sinf1", "sinf2", "two", "leastap", "leastgp"])
    if t == "sinf1":
        p, q = rng.choice([(1, 2), (2, 3), (1, 3), (3, 4), (-1, 2), (-1, 3), (-2, 3), (2, 5), (3, 5)]); a = (q - p) * ri(rng, 1, 4)
        S_ = Rational(a * q, q - p)
        return mk(f"A geometric progression has first term {a} and sum to infinity {fmt(S_)}. Find the common ratio.", "value", Rational(p, q),
                  ["Use S_infinity = a / (1 - r).", "Substitute a and S_infinity and solve for r.", "Check that |r| < 1, otherwise there is no sum to infinity."])
    if t == "sinf2":
        p, q = rng.choice([(1, 2), (2, 3), (1, 3), (3, 4), (-1, 2), (-1, 3), (-2, 3), (2, 5), (3, 5)]); a = (q - p) * ri(rng, 1, 4)
        return mk(f"A geometric progression has first term {a} and common ratio {p}/{q}. Find the sum to infinity.", "value", Rational(a * q, q - p),
                  ["The sum to infinity exists because |r| < 1.", "Use S_infinity = a / (1 - r)."])
    if t == "two":
        p, q = rng.choice([(1, 5), (2, 5), (1, 4), (1, 3), (1, 6), (2, 7)]); s0 = ri(rng, 1, 3)
        S_, u = q * q * s0, s0 * p * (q - p); r1, r2 = Rational(p, q), Rational(q - p, q)
        return mk(f"The second term of a geometric progression is {u} and its sum to infinity is {S_}. Find the two possible values of the first term and the common ratio. Give your answers as (a, r) pairs.",
                  "pairs", [(S_ * (1 - r1), r1), (S_ * (1 - r2), r2)],
                  ["Write the two facts: ar = second term, and a / (1 - r) = sum to infinity.", "Use the second to write a = S(1 - r), then substitute into the first to get a quadratic in r.", "Solve for r (both values have |r| < 1), then find a for each."])
    if t == "leastap":
        a, d = ri(rng, 2, 9), ri(rng, 2, 6); n0 = ri(rng, 12, 30); K = (n0 * (2 * a + (n0 - 1) * d)) // 2 - ri(rng, 0, 3)
        n = next(k for k in range(1, 500) if k * (2 * a + (k - 1) * d) // 2 > K)
        return mk(f"An arithmetic progression has first term {a} and common difference {d}. Find the least number of terms for the sum to exceed {K}.", "int", n,
                  ["Write S_n = n/2 (2a + (n - 1)d) and set up S_n > K.", "Rearrange to a quadratic inequality in n and find its critical value.", "n must be a whole number. Check n and the number below it."])
    a, r = ri(rng, 1, 4), rng.choice([2, 3]); n0 = ri(rng, 5, 9); K = a * (r**n0 - 1) // (r - 1) - ri(rng, 0, 2)
    n = next(k for k in range(1, 100) if a * (r**k - 1) // (r - 1) > K)
    return mk(f"A geometric progression has first term {a} and common ratio {r}. Find the least number of terms for the sum to exceed {K}.", "int", n,
              ["Write S_n = a(r^n - 1)/(r - 1) and set up S_n > K.", "Rearrange to get r^n on its own, then take logarithms.", "n must be a whole number, so round up and check."])

def vstr(a, b): return pstr([(a, "i"), (b, "j")])
TRIPLES = [(3, 4, 5), (4, 3, 5), (5, 12, 13), (12, 5, 13), (6, 8, 10), (8, 6, 10), (8, 15, 17), (15, 8, 17)]

@topic("vec", "Vectors in two dimensions")
def g_vec(rng, lv):
    if lv == "easy":
        t = rng.choice(["ab", "mag", "unit"])
        if t == "ab":
            p, q = (ri(rng, -6, 6), ri(rng, -6, 6)), (ri(rng, -6, 6), ri(rng, -6, 6))
            return mk(f"The position vectors of A and B, relative to an origin O, are {vstr(*p)} and {vstr(*q)}. Find the vector AB. Write it in the form ai + bj.", "vec", (q[0] - p[0], q[1] - p[1]),
                      ["AB = OB - OA (end point minus start point).", "Subtract the i components, then the j components."])
        if t == "mag":
            if rng.random() < 0.6:
                u, v, h = rng.choice(TRIPLES); u, v = u * rng.choice([1, -1]), v * rng.choice([1, -1]); ans = h
            else:
                u, v = ri(rng, -7, 7, True), ri(rng, -7, 7, True); ans = sqrt(u * u + v * v)
            return mk(f"Find the magnitude of the vector {vstr(u, v)}. Give an exact answer.", "value", ans,
                      ["The magnitude of ai + bj is sqrt(a^2 + b^2).", "Square each component, add, then take the square root."])
        u, v, h = rng.choice(TRIPLES); u, v = u * rng.choice([1, -1]), v * rng.choice([1, -1])
        return mk(f"Find the unit vector in the direction of {vstr(u, v)}.", "vec", (Rational(u, h), Rational(v, h)),
                  ["A unit vector has magnitude 1.", "Find the magnitude of the vector, then divide each component by it."])
    if lv == "medium":
        t = rng.choice(["par", "div", "like"])
        if t == "par":
            a, b = ri(rng, 1, 6) * rng.choice([1, -1]), ri(rng, 1, 6); lam = rng.choice([2, 3, -2, -3, 4])
            return mk(f"The vectors {vstr(a, b)} and {pstr([(lam * a, 'i'), ('k', 'j')])} are parallel. Find the value of k.", "set", [lam * b],
                      ["Parallel vectors are scalar multiples of each other.", "Compare the i components to find the scalar multiple.", "Use the same multiple on the j components."])
        if t == "div":
            m, n = rng.choice([(1, 2), (2, 3), (1, 3), (3, 2), (1, 4)]); A = (ri(rng, -5, 5), ri(rng, -5, 5))
            d = (ri(rng, -3, 3, True) * (m + n), ri(rng, -3, 3, True) * (m + n)); B = (A[0] + d[0], A[1] + d[1])
            P = (A[0] + Rational(m, m + n) * d[0], A[1] + Rational(m, m + n) * d[1])
            return mk(f"The position vectors of A and B are {vstr(*A)} and {vstr(*B)}. The point P lies on AB such that AP:PB = {m}:{n}. Find the position vector of P.", "vec", P,
                      ["Find AB = OB - OA.", f"AP is {m}/{m + n} of AB.", "OP = OA + AP."])
        while True:
            u, v = (ri(rng, -4, 4, True), ri(rng, -4, 4, True)), (ri(rng, -4, 4, True), ri(rng, -4, 4, True))
            if u[0] * v[1] - u[1] * v[0] != 0: break
        m_, n_ = ri(rng, -4, 4, True), ri(rng, -4, 4, True); tgt = (m_ * u[0] + n_ * v[0], m_ * u[1] + n_ * v[1])
        return mk(f"Given that m({vstr(*u)}) + n({vstr(*v)}) = {vstr(*tgt)}, find the values of m and n. Give your answer as (m, n).", "pairs", [(m_, n_)],
                  ["Expand the left side and collect the i terms and the j terms.", "Compare the i components, then the j components. This gives two equations in m and n.", "Solve them simultaneously."], names=["m", "n"])
    if rng.random() < 0.5:
        T_ = ri(rng, 2, 5); vp = (ri(rng, -4, 4), ri(rng, -4, 4)); vq = (ri(rng, -4, 4), ri(rng, -4, 4))
        if vp == vq: vq = (vq[0] + 1, vq[1])
        p0 = (ri(rng, -8, 8), ri(rng, -8, 8)); q0 = (p0[0] + (vp[0] - vq[0]) * T_, p0[1] + (vp[1] - vq[1]) * T_)
        X = (p0[0] + vp[0] * T_, p0[1] + vp[1] * T_)
        return mk(f"At time t = 0 seconds, particle P has position vector ({vstr(*p0)}) m and particle Q has position vector ({vstr(*q0)}) m. P moves with constant velocity ({vstr(*vp)}) m/s and Q with constant velocity ({vstr(*vq)}) m/s. The particles collide. Find the time of the collision and the position vector of the point of collision. Give your answer as (t, a, b), where the position vector is ai + bj.",
                  "pairs", [(T_, X[0], X[1])], ["Write the position vector of each particle at time t: initial position + t * velocity.", "At collision the two position vectors are equal. Equate the i components, then the j components.", "Solve for t (both equations should agree), then find the position."])
    T_ = ri(rng, 2, 6); u, v, h = rng.choice(TRIPLES); u, v = u * rng.choice([1, -1]), v * rng.choice([1, -1]); s_ = ri(rng, 1, 3)
    dv = (ri(rng, -4, 4, True), ri(rng, -4, 4)); rel = (s_ * u, s_ * v); d0 = (rel[0] - dv[0] * T_, rel[1] - dv[1] * T_)
    vp = (ri(rng, -3, 3), ri(rng, -3, 3)); vq = (vp[0] + dv[0], vp[1] + dv[1]); p0 = (ri(rng, -6, 6), ri(rng, -6, 6)); q0 = (p0[0] + d0[0], p0[1] + d0[1])
    return mk(f"At time t = 0 seconds, particle P has position vector ({vstr(*p0)}) m and particle Q has position vector ({vstr(*q0)}) m. P has constant velocity ({vstr(*vp)}) m/s and Q has constant velocity ({vstr(*vq)}) m/s. Find the distance between P and Q when t = {T_}.",
              "int", s_ * h, ["Find the position vector of P at time t = T: initial position + T * velocity. Do the same for Q.", "Subtract to get the vector PQ.", "The distance is the magnitude of PQ: square the components, add, take the square root."])

@topic("kin", "Kinematics: velocity, acceleration, distance")
def g_kin(rng, lv):
    def poly_t(c):  # c = {power: coef}
        return pstr([(c[k], "t" if k == 1 else ("" if k == 0 else f"t^{k}")) for k in sorted(c, reverse=True)])
    if lv == "easy":
        c3, c2, c1 = ri(rng, 1, 3), ri(rng, -9, 9), ri(rng, -12, 12)
        s_ = c3 * t_**3 + c2 * t_**2 + c1 * t_
        if rng.random() < 0.5:
            return mk(f"A particle moves in a straight line. Its displacement s metres from a fixed point after t seconds is s = {poly_t({3: c3, 2: c2, 1: c1})}. Find an expression for its velocity v in terms of t.", "expr", diff(s_, t_),
                      ["Velocity is the rate of change of displacement: v = ds/dt.", "Differentiate each term."], var="t")
        return mk(f"A particle moves in a straight line. Its displacement s metres from a fixed point after t seconds is s = {poly_t({3: c3, 2: c2, 1: c1})}. Find an expression for its acceleration a in terms of t.", "expr", diff(s_, t_, 2),
                  ["Velocity v = ds/dt, then acceleration a = dv/dt = d2s/dt2.", "Differentiate twice."], var="t")
    if lv == "medium":
        r1, r2 = sorted(rng.sample(range(1, 7), 2)); k = rng.choice([1, 2, 3]); v = expand(k * (t_ - r1) * (t_ - r2))
        if rng.random() < 0.5:
            return mk(f"A particle moves in a straight line. Its velocity v m/s at time t seconds (t >= 0) is v = {fmt(v)}. Find the times when the particle is at instantaneous rest.", "set", [r1, r2],
                      ["At rest means v = 0.", "Factorise or use the quadratic formula.", "Keep only t >= 0."])
        s0 = ri(rng, -5, 5)
        return mk(f"A particle moves in a straight line. Its velocity v m/s at time t seconds is v = {fmt(v)}. When t = 0 its displacement from the origin O is {s0} m. Find an expression for its displacement s in terms of t.", "expr", integrate(v, t_) + s0,
                  ["Displacement is the integral of velocity.", "Integrate term by term and add a constant c.", f"Use s = {s0} when t = 0 to find c."], var="t")
    while True:
        r1, r2 = sorted(rng.sample(range(1, 6), 2)); k = rng.choice([1, 2, 3, -1, -2]); T_ = ri(rng, r1 + 1, r2 + 3)
        if r2 < T_ or r1 < T_: break
    v = expand(k * (t_ - r1) * (t_ - r2)); br = [0] + [r for r in (r1, r2) if r < T_] + [T_]
    dist = sum(abs(integrate(v, (t_, lo, hi))) for lo, hi in zip(br, br[1:]))
    return mk(f"A particle moves in a straight line, starting from O. Its velocity v m/s at time t seconds is v = {fmt(v)}. Find the total distance the particle travels in the first {T_} seconds.", "value", dist,
              ["Find when v = 0, because the particle changes direction there.", "Integrate v over each interval where it keeps one sign.", "Distance is the sum of the sizes of those integrals (ignore minus signs)."])

@topic("rates", "Small changes, connected rates and optimisation")
def g_rates(rng, lv):
    if lv == "easy":
        from decimal import Decimal
        a, b, c = ri(rng, 1, 4), ri(rng, -5, 5), ri(rng, 1, 3); f = a * x**3 + b * x**2 + c * x; x0 = ri(rng, 1, 4)
        dx = rng.choice(["0.01", "0.02", "0.05", "0.1"])
        return mk(f"Given y = {fmt(f)}, use differentiation to find the approximate change in y when x increases from {x0} to {Decimal(x0) + Decimal(dx)}.", "value", diff(f, x).subs(x, x0) * Rational(dx),
                  ["Use delta y is approximately (dy/dx) * delta x.", "Differentiate and substitute the starting value of x.", "Multiply by the small change in x."])
    if lv == "medium":
        t = rng.choice(["circle", "sphere", "cube", "func", "rev"])
        if t == "circle":
            r0, rho = ri(rng, 2, 10), rng.choice([Rational(1, 2), 1, 2, 3, Rational(1, 4)])
            return mk(f"The radius of a circle is increasing at {fmt(rho)} cm/s. Find the rate of increase of the area when the radius is {r0} cm. Give your answer in terms of pi.", "value", 2 * pi * r0 * rho,
                      ["Write A = pi r^2 and find dA/dr.", "Use the chain rule: dA/dt = dA/dr * dr/dt.", "Substitute r and dr/dt."])
        if t == "sphere":
            r0, rho = ri(rng, 2, 8), rng.choice([Rational(1, 2), 1, 2, 3])
            return mk(f"The radius of a sphere is increasing at {fmt(rho)} cm/s. Find the rate of increase of the volume when the radius is {r0} cm. Give your answer in terms of pi.", "value", 4 * pi * r0**2 * rho,
                      ["The volume of a sphere is V = (4/3) pi r^3. Find dV/dr.", "Use dV/dt = dV/dr * dr/dt.", "Substitute r and dr/dt."])
        if t == "cube":
            x0, rho = ri(rng, 2, 9), ri(rng, 1, 4)
            return mk(f"The edge of a cube is increasing at {rho} cm/s. Find the rate of increase of its volume when the edge is {x0} cm.", "value", 3 * x0**2 * rho,
                      ["V = x^3, so find dV/dx.", "Use dV/dt = dV/dx * dx/dt.", "Substitute."])
        if t == "func":
            a, b = ri(rng, 1, 4), ri(rng, -5, 5, True); f = a * x**3 + b * x; x0 = ri(rng, 1, 3); c = ri(rng, 1, 4)
            return mk(f"A point moves along the curve y = {fmt(f)} so that x is increasing at {c} units per second. Find the rate of change of y when x = {x0}.", "value", diff(f, x).subs(x, x0) * c,
                      ["Find dy/dx.", "Use dy/dt = dy/dx * dx/dt.", "Substitute x and dx/dt."])
        r0, rho = ri(rng, 2, 8), ri(rng, 1, 4)
        return mk(f"The area of a circle is increasing at {2 * r0 * rho} pi cm^2/s. Find the rate of increase of the radius at the instant when the radius is {r0} cm.", "value", rho,
                  ["A = pi r^2 gives dA/dr = 2 pi r.", "dA/dt = dA/dr * dr/dt. Rearrange for dr/dt.", "Substitute dA/dt and r."])
    t = rng.choice(["box", "pen", "cuboid"])
    if t == "box":
        m = ri(rng, 1, 5); L = 6 * m
        return mk(f"A square sheet of metal has sides of {L} cm. A square of side x cm is cut from each corner and the sides are folded up to make an open box. Find the value of x that gives the greatest volume, and that volume. Give your answer as (x, V).", "pairs", [(m, 16 * m**3)],
                  ["Write the height as x and the base side as (L - 2x). Then V = x(L - 2x)^2.", "Differentiate and set dV/dx = 0. You get a quadratic in x.", "Reject the answer that gives a base of zero, then show it is a maximum with the second derivative."])
    if t == "pen":
        F = rng.choice([20, 24, 28, 32, 40, 48, 60])
        return mk(f"A farmer has {F} m of fencing to make three sides of a rectangular pen. The fourth side is a wall. The two sides perpendicular to the wall each have length x m. Find the value of x that gives the greatest area and that area. Give your answer as (x, A).", "pairs", [(Rational(F, 4), Rational(F * F, 8))],
                  ["Write the side parallel to the wall in terms of x, using the fencing total.", "Write the area A in terms of x only, then differentiate.", "Set dA/dx = 0, solve, and check it is a maximum."])
    n = ri(rng, 2, 7)
    return mk(f"A closed cuboid has a square base of side x cm and volume {n**3} cm^3. Find the value of x that gives the least total surface area, and that least area. Give your answer as (x, S).", "pairs", [(n, 6 * n * n)],
              ["Use the volume to write the height h in terms of x.", "Write the surface area S = 2x^2 + 4xh in terms of x only.", "Differentiate, set dS/dx = 0, and solve. Check that it is a minimum."])

@topic("area", "Areas under curves and between curves")
def g_area(rng, lv):
    if lv == "easy":
        a, b, c = ri(rng, 1, 4), ri(rng, 0, 5), ri(rng, 1, 6); f = a * x**2 + b * x + c; lo = ri(rng, 0, 2); hi = lo + ri(rng, 1, 3)
        return mk(f"Find the area of the region bounded by the curve y = {fmt(f)}, the x-axis and the lines x = {lo} and x = {hi}.", "value", integrate(f, (x, lo, hi)),
                  ["The curve is above the x-axis, so the area is the definite integral.", "Integrate, then substitute the upper limit and the lower limit.", "Subtract: upper minus lower."])
    if lv == "medium":
        if rng.random() < 0.5:
            while True:
                p, q = ri(rng, -5, 5), ri(rng, -5, 5)
                if p < q: break
            a = rng.choice([1, 1, 2, -1, -2]); f = expand(a * (x - p) * (x - q))
            return mk(f"The curve y = {fmt(f)} crosses the x-axis at two points. Find the area of the region enclosed by the curve and the x-axis.", "value", abs(Rational(a) * (q - p)**3 / 6),
                      ["Find where the curve crosses the x-axis: these are the limits.", "Integrate between the limits. The result is negative if the curve is below the axis.", "Area is positive, so take the size of the integral."])
        while True:
            x1, x2 = ri(rng, -4, 4), ri(rng, -4, 4)
            if x1 < x2: break
        a, b, c = rng.choice([1, 1, 2]), ri(rng, -4, 4), ri(rng, -5, 5); f = a * x**2 + b * x + c; g = expand(f - a * (x - x1) * (x - x2))
        return mk(f"The line y = {fmt(g)} meets the curve y = {fmt(f)} at two points, A and B. Find the area of the region enclosed by the line and the curve.", "value", Rational(a) * (x2 - x1)**3 / 6,
                  ["Set the line equal to the curve to find the x coordinates of A and B.", "Decide which is on top between A and B. Integrate (top - bottom).", "Evaluate the definite integral."])
    t = rng.choice(["cubic", "exp", "inv"])
    if t == "cubic":
        r = sorted(rng.sample(range(-4, 5), 3)); sg = rng.choice([1, -1]); f = expand(sg * (x - r[0]) * (x - r[1]) * (x - r[2]))
        ar = abs(integrate(f, (x, r[0], r[1]))) + abs(integrate(f, (x, r[1], r[2])))
        return mk(f"The curve y = {fmt(f)} crosses the x-axis at three points. Find the total area of the two regions enclosed by the curve and the x-axis.", "value", ar,
                  ["Find the three x-intercepts.", "Integrate between the first two, then between the last two. One answer is negative.", "Add the sizes of the two areas."])
    if t == "exp":
        a = ri(rng, 1, 4)
        return mk(f"Find the exact area of the region bounded by the curve y = e^({a}x), the x-axis, the y-axis and the line x = 1.", "value", (exp(a) - 1) / a,
                  ["The area is the definite integral from x = 0 to x = 1.", "The integral of e^(ax) is e^(ax)/a.", "Substitute the limits and leave e in your answer."])
    a, b, h = ri(rng, 1, 4), ri(rng, 1, 5), ri(rng, 1, 4)
    return mk(f"Find the exact area of the region bounded by the curve y = 1/({lin(a, b)}), the x-axis and the lines x = 0 and x = {h}.", "value", log(Rational(a * h + b, b)) / a,
              ["The integral of 1/(ax + b) is (1/a) ln(ax + b).", "Substitute x = h and x = 0.", "Use the law ln p - ln q = ln(p/q) if you want a single logarithm."])

@topic("lin", "Linear law")
def g_lin(rng, lv):
    if lv == "easy":
        t = rng.choice(["sq", "inv", "xy"]); a, b = ri(rng, -5, 6, True), ri(rng, -9, 9, True)
        X1, X2 = sorted(rng.sample(range(1, 7), 2))
        if t == "sq":
            return mk(f"The variables x and y are related by y = ax^2 + b, where a and b are constants. A graph of y against x^2 is a straight line passing through ({X1}, {a * X1 + b}) and ({X2}, {a * X2 + b}). Find the values of a and b. Give your answer as (a, b).", "pairs", [(a, b)],
                      ["Compare y = ax^2 + b with Y = mX + c, where Y = y and X = x^2.", "The gradient of the line is a: use the two points.", "Then use one point to find the intercept b."], names=["a", "b"])
        if t == "inv":
            return mk(f"The variables x and y are related by y = a/x + b, where a and b are constants. A graph of y against 1/x is a straight line passing through ({X1}, {a * X1 + b}) and ({X2}, {a * X2 + b}). Find the values of a and b. Give your answer as (a, b).", "pairs", [(a, b)],
                      ["Compare y = a(1/x) + b with Y = mX + c, where X = 1/x.", "The gradient is a, from the two points.", "Then find the intercept b."], names=["a", "b"])
        return mk(f"The variables x and y are related by y = ax + b/x, where a and b are constants. A graph of xy against x^2 is a straight line passing through ({X1}, {a * X1 + b}) and ({X2}, {a * X2 + b}). Find the values of a and b. Give your answer as (a, b).", "pairs", [(a, b)],
                "Multiply y = ax + b/x by x to get xy = a x^2 + b. Compare with Y = mX + c where X = x^2.|The gradient is a, from the two points.|Then find the intercept b.".split("|"), names=["a", "b"])
    if lv == "medium":
        c = ri(rng, 1, 3)
        if rng.random() < 0.5:
            n = rng.choice([2, 3, 4, -1, -2, Rational(3, 2), Rational(1, 2)])
            return mk(f"The variables x and y are related by y = Ax^n, where A and n are constants. A graph of lg y against lg x is a straight line with gradient {fmt(n)} that meets the vertical axis at (0, {c}). Find the values of A and n. Give your answer as (A, n).", "pairs", [(10**c, n)],
                      ["Take lg of both sides: lg y = n lg x + lg A.", "Compare with Y = mX + c: the gradient is n and the intercept is lg A.", "Solve lg A = intercept for A."], names=["A", "n"])
        m = rng.choice([1, 2, 3])
        return mk(f"The variables x and y are related by y = Ab^x, where A and b are constants. A graph of lg y against x is a straight line with gradient {m} that meets the vertical axis at (0, {c}). Find the values of A and b. Give your answer as (A, b).", "pairs", [(10**c, 10**m)],
                  ["Take lg of both sides: lg y = x lg b + lg A.", "Compare with Y = mX + c: the gradient is lg b and the intercept is lg A.", "Solve lg b = gradient and lg A = intercept."], names=["A", "b"])
    if rng.random() < 0.5:
        a, b = ri(rng, 1, 6), ri(rng, -6, 6, True); X1, X2 = sorted(rng.sample(range(1, 7), 2))
        return mk(f"The variables x and y are related by y = ax + bx^2, where a and b are constants. A graph of y/x against x is a straight line passing through ({X1}, {a + b * X1}) and ({X2}, {a + b * X2}). Find the values of a and b. Give your answer as (a, b).", "pairs", [(a, b)],
                  ["Divide y = ax + bx^2 by x to get y/x = bx + a.", "Compare with Y = mX + c. The gradient is b and the intercept is a.", "Use the two points to find the gradient, then the intercept."], names=["a", "b"])
    while True:
        mm, c = ri(rng, 1, 5), ri(rng, -9, 9)
        if mm * 8 + c > 0 and math.isqrt(int(mm * 8 + c))**2 == mm * 8 + c: break
    return mk(f"A graph of y^2 against x^3 is a straight line with gradient {mm} and intercept {c} on the vertical axis. Find the positive value of y when x = 2.", "int", math.isqrt(mm * 8 + c),
              ["The line has the form Y = mX + c with Y = y^2 and X = x^3.", f"So y^2 = {mm}x^3 + ({c}).", "Substitute x = 2, then take the positive square root."])

@topic("line", "Straight lines: equations, midpoints, perpendiculars")
def g_line(rng, lv):
    if lv == "easy":
        A, B = (ri(rng, -8, 8), ri(rng, -8, 8)), (ri(rng, -8, 8), ri(rng, -8, 8))
        if A == B: B = (B[0] + 2, B[1] + 1)
        if rng.random() < 0.5:
            return mk(f"A is the point ({A[0]}, {A[1]}) and B is the point ({B[0]}, {B[1]}). Find the midpoint of AB.", "pairs", [(Rational(A[0] + B[0], 2), Rational(A[1] + B[1], 2))],
                      ["The midpoint is the average of the x values and the average of the y values."])
        return mk(f"A is the point ({A[0]}, {A[1]}) and B is the point ({B[0]}, {B[1]}). Find the length of AB. Give an exact answer.", "value", sqrt((A[0] - B[0])**2 + (A[1] - B[1])**2),
                  ["Use length = sqrt((x2 - x1)^2 + (y2 - y1)^2).", "Leave the answer as a surd if it does not simplify."])
    if lv == "medium":
        if rng.random() < 0.5:
            while True:
                A, B = (ri(rng, -6, 6), ri(rng, -6, 6)), (ri(rng, -6, 6), ri(rng, -6, 6))
                if A[0] != B[0]: break
            m = Rational(B[1] - A[1], B[0] - A[0])
            return mk(f"Find the equation of the straight line through the points ({A[0]}, {A[1]}) and ({B[0]}, {B[1]}).", "expr", expand(m * (x - A[0]) + A[1]),
                      ["Find the gradient m = (y2 - y1)/(x2 - x1).", "Use y - y1 = m(x - x1) with one of the points.", "Rearrange to y = mx + c."])
        m = Rational(ri(rng, 1, 4) * rng.choice([1, -1]), ri(rng, 1, 3)); c = ri(rng, -6, 6); P = (ri(rng, -5, 5), ri(rng, -5, 5))
        mp = -1 / m
        return mk(f"Find the equation of the line through the point ({P[0]}, {P[1]}) that is perpendicular to the line y = {fmt(m*x + c)}.", "expr", expand(mp * (x - P[0]) + P[1]),
                  ["Read the gradient of the given line.", "The perpendicular gradient is -1 divided by it.", "Use y - y1 = m(x - x1) with the given point."])
    if rng.random() < 0.5:
        while True:
            A, B = (ri(rng, -6, 6), ri(rng, -6, 6)), (ri(rng, -6, 6), ri(rng, -6, 6))
            if A[0] != B[0] and A[1] != B[1] and (A[0] + B[0]) % 1 == 0: break
        m = Rational(B[1] - A[1], B[0] - A[0]); M = (Rational(A[0] + B[0], 2), Rational(A[1] + B[1], 2))
        return mk(f"A is the point ({A[0]}, {A[1]}) and B is the point ({B[0]}, {B[1]}). Find the equation of the perpendicular bisector of AB.", "expr", expand(-1 / m * (x - M[0]) + M[1]),
                  ["Find the midpoint of AB. The bisector passes through it.", "Find the gradient of AB. The bisector has gradient -1 divided by this.", "Use y - y1 = m(x - x1)."])
    m, c = ri(rng, 1, 4) * rng.choice([1, -1]), ri(rng, -6, 6); f0 = ri(rng, -4, 4); F = (f0, m * f0 + c); s_ = ri(rng, 1, 3) * rng.choice([1, -1])
    P = (F[0] - m * s_, F[1] + s_)
    return mk(f"The line l has equation y = {fmt(m*x + c)}. Find the coordinates of the foot of the perpendicular from the point P({P[0]}, {P[1]}) to l.", "pairs", [F],
              ["The perpendicular from P has gradient -1/m.", "Write its equation through P.", "Solve it simultaneously with l. The solution is the foot."])

def tterm(a, fn, b, c):
    out = ("-" if a < 0 else "") + ("" if abs(a) == 1 else str(abs(a)) + " ") + f"{fn}({'' if b == 1 else b}x)"
    return out + (f" + {c}" if c > 0 else f" - {-c}" if c < 0 else "")

def sq_text(v, a): return f"{v}^2" if a == 0 else f"({v} {'-' if a > 0 else '+'} {abs(a)})^2"

@topic("cgeo", "Coordinate geometry of the circle")
def g_cgeo(rng, lv):
    a, b = ri(rng, -6, 6), ri(rng, -6, 6)
    if lv == "easy":
        r = ri(rng, 2, 9)
        if rng.random() < 0.5:
            return mk(f"The equation of a circle is {sq_text('x', a)} + {sq_text('y', b)} = {r * r}. Write down the coordinates of the centre and the radius. Give your answer as (a, b, r), where (a, b) is the centre and r is the radius.", "pairs", [(a, b, r)],
                      ["The circle (x - a)^2 + (y - b)^2 = r^2 has centre (a, b) and radius r.", "Be careful with signs: (x + 3) means a = -3.", "The right side is r squared, so take the square root."])
        return mk(f"Find the equation of the circle with centre ({a}, {b}) and radius {r}.", "eqn", expand((x - a)**2 + (y - b)**2 - r * r),
                  ["Use (x - a)^2 + (y - b)^2 = r^2.", "Substitute the centre and the radius.", "You may leave it in bracket form or expand it."])
    if lv == "medium":
        t = rng.choice(["expand", "diam", "thru"])
        if t == "expand":
            r = ri(rng, 2, 9)
            return mk(f"A circle has equation {pstr([(1, 'x^2'), (1, 'y^2'), (-2 * a, 'x'), (-2 * b, 'y'), (a * a + b * b - r * r, '')])} = 0. Find the centre and the radius. Give your answer as (a, b, r), where (a, b) is the centre and r is the radius.", "pairs", [(a, b, r)],
                      ["Complete the square on the x terms and on the y terms.", "Move the constant to the right side.", "Read off the centre and r^2, then take the square root."])
        if t == "diam":
            u, v, h = rng.choice(TRIPLES); u, v = u * rng.choice([1, -1]), v * rng.choice([1, -1])
            return mk(f"A({a - u}, {b - v}) and B({a + u}, {b + v}) are the end points of a diameter of a circle. Find the equation of the circle.", "eqn", expand((x - a)**2 + (y - b)**2 - (u * u + v * v)),
                      ["The centre is the midpoint of AB.", "The radius is half the length of AB (or the distance from the centre to A).", "Use (x - a)^2 + (y - b)^2 = r^2."])
        u, v = ri(rng, -6, 6, True), ri(rng, -6, 6, True)
        return mk(f"A circle has centre ({a}, {b}) and passes through the point ({a + u}, {b + v}). Find the equation of the circle.", "eqn", expand((x - a)**2 + (y - b)**2 - (u * u + v * v)),
                  ["The radius is the distance from the centre to the point.", "Find r^2 = (difference in x)^2 + (difference in y)^2. You do not need r itself.", "Use (x - a)^2 + (y - b)^2 = r^2."])
    t = rng.choice(["tan", "inter", "k"])
    if t == "tan":
        u, v, h = rng.choice(TRIPLES); u, v = u * rng.choice([1, -1]), v * rng.choice([1, -1])
        P = (a + u, b + v); m = Rational(-u, v)
        return mk(f"The circle {sq_text('x', a)} + {sq_text('y', b)} = {h * h} passes through the point P({P[0]}, {P[1]}). Find the equation of the tangent to the circle at P.", "expr", expand(m * (x - P[0]) + P[1]),
                  ["Find the centre. The radius to P is perpendicular to the tangent.", "Find the gradient of the radius, then the gradient of the tangent (negative reciprocal).", "Use y - y1 = m(x - x1) with the point P."])
    if t == "inter":
        pts = []
        for h in (5, 10, 13, 15, 17, 25):
            pts += [(h, (u, v)) for u in range(-h, h + 1) for v in range(-h, h + 1) if u * u + v * v == h * h]
        opts = []
        for h, p1 in pts:
            for h2, p2 in pts:
                if h == h2 and p1[0] < p2[0]:
                    m = Rational(p2[1] - p1[1], p2[0] - p1[0]); kk = p1[1] - m * p1[0]
                    if m.is_integer and kk.is_integer: opts.append((h, p1, p2, int(m), int(kk)))
        h, p1, p2, m, kk = rng.choice(opts); kk2 = kk + b - m * a
        return mk(f"Find the coordinates of the points where the line y = {pstr([(m, 'x'), (kk2, '')])} meets the circle {sq_text('x', a)} + {sq_text('y', b)} = {h * h}.", "pairs", [(p1[0] + a, p1[1] + b), (p2[0] + a, p2[1] + b)],
                  ["Substitute the expression for y into the circle equation.", "Expand and collect to get a quadratic in x. Solve it.", "Find y for each x using the line."])
    p_, q_, h = rng.choice([(3, 4, 5), (4, 3, 5), (5, 12, 13), (12, 5, 13)]); r = ri(rng, 1, 5)
    base = -p_ * a + q_ * b
    return mk(f"The line {pstr([(q_, 'y')])} = {pstr([(p_, 'x'), ('k', '')])} is a tangent to the circle {sq_text('x', a)} + {sq_text('y', b)} = {r * r}. Find the two possible values of k.", "set", [base + r * h, base - r * h],
              ["A tangent is at distance r from the centre. Use the distance from a point to a line, or substitute y into the circle and set the discriminant to 0.", "If you use the discriminant, you get a quadratic in k.", "Solve it. There are two tangents with this gradient."])

@topic("tgraph", "Trigonometric graphs: amplitude, period, range")
def g_tgraph(rng, lv):
    fn = rng.choice(["sin", "cos"])
    if lv == "easy":
        a, b, c = ri(rng, 2, 5) * rng.choice([1, 1, -1]), ri(rng, 2, 4), ri(rng, -3, 3)
        return mk(f"State the amplitude and the period (in degrees) of y = {tterm(a, fn, b, c)}. Give your answer as (amplitude, period).", "pairs", [(abs(a), Rational(360, b))],
                  ["The amplitude of a sin(bx) + c is |a|.", "The period is 360 degrees divided by b."])
    if lv == "medium":
        a, b, c = ri(rng, 2, 6), ri(rng, 1, 3), ri(rng, -4, 4, True)
        return mk(f"Find the greatest and least values of y = {tterm(a, fn, b, c)}. Give your answer as (greatest, least).", "pairs", [(c + a, c - a)],
                  [f"{fn} of anything lies between -1 and 1.", "Multiply by the amplitude, then add the shift c."])
    a, b, c = ri(rng, 2, 6), ri(rng, 2, 5), ri(rng, -3, 4)
    return mk(f"The function y = a {fn}(bx) + c, where a > 0 and b > 0, has greatest value {c + a}, least value {c - a} and period {Rational(360, b)} degrees. Find a, b and c. Give your answer as (a, b, c).", "pairs", [(a, b, c)],
              ["a is half the difference between the greatest and least values.", "c is the average of the greatest and least values.", "The period is 360/b, so b = 360 divided by the period."])

# ---------- commands ----------
LEVELS = ("easy", "medium", "hard")

def build(qid):
    parts = qid.strip().split("-")
    if len(parts) != 3 or parts[0] not in GEN or parts[1] not in LEVELS: raise ValueError(f"Bad id: {qid}")
    t, lv, seed = parts[0], parts[1], int(parts[2])
    q = GEN[t][0](random.Random(f"{t}:{lv}:{seed}"), lv); q["id"] = qid; q["topic"] = t; q["level"] = lv
    return q

def show(q):
    print(f"ID: {q['id']}  ({GEN[q['topic']][1].split(':')[0]}, {q['level']})")
    print("QUESTION:", q["question"])

def main(a):
    if not a or a[0] in ("-h", "--help"): print(__doc__); return
    c = a[0]
    if c == "list":
        for k, (f, d) in GEN.items(): print(f"{k:8} {d}")
        print("levels: easy, medium, hard")
    elif c == "new":
        t = a[1]; lv = a[2] if len(a) > 2 else "medium"; seed = int(a[3]) if len(a) > 3 else random.randint(1000, 999999)
        show(build(f"{t}-{lv}-{seed}"))
    elif c == "followup":
        t = a[1]; base = int(a[2]) if len(a) > 2 else random.randint(1000, 999999)
        for i, lv in enumerate(LEVELS): show(build(f"{t}-{lv}-{base + i}")); print()
    elif c == "check":
        q = build(a[1]); v = verdict(q, a[2]); print(v)
        if v == "CORRECT" and q["kind"] == "value" and not q["answer"].is_rational: print("Exact form:", fmt(q["answer"]))
        try:                                            # a slip match never changes the verdict and never breaks a check
            import slips
            if v == "INCORRECT":
                d = slips.diagnose(q, a[2], sys.modules[__name__])
                if d: print(f"DIAGNOSIS ({d[0]}): {d[1]}")
            elif v == "CORRECT":
                n = slips.note(q, a[2])
                if n: print("NOTE:", n)
        except Exception: pass
    elif c == "hint":
        q = build(a[1]); n = int(a[2]) if len(a) > 2 else 1
        print(f"HINT {n}:", q["steps"][n - 1] if 1 <= n <= len(q["steps"]) else "No more hints. Reveal only after the student has tried the last step.")
    elif c == "reveal":
        q = build(a[1]); show(q)
        for i, s in enumerate(q["steps"], 1): print(f"Step {i}: {s}")
        print("ANSWER:", ans_str(q))
        if q.get("note"): print("NOTE:", q["note"])
    elif c == "dump":
        q = build(a[1]); print(json.dumps({"id": q["id"], "topic": q["topic"], "level": q["level"], "question": q["question"], "kind": q["kind"], "answer": ans_str(q)}))
    else: print(__doc__)

if __name__ == "__main__":
    import io, contextlib, datetime
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf): main(sys.argv[1:])
    except Exception as ex: buf.write(f"GEN FAILED: {ex}\n")
    out = buf.getvalue(); print(out, end="")
    try:  # one line per call, so you can see exactly what Edith ran
        logf = os.environ.get("EDITH_LOG") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "gen_calls.jsonl")
        os.makedirs(os.path.dirname(logf), exist_ok=True)
        with open(logf, "a", encoding="utf-8") as fh:
            rec = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "args": sys.argv[1:],
                   "result": out.strip().splitlines()[0] if out.strip() else ""}
            dm = re.search(r"^DIAGNOSIS \((\w+)\)", out, re.M)
            if dm: rec["diag"] = dm.group(1)
            fh.write(json.dumps(rec) + "\n")
    except Exception: pass
