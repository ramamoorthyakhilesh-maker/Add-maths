"""Edith question cards. Draws a question as a clean maths card (PNG) so it is easy to read on a phone.
Prints a line like  MEDIA:plots/q_diff-medium-123456.png  which OpenClaw sends to Telegram.

Usage:
  python tools/render.py diff-medium-123456              (card for a question made by gen.py)
  python tools/render.py --text "Solve x^2 - 5x + 6 = 0." [--title "Worked example"]

It only changes how a question LOOKS. The question text and the answer key come from gen.py.
On any problem it prints  RENDER FAILED: ...  and the question should be sent as plain text.
"""
import argparse, os, re, sys, time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ---------------------------------------------------------------- plain text -> mathtext
FUNCS = {"sin": r"\sin", "cos": r"\cos", "tan": r"\tan", "cot": r"\cot", "sec": r"\sec",
         "cosec": r"\mathrm{cosec}", "ln": r"\ln", "log": r"\log", "exp": r"\exp"}
UNITS = {"cm": r"\mathrm{cm}", "mm": r"\mathrm{mm}", "km": r"\mathrm{km}", "m": r"\mathrm{m}",
         "cm^2": r"\mathrm{cm}^{2}", "cm^3": r"\mathrm{cm}^{3}", "m^2": r"\mathrm{m}^{2}", "m^3": r"\mathrm{m}^{3}",
         "m/s": r"\mathrm{m\,s}^{-1}", "m/s^2": r"\mathrm{m\,s}^{-2}", "cm/s": r"\mathrm{cm\,s}^{-1}",
         "cm^2/s": r"\mathrm{cm}^{2}\mathrm{\,s}^{-1}", "cm^3/s": r"\mathrm{cm}^{3}\mathrm{\,s}^{-1}"}
UNIT_RE = "|".join(re.escape(u) for u in sorted(UNITS, key=len, reverse=True))


class Bad(Exception):
    pass


def lex(s):
    """Turn a plain-text maths string into tokens: (kind, text, space_before)."""
    s = re.sub(r"(?<=[\d\)xyt])\s*(" + UNIT_RE + r")(?![A-Za-z0-9^/])", lambda m: " @U{" + m.group(1) + "}", s)
    s = re.sub(r"(?<=\d)\s*degrees?\b", " @D", s)
    toks, i, n = [], 0, len(s)
    while i < n:
        sp = False
        while i < n and s[i] == " ":
            i += 1; sp = True
        if i >= n:
            break
        m = re.compile(r"@U\{([^}]*)\}").match(s, i)
        if m:
            toks.append(("unit", m.group(1), sp)); i = m.end(); continue
        if s.startswith("@D", i):
            toks.append(("deg", "", sp)); i += 2; continue
        m = re.compile(r"\d+(?:\.\d+)?").match(s, i)
        if m:
            toks.append(("num", m.group(), sp)); i = m.end(); continue
        m = re.compile(r"[A-Za-z]+").match(s, i)
        if m:
            w = m.group()
            if w == "sqrt" or w == "abs" or w == "pi" or w in FUNCS:
                toks.append(("word", w, sp)); i = m.end()
            else:  # split into single letters; keep the first space flag only
                for k, ch in enumerate(w):
                    toks.append(("var", ch, sp and k == 0))
                i = m.end()
            continue
        for op in ("<=", ">=", "!="):
            if s.startswith(op, i):
                toks.append(("op", op, sp)); i += 2; break
        else:
            toks.append(("op", s[i], sp)); i += 1
    return toks


class Parser:
    def __init__(self, toks):
        self.t, self.i, self.exp = toks, 0, 0
        self.display = any(t[0] == "op" and t[1] in ("=", "<=", ">=", "<", ">") for t in toks)
        self.depth = 0

    def peek(self, k=0):
        j = self.i + k
        return self.t[j] if j < len(self.t) else (None, None, False)

    def is_op(self, ch, k=0):
        t = self.peek(k)
        return t[0] == "op" and t[1] == ch

    def expr(self, closers=()):
        out, run = [], []   # run = juxtaposed items of the current product: (latex, group_inner)
        prev_kind = None    # to spot unary minus

        def flush():
            if run:
                out.append("".join(r[0] for r in run)); run.clear()

        while self.i < len(self.t):
            kind, txt, _ = self.peek()
            if kind == "op" and txt in closers:
                break
            if kind == "op" and txt in "+=<>:,;" or (kind == "op" and txt in ("<=", ">=", "!=")):
                flush()
                out.append({"<=": r"\leq ", ">=": r"\geq ", "!=": r"\neq ", ",": r",\;", ";": r";\;"}.get(txt, txt))
                self.i += 1; prev_kind = "op"; continue
            if kind == "op" and txt == "-":
                unary = prev_kind in (None, "op")
                flush(); out.append("{-}" if unary else "-"); self.i += 1; prev_kind = "op"; continue
            if kind == "op" and txt == "*":
                self.i += 1
                nxt = self.peek()
                last = run[-1][0] if run else ""
                run.append((r"\times " if (re.search(r"\d$", last) and nxt[0] == "num") else r"\,", None))
                prev_kind = "op"; continue
            if kind == "op" and txt == "/":
                self.i += 1
                den = self.atom()
                if den is None:
                    raise Bad("missing denominator")
                num = run[-1] if run else ("1", None)
                if run and run[-1][1] is None and len(run) >= 1 and run[-1][0] in (r"\,", r"\times "):
                    raise Bad("bad numerator")
                # numerator = the whole juxtaposed run so far (3x/2 -> frac(3x, 2))
                items = [r for r in run]
                ntex = items[0][1] if len(items) == 1 and items[0][1] is not None else "".join(r[0] for r in items) or "1"
                dtex = den[1] if den[1] is not None else den[0]
                run.clear()
                run.append((("\\frac{" if (self.exp or not self.display) else "\\dfrac{") + ntex + "}{" + dtex + "}", None))
                prev_kind = "atom"; continue
            a = self.atom()
            if a is None:
                raise Bad(f"unexpected {txt!r}")
            if run and re.match(r"\\(sin|cos|tan|cot|sec|ln|log|exp|mathrm\{cosec\})", a[0]) and run[-1][0] not in (r"\,", r"\times "):
                run.append((r"\,", None))
            run.append(a); prev_kind = "atom"
        flush()
        return "".join(out)

    def atom(self):
        kind, txt, _ = self.peek()
        if kind is None:
            return None
        lat, inner = None, None
        if kind == "num":
            self.i += 1; lat = txt
        elif kind == "unit":
            self.i += 1; return (r"\ " + UNITS.get(txt, r"\mathrm{" + txt + "}"), None)
        elif kind == "deg":
            self.i += 1; return (r"^{\circ}", None)
        elif kind == "var":
            self.i += 1
            if txt in "ij" and txt:
                lat = r"\mathbf{" + txt + "}"
            else:
                lat = txt
        elif kind == "word":
            self.i += 1
            if txt == "pi":
                lat = r"\pi"
            elif txt == "sqrt":
                if not self.is_op("("):
                    raise Bad("sqrt needs (")
                self.i += 1
                body = self.expr(closers=(")",)); self.eat(")")
                lat = r"\sqrt{" + body + "}"
            elif txt == "abs":
                if not self.is_op("("):
                    raise Bad("abs needs (")
                self.i += 1
                body = self.expr(closers=(")",)); self.eat(")")
                lat = r"\left|" + body + r"\right|"
            else:
                name = FUNCS[txt]
                sub = ""
                if txt == "log" and self.is_op("_"):
                    self.i += 1
                    b = self.peek()
                    if b[0] not in ("num", "var"):
                        raise Bad("log base")
                    self.i += 1; sub = "_{" + b[1] + "}"
                pw = ""
                if self.is_op("^"):          # sin^2 x
                    self.i += 1; pw = "^{" + self.exponent() + "}"
                if self.is_op("("):
                    self.i += 1
                    body = self.expr(closers=(")",)); self.eat(")")
                    if not pw and self.is_op("^"):   # sec(5x + 5)^2 means sec^2(5x + 5)
                        self.i += 1; pw = "^{" + self.exponent() + "}"
                    return (name + sub + pw + "(" + body + ")", None)
                return (name + sub + pw + r"\,", None)
        elif kind == "op" and txt == "(":
            self.i += 1
            body = self.expr(closers=(")",)); self.eat(")")
            lat, inner = "(" + body + ")", body
        elif kind == "op" and txt == "|":
            self.i += 1
            body = self.expr(closers=("|",)); self.eat("|")
            lat = r"\left|" + body + r"\right|"
        elif kind == "op" and txt == "-":     # unary minus on an atom (exponent / denominator)
            self.i += 1
            a = self.atom()
            if a is None:
                raise Bad("dangling -")
            return ("{-}" + a[0], None)
        else:
            return None
        while self.is_op("^"):
            self.i += 1
            lat = "{" + lat + "}" + "^{" + self.exponent() + "}" if lat.startswith("\\mathbf") else lat + "^{" + self.exponent() + "}"
            inner = None
        if self.is_op("_") and False:
            pass
        return (lat, inner)

    def exponent(self):
        self.exp += 1
        try:
            return self._exponent()
        finally:
            self.exp -= 1

    def _exponent(self):
        if self.is_op("("):
            self.i += 1
            body = self.expr(closers=(")",)); self.eat(")")
            return body
        neg = ""
        if self.is_op("-"):
            self.i += 1; neg = "-"
        kind, txt, _ = self.peek()
        if kind == "num":
            self.i += 1; return neg + txt
        if kind == "var":
            self.i += 1; return neg + txt
        if kind == "word" and txt == "pi":
            self.i += 1; return neg + r"\pi"
        raise Bad("bad exponent")

    def eat(self, ch):
        if not self.is_op(ch):
            raise Bad(f"expected {ch}")
        self.i += 1


def to_mathtext(span):
    """Plain-text maths -> a mathtext body (no dollar signs). Raises Bad on anything odd."""
    span = span.replace("log_", "log_")
    span = re.sub(r"log base (\w+) of ", r"log_\1 ", span)
    toks = lex(span)
    p = Parser(toks)
    out = p.expr()
    if p.i != len(toks):
        raise Bad("leftover tokens")
    return out


# ---------------------------------------------------------------- split a sentence into text and maths
OPS = {"+", "-", "=", "<", ">", "<=", ">=", ":"}
SINGLE_MATH = set("bcdefghijklmnopqrstuvwxyz") - {"a"}      # lone lowercase letters (a is handled separately)
TWO_MATH = {"ax", "bx", "cx", "xy", "ai", "bj", "aj", "bi", "kj", "ki", "mj", "nj", "kx", "ky", "mx", "nx"}
CAP_TEXT = {"AP", "GP", "A", "I", "CAIE", "IGCSE", "OK"}
A_FOLLOWERS = {"is", "and", "to", "has", "lies", "are", "or", "be"}
TRAIL = ",.;:?!"
MATH_CHARS = set("^=/*|()<>+:_")


def tokenize(s):
    """Split on spaces that are outside brackets, so '(7, -3)' stays one token."""
    toks, cur, depth = [], "", 0
    for ch in s:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        if ch == " " and depth == 0:
            if cur:
                toks.append(cur); cur = ""
        else:
            cur += ch
    if cur:
        toks.append(cur)
    return toks


def strip_trail(tok):
    core, trail = tok, ""
    while core and core[-1] in TRAIL and core not in ("..",):
        trail = core[-1] + trail; core = core[:-1]
    return core, trail


def long_words(core):
    """True if the token contains a real word (3+ letters that are not a function name)."""
    for w in re.findall(r"[A-Za-z]{3,}", core):
        if w not in FUNCS and w not in ("sqrt", "abs", "pi", "cm", "mm", "km"):
            return True
    return False


def is_mathy(core, prev_core, next_core, tok_trail=""):
    if not core:
        return False
    if re.fullmatch(r"\d+(st|nd|rd|th)", core):
        return False
    if re.fullmatch(r"[A-Za-z]+-[A-Za-z]+", core):
        return False
    if core in OPS:
        return None            # decided by neighbours
    if core == "a" or core == "A":
        if next_core in A_FOLLOWERS or next_core in OPS or tok_trail == "," or (prev_core is not None and prev_core in OPS):
            return True
        return False
    if core in CAP_TEXT:
        return False
    if core in ("degrees", "degree"):
        return None
    if re.fullmatch(r"[A-Za-z]", core):
        return core in SINGLE_MATH or core.isupper()
    if core in TWO_MATH:
        return True
    if re.fullmatch(r"[A-Z]{2}", core):
        return True
    if core in UNITS:
        return None            # unit: math only after a number
    if any(ch.isdigit() for ch in core) or any(ch in MATH_CHARS for ch in core):
        if long_words(core):
            return False
        return True
    if core == "pi":
        return True
    if re.fullmatch(r"(?:sin|cos|tan|cot|sec|cosec|ln|log|exp|sqrt|abs)", core):
        return None            # a function name is maths only when something maths follows it
    return False


def split_sentence(text):
    """Return atoms: list of ('t', word) / ('m', plain_maths) with a glue flag for trailing punctuation."""
    text = re.sub(r"log base (\w+) of (\([^)]*\)|\w+)", lambda m: "log_" + m.group(1) + (m.group(2) if m.group(2).startswith("(") else "(" + m.group(2) + ")"), text)
    toks = tokenize(text)
    info = []
    for k, tok in enumerate(toks):
        core, trail = strip_trail(tok)
        prev_core = strip_trail(toks[k - 1])[0] if k else None
        next_core = strip_trail(toks[k + 1])[0] if k + 1 < len(toks) else None
        info.append([core, trail, is_mathy(core, prev_core, next_core, trail)])
    # resolve neighbour-dependent tokens
    for k, rec in enumerate(info):
        core, trail, m = rec
        if m is None:
            before = info[k - 1] if k else None
            after = info[k + 1] if k + 1 < len(info) else None
            b_ok = before is not None and before[2] is True and not before[1]
            a_ok = after is not None and after[2] is True
            if core in OPS:
                rec[2] = bool(b_ok and a_ok) or bool(a_ok and (before is None or before[2] is True))
            elif re.fullmatch(r"(?:sin|cos|tan|cot|sec|cosec|ln|log|exp|sqrt|abs)", core):
                rec[2] = bool(after is not None and after[2] is True)
            elif core in ("degrees", "degree"):
                rec[2] = bool(before is not None and before[2] is True and re.search(r"\d$", before[0]))
            else:   # unit
                rec[2] = bool(before is not None and before[2] is True and re.search(r"[\d\)xyt]$", before[0]) and not before[1])
    # x-axis style tokens
    atoms = []   # (kind, text, glue_left)
    k = 0
    cur = None
    for core, trail, m in info:
        if m:
            if cur is not None and cur[0] == "m" and not cur[3]:
                cur[1] += " " + core
            else:
                if cur is not None:
                    atoms.append(tuple(cur[:3]))
                cur = ["m", core, False, False]
            if trail:                      # punctuation ends the maths span
                atoms.append(tuple(cur[:3])); cur = None
                atoms.append(("t", trail, True))
        else:
            if cur is not None:
                atoms.append(tuple(cur[:3])); cur = None
            mm = re.fullmatch(r"([xyt])(-axis|-coordinate|-intercept|-values?)", core)
            if mm:
                atoms.append(("m", mm.group(1), False)); atoms.append(("t", mm.group(2) + trail, True))
            else:
                atoms.append(("t", core + trail, False))
    if cur is not None:
        atoms.append(tuple(cur[:3]))
    return atoms


# ---------------------------------------------------------------- drawing
plt.rcParams["font.family"] = "STIXGeneral"
plt.rcParams["mathtext.fontset"] = "stix"
DPI = 200
W_IN = 5.0
FS = 15.0
INK = "#1f2933"
MUTED = "#7b8794"
PAPER = "#fbfaf6"
LEVEL_COL = {"easy": "#2f9e6f", "medium": "#d98e04", "hard": "#d1495b"}


def build_chunks(text):
    """('t'|'m', plain, glue) -> (kind, drawable string, glue). Maths that fails to convert is drawn as plain italic text."""
    out = []
    for kind, s, glue in split_sentence(text):
        if kind == "m":
            try:
                body = to_mathtext(s)
                out.append(("m", "$" + body + "$", glue, s))
            except Bad:
                out.append(("t", s.replace("$", ""), glue, s))
        else:
            out.append(("t", s.replace("$", r"\$"), glue, s))
    return out


def safe_extent(renderer, fig, s, fs, bold=False):
    """Return (obj, width, ascent, descent) in pixels; falls back to plain text if mathtext rejects the string."""
    for cand in (s, re.sub(r"[$\\{}]", "", s)):
        try:
            t = fig.text(0, 0, cand, fontsize=fs, transform=None, va="baseline", ha="left",
                         fontweight="bold" if bold else "normal")
            bb = t.get_window_extent(renderer)
            return cand, bb.width, max(0.0, bb.y1), max(0.0, -bb.y0)
        except Exception:
            try:
                t.remove()
            except Exception:
                pass
    raise Bad("cannot draw " + s)


def layout(chunks, width_px, fs_px_pt, renderer, fig):
    """Greedy line wrap. Returns lines: list of (items, ascent, descent); item = (string, x_px)."""
    space = fs_px_pt * DPI / 72 * 0.27
    atoms, cur = [], None
    for kind, drawable, glue, plain in chunks:
        if glue and cur is not None:
            cur.append((kind, drawable))
        else:
            cur = [(kind, drawable)]; atoms.append(cur)
    lines, line, x, asc, desc = [], [], 0.0, 0.0, 0.0
    text_asc, text_desc = fs_px_pt * DPI / 72 * 0.78, fs_px_pt * DPI / 72 * 0.22
    for atom in atoms:
        measured = []
        total = 0.0
        a_asc, a_desc = text_asc, text_desc
        for kind, drawable in atom:
            cand, w, ya, yd = safe_extent(renderer, fig, drawable, fs_px_pt)
            for t in list(fig.texts):
                t.remove()
            measured.append((cand, w)); total += w
            if kind == "m":
                a_asc, a_desc = max(a_asc, ya), max(a_desc, yd)
        need = total + (space if line else 0)
        if line and x + need > width_px:
            lines.append((line, asc, desc)); line, x, asc, desc = [], 0.0, 0.0, 0.0
            need = total
        start = x + (space if line else 0)
        for cand, w in measured:
            line.append((cand, start)); start += w
        x = start
        asc, desc = max(asc, a_asc, text_asc), max(desc, a_desc, text_desc)
    if line:
        lines.append((line, asc, desc))
    return lines


def draw_card(text, title, level, qid, out_path):
    W = int(W_IN * DPI)
    pad = int(0.38 * DPI)
    body_w = W - 2 * pad
    fig0 = plt.figure(figsize=(W_IN, 4), dpi=DPI)
    renderer = fig0.canvas.get_renderer()
    lines = layout(build_chunks(text), body_w, FS, renderer, fig0)
    plt.close(fig0)

    gap = FS * DPI / 72 * 0.55
    head_h = int(0.62 * DPI)
    foot_h = int(0.46 * DPI)
    body_h = sum(a + d for _, a, d in lines) + gap * (len(lines) - 1)
    H = int(head_h + 0.30 * DPI + body_h + 0.30 * DPI + foot_h)

    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI)
    fig.patch.set_facecolor(PAPER)
    col = LEVEL_COL.get(level, MUTED)
    # header
    fig.patches.append(plt.Rectangle((0, H - 0.09 * DPI), W, 0.09 * DPI, transform=None, facecolor=col, edgecolor="none"))
    fig.text(pad, H - 0.40 * DPI, title, transform=None, fontsize=12.5, color=MUTED, va="center", ha="left", fontweight="bold")
    if level:
        fig.text(W - pad, H - 0.40 * DPI, level.upper(), transform=None, fontsize=11, color=col, va="center", ha="right", fontweight="bold")
    fig.add_artist(plt.Line2D([pad, W - pad], [H - head_h, H - head_h], transform=None, color="#e4e7eb", linewidth=1.0))
    # body
    y = H - head_h - 0.30 * DPI
    for items, asc, desc in lines:
        y -= asc
        for s, x in items:
            fig.text(pad + x, y, s, transform=None, fontsize=FS, color=INK, va="baseline", ha="left")
        y -= desc + gap
    # footer
    fig.add_artist(plt.Line2D([pad, W - pad], [foot_h, foot_h], transform=None, color="#e4e7eb", linewidth=1.0))
    if qid:
        fig.text(pad, foot_h * 0.5, "ID  " + qid, transform=None, fontsize=10, color=MUTED, va="center", ha="left", family="DejaVu Sans Mono")
    fig.text(W - pad, foot_h * 0.5, "Edith  |  CAIE 0606", transform=None, fontsize=10, color=MUTED, va="center", ha="right")
    fig.savefig(out_path, dpi=DPI, facecolor=PAPER)
    plt.close(fig)


def topic_title(q, gen):
    return gen.GEN[q["topic"]][1].split(":")[0].split(" (")[0]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("qid", nargs="?")
    ap.add_argument("--text")
    ap.add_argument("--title", default="Question")
    ap.add_argument("--level", default="")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    qid, level, title, text = None, a.level, a.title, a.text
    if a.qid:
        sys.path.insert(0, HERE)
        import gen
        q = gen.build(a.qid)
        qid, level, title, text = q["id"], q["level"], topic_title(q, gen), q["question"]
    if not text:
        raise Bad("give a question ID or --text")
    out_dir = os.path.join(ROOT, "plots")
    os.makedirs(out_dir, exist_ok=True)
    name = f"q_{qid}.png" if qid else f"q_text_{int(time.time() * 1000) % 10**9}.png"
    path = a.out or os.path.join(out_dir, name)
    draw_card(text, title, level, qid, path)
    if a.out:
        print(path)
    else:
        print(f"MEDIA:plots/{name}")


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Exception as ex:
        print("RENDER FAILED:", ex)
