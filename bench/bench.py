"""Edith benchmark: how well do free OpenRouter models solve 0606-style questions on their own?

It sends questions from tools/gen.py to each model, with NO tools and NO hints, and scores the final answer with the same
checker Edith uses. The result is a number you can quote ("model X solved 71% of 69 questions") and an order for the fallback chain.
This measures the raw models. It is a floor for Edith, who also has the generator, the checker and the syllabus notes.

Needs OPENROUTER_API_KEY in the environment (it is never written to disk). Standard library only, plus the sympy that tools/gen.py needs.

  python bench/bench.py list-free                         show free models that OpenRouter lists right now
  python bench/bench.py run --models-file bench/models.txt [--per-cell 1] [--max-requests 45]
  python bench/bench.py report                            write bench/REPORT.md from the saved results
  python bench/bench.py run --dry-run ...                 count the requests without sending any

Free models are limited to 20 requests per minute and, on an account with under 10 USD of credits ever bought, 50 per day (1000 per day above that).
The run stops cleanly when the day limit is hit. Run it again tomorrow: finished (model, question) pairs are skipped.
"""
import os, sys, re, json, time, math, random, argparse, urllib.request, urllib.error, statistics, datetime, collections

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))
import gen  # noqa: E402

BASE = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
SCALE = float(os.environ.get("BENCH_BACKOFF_SCALE", "1"))   # tests set this near 0 so retries do not wait

def nap(sec): time.sleep(sec * SCALE)
SYSTEM = ("You are solving a question from the CAIE IGCSE Additional Mathematics (0606) syllabus. "
          "Work it out step by step, briefly. Then write the final answer alone on the LAST line, exactly in this form:\n"
          "ANSWER: <your answer>\n"
          "Use plain text only, no LaTeX: x^2, sqrt(3), pi, e^(2x), ln(5), fractions like 3/4. "
          "Follow the answer format the question asks for, for example (a, b) or x < 2 or x > 5. Do not write anything after the ANSWER line.")

# ---------- question suite ----------
def suite(topics, levels, per_cell, seed0):
    qs = []
    for i in range(per_cell):
        for lv in levels:
            for t in topics:
                qs.append(f"{t}-{lv}-{seed0 + len(qs)}")
    return qs

# ---------- cleaning model output ----------
def _braces(s, cmd, fmt_):
    pat = re.compile(r"\\" + cmd + r"\s*\{([^{}]*)\}")
    while True:
        n = pat.sub(fmt_, s)
        if n == s: return s
        s = n

def delatex(a):
    a = a.strip().strip("*").strip()
    a = re.sub(r"\\(?:boxed|text|mathrm|mathbf)\s*\{([^{}]*)\}", r"\1", a)
    for _ in range(4):
        a = re.sub(r"\\[dt]?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}", r"(\1)/(\2)", a)
        a = re.sub(r"\\sqrt\s*\{([^{}]*)\}", r"sqrt(\1)", a)
        a = re.sub(r"\^\s*\{([^{}]*)\}", r"^(\1)", a)
        a = re.sub(r"_\s*\{([^{}]*)\}", r"_\1", a)
    for k, v in ((r"\left", ""), (r"\right", ""), (r"\,", ""), (r"\;", ""), (r"\!", ""), (r"\ ", " "), ("$", ""), (r"\(", ""), (r"\)", ""),
                 (r"\[", ""), (r"\]", ""), (r"\pi", "pi"), (r"\times", "*"), (r"\cdot", "*"), (r"\leq", "<="), (r"\geq", ">="), (r"\le", "<="), (r"\ge", ">="),
                 (r"\ln", "ln"), (r"\sin", "sin"), (r"\cos", "cos"), (r"\tan", "tan"), (r"\pm", "\u00b1"), (r"^\circ", ""), ("^{\\circ}", ""), ("\u00b0", ""),
                 (r"\infty", "oo"), ("{", "("), ("}", ")"), ("\\", "")):
        a = a.replace(k, v)
    a = a.replace("**", "^")
    return a.strip().rstrip(".").strip()

def extract(text):
    if not text: return None
    m = re.findall(r"(?im)^[\s>*#_`$\\(\[]*(?:final\s+)?answer\s*[:=]\s*(.+?)\s*$", text)
    if not m:
        b = re.findall(r"\\boxed\s*\{(.+)\}", text)
        if not b: return None
        m = b
    return delatex(m[-1])

# ---------- HTTP ----------
class DayLimit(Exception): pass
class AuthError(Exception): pass

def http(path, body=None, key=None, timeout=180):
    req = urllib.request.Request(BASE + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "HTTP-Referer": "https://github.com/", "X-Title": "Edith benchmark",
                                          **({"Authorization": "Bearer " + key} if key else {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))

def ask(model, question, key, timeout, max_tokens):
    body = {"model": model, "temperature": 0, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]}
    for attempt in range(4):
        try:
            d = http("/chat/completions", body, key, timeout)
            if "error" in d and "choices" not in d:
                msg = json.dumps(d["error"])[:400]
                if "per-day" in msg or "per_day" in msg: raise DayLimit(msg)
                if attempt < 3: nap(10 * (attempt + 1)); continue
                return None, msg
            m = d["choices"][0]["message"]
            return (m.get("content") or ""), None
        except urllib.error.HTTPError as e:
            txt = e.read().decode("utf-8", "replace")[:500]
            if e.code in (401, 403): raise AuthError(f"HTTP {e.code}: {txt[:200]}")
            if e.code == 429:
                if "per-day" in txt or "per_day" in txt: raise DayLimit(txt)
                wait = int(e.headers.get("Retry-After", "0") or 0) or 20 * (attempt + 1)
                if attempt < 3: nap(min(wait, 90)); continue
            elif e.code in (500, 502, 503, 504) and attempt < 2: nap(8 * (attempt + 1)); continue
            return None, f"HTTP {e.code}: {txt[:200]}"
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt < 2: nap(8 * (attempt + 1)); continue
            return None, f"network: {e}"
    return None, "gave up"

# ---------- storage ----------
def load(path):
    done = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            try: r = json.loads(line)
            except Exception: continue
            done[(r["model"], r["qid"])] = r
    return done

def score(q, ans):
    if ans is None: return 0.0, "NO ANSWER LINE"
    v = gen.verdict(q, ans)
    return (1.0 if v == "CORRECT" else 0.0), v.split(":")[0]

# ---------- commands ----------
def models_from(a):
    ms = []
    if a.models: ms += [m.strip() for m in a.models.split(",") if m.strip()]
    if a.models_file:
        for line in open(a.models_file, encoding="utf-8"):
            line = line.split("#")[0].strip()
            if line: ms.append(line)
    ms = [m[len("openrouter/"):] if m.startswith("openrouter/") else m for m in ms]
    return list(dict.fromkeys(ms))

def cmd_list_free(a):
    d = http("/models", None, os.environ.get("OPENROUTER_API_KEY"))
    rows = []
    for m in d.get("data", []):
        p = m.get("pricing") or {}
        try: free = float(p.get("prompt", 1)) == 0 and float(p.get("completion", 1)) == 0
        except (TypeError, ValueError): free = False
        if free or m["id"].endswith(":free"): rows.append((m["id"], m.get("context_length", "?")))
    for i, c in sorted(rows): print(f"{i:60} context {c}")
    print(f"{len(rows)} free models listed")

def cmd_run(a):
    key = os.environ.get("OPENROUTER_API_KEY")
    models = models_from(a)
    if not models: sys.exit("No models. Use --models a,b or --models-file bench/models.txt")
    topics = a.topics.split(",") if a.topics else list(gen.GEN)
    levels = a.levels.split(",")
    qids = suite(topics, levels, a.per_cell, a.seed)
    out = a.out; done = load(out)
    todo = [(qid, m) for qid in qids for m in models if (m, qid) not in done or done[(m, qid)].get("error")]
    print(f"{len(qids)} questions x {len(models)} models = {len(qids) * len(models)} pairs; {len(qids) * len(models) - len(todo)} already done; {len(todo)} to do.")
    print(f"This run will send at most {a.max_requests} requests (daily free limit is 50 under 10 USD of credits ever bought, 1000 above).")
    if a.dry_run: return
    if not key and "openrouter.ai" in BASE: sys.exit("Set OPENROUTER_API_KEY first.")
    try:
        listed = {m["id"] for m in http("/models", None, key).get("data", [])}
        for m in models:
            if m not in listed: print(f"WARNING: {m} is not in OpenRouter's model list right now (run list-free). Its requests will probably fail.")
    except Exception as e: print("Could not fetch the model list:", e)
    gap = 60.0 / a.rpm; sent = 0; last = 0.0
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "a", encoding="utf-8") as fh:
        for qid, m in todo:
            if sent >= a.max_requests: print("Request budget for this run used. Run again to continue."); break
            q = gen.build(qid)
            wait = gap - (time.time() - last)
            if wait > 0: time.sleep(wait)
            t0 = time.time(); last = t0; sent += 1
            try: raw, err = ask(m, q["question"], key, a.timeout, a.max_tokens)
            except DayLimit as e:
                print("Daily free-model limit reached. Stopping. Run again tomorrow.\n", str(e)[:200]); break
            except AuthError as e:
                print("STOPPED: OpenRouter rejected the API key (", str(e)[:160], ").\nCheck that OPENROUTER_API_KEY is set in THIS PowerShell window and that the key is correct and not revoked. Nothing was recorded for this request."); break
            lat = round(time.time() - t0, 1)
            ans = extract(raw) if raw is not None else None
            sc, vd = score(q, ans) if err is None else (0.0, "ERROR")
            rec = {"model": m, "qid": qid, "topic": q["topic"], "level": q["level"], "question": q["question"], "raw_tail": (raw or "")[-300:],
                   "extracted": ans, "verdict": vd, "score": sc, "latency": lat, "error": err, "ts": datetime.datetime.now().isoformat(timespec="seconds")}
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n"); fh.flush()
            print(f"[{sent}/{min(len(todo), a.max_requests)}] {m.split('/')[-1][:34]:34} {qid:22} {'OK ' if sc else 'no '} {vd:14} {lat}s")
    bad = sum(1 for r in load(out).values() if r.get("error"))
    if bad: print(f"WARNING: {bad} recorded requests failed with an error (not a wrong answer). They are retried the next time you run this command.")
    print("Done. Results are in", out, "\nNext: python bench/bench.py report")

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (c - s) / d), min(1.0, (c + s) / d)

def cmd_report(a):
    rs = [r for r in load(a.out).values()]
    if not rs: sys.exit("No results yet.")
    models = sorted({r["model"] for r in rs})
    by = collections.defaultdict(dict)
    for r in rs:
        if not r.get("error"): by[r["model"]][r["qid"]] = r
    common = set.intersection(*[set(by[m]) for m in models]) if models else set()
    lines = ["# Edith benchmark report", "", f"Generated {datetime.date.today().isoformat()}. Raw models, no tools, no hints, temperature 0.",
             f"Questions answered by every model (the fair comparison set): {len(common)}. Models: {len(models)}.", ""]
    if len(common) < 10:
        lines += ["> Fewer than 10 common questions. Treat every number below as a rough guide only.", ""]
    rows = []
    for m in models:
        rr = [by[m][q] for q in common]; n = len(rr); k = sum(r["score"] for r in rr)
        lo, hi = wilson(k, n); lat = [r["latency"] for r in rr if r["latency"]]
        unread = sum(1 for r in rr if r["verdict"] in ("NO ANSWER LINE", "COULD NOT READ THE ANSWER", "AMBIGUOUS", "NOT EXACT"))
        errs = sum(1 for r in rs if r["model"] == m and r.get("error"))
        rows.append((m, k, n, lo, hi, statistics.median(lat) if lat else float("nan"), unread, errs))
    rows.sort(key=lambda r: (-(r[1] / r[2] if r[2] else 0), r[5]))
    cov = {m: len(by[m]) for m in models}; top = max(cov.values())
    short = [f"{m} ({cov[m]}/{top})" for m in models if cov[m] < top]
    if short: lines += ["> Coverage is uneven, so the common set is small: " + ", ".join(short) + ". Run `bench.py run` again to finish them.", ""]
    lines += ["## Overall (common set)", "", "| Rank | Model | Correct | Accuracy | 95% interval | Median seconds | Format failures | Request errors |", "|---|---|---|---|---|---|---|---|"]
    for i, (m, k, n, lo, hi, med, un, er) in enumerate(rows, 1):
        lines.append(f"| {i} | {m} | {int(k)}/{n} | {100 * k / n:.0f}% | {100 * lo:.0f}% to {100 * hi:.0f}% | {'-' if med != med else format(med, '.0f')} | {un} | {er} |")
    lines += ["", "Format failures are answers the checker could not read, or answers with a missing ANSWER line, ambiguous division, or a decimal where an exact value was needed. They count as wrong.", ""]
    for key, label in (("level", "Accuracy by level"), ("topic", "Accuracy by topic")):
        cats = sorted({by[models[0]][q][key] for q in common}, key=(lambda c: gen.LEVELS.index(c)) if key == "level" else None)
        lines += [f"## {label}", "", "| " + key + " | " + " | ".join(m.split("/")[-1][:22] for m in models) + " |", "|---|" + "---|" * len(models)]
        for c in cats:
            cells = []
            for m in models:
                rr = [by[m][q] for q in common if by[m][q][key] == c]
                cells.append(f"{sum(r['score'] for r in rr):.0f}/{len(rr)}")
            lines.append(f"| {c} | " + " | ".join(cells) + " |")
        lines.append("")
    lines += ["## Suggested fallback order", "", "Highest accuracy first, ties broken by speed. Drop models with a wide interval and low accuracy, and models with many request errors:", ""]
    lines += [f"{i}. {r[0]}" for i, r in enumerate(rows, 1)]
    lines += ["", "## What this does and does not show", "",
              "- It measures raw model arithmetic and algebra on generated 0606-style questions. Edith also has the question generator, the answer checker and the syllabus notes, so her real accuracy on practice questions is higher than these numbers.",
              "- It does not measure how well a model teaches. Read a few chat transcripts for that.",
              "- Small samples are noisy. The interval column shows how much. Free models also change or disappear, so re-run before quoting a result.",
              f"- Questions come from tools/gen.py with fixed seeds, so the run can be repeated exactly (suite seed shown in the results file IDs)."]
    open(a.md, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines[:22])); print("... full report written to", a.md)

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list-free")
    r = sub.add_parser("run")
    r.add_argument("--models"); r.add_argument("--models-file"); r.add_argument("--topics"); r.add_argument("--levels", default="easy,medium,hard")
    r.add_argument("--per-cell", type=int, default=1); r.add_argument("--seed", type=int, default=7000)
    r.add_argument("--max-requests", type=int, default=45); r.add_argument("--rpm", type=float, default=15)
    r.add_argument("--timeout", type=int, default=180); r.add_argument("--max-tokens", type=int, default=3000)
    r.add_argument("--out", default=os.path.join(HERE, "results.jsonl")); r.add_argument("--dry-run", action="store_true")
    q = sub.add_parser("report"); q.add_argument("--out", default=os.path.join(HERE, "results.jsonl")); q.add_argument("--md", default=os.path.join(HERE, "REPORT.md"))
    a = p.parse_args()
    {"list-free": cmd_list_free, "run": cmd_run, "report": cmd_report}[a.cmd](a)

if __name__ == "__main__":
    main()
