"""Edith mistake diagnosis. When a student's answer is INCORRECT, find out which usual slip it matches.

Nothing here is guessed by a language model. For each question we compute the answers that the common mistakes would
produce (forget the chain rule, drop a minus sign, find only one of two solutions, use the tangent instead of the normal,
and so on) and compare the student's answer with each one, using the same checker that marks answers.
A match gives a fixed piece of advice. The advice never contains the correct answer.

  python tools/gen.py check <id> "<answer>"     prints INCORRECT, then a DIAGNOSIS line when a slip matches

Library use:
  diagnose(q, student_text)  ->  (code, advice) or None
  note(q, student_text)      ->  a short extra remark for a CORRECT answer, or None
"""
import re, math, collections
from sympy import (Symbol, Rational, Integer, sqrt, exp, log, sin, cos, tan, pi, diff, integrate, expand, simplify,
                   binomial, factorial, solve, sympify, Abs, Mul, preorder_traversal, degree, S, EmptySet)

Slip = collections.namedtuple("Slip", "code cand kw", defaults=({},))   # kw: extra question fields for matching, such as a looser tol

# ---------- advice (fixed text, never built from the answer) ----------
ADV = {
    # any topic
    "sign": "Your answer has the wrong sign throughout. Look back for a minus sign that was dropped, or a subtraction done the wrong way round.",
    "sign1": "The sign of the first value is wrong. The other values look right.",
    "sign2": "The sign of the second value is wrong. The other values look right.",
    "sign3": "The sign of the third value is wrong. The other values look right.",
    "double": "Your answer is exactly double the correct one. Look for a factor of one half that was left out, or something counted twice.",
    "half": "Your answer is exactly half the correct one. Look for a step where you should have multiplied, for example by two or by a coefficient.",
    "offset": "Your expression differs from the correct one only by a constant. Check the constant term: the intercept, the y value of the point, or a constant of integration that needs a given condition.",
    "factor": "Your expression has the right shape but it is a constant multiple of the correct one. Check the coefficients, and any factor that comes from inside a bracket.",
    "incomplete": "Everything you wrote is right, but you have not found all the solutions. Check the range or conditions in the question, whether there is a plus-or-minus, and whether a second case gives more answers.",
    "extra": "All the correct answers are in your list, but at least one value does not belong. Put each value back into the original question and check the conditions: logarithms need positive inputs, a modulus can never equal a negative number, and angles must lie in the range.",
    "swap": "Your values look right but they are in the wrong order. Check which value the question asks for first.",
    "onlyx": "Your x values are right. The question asks for coordinates, so put each x into the equation to find the matching y.",
    "onlyy": "Your y values are right. The question also needs the x values, so work back to find them.",
    "radians": "These look like radians. The question needs degrees, so check your calculator mode or convert.",
    # differentiation and integration
    "chain": "You differentiated the outer function but forgot the chain rule. Multiply by the derivative of the inside function.",
    "prod_sep": "You differentiated each factor and multiplied the results. The product rule is u v' + v u'. Both terms are needed.",
    "quot_order": "The quotient rule has a fixed order: the numerator is v u' - u v', with the derivative of the top first. Yours is the wrong way round.",
    "quot_sq": "The quotient rule divides by v squared, not by v.",
    "quot_sep": "You differentiated the top and the bottom separately. Use the quotient rule: (v u' - u v') / v^2.",
    "nodivide": "When the inside of the function is ax + b, reversing the chain rule means dividing by a, the coefficient of x. Check that step.",
    "differentiated": "You differentiated instead of integrating.",
    "upper_only": "You put in the upper limit but not the lower limit. Substitute both and subtract: upper minus lower.",
    "limits_add": "Subtract the value at the lower limit from the value at the upper limit. Do not add them.",
    # logs, binomial, factor theorem
    "logmul": "Rewrite the logarithm as a power: log base b of x = n means x = b^n. You multiplied instead.",
    "logswap": "log base b of x = n means x = b^n. The base is the number that gets raised to a power. You have the two numbers the wrong way round.",
    "logdivide": "Take logarithms of both sides first. Dividing the two numbers does not solve an equation with x in the power.",
    "lognobase": "After taking logs you have x log a = log b. Divide by log a, not by a.",
    "log_prod": "The product law says log a + log b = log(ab). Then rewrite as a power of the base: the product equals b^n, not n.",
    "log_add": "Two logarithms with the same base add to a logarithm of a product, not of a sum. Combine them with the product law first.",
    "logy": "You stopped at the quadratic. These values are what the power equals, not x. Solve the power equation for each one to find x.",
    "bin_b": "In (a + bx)^n the term in x^r contains b^r. You left out the power of the number that multiplies x.",
    "bin_a": "In the term in x^r the first number is raised to the power n - r. Check that you included it.",
    "bin_c": "You left out the binomial coefficient nCr.",
    "wrongroot": "Check which value of x makes the bracket zero. The bracket (x - r) is zero when x = r, so substitute r, not -r.",
    # functions, tangents, geometry
    "tn_swap": "You found the tangent when the question asks for the normal, or the other way round. The tangent has gradient dy/dx. The normal is perpendicular to it.",
    "gradflip": "The normal's gradient is the negative reciprocal of the tangent's: flip the fraction and change the sign. Doing only one of those is not enough.",
    "recip": "f^-1(x) is the inverse function, not 1/f(x). To find it, write y = f(x), rearrange for x, then swap x and y.",
    "invorder": "Undo the operations in reverse order when you rearrange for x: undo the addition or subtraction first, then the multiplication.",
    "invsign": "Check the sign when you move the constant across: if y = ax + b then ax = y - b.",
    "compswap": "You applied the functions in the wrong order. fg(x) means f(g(x)): put g(x) into f. gf(x) means g(f(x)).",
    "compmul": "fg(x) means f of g of x. It is not f(x) multiplied by g(x).",
    "circ_formula": "You used the formula for the other quantity. Arc length is r theta and sector area is half r squared theta.",
    "circ_square": "Check which part is squared. The area is (1/2) r^2 theta: the radius is squared, not the angle.",
    "line_grad": "The gradient is the change in y divided by the change in x. Yours looks inverted or has the wrong sign.",
    "perp_par": "A perpendicular line does not have the same gradient. Its gradient is -1 divided by the original.",
    "perp_grad": "The perpendicular gradient is the negative reciprocal: flip the fraction and change the sign. You did only one of those.",
    "bis_point": "A perpendicular bisector passes through the midpoint of AB, not through A or B.",
    "mid_sum": "The midpoint is the average of the two points: divide each sum by two.",
    "len_sqrt": "That is the length squared. Take the square root at the end.",
    "len_add": "Do not add the differences. Square each one, add, then take the square root.",
    "cg_sign": "In (x - a)^2 + (y - b)^2 = r^2 the centre is (a, b). A bracket such as (x + 3) means a is -3: the centre has the opposite sign to the one you see.",
    "cg_r2": "The number on the right of the equation is r squared. Take the square root for the radius, or square the radius when you write the equation.",
    "cg_half": "The centre is half of minus the coefficient of x (and of y). Remember to halve.",
    "cg_tan": "The tangent is perpendicular to the radius. Use the negative reciprocal of the radius gradient, not the gradient itself.",
    "tg_period": "The period of a sin(bx) + c is 360/b degrees. Check that you divided 360 by b.",
    "tg_shift": "You have not used the vertical shift. The whole graph moves up or down by c, so the greatest and the least value both change by c.",
    "tg_a": "a is the amplitude: half the difference between the greatest and least values. c is halfway between them.",
    "tg_b": "b is not the period. The period is 360/b.",
    "lin_lgA": "The intercept is lg A, so A is 10 raised to the intercept. You gave lg A.",
    "lin_lgb": "The gradient is lg b, so b is 10 raised to the gradient. You gave lg b.",
    # counting, progressions, vectors, mechanics, calculus applications
    "perm_order": "Order matters in this question, so use permutations: n!/(n - r)!, not combinations.",
    "comb_order": "Order does not matter for a team, so use combinations: n!/(r!(n - r)!). Permutations count each team several times.",
    "perm_pair": "When two people are treated as one block, the two can swap places inside it, so multiply the block count by 2. Check that you did that when counting the arrangements where they are together.",
    "perm_complement": "You found the number of arrangements where the two ARE together. Subtract that from the total number of arrangements.",
    "perm_atleast": "At least means that number or more. Work out each case and add them. You have counted only one case.",
    "perm_double": "Choosing the required people first and then the rest from everyone counts some committees more than once. Split into separate cases, exactly j women, exactly j + 1, and so on, then add.",
    "ineq_side": "You have the right critical values but the wrong region. Sketch the graph, or test a value from each region, to see where the expression is positive or negative.",
    "ineq_strict": "Check the end points. Use < and > when the end values are excluded, <= and >= when they are included, matching the sign in the question.",
    "prog_ap": "The nth term of an arithmetic progression is a + (n - 1)d. Check that you used n - 1, not n.",
    "prog_gp": "The nth term of a geometric progression is a r^(n - 1). Check that the power is n - 1.",
    "prog_sum": "The sum of the first n terms is n/2 (2a + (n - 1)d). Check the bracket.",
    "prog_round": "The last step is off by one. n must be a whole number, so test n and the whole numbers next to it in S_n to find the first one that exceeds the target.",
    "sinf_sign": "The sum to infinity is a/(1 - r). Check the sign in the denominator, especially when r is negative.",
    "vec_ab": "AB = OB - OA: the end point minus the start point. You subtracted the other way round.",
    "vec_sqrt": "The magnitude is sqrt(a^2 + b^2). You have not taken the square root.",
    "vec_add": "The magnitude is sqrt(a^2 + b^2). Square each component, add, then take the square root. Do not just add the components.",
    "vec_unit": "A unit vector has length one. Divide the vector by its magnitude.",
    "vec_ratio": "AP:PB = m:n means P is m/(m + n) of the way from A to B. Check the fraction you used.",
    "kin_order": "Check how many times you differentiated. Velocity is the first derivative of displacement. Acceleration is the second.",
    "kin_dir": "Displacement comes from integrating velocity. You differentiated it.",
    "kin_const": "You integrated, but the constant of integration is missing. Use the given value of s when t = 0 to find it.",
    "kin_dist": "You found the displacement. Distance counts every stretch as positive. Find when v = 0, split the integral there and add the sizes.",
    "rate_nodiff": "You used the formula for the quantity itself. A rate of change needs its derivative: find dV/dr (or dA/dr) first.",
    "rate_nochain": "You found the derivative but did not finish. Multiply by the rate at which the variable is changing, or by the small change in it, as the question needs.",
    "rate_exact": "That is the exact change. The question asks for the approximate change using differentiation: dy/dx times the small change in x.",
    "rate_div": "From dA/dt = dA/dr x dr/dt you get dr/dt by dividing dA/dt by dA/dr. You multiplied.",
    "area_net": "Part of the region is below the x-axis. Integrate each part separately and add the sizes, because a single signed integral lets the parts cancel.",
    "area_nodiv": "When you integrate e^(ax) or 1/(ax + b), divide by a. Check that step.",
}

# advice that reads better for one topic than the general text
TOPIC_ADV = {
    ("trig", "double"): "Your values are exactly double the correct ones. If the question has 2x or another multiple of x, divide by it at the end.",
    ("trig", "half"): "Your values are exactly half the correct ones. If you divided by a coefficient, check that you did it only once.",
    ("trig", "incomplete"): "Everything you wrote is right, but there are more solutions in the range. Use the CAST diagram or the graph to find the angle in each other quadrant, and check that each one lies in the range.",
    ("trig", "extra"): "All the correct angles are in your list, but at least one does not belong. Check that each angle lies in the range, and that sin or cos never equals a value outside -1 to 1.",
    ("mod", "extra"): "All the correct answers are in your list, but at least one is false. Put each answer back into the original equation. A modulus can never equal a negative number.",
    ("log", "extra"): "All the correct answers are in your list, but at least one is not allowed. A logarithm needs a positive input, so put each answer back into every logarithm in the question.",
    ("quad", "sign1"): "The sign of the first value is wrong. If you completed the square, remember that a(x + h)^2 + k has its turning point at x = -h.",
    ("tgraph", "sign1"): "An amplitude is a positive size. A negative sign in front of the sine or cosine only flips the graph.",
    ("diff", "sign"): "Your answer has the wrong sign throughout. Check the signs of the standard derivatives (cos x differentiates to -sin x), and the order of subtraction in the quotient rule.",
    ("integ", "sign"): "Your answer has the wrong sign throughout. Check the signs of the standard integrals (the integral of sin x is -cos x), and which limit you subtracted from which.",
    ("vec", "sign"): "Your answer has the wrong sign throughout. For vectors, subtract in the order end point minus start point.",
    ("area", "sign"): "Your answer has the wrong sign. An area is positive. Check which curve is on top, and whether the curve lies below the axis.",
}

def advice(code, topic):
    return TOPIC_ADV.get((topic, code)) or ADV[code]

# ---------- helpers ----------
def _lin_coeff(f, x):
    """The coefficient a of the first inner expression ax + b found inside f, or None."""
    for e in preorder_traversal(f):
        if e == x or not e.has(x) or not (e.is_Add or e.is_Mul): continue
        try:
            if e.is_polynomial(x) and degree(e, x) == 1:
                d = diff(e, x)
                if d.is_number: return d
        except Exception:
            continue
    return None

def _chain(g, x):
    """For g = outer(inner): the derivative of the outer function with the inside left alone, and the inside."""
    if g.func in (sin, cos, exp, log) and len(g.args) == 1:
        u = g.args[0]
        return {sin: cos(u), cos: -sin(u), exp: exp(u), log: 1 / u}[g.func], u
    if g.is_Pow and not g.exp.has(x):
        u = g.base
        return g.exp * u ** (g.exp - 1), u
    return None

def _line(x, m, p):
    return expand(m * (x - p[0]) + p[1])

def _nums(m, a, b):
    return [Integer(int(m.group(i))) for i in range(a, b + 1)]

# ---------- topic hooks: answers that this topic's usual slips produce ----------
HOOKS = {}
def hook(name):
    def deco(f): HOOKS[name] = f; return f
    return deco

@hook("diff")
def h_diff(G, q):
    m = re.fullmatch(r"Differentiate y = (.+) with respect to x\.", q["question"])
    if not m: return []
    x = G.x; f = G.to_expr(m.group(1)); out = []
    c, g = f.as_independent(x, as_Add=False)
    r = _chain(g, x)
    if r and simplify(diff(r[1], x) - 1) != 0:
        out.append(Slip("chain", c * r[0]))
    fs = Mul.make_args(g)
    if len(fs) == 2:
        neg = [h for h in fs if h.is_Pow and h.exp.is_negative]
        if len(neg) == 1:
            v = neg[0].base ** (-neg[0].exp); u = fs[0] if fs[1] is neg[0] else fs[1]
            du, dv = diff(u, x), diff(v, x)
            out += [Slip("quot_order", c * (u * dv - v * du) / v ** 2), Slip("quot_sq", c * (v * du - u * dv) / v)]
            if dv != 0: out.append(Slip("quot_sep", c * du / dv))
        elif not neg:
            out.append(Slip("prod_sep", c * diff(fs[0], x) * diff(fs[1], x)))
    return out

@hook("integ")
def h_integ(G, q):
    t = q["question"]; x = G.x; out = []
    m = re.fullmatch(r"Find the integral of (.+) with respect to x\.", t)
    if m:
        f = G.to_expr(m.group(1)); A = q["answer"]; a = _lin_coeff(f, x)
        if a is not None and a not in (0, 1): out += [Slip("nodivide", a * A), Slip("nodivide", a * a * A)]
        return out + [Slip("differentiated", diff(f, x))]
    m = re.fullmatch(r"Evaluate the definite integral of (.+) from x = (.+) to x = (.+)\. Give an exact answer\.", t)
    if m:
        f = G.to_expr(m.group(1)); hi = G.to_expr(m.group(3))
        out.append(Slip("upper_only", simplify(integrate(f, x).subs(x, hi))))
    return out

@hook("log")
def h_log(G, q):
    t = q["question"]; x = G.x; out = []
    m = re.fullmatch(r"Solve log base (\d+) of x = (-?\d+)\.", t)
    if m:
        b, n = _nums(m, 1, 2)
        return [Slip("logmul", b * n), Slip("logswap", n ** b)]
    m = re.fullmatch(r"Solve (\d+)\^x = (\d+)\. Give your answer correct to 3 significant figures\.", t)
    if m:
        a, b = _nums(m, 1, 2)
        return [Slip("logdivide", b / a), Slip("lognobase", log(b) / a)]
    m = re.fullmatch(r"Solve log base (\d+) of x \+ log base \d+ of \(x - (\d+)\) = (\d+)\.", t)
    if m:
        b, d, n = _nums(m, 1, 3)
        return [Slip("log_prod", [r for r in solve(x * (x - d) - n, x)]), Slip("log_add", [(b ** n + d) / 2])]
    m = re.fullmatch(r"Solve (.+) = 0\.", t)
    if m and q["kind"] == "set":
        bm = re.search(r"(\d+)\^\(?2?\*?x", m.group(1))
        if bm:
            b = Integer(int(bm.group(1))); return [Slip("logy", [b ** v for v in q["answer"]])]
    return out

@hook("binom")
def h_binom(G, q):
    m = re.fullmatch(r"Find the coefficient of x\^(\d+) in the expansion of \((.+)\)\^(\d+)\.", q["question"])
    if not m: return []
    x = G.x; r, n = int(m.group(1)), int(m.group(3)); base = G.to_expr(m.group(2))
    a, b = base.subs(x, 0), diff(base, x)
    return [Slip("bin_b", binomial(n, r) * a ** (n - r)), Slip("bin_a", binomial(n, r) * b ** r), Slip("bin_c", a ** (n - r) * b ** r)]

@hook("factor")
def h_factor(G, q):
    t = q["question"]; x = G.x
    m = re.fullmatch(r"Find the remainder when (.+) is divided by \(x ([+-]) (\d+)\)\.", t)
    if m:
        f = G.to_expr(m.group(1)); r0 = int(m.group(3)) * (1 if m.group(2) == "-" else -1)
        return [Slip("wrongroot", f.subs(x, -r0))]
    m = re.fullmatch(r"\(x ([+-]) (\d+)\) is a factor of (.+)\. Find the value of k\.", t)
    if m:
        f = G.to_expr(m.group(3)); r0 = int(m.group(2)) * (1 if m.group(1) == "-" else -1)
        sol = solve(f.subs(x, -r0), G.k_)
        return [Slip("wrongroot", sol[0])] if sol else []
    return []

@hook("trig")
def h_trig(G, q):
    return [Slip("radians", [v * pi / 180 for v in q["answer"]], {"tol": 5e-3})] if q["kind"] == "set" else []

@hook("tangent")
def h_tangent(G, q):
    m = re.fullmatch(r"Find the equation of the (tangent|normal) to the curve y = (.+) at the point where x = (-?\d+)\.(?: Give exact values\.)?", q["question"])
    if not m: return []
    x = G.x; f = G.to_expr(m.group(2)); x0 = int(m.group(3)); g = diff(f, x).subs(x, x0); p = (x0, f.subs(x, x0))
    if g == 0: return []
    if m.group(1) == "tangent": return [Slip("tn_swap", _line(x, -1 / g, p))]
    return [Slip("tn_swap", _line(x, g, p)), Slip("gradflip", _line(x, 1 / g, p)), Slip("gradflip", _line(x, -g, p))]

@hook("func")
def h_func(G, q):
    t = q["question"]; x = G.x
    m = re.fullmatch(r"f\(x\) = (.+)\. Find f\^-1\(x\)\.", t)
    if m:
        f = G.to_expr(m.group(1)); out = [Slip("recip", 1 / f)]
        if f.is_polynomial(x) and degree(f, x) == 1:
            a, b = diff(f, x), f.subs(x, 0); out += [Slip("invsign", (x + b) / a), Slip("invorder", x / a - b)]
        return out
    m = re.fullmatch(r"f\(x\) = (.+) and g\(x\) = (.+)\. Find (fg|gf)\(x\)\.", t)
    if m:
        f, g = G.to_expr(m.group(1)), G.to_expr(m.group(2))
        other = g.subs(x, f) if m.group(3) == "fg" else f.subs(x, g)
        return [Slip("compswap", expand(other)), Slip("compmul", expand(f * g))]
    return []

@hook("circ")
def h_circ(G, q):
    m = re.fullmatch(r"A sector of a circle has radius (\d+) cm and angle (.+) radians\. Find (the arc length|its area)\.", q["question"])
    if not m: return []
    r = Integer(int(m.group(1))); th = G.to_expr(m.group(2))
    if m.group(3) == "the arc length": return [Slip("circ_formula", r * r * th / 2)]
    return [Slip("circ_formula", r * th), Slip("circ_square", r * th * th / 2)]

@hook("perm")
def h_perm(G, q):
    t = q["question"]; out = []
    m = re.match(r"A club has (\d+) members\. A president", t)
    if m: n = int(m.group(1)); return [Slip("perm_order", binomial(n, 3))]
    m = re.match(r"(\d+) runners take part in a race\. In how many ways can the first (\d+) places be filled", t)
    if m: n, r = int(m.group(1)), int(m.group(2)); return [Slip("perm_order", binomial(n, r))]
    m = re.match(r"A team of (\d+) is chosen from (\d+) people", t)
    if m: r, n = int(m.group(1)), int(m.group(2)); return [Slip("comb_order", factorial(n) / factorial(n - r))]
    m = re.match(r"(\d+) people stand in a row\. Two particular people must not stand next to each other", t)
    if m: n = int(m.group(1)); return [Slip("perm_pair", factorial(n) - factorial(n - 1)), Slip("perm_complement", 2 * factorial(n - 1))]
    m = re.match(r"A committee of (\d+) is chosen from (\d+) men and (\d+) women\. It must contain at least (\d+) women", t)
    if m:
        r, mm, w, j = (int(m.group(i)) for i in range(1, 5))
        return [Slip("perm_atleast", binomial(w, j) * binomial(mm, r - j)), Slip("perm_double", binomial(w, j) * binomial(mm + w - j, r - j))]
    return out

@hook("ineq")
def h_ineq(G, q):
    s = q["answer"]; out = []
    try:
        comp = s.complement(S.Reals)
        pairs = [("ineq_side", comp), ("ineq_side", comp.interior), ("ineq_side", comp.closure),
                 ("ineq_strict", s.interior), ("ineq_strict", s.closure)]
    except Exception:
        return []
    for code, c in pairs:
        try:
            if c is EmptySet or c == s or c == S.Reals or not G.only_intervals(c): continue
        except Exception:
            continue
        out.append(Slip(code, c))
    return out

@hook("prog")
def h_prog(G, q):
    t = q["question"]; x = G.x
    m = re.fullmatch(r"An arithmetic progression has first term (-?\d+) and common difference (-?\d+)\. Find the (\d+)(?:st|nd|rd|th) term\.", t)
    if m: a, d, n = _nums(m, 1, 3); return [Slip("prog_ap", a + n * d)]
    m = re.fullmatch(r"An arithmetic progression has first term (-?\d+) and common difference (-?\d+)\. Find the sum of the first (\d+) terms\.", t)
    if m: a, d, n = _nums(m, 1, 3); return [Slip("prog_sum", n / 2 * (2 * a + n * d))]
    m = re.fullmatch(r"A geometric progression has first term (-?\d+) and common ratio (-?\d+)/(\d+)\. Find the sum to infinity\.", t)
    if m: a, p, qq = _nums(m, 1, 3); return [Slip("sinf_sign", a / (1 + p / qq))]
    m = re.fullmatch(r"A geometric progression has first term (-?\d+) and common ratio (.+)\. Find the (\d+)(?:st|nd|rd|th) term\.", t)
    if m: return [Slip("prog_gp", Integer(int(m.group(1))) * G.to_expr(m.group(2)) ** int(m.group(3)))]
    if "Find the least number of terms" in t and q["kind"] == "int":
        return [Slip("prog_round", q["answer"] - 1), Slip("prog_round", q["answer"] + 1)]
    return []

def _vec(G, text):
    if text.strip() == "0": return (Integer(0), Integer(0))      # the generator writes the zero vector as 0
    return tuple(sympify(c) for c in G.vec_parse(text))

@hook("vec")
def h_vec(G, q):
    t = q["question"]
    m = re.fullmatch(r"The position vectors of A and B, relative to an origin O, are (.+) and (.+)\. Find the vector AB\. Write it in the form ai \+ bj\.", t)
    if m: a = q["answer"]; return [Slip("vec_ab", (-a[0], -a[1]))]
    m = re.fullmatch(r"Find the magnitude of the vector (.+)\. Give an exact answer\.", t)
    if m:
        u, v = _vec(G, m.group(1)); return [Slip("vec_sqrt", u * u + v * v), Slip("vec_add", Abs(u) + Abs(v)), Slip("vec_add", u + v)]
    m = re.fullmatch(r"Find the unit vector in the direction of (.+)\.", t)
    if m: return [Slip("vec_unit", _vec(G, m.group(1)))]
    m = re.fullmatch(r"The position vectors of A and B are (.+?) and (.+?)\. The point P lies on AB such that AP:PB = (\d+):(\d+)\. Find the position vector of P\.", t)
    if m:
        A, B = _vec(G, m.group(1)), _vec(G, m.group(2)); mm, n = int(m.group(3)), int(m.group(4)); d = (B[0] - A[0], B[1] - A[1])
        return [Slip("vec_ratio", (A[0] + Rational(n, mm + n) * d[0], A[1] + Rational(n, mm + n) * d[1])),
                Slip("vec_ratio", (A[0] + Rational(mm, n) * d[0], A[1] + Rational(mm, n) * d[1]))]
    return []

@hook("kin")
def h_kin(G, q):
    t = q["question"]; T = G.t_
    m = re.fullmatch(r"A particle moves in a straight line\. Its displacement s metres from a fixed point after t seconds is s = (.+)\. Find an expression for its (velocity v|acceleration a) in terms of t\.", t)
    if m:
        s = G.to_expr(m.group(1))
        return [Slip("kin_order", diff(s, T, 2) if m.group(2).startswith("velocity") else diff(s, T))]
    m = re.fullmatch(r"A particle moves in a straight line\. Its velocity v m/s at time t seconds is v = (.+)\. When t = 0 its displacement from the origin O is (-?\d+) m\. Find an expression for its displacement s in terms of t\.", t)
    if m:
        v = G.to_expr(m.group(1)); return [Slip("kin_dir", diff(v, T)), Slip("kin_const", integrate(v, T))]
    m = re.fullmatch(r"A particle moves in a straight line, starting from O\. Its velocity v m/s at time t seconds is v = (.+)\. Find the total distance the particle travels in the first (\d+) seconds\.", t)
    if m:
        v = G.to_expr(m.group(1)); d = integrate(v, (T, 0, int(m.group(2)))); return [Slip("kin_dist", d), Slip("kin_dist", Abs(d))]
    return []

@hook("rates")
def h_rates(G, q):
    t = q["question"]; x = G.x
    m = re.fullmatch(r"Given y = (.+), use differentiation to find the approximate change in y when x increases from (\d+) to ([\d.]+)\.", t)
    if m:
        f = G.to_expr(m.group(1)); x0 = int(m.group(2)); x1 = Rational(m.group(3))
        return [Slip("rate_exact", f.subs(x, x1) - f.subs(x, x0)), Slip("rate_nochain", diff(f, x).subs(x, x0))]
    m = re.fullmatch(r"The radius of a circle is increasing at (.+) cm/s\. Find the rate of increase of the area when the radius is (\d+) cm\. Give your answer in terms of pi\.", t)
    if m: rho = G.to_expr(m.group(1)); r = Integer(int(m.group(2))); return [Slip("rate_nodiff", pi * r * r * rho), Slip("rate_nochain", 2 * pi * r)]
    m = re.fullmatch(r"The radius of a sphere is increasing at (.+) cm/s\. Find the rate of increase of the volume when the radius is (\d+) cm\. Give your answer in terms of pi\.", t)
    if m:
        rho = G.to_expr(m.group(1)); r = Integer(int(m.group(2)))
        return [Slip("rate_nodiff", Rational(4, 3) * pi * r ** 3 * rho), Slip("rate_nochain", 4 * pi * r * r)]
    m = re.fullmatch(r"The edge of a cube is increasing at (\d+) cm/s\. Find the rate of increase of its volume when the edge is (\d+) cm\.", t)
    if m: rho, e = _nums(m, 1, 2); return [Slip("rate_nodiff", e ** 3 * rho), Slip("rate_nochain", 3 * e * e)]
    m = re.fullmatch(r"A point moves along the curve y = (.+) so that x is increasing at (\d+) units per second\. Find the rate of change of y when x = (\d+)\.", t)
    if m:
        f = G.to_expr(m.group(1)); c, x0 = int(m.group(2)), int(m.group(3))
        return [Slip("rate_nodiff", f.subs(x, x0) * c), Slip("rate_nochain", diff(f, x).subs(x, x0))]
    m = re.fullmatch(r"The area of a circle is increasing at (\d+) pi cm\^2/s\. Find the rate of increase of the radius at the instant when the radius is (\d+) cm\.", t)
    if m: d, r = _nums(m, 1, 2); return [Slip("rate_div", d * pi * 2 * pi * r)]
    return []

@hook("area")
def h_area(G, q):
    t = q["question"]; x = G.x
    m = re.fullmatch(r"Find the area of the region bounded by the curve y = (.+), the x-axis and the lines x = (\d+) and x = (\d+)\.", t)
    if m:
        F = integrate(G.to_expr(m.group(1)), x); lo, hi = int(m.group(2)), int(m.group(3))
        return [Slip("upper_only", F.subs(x, hi)), Slip("limits_add", F.subs(x, hi) + F.subs(x, lo))]
    m = re.fullmatch(r"The curve y = (.+) crosses the x-axis at three points\. Find the total area of the two regions enclosed by the curve and the x-axis\.", t)
    if m:
        f = G.to_expr(m.group(1)); rts = sorted(solve(f, x)); net = integrate(f, (x, rts[0], rts[-1]))
        return [Slip("area_net", Abs(net)), Slip("area_net", net), Slip("area_net", Abs(integrate(f, (x, rts[0], rts[1]))))]
    m = re.fullmatch(r"Find the exact area of the region bounded by the curve y = e\^\((\d+)x\), the x-axis, the y-axis and the line x = 1\.", t)
    if m: a = Integer(int(m.group(1))); return [Slip("area_nodiv", exp(a) - 1)]
    m = re.fullmatch(r"Find the exact area of the region bounded by the curve y = 1/\((.+)\), the x-axis and the lines x = 0 and x = (\d+)\.", t)
    if m:
        lin = G.to_expr(m.group(1)); b = lin.subs(x, 0); h = int(m.group(2))
        return [Slip("area_nodiv", log(lin.subs(x, h) / b))]
    return []

@hook("lin")
def h_lin(G, q):
    names = q.get("names")
    if q["kind"] != "pairs" or names not in (["A", "n"], ["A", "b"]): return []
    A, second = q["answer"][0]; lgA = simplify(log(A, 10))
    if names == ["A", "n"]: return [Slip("lin_lgA", [(lgA, second)])]
    lgb = simplify(log(second, 10))
    return [Slip("lin_lgA", [(lgA, second)]), Slip("lin_lgb", [(A, lgb)]), Slip("lin_lgb", [(lgA, lgb)])]

@hook("line")
def h_line(G, q):
    t = q["question"]; x = G.x
    pt = r"\((-?\d+), (-?\d+)\)"
    m = re.fullmatch(r"A is the point " + pt + r" and B is the point " + pt + r"\. Find the midpoint of AB\.", t)
    if m: a0, a1, b0, b1 = _nums(m, 1, 4); return [Slip("mid_sum", [(a0 + b0, a1 + b1)])]
    m = re.fullmatch(r"A is the point " + pt + r" and B is the point " + pt + r"\. Find the length of AB\. Give an exact answer\.", t)
    if m:
        a0, a1, b0, b1 = _nums(m, 1, 4); dx, dy = b0 - a0, b1 - a1
        return [Slip("len_sqrt", dx * dx + dy * dy), Slip("len_add", Abs(dx) + Abs(dy))]
    m = re.fullmatch(r"Find the equation of the straight line through the points " + pt + " and " + pt + r"\.", t)
    if m:
        a0, a1, b0, b1 = _nums(m, 1, 4); mm = Rational(b1 - a1, b0 - a0); out = [Slip("line_grad", _line(x, -mm, (a0, a1)))]
        if mm != 0: out += [Slip("line_grad", _line(x, 1 / mm, (a0, a1))), Slip("line_grad", _line(x, -1 / mm, (a0, a1)))]
        return out
    m = re.fullmatch(r"Find the equation of the line through the point " + pt + r" that is perpendicular to the line y = (.+)\.", t)
    if m:
        p = (int(m.group(1)), int(m.group(2))); mm = diff(G.to_expr(m.group(3)), x)
        return [Slip("perp_par", _line(x, mm, p)), Slip("perp_grad", _line(x, -mm, p)), Slip("perp_grad", _line(x, 1 / mm, p))]
    m = re.fullmatch(r"A is the point " + pt + r" and B is the point " + pt + r"\. Find the equation of the perpendicular bisector of AB\.", t)
    if m:
        a0, a1, b0, b1 = _nums(m, 1, 4); mm = Rational(b1 - a1, b0 - a0); mid = ((a0 + b0) / 2, (a1 + b1) / 2)
        return [Slip("perp_par", _line(x, mm, mid)), Slip("perp_grad", _line(x, -mm, mid)),
                Slip("perp_grad", _line(x, 1 / mm, mid)), Slip("bis_point", _line(x, -1 / mm, (a0, a1))), Slip("bis_point", _line(x, -1 / mm, (b0, b1)))]
    return []

@hook("cgeo")
def h_cgeo(G, q):
    x, y = G.x, G.y; k = q["kind"]; a = q["answer"]; t = q["question"]
    if k == "eqn":
        a_, b_ = -a.coeff(x, 1) / 2, -a.coeff(y, 1) / 2; r2 = a_ ** 2 + b_ ** 2 - a.subs({x: 0, y: 0})
        if r2 <= 0: return []
        return [Slip("cg_sign", expand((x + a_) ** 2 + (y + b_) ** 2 - r2)), Slip("cg_r2", expand((x - a_) ** 2 + (y - b_) ** 2 - sqrt(r2)))]
    if k == "pairs" and len(a[0]) == 3:
        (c0, c1, r), = a
        out = [Slip("cg_sign", [(-c0, -c1, r)]), Slip("cg_r2", [(c0, c1, r * r)])]
        if t.startswith("A circle has equation"): out.append(Slip("cg_half", [(2 * c0, 2 * c1, r)]))
        return out
    m = re.fullmatch(r"The circle (.+) = (\d+) passes through the point P\((-?\d+), (-?\d+)\)\. Find the equation of the tangent to the circle at P\.", t)
    if m and k == "expr":
        mt = diff(a, x); p = (int(m.group(3)), int(m.group(4)))
        if mt == 0: return []
        return [Slip("cg_tan", _line(x, -1 / mt, p)), Slip("cg_tan", _line(x, 1 / mt, p)), Slip("cg_tan", _line(x, -mt, p))]
    return []

@hook("tgraph")
def h_tgraph(G, q):
    if q["kind"] != "pairs": return []
    (tup,) = q["answer"]; lv = q["level"]
    if lv == "easy":
        amp, per = tup; b = 360 / per; return [Slip("tg_period", [(amp, 360 * b)]), Slip("tg_period", [(amp, b)])]
    if lv == "medium":
        g, l = tup; a = (g - l) / 2; return [Slip("tg_shift", [(a, -a)])]
    a, b, c = tup
    return [Slip("tg_a", [(a + c, b, 0)]), Slip("tg_b", [(a, 360 / b, c)])]

# ---------- generic slips that need no topic knowledge ----------
def _neg(k, a):
    if k == "set": return [-v for v in a]
    if k == "pairs": return [tuple(-c for c in p) for p in a]
    if k == "vec": return (-a[0], -a[1])
    if k in ("int", "value", "num3sf", "expr", "antider"): return -a
    return None

def generic(q):
    k, a = q["kind"], q["answer"]; out = []
    n = _neg(k, a)
    if n is not None: out.append(Slip("sign", n))
    if k == "pairs":
        for i in range(len(a[0])): out.append(Slip(f"sign{i + 1}", [tuple(-c if j == i else c for j, c in enumerate(p)) for p in a]))
        if len(a[0]) == 2: out.append(Slip("swap", [(p[1], p[0]) for p in a]))
    if k == "vec": out.append(Slip("swap", (a[1], a[0])))
    if k in ("set", "int", "value", "num3sf", "expr", "antider"):
        scale = (lambda c: [c * v for v in a]) if k == "set" else (lambda c: c * a)
        out += [Slip("double", scale(2)), Slip("half", scale(Rational(1, 2)))]
    return out

def candidates(G, q):
    """Every (code, answer) pair worth testing for this question, most specific first."""
    out = []
    h = HOOKS.get(q["topic"])
    if h:
        try: out += h(G, q)
        except Exception: pass
    try: out += generic(q)
    except Exception: pass
    return out

def cand_q(q, sl):
    """The question with the slip's answer in place of the right one, ready for the checker."""
    return dict(q, answer=sl.cand, **sl.kw)

def cand_text(G, q, cand):
    """The candidate written the way a student would type it."""
    if q["kind"] == "interval": return G.set_text(cand)
    qq = dict(q, answer=cand); qq.pop("ans_text", None)
    return G.ans_str(qq)

# ---------- relations that are not a single wrong answer ----------
def _near(u, w, tol=1e-6): return abs(u - w) <= tol * max(1, abs(w))
def _uniq(L, tol):
    out = []
    for u in L:
        if not any(_near(u, w, tol) for w in out): out.append(u)
    return out

def relation(G, q, s):
    k = q["kind"]
    try:
        if k == "set":
            tol = q.get("tol", 1e-6); vs = _uniq(G.values(s), tol); ts = _uniq([G.num(e) for e in q["answer"]], tol)
            inn = lambda u, L: any(_near(u, w, tol) for w in L)
            allv, allt = all(inn(u, ts) for u in vs), all(inn(w, vs) for w in ts)
            if vs and allv and not allt: return "incomplete"
            if vs and allt and not allv: return "extra"
        elif k == "pairs":
            tv = [tuple(G.num(c) for c in p) for p in q["answer"]]
            got = G.tuples(G.clean(s)) or G.xy_pairs(s)
            if not got and q.get("names"): got = G.named_tuple(s, q["names"])
            if got:
                gv = [tuple(G.num(c) for c in p) for p in got]
                if any(len(g) != len(tv[0]) for g in gv): return None
                same = lambda g, t: all(_near(c1, c2) for c1, c2 in zip(g, t))
                allg, allt = all(any(same(g, t) for t in tv) for g in gv), all(any(same(g, t) for g in gv) for t in tv)
                if allg and not allt: return "incomplete"
                if allt and not allg: return "extra"
            elif len(tv[0]) == 2:
                vs = _uniq(G.values(s), 1e-6)
                for code, idx in (("onlyx", 0), ("onlyy", 1)):
                    cs = _uniq([t[idx] for t in tv], 1e-6)
                    if len(vs) == len(cs) and all(any(_near(u, w) for w in cs) for u in vs): return code
        elif k in ("expr", "antider"):
            v = Symbol(q["var"]) if q.get("var") else G.x
            f = G.student_func(s, v); a = q["answer"]
            if k == "antider": f, a = diff(f, v), diff(a, v)
            ds, rs = [], []
            for p in G.SAMPLES:
                try: fv, av = G.num(f.subs(v, p)), G.num(a.subs(v, p))
                except Exception: continue
                ds.append(fv - av); rs.append((fv, av))
            if len(ds) < 3: return None
            if k == "expr" and all(_near(d, ds[0], 1e-6) for d in ds) and abs(ds[0]) > 1e-9: return "offset"
            if all(abs(av) > 1e-9 for _, av in rs):
                rr = [fv / av for fv, av in rs]
                if all(_near(r, rr[0], 1e-6) for r in rr) and abs(rr[0] - 1) > 1e-9: return "factor"
    except Exception:
        return None
    return None

# ---------- public ----------
def _gen():
    import gen
    return gen

def diagnose(q, s, G=None):
    """(code, advice) for the first slip that the student's answer matches, or None. Call it only after INCORRECT.
    Order: this topic's own slips, then "some of the solutions" for sets and points, then the generic slips
    (sign, double, half, swapped), then "constant offset" and "constant multiple" for expressions."""
    G = G or _gen(); cs = candidates(G, q); gen_n = len(_safe_generic(q)); n_topic = len(cs) - gen_n
    early = q["kind"] in ("set", "pairs")
    def hit(sl):
        try: return G.check(cand_q(q, sl), s) is True
        except Exception: return False
    for sl in cs[:n_topic]:
        if hit(sl): return sl.code, advice(sl.code, q["topic"])
    if early:
        code = relation(G, q, s)
        if code: return code, advice(code, q["topic"])
    for sl in cs[n_topic:]:
        if hit(sl): return sl.code, advice(sl.code, q["topic"])
    if not early:
        code = relation(G, q, s)
        if code: return code, advice(code, q["topic"])
    return None

def _safe_generic(q):
    try: return generic(q)
    except Exception: return []

def note(q, s):
    """An extra remark for a CORRECT answer. At present: an indefinite integral without + c."""
    if q.get("kind") == "antider" and not re.search(r"\+\s*[a-zA-Z]\s*$", s.strip()):
        return "Add + c. In an exam, leaving out the constant of integration can cost a mark."
    return None
