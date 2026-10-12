"""Edith graph tool. Draws graphs and saves a PNG into ../plots/.
Prints a line like  MEDIA:plots/graph_123456.png  which OpenClaw sends to Telegram.

Usage:
  python plot.py "x^2-4x+3"
  python plot.py "x^2-4x+3; 2x-1" --xmin -2 --xmax 6          (several curves, separate with ;)
  python plot.py "x^3-3x" --mark                               (mark intercepts and stationary points)
  python plot.py "x^2" --tangent 1                             (tangent at x = 1)
  python plot.py "x^2" --shade 0 2                             (shade area between curve and x-axis)
  python plot.py "abs(2x-1)" --ymin -1 --ymax 6
Write maths in plain text: ^ for powers, ln(x), sqrt(x), e^x, abs(x), sin(x).
"""
import argparse, os, sys, time
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sympy import Symbol, lambdify, diff, solve, N, im, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check import P

x = Symbol("x")

def real_vals(vals, lo, hi):
    out = []
    for v in vals:
        try:
            v = complex(N(v))
            if abs(v.imag) < 1e-9 and lo <= v.real <= hi:
                out.append(v.real)
        except Exception:
            pass
    return sorted(set(round(o, 6) for o in out))

def main():
    ap = argparse.ArgumentParser(add_help=True, usage=__doc__)
    ap.add_argument("funcs")
    ap.add_argument("--xmin", type=float, default=-6); ap.add_argument("--xmax", type=float, default=6)
    ap.add_argument("--ymin", type=float); ap.add_argument("--ymax", type=float)
    ap.add_argument("--mark", action="store_true")
    ap.add_argument("--tangent", type=float)
    ap.add_argument("--shade", type=float, nargs=2)
    a = ap.parse_args()

    exprs = [P(s.strip()) for s in a.funcs.split(";") if s.strip()]
    xs = np.linspace(a.xmin, a.xmax, 2000)
    fig, ax = plt.subplots(figsize=(6, 5))
    allys = []
    for i, f in enumerate(exprs):
        fn = lambdify(x, f, modules=["numpy"])
        with np.errstate(all="ignore"):
            ys = np.array(fn(xs), dtype=float) * np.ones_like(xs)
        ys[~np.isfinite(ys)] = np.nan
        allys.append(ys)
    flat = np.concatenate([y[np.isfinite(y)] for y in allys]) if allys else np.array([0.0])
    if a.ymin is None or a.ymax is None:
        lo, hi = (np.percentile(flat, 2), np.percentile(flat, 98)) if flat.size else (-5, 5)
        lo, hi = max(lo, -10), min(hi, 10)
        if hi - lo < 2: lo, hi = lo - 1, hi + 1
        pad = 0.15 * max(hi - lo, 1)
        ymin, ymax = lo - pad, hi + pad
    ymin = a.ymin if a.ymin is not None else ymin
    ymax = a.ymax if a.ymax is not None else ymax
    for i, (f, ys) in enumerate(zip(exprs, allys)):
        yy = ys.copy(); yy[(yy > ymax * 5) | (yy < ymin * 5 if ymin < 0 else yy < -1e9)] = np.nan
        # break the line at asymptotes
        jump = np.abs(np.diff(yy, prepend=yy[0])) > (ymax - ymin) * 2
        yy[jump] = np.nan
        ax.plot(xs, yy, label="y = " + str(f).replace("**", "^").replace("log", "ln"), linewidth=2)
        if a.mark:
            try:
                roots = real_vals(solve(f, x), a.xmin, a.xmax)
                ax.scatter(roots, [0] * len(roots), color="black", zorder=5)
                for r in roots: ax.annotate(f"({r:g}, 0)", (r, 0), textcoords="offset points", xytext=(4, -14), fontsize=8)
                y0 = complex(N(f.subs(x, 0)))
                if abs(y0.imag) < 1e-9 and ymin <= y0.real <= ymax and a.xmin <= 0 <= a.xmax and abs(y0.real) > 1e-9:
                    ax.scatter([0], [y0.real], color="black", zorder=5)
                    ax.annotate(f"(0, {y0.real:g})", (0, y0.real), textcoords="offset points", xytext=(4, 4), fontsize=8)
                for s in real_vals(solve(diff(f, x), x), a.xmin, a.xmax):
                    yv = float(N(f.subs(x, s)))
                    ax.scatter([s], [yv], color="red", zorder=5)
                    ax.annotate(f"({s:g}, {yv:g})", (s, yv), textcoords="offset points", xytext=(4, 6), fontsize=8, color="red")
            except Exception:
                pass
        if i == 0 and a.tangent is not None:
            x0 = a.tangent; m = float(N(diff(f, x).subs(x, x0))); y0 = float(N(f.subs(x, x0)))
            ax.plot(xs, m * (xs - x0) + y0, "--", label=f"tangent at x = {x0:g} (gradient {m:g})")
            ax.scatter([x0], [y0], color="black", zorder=5)
        if i == 0 and a.shade:
            lo_s, hi_s = a.shade
            m = (xs >= lo_s) & (xs <= hi_s)
            ax.fill_between(xs[m], 0, np.nan_to_num(ys[m]), alpha=0.25)
    ax.axhline(0, color="black", linewidth=0.8); ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlim(a.xmin, a.xmax); ax.set_ylim(ymin, ymax)
    ax.set_xlabel("x"); ax.set_ylabel("y"); ax.grid(alpha=0.3); ax.legend(loc="best", fontsize=8)
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plots")
    os.makedirs(out_dir, exist_ok=True)
    name = f"graph_{int(time.time()*1000) % 10**9}.png"
    fig.tight_layout(); fig.savefig(os.path.join(out_dir, name), dpi=130); plt.close(fig)
    print(f"MEDIA:plots/{name}")

if __name__ == "__main__":
    try: main()
    except SystemExit: raise
    except Exception as ex: print("PLOT FAILED:", ex)