"""Builds knowledge/topics/*.md. Every worked example is computed or asserted with sympy while the files are built,
so a wrong number stops the build. Original notes, written for the tutor. Run:  python build_knowledge.py"""
import os, math
from sympy import (symbols, Rational as R, sqrt, expand, factor, solve, diff, integrate, simplify, sin, cos, tan, exp, log, pi,
                   binomial, factorial, Eq, N, Abs, S, oo, nsimplify, sec, atan)

x, y, t, k, r_, u = symbols("x y t k r u")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge", "topics")
os.makedirs(OUT, exist_ok=True)

def fm(e):
    s = str(e).replace("**", "^").replace("exp(", "e^(").replace("log(", "ln(")
    import re
    return re.sub(r"(?<![\^\w.])(\d+)\*(?=[a-zA-Z(])", r"\1", s)

def ex(title, q, steps, ans):
    body = "\n".join(f"  {i}. {s}" for i, s in enumerate(steps, 1))
    return f"### {title}\nQuestion: {q}\n{body}\n  Answer: {ans}\n"

HEAD = "Original study notes for the tutor, written in plain text. Not Cambridge text. Check scope against syllabus.md.\n"
def page(fname, title, topic_no, gens, scope, methods, traps, examples, technique, teach):
    txt = f"# {title}\n{HEAD}Syllabus topic: {topic_no}. Practice generators: {gens}\n\n"
    txt += "## What the syllabus asks\n" + "\n".join(f"- {s}" for s in scope) + "\n\n"
    txt += "## Core methods\n" + "\n".join(f"- {s}" for s in methods) + "\n\n"
    txt += "## Common traps\n" + "\n".join(f"- {s}" for s in traps) + "\n\n"
    txt += "## Worked examples (each one checked with sympy when this file was built)\n" + "\n".join(examples) + "\n"
    txt += "## Exam technique\n" + "\n".join(f"- {s}" for s in technique) + "\n\n"
    txt += "## Teaching order\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(teach, 1)) + "\n"
    open(os.path.join(OUT, fname), "w", encoding="utf-8", newline="\n").write(txt)

TEACH_STD = ["Ask a diagnostic question or ask what the student already knows.", "Teach the idea with a worked example on a different question (use one above, change the numbers).",
             "Hint ladder on a generator question: nudge, method name, partial step, worked similar example.", "After a correct answer give three follow-ups (easy, medium, exam-level) from the generator."]

# ---------------- 01 functions ----------------
f_ = 2 * x + 3; g_ = x**2 - 1
fg = expand(f_.subs(x, g_)); gf = expand(g_.subs(x, f_)); assert fg == 2 * x**2 + 1 and gf == 4 * x**2 + 12 * x + 8
inv = solve(Eq(y, (3 * x + 1) / (x - 2)), x)[0]; assert simplify(inv - (2 * y + 1) / (y - 3)) == 0
assert expand((x - 2)**2 - 3 - (x**2 - 4 * x + 1)) == 0
page("01-functions.md", "Functions", "1", "func",
     ["Function notation, domain and range. One-one and many-one functions.", "Composite functions fg(x) and inverse functions f^-1(x).",
      "The graph of an inverse is the reflection of the graph in y = x.", "The graph of y = |f(x)| and how it relates to y = f(x), for linear, quadratic, cubic and trig f."],
     ["A function gives exactly one output for each input. Domain = allowed inputs, range = outputs that actually happen.",
      "fg(x) means f(g(x)): apply g first, then f. Replace every x in f by the whole of g.",
      "Inverse: write y = f(x), make x the subject, then swap the letters. The domain of f^-1 is the range of f. The range of f^-1 is the domain of f.",
      "Only one-one functions have an inverse. If f is many-one, restrict the domain (for example x >= 2) so that it becomes one-one.",
      "To find the range of a quadratic, complete the square and use the minimum or maximum, but only inside the stated domain.",
      "Sketch y = |f(x)|: sketch y = f(x), then reflect every part below the x-axis in the x-axis. The result never goes below the axis.",
      "f f^-1(x) = x and f^-1 f(x) = x. A point (a, b) on f means (b, a) is on f^-1."],
     ["f^-1(x) is NOT 1/f(x). The -1 marks the inverse function.", "fg and gf are usually different. Check the order of application.",
      "Forgetting to state the domain or range when the question asks for it.", "Giving the range of a quadratic over all real x when the domain is restricted.",
      "In |f(x)|, reflecting the wrong part, or forgetting that turning points below the axis become peaks above it."],
     [ex("Composite functions", "f(x) = 2x + 3 and g(x) = x^2 - 1. Find fg(x) and gf(x).",
         ["fg(x) = f(g(x)) = 2(x^2 - 1) + 3.", f"This simplifies to {fm(fg)}.", "gf(x) = g(f(x)) = (2x + 3)^2 - 1.", f"Expanding gives {fm(gf)}."], f"fg(x) = {fm(fg)}, gf(x) = {fm(gf)}"),
      ex("Inverse of a fraction", "f(x) = (3x + 1)/(x - 2), x not equal to 2. Find f^-1(x) and state its domain.",
         ["y = (3x + 1)/(x - 2), so y(x - 2) = 3x + 1.", "xy - 2y = 3x + 1, so xy - 3x = 2y + 1.", "x(y - 3) = 2y + 1, so x = (2y + 1)/(y - 3).",
          "Swap letters: f^-1(x) = (2x + 1)/(x - 3).", "f never takes the value 3 (y = 3 would need 0 = 7), so the range of f is y not equal to 3. That is the domain of f^-1."],
         "f^-1(x) = (2x + 1)/(x - 3), x not equal to 3"),
      ex("Range on a restricted domain", "f(x) = x^2 - 4x + 1 for x >= 2. Find the range.", ["Complete the square: x^2 - 4x + 1 = (x - 2)^2 - 3.", "The minimum is -3 at x = 2, which is in the domain.", "For x >= 2 the function only increases."], "f(x) >= -3")],
     ["Write the order of application before you start (g first, then f).", "For 'find the inverse', end with f^-1(x) = ... in terms of x.", "State domain and range using inequalities or set words, as the question asks."],
     ["Start with a mapping diagram idea: input, rule, output.", "Teach composite (concrete numbers first, then algebra).", "Teach inverse as undoing steps in reverse order, then the algebra method.", "Do domain and range with a sketch, and |f(x)| last."])

# ---------------- 02 quadratics ----------------
a = 2; assert expand(2 * (x - 3)**2 - 11 - (2 * x**2 - 12 * x + 7)) == 0
disc = expand((x**2 - 4 * x + 5 - k) .coeff(x, 1)**2 - 4 * 1 * (5 - k)); sk = solve(disc, k); assert sk == [1]
kk = solve(16 - 4 * k**2 < 0, k)
page("02-quadratics.md", "Quadratic functions", "2", "quad, ineq",
     ["Maximum and minimum values by completing the square, and using them for sketches and for range.", "The discriminant and the nature of the roots.",
      "Intersection of a line and a curve, and the tangent condition.", "Solving quadratic equations and quadratic inequalities."],
     ["Complete the square: a x^2 + b x + c = a(x + p)^2 + q. The turning point is (-p, q). It is a minimum if a > 0 and a maximum if a < 0.",
      "Discriminant D = b^2 - 4ac. D > 0: two different real roots. D = 0: equal roots (the curve touches the x-axis). D < 0: no real roots.",
      "Line and curve: put y from the line into the curve to get a quadratic in x. D > 0: they cross twice. D = 0: the line is a tangent. D < 0: they miss.",
      "Quadratic inequality: factorise, sketch, mark roots, shade the part above or below the axis. Write the answer with x.",
      "'Positive for all x' needs a > 0 and D < 0. 'Negative for all x' needs a < 0 and D < 0."],
     ["Sign slips when the coefficient of x^2 is not 1: take it out of the first two terms first.", "Writing D = 0 when the question says 'two distinct roots' (that needs D > 0).",
      "Giving a single bracket answer for an inequality such as x^2 > 9: the answer is x < -3 or x > 3.", "Dividing by a variable that could be negative or zero."],
     [ex("Completing the square", "Find the minimum value of 2x^2 - 12x + 7 and where it happens.", ["Take 2 out of the x terms: 2(x^2 - 6x) + 7.", "Complete the square: 2[(x - 3)^2 - 9] + 7 = 2(x - 3)^2 - 11.", "The square is never negative, so the minimum is -11 when x = 3."], "Minimum value -11 at x = 3"),
      ex("Tangent condition", "The line y = x + k is a tangent to y = x^2 - 3x + 5. Find k.", ["Set equal: x^2 - 3x + 5 = x + k, so x^2 - 4x + (5 - k) = 0.", "Tangent means D = 0: 16 - 4(5 - k) = 0.", "16 - 20 + 4k = 0, so k = 1."], "k = 1"),
      ex("Positive for all x", "Find the values of k for which kx^2 + 4x + k > 0 for all real x.", ["Need k > 0 (curve opens up) and D < 0.", "D = 16 - 4k^2 < 0 gives k^2 > 4, so k > 2 or k < -2.", "Combine with k > 0."], "k > 2")],
     ["Show the discriminant line clearly: it earns a mark even if the arithmetic goes wrong later.", "For 'show that' questions, state the conclusion in words about the roots."],
     TEACH_STD)

# ---------------- 03 polynomials ----------------
f3 = 2 * x**3 - 3 * x**2 - 11 * x + 6; assert f3.subs(x, 3) == 0 and factor(f3) == (x - 3) * (2 * x - 1) * (x + 2)
aa = symbols("a"); assert solve((x**3 + aa * x**2 - 2 * x + 4).subs(x, 2) - 10, aa) == [R(1, 2)]
p_, q_ = symbols("p q"); sol = solve([(x**3 + p_ * x**2 + q_ * x - 6).subs(x, -1), (x**3 + p_ * x**2 + q_ * x - 6).subs(x, 2) - 12], [p_, q_]); assert sol == {p_: 4, q_: -3}
page("03-polynomials.md", "Factors of polynomials", "3", "factor",
     ["Remainder theorem and factor theorem.", "Finding factors of cubics and solving cubic equations."],
     ["Remainder theorem: the remainder when f(x) is divided by (x - r) is f(r). For (ax - b) the remainder is f(b/a).", "Factor theorem: (x - r) is a factor exactly when f(r) = 0.",
      "To factorise a cubic: try r = +-1, +-2, +-3 (divisors of the constant term, over divisors of the leading coefficient) until f(r) = 0.",
      "Then divide (long division or inspection) to get a quadratic, and factorise that.", "Unknown constants: substitute the root or the remainder condition to make an equation, then solve. Two unknowns need two conditions."],
     ["Using f(-r) instead of f(r): (x + 2) goes with x = -2.", "Stopping after one root. A cubic can have three.", "Dropping the leading coefficient when dividing, such as the 2 in 2x^3.", "Division errors from skipped zero terms: write 0x^2 when a power is missing."],
     [ex("Factorise and solve a cubic", "Solve 2x^3 - 3x^2 - 11x + 6 = 0.", ["Try x = 3: 54 - 27 - 33 + 6 = 0, so (x - 3) is a factor.", "Divide: 2x^3 - 3x^2 - 11x + 6 = (x - 3)(2x^2 + 3x - 2).", "Factorise the quadratic: 2x^2 + 3x - 2 = (2x - 1)(x + 2).", "Roots: x = 3, 1/2, -2."], "x = 3, 1/2, -2"),
      ex("Remainder with an unknown", "x^3 + ax^2 - 2x + 4 leaves remainder 10 when divided by (x - 2). Find a.", ["Remainder = f(2) = 8 + 4a - 4 + 4 = 8 + 4a.", "8 + 4a = 10, so a = 1/2."], "a = 1/2"),
      ex("Two conditions", "(x + 1) is a factor of x^3 + px^2 + qx - 6 and the remainder is 12 on division by (x - 2). Find p and q.", ["f(-1) = 0: -1 + p - q - 6 = 0, so p - q = 7.", "f(2) = 12: 8 + 4p + 2q - 6 = 12, so 2p + q = 5.", "Add the equations: 3p = 12, p = 4. Then q = -3."], "p = 4, q = -3")],
     ["Write 'f(r) = 0' explicitly before concluding that something is a factor.", "In 'hence' questions use the factor you just found."], TEACH_STD)

# ---------------- 04 equations, inequalities, graphs ----------------
xr = symbols('xr', real=True); assert sorted(solve(Eq(Abs(2 * xr - 3), xr + 1), xr)) == [R(2, 3), 4]
r4 = set(solve(x**2 - 5 * x - 6, x)) | set(solve(x**2 - 5 * x + 6, x)); assert sorted(r4) == [-1, 2, 3, 6]
assert sorted(solve(x**4 - 10 * x**2 + 9, x)) == [-3, -1, 1, 3]
page("04-equations-inequalities-graphs.md", "Equations, inequalities and graphs (modulus, substitution, cubics)", "4", "mod, ineq",
     ["Solve |ax + b| = c, |ax + b| = cx + d, |ax + b| = |cx + d|, |ax^2 + bx + c| = d.", "Solve modulus inequalities such as k|ax + b| > c, |ax + b| <= cx + d, |ax^2 + bx + c| > d.",
      "Solve equations that become quadratics after a substitution.", "Sketch a cubic given as a product of three linear factors, and its modulus. Solve cubic inequalities with a graph."],
     ["|a| is the distance from zero. |a| = c (c > 0) means a = c or a = -c.", "|a| = b + (something): solve the two cases a = rhs and a = -rhs, then CHECK each answer. The right side must not be negative.",
      "|f| = |g|: either f = g or f = -g. Squaring both sides also works.", "|x - a| < b means a - b < x < a + b. |x - a| > b means x < a - b or x > a + b.",
      "For harder modulus inequalities: find the critical values (where the two sides are equal), then test a value in each region. A sketch of both sides helps.",
      "Substitution: x^4 - 10x^2 + 9 = 0 with u = x^2 gives u^2 - 10u + 9 = 0. Solve for u, then for x. Reject impossible values, such as x^2 = -4.",
      "Cubic inequality: mark the roots on the axis, sketch the curve using the sign of the leading coefficient, and read off where it is above or below the axis."],
     ["Not checking answers in |ax + b| = cx + d. One of the two cases is often false.", "Writing x > a or x < b as one chain: a combined chain such as 5 < x < 2 is impossible.",
      "Squaring an inequality without care. Squaring |A| < |B| is fine since both sides are non-negative.", "Forgetting the negative square root after substitution.", "In a sketch of |f(x)|, leaving parts below the axis."],
     [ex("Modulus with x on both sides", "Solve |2x - 3| = x + 1.", ["Case 1: 2x - 3 = x + 1, so x = 4.", "Case 2: 2x - 3 = -(x + 1), so 3x = 2 and x = 2/3.", "Check: x + 1 is positive for both, so both are valid. (At x = 4: |5| = 5. At x = 2/3: |-5/3| = 5/3.)"], "x = 4 or x = 2/3"),
      ex("Modulus of a quadratic", "Solve |x^2 - 5x| = 6.", ["x^2 - 5x = 6 gives (x - 6)(x + 1) = 0, so x = 6 or -1.", "x^2 - 5x = -6 gives (x - 2)(x - 3) = 0, so x = 2 or 3.", "All four satisfy the original equation."], "x = -1, 2, 3, 6"),
      ex("Modulus inequality", "Solve |x - 2| > 3.", ["Either x - 2 > 3 or x - 2 < -3.", "So x > 5 or x < -1."], "x < -1 or x > 5"),
      ex("Substitution", "Solve x^4 - 10x^2 + 9 = 0.", ["Let u = x^2: u^2 - 10u + 9 = 0, so (u - 1)(u - 9) = 0.", "u = 1 gives x = +-1. u = 9 gives x = +-3."], "x = -3, -1, 1, 3"),
      ex("Cubic inequality", "Solve (x + 2)(x - 1)(x - 3) < 0.", ["Roots at -2, 1, 3. The leading coefficient is positive, so the curve goes up on the far right.", "From the right: positive beyond 3, negative between 1 and 3, positive between -2 and 1, negative below -2.", "Negative regions: x < -2 and 1 < x < 3."], "x < -2 or 1 < x < 3")],
     ["Always show the case split in modulus work. Method marks are given for it.", "Finish with a statement about which values are valid."], TEACH_STD)

# ---------------- 05 simultaneous ----------------
assert sorted(solve([2 * x + y - 5, x**2 + x * y - 6], [x, y]), key=lambda s: s[0]) == [(2, 1), (3, -1)]
assert sorted(solve([x - y - 2, x**2 + y**2 - 10], [x, y]), key=lambda s: s[0]) == [(-1, -3), (3, 1)]
page("05-simultaneous-equations.md", "Simultaneous equations", "5", "simul",
     ["Solve two equations in two unknowns where one is linear and one is non-linear (including circles and curves)."],
     ["Rearrange the LINEAR equation to make one variable the subject (choose the one with no fraction).", "Substitute into the non-linear equation. Expand carefully, collect to the form ax^2 + bx + c = 0, and solve.",
      "Put each answer back into the LINEAR equation to find the other variable. This avoids false pairs.", "Present as pairs: (x1, y1) and (x2, y2).",
      "Discriminant of the quadratic tells how many intersection points: two, one (tangent) or none."],
     ["Pairing x values with the wrong y values.", "Substituting into the non-linear equation to find the second variable: it can give extra false pairs.", "Expanding (a - b)^2 incorrectly.", "Stopping after finding only the x values."],
     [ex("Line and a product", "Solve 2x + y = 5 and x^2 + xy = 6.", ["y = 5 - 2x.", "x^2 + x(5 - 2x) = 6 gives -x^2 + 5x - 6 = 0, so x^2 - 5x + 6 = 0.", "x = 2 or 3. Then y = 5 - 2x gives y = 1 and y = -1."], "(2, 1) and (3, -1)"),
      ex("Line and a circle", "Solve x - y = 2 and x^2 + y^2 = 10.", ["x = y + 2.", "(y + 2)^2 + y^2 = 10 gives 2y^2 + 4y - 6 = 0, so y^2 + 2y - 3 = 0.", "(y + 3)(y - 1) = 0, so y = -3 or 1. Then x = y + 2 gives x = -1 or 3."], "(-1, -3) and (3, 1)")],
     ["Write the substitution line clearly. Check at least one pair in both original equations."], TEACH_STD)

# ---------------- 06 logs and exponentials ----------------
v1 = N(log(20) / log(3), 4); assert abs(float(v1) - 2.727) < 1e-3
assert sorted(solve(x * (x - 2) - 8, x)) == [-2, 4]
assert sorted(solve(u**2 - 6 * u + 8, u)) == [2, 4]
assert sorted(solve(u + 3 / u - 4, u)) == [1, 3]
page("06-logs-and-exponentials.md", "Logarithmic and exponential functions", "6", "log",
     ["Graphs and asymptotes of y = e^x and y = ln x.", "Laws of logarithms and change of base.", "Solve a^x = b and equations involving logarithms."],
     ["Laws (any valid base): log xy = log x + log y. log (x/y) = log x - log y. log x^n = n log x. log_a a = 1. log_a 1 = 0.", "Change of base: log_a b = log_c b / log_c a. In particular log_a b = 1/(log_b a).",
      "ln x is log base e. e^x and ln x are inverses: e^(ln x) = x and ln(e^x) = x.", "Solve a^x = b: take logs of both sides, x log a = log b, x = log b / log a.",
      "Equations with logs: combine into one log with the laws, write as a power (log_a N = c means N = a^c), solve, then CHECK that every log argument is positive.",
      "Equations like 2^(2x) - 6(2^x) + 8 = 0: let u = 2^x, solve the quadratic, then solve 2^x = u. A value u <= 0 gives no solution.",
      "Graphs: y = e^x goes through (0, 1), is always positive, and has the x-axis as an asymptote. y = ln x goes through (1, 0), exists only for x > 0, and has the y-axis as an asymptote. They are mirror images in y = x."],
     ["Writing log(x + y) = log x + log y. There is no such law.", "Forgetting to reject solutions that put a negative number inside a log.", "Treating log x^2 as (log x)^2.", "Rounding too early. Keep full calculator values until the end."],
     [ex("Exponential equation", "Solve 3^x = 20, giving the answer to 3 significant figures.", ["Take logs: x ln 3 = ln 20.", f"x = ln 20 / ln 3 = {v1}.", "To 3 significant figures: 2.73."], "x = 2.73"),
      ex("Combine logs", "Solve log2 x + log2 (x - 2) = 3.", ["log2 [x(x - 2)] = 3, so x(x - 2) = 2^3 = 8.", "x^2 - 2x - 8 = 0, so (x - 4)(x + 2) = 0.", "x = 4 or x = -2. For x = -2, log2 (-2) does not exist, so reject it."], "x = 4"),
      ex("Quadratic in 2^x", "Solve 2^(2x) - 6(2^x) + 8 = 0.", ["Let u = 2^x: u^2 - 6u + 8 = 0, so u = 2 or 4.", "2^x = 2 gives x = 1. 2^x = 4 gives x = 2."], "x = 1 or x = 2"),
      ex("Change of base", "Solve log2 x + 3 log_x 2 = 4.", ["log_x 2 = 1/(log2 x). Let u = log2 x: u + 3/u = 4.", "u^2 - 4u + 3 = 0, so u = 1 or 3.", "x = 2^1 = 2 or x = 2^3 = 8."], "x = 2 or x = 8")],
     ["Show the law you use. State the rejection of an invalid root in words.", "Give logs answers exactly when asked, as ln 5 / ln 3, not a decimal."], TEACH_STD)

# ---------------- 07 straight lines and linear law ----------------
A_, B_ = (1, 2), (5, 10); m7 = R(10 - 2, 5 - 1); mid = (3, 6); bis = expand(-(x - 3) / m7 + 6); assert bis == -x / 2 + R(15, 2)
gA, gB = 0.699, 1.903; slope = (gB - gA) / 4; bcalc = 10**slope; Acalc = 10**gA
page("07-straight-lines-and-linear-law.md", "Straight-line graphs and the linear law", "7", "line, lin",
     ["Equation of a line, parallel and perpendicular lines, midpoint, length of a segment, perpendicular bisector.",
      "Linear law: convert y = A x^n and y = A b^x to straight-line form, find the constants from the gradient and intercept. Also read relations such as y^2 against x^3."],
     ["Gradient m = (y2 - y1)/(x2 - x1). Line: y - y1 = m(x - x1), or y = mx + c.", "Parallel lines: same gradient. Perpendicular: m1 m2 = -1 (negative reciprocal).",
      "Midpoint = ((x1 + x2)/2, (y1 + y2)/2). Length = sqrt((x2 - x1)^2 + (y2 - y1)^2).", "Perpendicular bisector of AB: passes through the midpoint of AB and has gradient equal to the negative reciprocal of the gradient of AB.",
      "Linear law method: write the relation in the form Y = mX + c where Y and X are the quantities plotted. The gradient is m and the vertical intercept is c.",
      "y = A x^n: take lg: lg y = n lg x + lg A. Plot lg y against lg x. Gradient n, intercept lg A.", "y = A b^x: lg y = x lg b + lg A. Plot lg y against x. Gradient lg b, intercept lg A.",
      "y = a x^2 + b: plot y against x^2. y = ax + b/x: multiply by x to get xy = a x^2 + b, plot xy against x^2.", "To find A from lg A = c, calculate A = 10^c (for lg) or e^c (for ln)."],
     ["Using the same gradient for a perpendicular line.", "Mixing up which axis is which: always say 'Y = ... against X = ...' first.", "Reading A as the intercept: the intercept is lg A, not A.", "Using the points on the graph in the wrong order for the gradient."],
     [ex("Perpendicular bisector", "A is (1, 2) and B is (5, 10). Find the equation of the perpendicular bisector of AB.", ["Gradient of AB = (10 - 2)/(5 - 1) = 2.", "Midpoint = (3, 6).", "Perpendicular gradient = -1/2.", "y - 6 = -1/2 (x - 3), so y = -x/2 + 15/2."], "y = -x/2 + 15/2, which is x + 2y = 15"),
      ex("Linear law with y = A b^x", f"A graph of lg y against x is a straight line through (0, 0.699) and (4, 1.903). Find A and b in y = A b^x.",
         ["lg y = x lg b + lg A, so the gradient is lg b and the intercept is lg A.", f"Gradient = (1.903 - 0.699)/4 = {slope:.3f}, so b = 10^{slope:.3f} = {bcalc:.2f}.", f"Intercept 0.699 = lg A, so A = 10^0.699 = {Acalc:.2f}."], "A = 5.00 and b = 2.00 (to 3 s.f.), so y = 5(2^x)")],
     ["Name the plotted variables first. Then show the line equation, then the gradient and intercept. Every step carries a mark.", "If the question gives a table, check the points lie on a straight line before you start."], TEACH_STD)

# ---------------- 08 circle geometry ----------------
assert expand((x - 3)**2 + (y + 2)**2 - 25) == x**2 + y**2 - 6 * x + 4 * y - 12
tan_line = expand(R(-4, 3) * (x - 7) + 1); assert 3 * tan_line - (-4 * x + 31) == 0
sx = solve(x**2 + (x + 1)**2 - 25, x); assert sorted(sx) == [-4, 3]
page("08-circle-geometry.md", "Coordinate geometry of the circle", "8", "cgeo, simul",
     ["Equation of a circle with centre (a, b) and radius r (given in the formula list).", "Intersection of a line and a circle, and of two circles.", "Tangents and chords. Common chords."],
     ["(x - a)^2 + (y - b)^2 = r^2 has centre (a, b) and radius r.", "Expanded form: x^2 + y^2 + 2gx + 2fy + c = 0. Centre (-g, -f), r^2 = g^2 + f^2 - c. Or complete the square on x and on y.",
      "Radius to a point of tangency is perpendicular to the tangent: tangent gradient = -1 / (radius gradient).", "Line and circle: substitute the line into the circle to get a quadratic in x. D > 0: two points. D = 0: tangent. D < 0: no intersection.",
      "Chord: the perpendicular from the centre to a chord bisects the chord. Use right triangles with the radius as the hypotenuse.", "Common chord of two circles: subtract one equation from the other. The result is the line through the two intersection points. Then intersect that line with either circle.",
      "Circle through three points or with a given diameter: the centre is the midpoint of a diameter. Find the radius as the distance from the centre to one of the points."],
     ["Sign errors when reading the centre: (x + 2)^2 means a = -2.", "Forgetting to take the square root: the right side is r^2.", "Using the wrong gradient for the tangent (must use the negative reciprocal of the radius gradient).", "Leaving out the check that a point lies on the circle before finding its tangent."],
     [ex("Centre and radius", "Find the centre and radius of x^2 + y^2 - 6x + 4y - 12 = 0.", ["Group: (x^2 - 6x) + (y^2 + 4y) = 12.", "Complete the squares: (x - 3)^2 - 9 + (y + 2)^2 - 4 = 12.", "(x - 3)^2 + (y + 2)^2 = 25."], "Centre (3, -2), radius 5"),
      ex("Tangent at a point", "Find the tangent to that circle at P(7, 1).", ["Check P: (7 - 3)^2 + (1 + 2)^2 = 16 + 9 = 25. It is on the circle.", "Gradient of the radius from (3, -2) to (7, 1) is 3/4.", "Tangent gradient = -4/3.", "y - 1 = -4/3 (x - 7), so 3y + 4x = 31."], "4x + 3y = 31"),
      ex("Line meets circle", "The line y = x + 1 meets x^2 + y^2 = 25 at A and B. Find A, B and the length AB.", ["x^2 + (x + 1)^2 = 25 gives 2x^2 + 2x - 24 = 0, so x^2 + x - 12 = 0.", "(x + 4)(x - 3) = 0. Points: (-4, -3) and (3, 4).", "Length = sqrt(7^2 + 7^2) = 7 sqrt(2)."], "A(-4, -3), B(3, 4), AB = 7 sqrt(2)"),
      ex("Common chord", "Find the common chord of x^2 + y^2 = 25 and (x - 6)^2 + y^2 = 25, and its length.", ["Second equation: x^2 - 12x + 36 + y^2 = 25.", "Subtract the first from it: -12x + 36 = 0, so x = 3.", "Put x = 3 in the first: y^2 = 16, so y = +-4.", "The chord joins (3, 4) and (3, -4), so its length is 8."], "x = 3; length 8")],
     ["Draw a quick sketch with the centre, the point and the radius marked.", "Say 'tangent, so D = 0' or 'tangent, so perpendicular to radius' to show the method."], TEACH_STD)

# ---------------- 09 circular measure ----------------
seg = 50 * (1.2 - math.sin(1.2)); assert abs(seg - 13.398) < 1e-2
page("09-circular-measure.md", "Circular measure (radians)", "9", "circ, tgraph",
     ["Convert between degrees and radians.", "Arc length s = r theta, sector area A = (1/2) r^2 theta, with theta in radians. Problems that combine sectors with triangles."],
     ["pi radians = 180 degrees. Degrees to radians: multiply by pi/180. Radians to degrees: multiply by 180/pi.", "Arc length s = r theta. Sector area A = (1/2) r^2 theta. Perimeter of a sector = 2r + r theta.",
      "Triangle area = (1/2) a b sin C (given in the formula list). Segment area = sector area - triangle area = (1/2) r^2 (theta - sin theta).", "Chord length = 2 r sin (theta/2). Use right triangles by splitting the isosceles triangle.",
      "Keep angles in radians when you use a calculator for sin theta. Check the mode."],
     ["Using the formulas with degrees.", "Calculator in the wrong mode.", "Forgetting the two radii in the perimeter of a sector.", "Using the segment formula with theta in degrees."],
     [ex("Arc and area", "A sector has radius 8 cm and angle 0.7 radians. Find the arc length and the area.", ["s = 8 x 0.7 = 5.6 cm.", "A = (1/2)(64)(0.7) = 22.4 cm^2."], "5.6 cm and 22.4 cm^2"),
      ex("Convert", "Write 150 degrees in radians and find the arc length for r = 6.", ["150 x pi/180 = 5pi/6.", "s = 6 x 5pi/6 = 5pi, about 15.7 cm."], "5pi/6; arc 5pi cm"),
      ex("Segment", "A sector has radius 10 cm and angle 1.2 radians. Find the area of the segment.", ["Sector = (1/2)(100)(1.2) = 60.", f"Triangle = (1/2)(100) sin 1.2 = {50 * math.sin(1.2):.3f}.", f"Segment = 60 - {50 * math.sin(1.2):.3f} = {seg:.3f}."], "13.4 cm^2 (3 s.f.)"),
      ex("Find the angle", "A sector of radius 5 has area 30. Find the angle and the arc length.", ["30 = (1/2)(25) theta, so theta = 2.4.", "s = 5 x 2.4 = 12."], "theta = 2.4 radians, arc 12")],
     ["Write the formula first. Use exact pi when asked for exact answers.", "State the units of the answer."], TEACH_STD)

# ---------------- 10 trigonometry ----------------
assert sorted(solve(2 * u**2 - u - 1, u)) == [R(-1, 2), 1]
page("10-trigonometry.md", "Trigonometry", "10", "trig, tgraph",
     ["sin, cos, tan, sec, cosec, cot. Exact values for standard angles (30, 45, 60 degrees and the radian equivalents).", "Graphs of a sin(bx) + c, a cos(bx) + c, a tan(bx) + c: amplitude and period.",
      "The three Pythagorean identities. Solve trig equations in a given range. Prove identities.", "Degrees or radians as the question states."],
     ["sec x = 1/cos x, cosec x = 1/sin x, cot x = 1/tan x. tan x = sin x / cos x.", "sin^2 x + cos^2 x = 1. 1 + tan^2 x = sec^2 x. 1 + cot^2 x = cosec^2 x. These three are in the formula list.",
      "Exact values: sin 30 = 1/2, cos 60 = 1/2, sin 45 = cos 45 = sqrt(2)/2, sin 60 = cos 30 = sqrt(3)/2, tan 30 = 1/sqrt(3), tan 45 = 1, tan 60 = sqrt(3).",
      "Graph of a sin(bx) + c: amplitude |a|, period 360/b degrees (2 pi / b radians), midline y = c. For tan the period is 180/b degrees.",
      "Solve: get one trig function equal to a number. Find the acute angle, then use the graph or the CAST diagram for all angles in the range. For sin (bx), widen the range for bx first, then divide.",
      "Quadratics in sin, cos or tan: use an identity to get one function, factorise, solve each. Reject values outside -1 to 1 for sin and cos.",
      "Do not divide by sin x or cos x when solving: move everything to one side and factorise, or you lose solutions.", "Prove an identity: work on one side only (usually the more complicated), change to sin and cos, and reach the other side."],
     ["Dividing by sin x (loses solutions where sin x = 0).", "Forgetting solutions from the other quadrants.", "Not widening the range when the angle is 2x or 3x.", "Calculator mode mismatch (degrees vs radians).", "Writing sin^2 x as sin x^2."],
     [ex("Identity into a quadratic", "Solve 2 sin^2 x + cos x - 1 = 0 for 0 <= x <= 360 degrees.", ["Replace sin^2 x with 1 - cos^2 x: 2 - 2cos^2 x + cos x - 1 = 0.", "-2cos^2 x + cos x + 1 = 0, so 2cos^2 x - cos x - 1 = 0.", "(2cos x + 1)(cos x - 1) = 0. cos x = -1/2 gives 120 and 240. cos x = 1 gives 0 and 360."], "x = 0, 120, 240, 360"),
      ex("Do not divide", "Solve tan x = 2 sin x for 0 <= x <= 360 degrees.", ["sin x / cos x = 2 sin x, so sin x = 2 sin x cos x.", "sin x (1 - 2 cos x) = 0.", "sin x = 0 gives 0, 180, 360. cos x = 1/2 gives 60 and 300."], "x = 0, 60, 180, 300, 360"),
      ex("Prove an identity", "Prove tan x + cot x = sec x cosec x.", ["LHS = sin x / cos x + cos x / sin x.", "Common denominator: (sin^2 x + cos^2 x)/(sin x cos x).", "The top is 1, so LHS = 1/(sin x cos x) = sec x cosec x."], "Proved"),
      ex("Radians", "Solve sin x = 1/2 for 0 <= x <= 2 pi.", ["Acute angle: pi/6.", "sin is positive in the first and second quadrants: x = pi/6 and pi - pi/6."], "x = pi/6 and 5pi/6")],
     ["Write 'hence' answers using the result just proved.", "In an identity proof, never treat it as an equation and do the same thing to both sides."], TEACH_STD)

# ---------------- 11 permutations and combinations ----------------
assert binomial(8, 5) == 56 and 7 * 6 * 5 * 4 == 840 and 3 * 6 * 5 * 4 == 360
cm = binomial(10, 4) - binomial(6, 4) - 4 * binomial(6, 3); assert cm == 115 and 6 * binomial(4, 2) * 0 + (binomial(4, 2) * binomial(6, 2) + binomial(4, 3) * 6 + 1) == 115
page("11-permutations-and-combinations.md", "Permutations and combinations", "11", "perm",
     ["n!, nPr and nCr.", "Arrangement and selection problems, with and without restrictions."],
     ["Order matters: arrangement (permutation). nPr = n!/(n - r)!. Order does not matter: selection (combination). nCr = n!/(r!(n - r)!). nCr = nC(n - r).",
      "n people in a row: n! arrangements. r from n in order: nPr. A team of r from n: nCr.", "Two people together: treat them as one block, arrange the block with the others, then multiply by 2 for the order inside the block.",
      "Two people NOT together: total arrangements - arrangements together.", "'At least' problems: add the cases, or take the complement (total - the cases that are not allowed).",
      "Digits with conditions: fill the restricted position first (for an even number, choose the last digit first)."],
     ["Using nCr when order matters, or the reverse. Ask: would swapping two items give a different outcome?", "Counting cases twice.", "Forgetting that digits cannot start with 0 in a number.", "Forgetting to multiply the independent choices."],
     [ex("Selection", "Choose 5 books from 8.", ["Order does not matter: 8C5 = 8!/(5! 3!) = 56."], "56"),
      ex("Even numbers", "How many four-digit numbers can be made from the digits 1 to 7, with no repeats, that are even?", ["Last digit even: 2, 4 or 6, so 3 choices.", "The other three places from the remaining 6 digits in order: 6 x 5 x 4 = 120.", "Total = 3 x 120 = 360."], "360"),
      ex("At least two women", "A committee of 4 is chosen from 6 men and 4 women. It must have at least 2 women. How many committees?", ["Total with no restriction: 10C4 = 210.", "No women: 6C4 = 15. Exactly one woman: 4 x 6C3 = 80.", "210 - 15 - 80 = 115. Check by cases: 2 women 6C2 x 4C2 = 90, 3 women 4C3 x 6 = 24, 4 women 1. 90 + 24 + 1 = 115."], "115"),
      ex("Together and apart", "Six people stand in a row. Two particular people must (a) be together, (b) not be together.", ["(a) Block: 5! x 2 = 240.", "(b) Total 6! = 720, so 720 - 240 = 480."], "(a) 240 (b) 480")],
     ["Say in a phrase whether it is a permutation or a combination, and why.", "Show the calculation in factorials or nPr/nCr form before the number."], TEACH_STD)

# ---------------- 12 series ----------------
c12 = binomial(5, 3) * 2**2 * 3**3; assert c12 == 1080
tind = binomial(6, 4) * 2**4; assert tind == 240 and expand((x**2 + 2 / x)**6).coeff(x, 0) == 240
d12 = R(34 - 14, 8 - 3); a12 = 14 - 2 * d12; s10 = R(10, 2) * (2 * a12 + 9 * d12); assert (d12, a12, s10) == (4, 6, 240)
assert 5 * (2**11 - 1) > 10000 and 5 * (2**10 - 1) < 10000
page("12-series.md", "Series: binomial, arithmetic and geometric progressions", "12", "binom, prog",
     ["Binomial expansion of (a + b)^n for positive integer n; general term; the term independent of x.", "Arithmetic and geometric progressions: nth term and sum.", "Sum to infinity of a GP and the condition for convergence.", "Contextual problems."],
     ["Binomial: (a + b)^n = sum over r of nCr a^(n - r) b^r. General term (r + 1th) = nCr a^(n - r) b^r. Pascal's triangle gives nCr for small n.",
      "Coefficient of x^m: write the general term with all powers of x, set the power equal to m, solve for r.", "Brackets like (1 + 2x)^5: keep the constants and signs inside the power.",
      "AP: u_n = a + (n - 1)d. S_n = (n/2)[2a + (n - 1)d] = (n/2)(a + l). GP: u_n = a r^(n - 1). S_n = a(1 - r^n)/(1 - r) = a(r^n - 1)/(r - 1). S_infinity = a/(1 - r) only if |r| < 1.",
      "Two given terms: write two equations in a and d (or a and r). Subtract for d. Divide for r.", "Least n such that a sum exceeds K: write the inequality, solve with algebra (quadratic) or logs (GP), then round UP to a whole n and check n and n - 1.",
      "Dividing inequalities by log of a number less than 1 reverses the inequality sign."],
     ["Writing the (r)th term when you mean the (r + 1)th term.", "Using S_infinity when |r| >= 1.", "Forgetting the sign when b is negative: (2 - 3x)^4 has alternating signs.", "Rounding n down."],
     [ex("Coefficient", "Find the coefficient of x^3 in (2 + 3x)^5.", ["General term = 5Cr 2^(5 - r) (3x)^r. For x^3, r = 3.", "5C3 x 2^2 x 3^3 = 10 x 4 x 27 = 1080."], "1080"),
      ex("Term independent of x", "Find the term independent of x in (x^2 + 2/x)^6.", ["General term = 6Cr (x^2)^(6 - r) (2/x)^r = 6Cr 2^r x^(12 - 3r).", "Power 0: 12 - 3r = 0, r = 4.", "6C4 x 2^4 = 15 x 16 = 240."], "240"),
      ex("AP from two terms", "In an AP the 3rd term is 14 and the 8th is 34. Find a, d and S_10.", ["a + 2d = 14 and a + 7d = 34. Subtract: 5d = 20, d = 4, a = 6.", "S_10 = (10/2)(2 x 6 + 9 x 4) = 5 x 48 = 240."], "a = 6, d = 4, S_10 = 240"),
      ex("Sum to infinity", "A GP has first term 3 and ratio 2/3. Find S_infinity.", ["|r| = 2/3 < 1, so it converges.", "S_infinity = 3/(1 - 2/3) = 9."], "9"),
      ex("Least n", "The GP 5, 10, 20, ... has sum S_n = 5(2^n - 1). Find the least n for which S_n > 10000.", ["2^n - 1 > 2000, so 2^n > 2001.", "n > ln 2001 / ln 2 = 10.97, so n = 11.", "Check: S_11 = 5 x 2047 = 10235 > 10000 and S_10 = 5115 < 10000."], "n = 11")],
     ["For 'show that' sum questions, quote the formula, substitute, and simplify to the target.", "Write the condition |r| < 1 before using S_infinity."], TEACH_STD)

# ---------------- 13 vectors ----------------
assert sqrt(3**2 + 4**2) == 5 and (1 - 3, -2 - 4) == (-2, -6) and sqrt(40) == 2 * sqrt(10)
tt = symbols("tt"); assert solve([2 + 3 * tt - (17 - 2 * tt), 1 - tt - (-8 + 2 * tt)], [tt]) == {tt: 3}
page("13-vectors.md", "Vectors in two dimensions", "13", "vec",
     ["Notation: column vectors, i and j form, AB, single letters. Position vectors, unit vectors, magnitude. Add, subtract, scalar multiples.", "Vector geometry; equate like vectors. Velocity vectors; motion of particles, collisions."],
     ["Magnitude |ai + bj| = sqrt(a^2 + b^2). Unit vector = vector / magnitude.", "AB = OB - OA = b - a (end minus start).", "Parallel vectors are scalar multiples: if p = lambda q then p is parallel to q. Collinear points A, B, C: AB = lambda BC.",
      "Point P on AB with AP:PB = m:n has OP = OA + m/(m + n) AB.", "Equating vectors: if a i + b j = c i + d j then a = c and b = d. Use this to get two equations.",
      "Moving particle: position r = r0 + v t (initial position r0, constant velocity v). Speed = |v|.", "Collision: two particles are at the same place at the same time. Equate the i components and the j components, solve for t, and CHECK it works in both.",
      "Distance between two moving particles at time t: find both position vectors at that time, subtract to get PQ, then take the magnitude."],
     ["AB = a - b (the wrong way round).", "Forgetting to square-root a magnitude.", "Solving the i equation only: a collision needs both components to give the same t.", "Mixing speed (a number) and velocity (a vector)."],
     [ex("Basic vectors", "a = 3i + 4j and b = i - 2j. Find |a|, a unit vector along a, and AB.", ["|a| = sqrt(9 + 16) = 5.", "Unit vector = (3i + 4j)/5.", "AB = b - a = (1 - 3)i + (-2 - 4)j = -2i - 6j. |AB| = sqrt(40) = 2 sqrt(10)."], "5; (3i + 4j)/5; -2i - 6j"),
      ex("Point dividing a line", "A(1, 2), B(7, 5). P is on AB with AP:PB = 2:1. Find OP.", ["AB = (6, 3).", "AP = 2/3 of AB = (4, 2).", "OP = OA + AP = (1 + 4, 2 + 2) = (5, 4)."], "OP = 5i + 4j"),
      ex("Collision", "P starts at (2i + j) with velocity (3i - j). Q starts at (17i - 8j) with velocity (-2i + 2j). Do they collide?", ["P at time t: (2 + 3t)i + (1 - t)j. Q at time t: (17 - 2t)i + (-8 + 2t)j.", "i components equal: 2 + 3t = 17 - 2t, so t = 3.", "j components equal: 1 - t = -8 + 2t, so t = 3. Same value, so they collide.", "Position: (2 + 9)i + (1 - 3)j = 11i - 2j."], "Yes, at t = 3, at 11i - 2j")],
     ["Draw a sketch with arrows. Use the capital-letter notation (AB) consistently.", "Do not mix notations in one line."], TEACH_STD)

# ---------------- 14 differentiation ----------------
d1 = simplify(diff(x**2 * exp(3 * x), x)); assert simplify(d1 - exp(3 * x) * (2 * x + 3 * x**2)) == 0
d2 = simplify(diff((2 * x + 1) / (x**2 + 1), x)); assert simplify(d2 - (-2 * x**2 - 2 * x + 2) / (x**2 + 1)**2) == 0
f14 = x**3 - 6 * x**2 + 9 * x + 1; assert solve(diff(f14, x), x) == [1, 3] and f14.subs(x, 1) == 5 and f14.subs(x, 3) == 1 and diff(f14, x, 2).subs(x, 1) < 0
yl = log(3 * x - 2); assert diff(yl, x).subs(x, 1) == 3 and yl.subs(x, 1) == 0
page("14-differentiation.md", "Differentiation", "14 (calculus: differentiation)", "diff, stat, tangent, rates",
     ["Notation f'(x), f''(x), dy/dx, d2y/dx2.", "Derivatives of x^n (any rational n), sin x, cos x, tan x, e^x, ln x; constant multiples and sums.", "Chain rule, product rule, quotient rule.", "Tangents and normals. Stationary points and their nature.", "Connected rates of change, small increments, practical maximum and minimum problems."],
     ["x^n gives n x^(n - 1). sin x gives cos x. cos x gives -sin x. tan x gives sec^2 x. e^x gives e^x. ln x gives 1/x. For e^(ax) the derivative is a e^(ax).",
      "Rewrite roots and fractions as powers first: sqrt(x) = x^(1/2), 1/x^2 = x^-2.", "Chain rule: dy/dx = dy/du x du/dx. Product rule: d(uv) = u v' + v u'. Quotient rule: d(u/v) = (v u' - u v')/v^2.",
      "Tangent at x = x0: gradient m = dy/dx at x0, point (x0, y0), line y - y0 = m(x - x0). Normal gradient = -1/m.", "Stationary points: dy/dx = 0. Nature: d2y/dx2 > 0 minimum, < 0 maximum. If d2y/dx2 = 0, check the sign of dy/dx either side.",
      "Small change: delta y is approximately (dy/dx) delta x. Connected rates: dy/dt = dy/dx x dx/dt.", "Optimisation: write the quantity as a function of ONE variable using the constraint, differentiate, set to zero, prove it is a max or a min, answer the question that was asked."],
     ["Forgetting the chain rule factor, such as d/dx sin(3x) = 3 cos 3x.", "Quotient rule order: v u' - u v', not u v' - v u'.", "Differentiating the constant: it becomes 0.", "Stopping at the x value of a stationary point when the question wants coordinates.", "Using the tangent gradient for the normal."],
     [ex("Product rule", "Differentiate y = x^2 e^(3x).", ["u = x^2, v = e^(3x). u' = 2x, v' = 3e^(3x).", f"dy/dx = x^2 (3e^(3x)) + e^(3x)(2x) = e^(3x)(3x^2 + 2x)."], "dy/dx = e^(3x)(3x^2 + 2x)"),
      ex("Quotient rule", "Differentiate y = (2x + 1)/(x^2 + 1).", ["u = 2x + 1, v = x^2 + 1. u' = 2, v' = 2x.", "dy/dx = [(x^2 + 1)(2) - (2x + 1)(2x)]/(x^2 + 1)^2.", "Numerator: 2x^2 + 2 - 4x^2 - 2x = -2x^2 - 2x + 2."], "dy/dx = (-2x^2 - 2x + 2)/(x^2 + 1)^2"),
      ex("Stationary points", "Find and classify the stationary points of y = x^3 - 6x^2 + 9x + 1.", ["dy/dx = 3x^2 - 12x + 9 = 3(x - 1)(x - 3) = 0, so x = 1 or 3.", "y(1) = 5 and y(3) = 1.", "d2y/dx2 = 6x - 12. At x = 1 it is -6 (maximum). At x = 3 it is +6 (minimum)."], "(1, 5) maximum; (3, 1) minimum"),
      ex("Tangent and normal", "Find the tangent and normal to y = ln(3x - 2) at x = 1.", ["dy/dx = 3/(3x - 2) = 3 at x = 1. y = ln 1 = 0.", "Tangent: y - 0 = 3(x - 1), so y = 3x - 3.", "Normal gradient -1/3: y = -(x - 1)/3."], "tangent y = 3x - 3; normal y = -(x - 1)/3")],
     ["Name the rule you use in a few words. Show u, v, u', v' for product and quotient questions.", "For 'show that' stationary point questions, show both the derivative equal to zero and the value."],
     TEACH_STD)

# ---------------- 15 integration ----------------
i1 = integrate(3 * x**2 - 4 / x**2 + 2 * exp(2 * x), x); assert simplify(i1 - (x**3 + 4 / x + exp(2 * x))) == 0
assert simplify(diff((2 * x - 1)**5 / 10, x) - (2 * x - 1)**4) == 0 and simplify(diff(log(3*x+1)/3, x) - 1/(3*x+1)) == 0 and simplify(diff(tan(2*x)/2, x) - sec(2*x)**2) == 0
assert integrate(2 * x - x**2, (x, 0, 2)) == R(4, 3)
assert simplify(integrate(cos(2 * x), (x, 0, pi / 6)) - sqrt(3) / 4) == 0
page("15-integration.md", "Integration", "14 (calculus: integration)", "integ, area",
     ["Integration as the reverse of differentiation, with a constant of integration.", "Powers of x including 1/x, (ax + b)^n for any rational n (including n = -1), sin(ax + b), cos(ax + b), sec^2(ax + b), e^(ax + b).", "Definite integrals. Area under a curve, between a curve and a line, between two curves, and sums of areas."],
     ["x^n gives x^(n + 1)/(n + 1) for n not equal to -1. 1/x gives ln|x|. e^x gives e^x.", "Linear inside: divide by the coefficient of x. (ax + b)^n gives (ax + b)^(n + 1)/(a(n + 1)). 1/(ax + b) gives (1/a) ln|ax + b|. e^(ax + b) gives e^(ax + b)/a. sin(ax + b) gives -cos(ax + b)/a. cos(ax + b) gives sin(ax + b)/a. sec^2(ax + b) gives tan(ax + b)/a.",
      "Always add + c to an indefinite integral. For a definite integral no constant is needed.", "Find c with a given point: substitute the point into the integrated function.",
      "Area under y = f(x) from x = a to x = b is the integral of f if f >= 0 on the interval. Where the curve is below the axis the integral is negative: take the size.", "Area between curves: integral of (top - bottom). Find the intersections first.",
      "Several regions: split at the x-intercepts, integrate each, take the positive size of each, add."],
     ["Forgetting + c or the division by the coefficient of x.", "Using x^(n + 1)/(n + 1) for 1/x.", "Writing a negative area as the answer.", "Using the wrong limits order: upper limit minus lower limit.", "Integrating the product of two functions term by term. It is not allowed."],
     [ex("Mixed integral", "Find the integral of 3x^2 - 4/x^2 + 2e^(2x).", ["Rewrite 4/x^2 as 4x^-2.", "Integrate each: x^3, +4/x (since the integral of -4x^-2 is 4x^-1), and e^(2x).", "Add the constant."], "x^3 + 4/x + e^(2x) + c"),
      ex("Reverse chain rule", "Find the integral of (2x - 1)^4, then of 1/(3x + 1), then of sec^2(2x).", ["(2x - 1)^5 / (5 x 2) = (2x - 1)^5 / 10 + c.", "(1/3) ln|3x + 1| + c.", "(1/2) tan 2x + c."], "(2x - 1)^5/10 + c; (1/3) ln|3x + 1| + c; (1/2) tan 2x + c"),
      ex("Area between a line and a curve", "Find the area between y = x^2 and y = 2x.", ["Intersections: x^2 = 2x gives x = 0, 2.", "Between them the line is above the curve.", "Area = integral from 0 to 2 of (2x - x^2) dx = [x^2 - x^3/3] = 4 - 8/3 = 4/3."], "4/3"),
      ex("Exact trig integral", "Evaluate the integral of cos 2x from 0 to pi/6.", ["Integral = (1/2) sin 2x.", "At pi/6: (1/2) sin(pi/3) = sqrt(3)/4. At 0: 0."], "sqrt(3)/4")],
     ["Show the integrated function in brackets or square brackets, then the limits.", "Leave exact values (pi, e, ln, surds) when the question says exact."], TEACH_STD)

# ---------------- 16 kinematics ----------------
s16 = t**3 - 6 * t**2 + 9 * t; v16 = diff(s16, t); assert solve(v16, t) == [1, 3] and s16.subs(t, 1) == 4 and s16.subs(t, 3) == 0 and s16.subs(t, 4) == 4
a_ = 6 * t - 4; v_ = integrate(a_, t) + 3; s_ = integrate(v_, t); assert v_ == 3 * t**2 - 4 * t + 3 and s_ == t**3 - 2 * t**2 + 3 * t
page("16-kinematics.md", "Kinematics (straight-line motion)", "14 (calculus: kinematics)", "kin",
     ["Displacement, velocity and acceleration in a straight line, with constant or variable acceleration.", "Displacement-time, distance-time, velocity-time, speed-time and acceleration-time graphs."],
     ["v = ds/dt and a = dv/dt = d2s/dt2. Going the other way: v = integral of a dt, s = integral of v dt.", "Each integration needs its constant. Use the given condition, such as 'at rest at t = 0' or 'v = 3 when t = 0', to find it.",
      "Instantaneous rest: v = 0. Greatest or least displacement happens where v = 0 and changes sign.", "Displacement is the final position minus the start. Distance travelled adds the sizes of the pieces: split the interval wherever v = 0.",
      "Speed = |v|. Direction change: v changes sign.", "Graphs: the gradient of an s-t graph is v. The gradient of a v-t graph is a. The area under a v-t graph is displacement (areas below the axis count as negative; for distance take sizes)."],
     ["Calculating distance as s(end) - s(start) when the particle turns round.", "Leaving out the constant of integration.", "Finding t = 0 at rest when the question says t > 0, or including negative t values.", "Mixing up displacement from the start and displacement from O."],
     [ex("Rest and distance", "s = t^3 - 6t^2 + 9t metres. Find when the particle is at rest and the distance travelled in the first 4 seconds.", ["v = 3t^2 - 12t + 9 = 3(t - 1)(t - 3), so v = 0 at t = 1 and t = 3.", "s(0) = 0, s(1) = 4, s(3) = 0, s(4) = 4.", "Path: 0 to 4 (distance 4), 4 to 0 (distance 4), 0 to 4 (distance 4). Total 12 m."], "At rest at t = 1 and 3; distance 12 m (displacement 4 m)"),
      ex("Integrate with conditions", "a = 6t - 4. When t = 0, v = 3 and s = 0. Find v and s.", ["v = 3t^2 - 4t + c. At t = 0, v = 3, so c = 3.", "s = t^3 - 2t^2 + 3t + d. At t = 0, s = 0, so d = 0."], "v = 3t^2 - 4t + 3; s = t^3 - 2t^2 + 3t")],
     ["Write which quantity you are finding (v, a, s) and the rule linking them.", "Finish with a sentence including units."], TEACH_STD)

# ---------------- INDEX ----------------
rows = [("01-functions.md", "functions, domain, range, composite, inverse, modulus graph", "func"),
        ("02-quadratics.md", "completing the square, discriminant, tangent to a curve, quadratic inequality", "quad, ineq"),
        ("03-polynomials.md", "remainder theorem, factor theorem, cubic, long division", "factor"),
        ("04-equations-inequalities-graphs.md", "modulus equation, modulus inequality, substitution, cubic inequality, sketch of a cubic", "mod, ineq"),
        ("05-simultaneous-equations.md", "simultaneous equations, line and curve, line and circle", "simul"),
        ("06-logs-and-exponentials.md", "logarithm, ln, e^x, solve a^x = b, laws of logs, change of base", "log"),
        ("07-straight-lines-and-linear-law.md", "gradient, midpoint, perpendicular bisector, linear law, lg graph", "line, lin"),
        ("08-circle-geometry.md", "equation of a circle, tangent to a circle, chord, common chord", "cgeo"),
        ("09-circular-measure.md", "radians, arc length, sector, segment", "circ"),
        ("10-trigonometry.md", "sin, cos, tan, sec, cosec, cot, identities, trig equations, amplitude, period", "trig, tgraph"),
        ("11-permutations-and-combinations.md", "permutation, combination, arrangements, selections", "perm"),
        ("12-series.md", "binomial expansion, arithmetic progression, geometric progression, sum to infinity", "binom, prog"),
        ("13-vectors.md", "vectors, position vector, velocity vector, collision, parallel", "vec"),
        ("14-differentiation.md", "derivative, chain rule, product rule, quotient rule, tangent, normal, stationary point, rates of change, optimisation", "diff, stat, tangent, rates"),
        ("15-integration.md", "integral, area under a curve, area between curves", "integ, area"),
        ("16-kinematics.md", "displacement, velocity, acceleration, particle moving in a line", "kin")]
idx = "# Topic notes index\nOriginal study notes (not Cambridge text). Before teaching a topic, read the matching file. Every worked example in them was checked with sympy.\n\n"
idx += "| File | Use for | Practice generator topics |\n|---|---|---|\n" + "\n".join(f"| {a} | {b} | {c} |" for a, b, c in rows) + "\n"
idx += "\nIf a question does not match any file, check syllabus.md first. If it is not in the syllabus, say it is outside 0606.\n"
open(os.path.join(OUT, "INDEX.md"), "w", encoding="utf-8", newline="\n").write(idx)
print("built", len(rows), "topic files + INDEX")
