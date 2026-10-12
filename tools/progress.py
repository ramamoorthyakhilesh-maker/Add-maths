"""Edith progress tracker. Reads logs/gen_calls.jsonl (written by gen.py) and reports how the student is doing.

Usage:
  python progress.py stats             every topic, weakest first
  python progress.py stats <topic>     one topic, split by level
  python progress.py next              suggest the next topic and level to practise
  python progress.py history [n]       the last n questions (default 10)

Scoring, one score per question (hints are allowed, but they cost marks):
  1.0  solved on the first check with no hint
  0.5  solved after a wrong check or after a hint
  0.0  not solved: the answer was revealed first, or the question was left more than a day ago
Questions that were only asked, or are still open today, are not scored.
Recent work counts more: a question's weight halves every 14 days.
Mastery is smoothed, so one or two questions never swing a topic to 0% or 100%.
"""
import sys, os, json, datetime, collections

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.environ.get("EDITH_LOG") or os.path.join(os.path.dirname(HERE), "logs", "gen_calls.jsonl")
LEVELS = ("easy", "medium", "hard")
HALF_LIFE_DAYS = 14.0
PRIOR, PRIOR_N = 0.5, 2.0       # smoothing: act as if there were 2 earlier questions at 50%
MASTERED = 0.7                  # a level counts as mastered at 70% with at least 2 scored questions
ABANDON_AFTER = datetime.timedelta(days=1)

def known_topics():
    try:
        sys.path.insert(0, HERE)
        from gen import GEN
        return list(GEN)
    except Exception:
        return []

def load_events():
    out = []
    if not os.path.exists(LOG): return out
    with open(LOG, encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
                out.append((datetime.datetime.fromisoformat(d["ts"]), d["args"], d.get("result", "")))
            except Exception:
                continue
    out.sort(key=lambda e: e[0])
    return out

def parse_id(qid):
    p = str(qid).split("-")
    if len(p) == 3 and p[1] in LEVELS and p[2].isdigit(): return p[0], p[1]
    return None

def build_questions(events, topics):
    qs = collections.OrderedDict()
    for ts, a, r in events:
        if len(a) < 2 or a[0] not in ("check", "hint", "reveal"): continue
        pid = parse_id(a[1])
        if not pid or (topics and pid[0] not in topics): continue
        q = qs.setdefault(a[1], {"id": a[1], "topic": pid[0], "level": pid[1], "last": ts, "wrong": 0, "hints": 0,
                                 "solved": False, "helped": False, "revealed": False})
        q["last"] = ts
        if q["solved"]: continue                      # anything after the solve is review, not scored
        if a[0] == "check":
            if r == "CORRECT":
                q["solved"] = True
                q["helped"] = q["wrong"] > 0 or q["hints"] > 0 or q["revealed"]
            elif r == "INCORRECT":
                q["wrong"] += 1                       # AMBIGUOUS and COULD NOT READ are ignored on purpose
        elif a[0] == "hint":
            if "No more hints" not in r: q["hints"] += 1
        elif a[0] == "reveal":
            q["revealed"] = True
    return list(qs.values())

def score(q, now):
    if q["solved"]: return 0.5 if q["helped"] else 1.0
    if q["revealed"]: return 0.0
    if now - q["last"] > ABANDON_AFTER and (q["wrong"] or q["hints"]): return 0.0
    return None                                       # still open, not scored

def status(q, now):
    if q["solved"]: return "solved with help" if q["helped"] else "solved clean"
    if q["revealed"]: return "answer revealed, not solved"
    if now - q["last"] > ABANDON_AFTER: return "left unsolved"
    return "open"

def agg(items, now):
    w = s = 0.0; n = clean = helped = failed = 0
    for q in items:
        sc = score(q, now)
        if sc is None: continue
        ww = 0.5 ** (((now - q["last"]).total_seconds() / 86400.0) / HALF_LIFE_DAYS)
        w += ww; s += ww * sc; n += 1
        if sc == 1.0: clean += 1
        elif sc == 0.5: helped += 1
        else: failed += 1
    mastery = (s + PRIOR * PRIOR_N) / (w + PRIOR_N)
    raw = (s / w) if w else 0.0
    return {"n": n, "clean": clean, "helped": helped, "failed": failed, "mastery": mastery, "raw": raw}

def ago(ts, now):
    d = (now - ts).total_seconds()
    if d < 3600: return f"{max(1, int(d // 60))}m ago"
    if d < 86400: return f"{int(d // 3600)}h ago"
    return f"{int(d // 86400)}d ago"

def by_topic(qs):
    g = collections.defaultdict(list)
    for q in qs: g[q["topic"]].append(q)
    return g

def plural(n, word): return f"{n} {word}" + ("" if n == 1 else "s")

def line(name, a, last, now):
    return (f"{name}: {round(a['mastery'] * 100)}% mastery ({plural(a['n'], 'question')}: {a['clean']} clean, "
            f"{a['helped']} with help, {a['failed']} not solved), last {ago(last, now)}")

def level_for(items, now):
    for lv in LEVELS:
        a = agg([q for q in items if q["level"] == lv], now)
        if a["n"] < 2 or a["raw"] < MASTERED: return lv, a
    return "hard", agg([q for q in items if q["level"] == "hard"], now)

def cmd_stats(qs, topics, now, only=None):
    g = by_topic(qs)
    if only:
        if topics and only not in topics: print(f"Unknown topic '{only}'. Topics: {', '.join(topics)}"); return
        items = g.get(only, [])
        if not [q for q in items if score(q, now) is not None]: print(f"No scored questions for {only} yet."); return
        print(f"{only}, by level:")
        for lv in LEVELS:
            li = [q for q in items if q["level"] == lv]; a = agg(li, now)
            if a["n"]: print("  " + line(lv, a, max(q["last"] for q in li), now))
            else: print(f"  {lv}: not tried")
        lv, _ = level_for(items, now); print(f"Next level to practise: {lv}"); return
    rows, untried = [], []
    for t in (topics or sorted(g)):
        items = g.get(t, []); a = agg(items, now)
        if a["n"]: rows.append((a["mastery"], t, a, max(q["last"] for q in items)))
        else: untried.append(t)
    if not rows and not untried: print("No attempts logged yet."); return
    print("Progress, weakest first:")
    for m, t, a, last in sorted(rows): print(line(t, a, last, now))
    if untried: print("Not tried yet: " + ", ".join(untried))
    tot = agg([q for q in qs], now)
    print(f"Overall: {plural(tot['n'], 'scored question')}, {tot['clean']} clean, {tot['helped']} with help, {tot['failed']} not solved.")

def cmd_next(qs, topics, now):
    g = by_topic(qs); ranked = []
    for t in (topics or sorted(g)):
        items = g.get(t, []); a = agg(items, now)
        last = max((q["last"] for q in items), default=datetime.datetime.min)
        ranked.append((a["mastery"], last, t, a))
    if not ranked: print("No topics found."); return
    ranked.sort(key=lambda r: (r[0], r[1]))
    m, last, t, a = ranked[0]; lv, la = level_for(g.get(t, []), now)
    if a["n"] == 0: why = f"{t} has not been tried yet."
    else: why = f"{t} is the weakest topic at {round(m * 100)}% mastery ({plural(a['n'], 'question')})."
    print(f"SUGGEST: {t} {lv}")
    print(f"WHY: {why} " + (f"{lv} is the first level not yet mastered." if la["n"] or lv == "easy" else ""))
    print(f"RUN: python tools/gen.py new {t} {lv}")
    if len(ranked) > 1: print("AFTER THAT: " + ", ".join(r[2] for r in ranked[1:3]))

def cmd_history(qs, now, n):
    if not qs: print("No questions logged yet."); return
    for q in sorted(qs, key=lambda q: q["last"], reverse=True)[:n]:
        print(f"{q['last'].strftime('%Y-%m-%d %H:%M')}  {q['id']}  {status(q, now)}"
              + (f"  ({q['wrong']} wrong, {plural(q['hints'], 'hint')})" if q["wrong"] or q["hints"] else ""))

def main(a):
    if not a or a[0] in ("-h", "--help"): print(__doc__); return
    if not os.path.exists(LOG): print(f"No log yet at {LOG}. Answer a question through Edith first."); return
    now = datetime.datetime.now(); topics = known_topics()
    qs = build_questions(load_events(), topics)
    c = a[0]
    if c == "stats": cmd_stats(qs, topics, now, a[1] if len(a) > 1 else None)
    elif c == "next": cmd_next(qs, topics, now)
    elif c == "history": cmd_history(qs, now, int(a[1]) if len(a) > 1 else 10)
    else: print(__doc__)

if __name__ == "__main__":
    try: main(sys.argv[1:])
    except Exception as ex: print("PROGRESS FAILED:", ex)