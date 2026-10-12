"""Edith maths checker. Usage:  python check.py <command> <args>

Commands (write maths in plain text; ^ means power, ln = natural log):
  diff      "x^2*ln(x)" x              derivative
  integrate "2x*e^(x^2)" x             indefinite integral (+ C)
  integrate "x^2" x 0 3                definite integral from 0 to 3
  solve     "x^2-5x+6=0" x             solve equation(s) for x
  expand    "(x+2)^3"
  factor    "x^3-7x+6"
  simplify  "sin(x)^2+cos(x)^2"
  equal     "expr1" "expr2"            are the two expressions identical?
  eval      "sqrt(2)*3" [x=2]          numeric value, optional substitutions
  stationary "x^3-3x" x                stationary points and their nature
"""
import sys
from sympy import (symbols, sympify, diff, integrate, solve, expand, factor, simplify,
                   Eq, N, Symbol, oo, S)
from sympy.parsing.sympy_parser import (parse_expr, standard_transformations,
    implicit_multiplication_application, convert_xor)

T = standard_transformations + (implicit_multiplication_application, convert_xor)
LOCALS = {"ln": __import__("sympy").log, "e": __import__("sympy").E,
          "cosec": lambda a: 1/__import__("sympy").sin(a),
          "sec": lambda a: 1/__import__("sympy").cos(a),
          "cot": lambda a: 1/__import__("sympy").tan(a)}

_GLOB = {}
exec("from sympy import *", _GLOB)
_WORDS = {"sqrt", "sin", "cos", "tan", "sec", "cosec", "cot", "exp", "ln", "log", "abs", "Abs", "asin", "acos", "atan", "pi"}

def _parse(s):
    """Parse plain-text maths safely: plain characters only, no huge powers, no Python internals."""
    import re
    from gen import guard
    from sympy.parsing.sympy_parser import stringify_expr, eval_expr
    s = s.strip()
    if len(s) > 300 or "__" in s or re.search(r"[^0-9A-Za-z_+\-*/^().,\s]", s) or re.search(r"\.[A-Za-z_]", s):
        raise ValueError("input is not plain maths")
    for w in re.findall(r"[A-Za-z_]+", s):
        if w not in _WORDS and len(w) > 4: raise ValueError("unknown word " + w)
    code = stringify_expr(s, dict(LOCALS), _GLOB, T)
    guard(code)
    return eval_expr(code, dict(LOCALS), _GLOB)

def P(s):
    s = s.replace("**", "^")
    if "=" in s:
        l, r = s.split("=", 1)
        return Eq(_parse(l), _parse(r))
    return _parse(s)

def main(a):
    if len(a) < 2: print(__doc__); return
    c = a[0]
    if c == "diff":
        print(diff(P(a[1]), Symbol(a[2])))
    elif c == "integrate":
        x = Symbol(a[2])
        if len(a) >= 5:
            print(integrate(P(a[1]), (x, P(a[3]), P(a[4]))))
        else:
            print(str(integrate(P(a[1]), x)) + " + C")
    elif c == "solve":
        print(solve(P(a[1]), Symbol(a[2]) if len(a) > 2 else None))
    elif c == "expand": print(expand(P(a[1])))
    elif c == "factor": print(factor(P(a[1])))
    elif c == "simplify": print(simplify(P(a[1])))
    elif c == "equal":
        print("EQUAL" if simplify(P(a[1]) - P(a[2])) == 0 else "NOT EQUAL")
    elif c == "eval":
        subs = {Symbol(k): P(v) for k, v in (s.split("=") for s in a[2:])}
        v = P(a[1]).subs(subs)
        print(v, "=", N(v, 8))
    elif c == "stationary":
        x = Symbol(a[2]); f = P(a[1]); d2 = diff(f, x, 2)
        for s in solve(diff(f, x), x):
            k = d2.subs(x, s)
            nat = "minimum" if k > 0 else "maximum" if k < 0 else "inconclusive (check sign change)"
            print(f"x = {s}, y = {f.subs(x, s)}, f'' = {k}: {nat}")
    else:
        print("Unknown command.\n" + __doc__)

if __name__ == "__main__":
    try: main(sys.argv[1:])
    except Exception as ex: print("CHECK FAILED:", ex)
