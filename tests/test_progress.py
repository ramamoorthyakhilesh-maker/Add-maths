"""progress.py turns the call log into scores. Only real, finished questions count, and only the first outcome."""
import datetime, importlib, json
import pytest

NOW = datetime.datetime.now()


def ts(days=0, hours=0, minutes=0):
    return (NOW - datetime.timedelta(days=days, hours=hours) + datetime.timedelta(minutes=minutes)).isoformat(timespec="seconds")


def events():
    L = []

    def add(t, *args, result=""):
        L.append({"ts": t, "args": list(args), "result": result})
    add(ts(1, 5), "new", "diff", "easy", result="ID: diff-easy-1  (Differentiation, easy)")
    add(ts(1, 4), "check", "diff-easy-1", "x", result="CORRECT")                                   # clean
    add(ts(1, 3), "check", "diff-easy-2", "x", result="INCORRECT"); add(ts(1, 3, 1), "check", "diff-easy-2", "y", result="CORRECT")   # needed help
    add(ts(1, 2), "check", "diff-medium-3", "z", result="INCORRECT")
    add(ts(1, 2, 1), "hint", "diff-medium-3", "1", result="HINT 1"); add(ts(1, 2, 3), "reveal", "diff-medium-3", result="ID: diff-medium-3")   # revealed
    add(ts(1, 1), "hint", "quad-easy-4", "1", result="HINT 1"); add(ts(1, 1, 1), "check", "quad-easy-4", "k", result="CORRECT")   # hint then right
    add(ts(1, 0, 30), "check", "trig-medium-5", "a", result="AMBIGUOUS: x"); add(ts(1, 0, 29), "check", "trig-medium-5", "b", result="CORRECT")
    add(ts(1, 0, 20), "check", "log-easy-6", "??", result="COULD NOT READ THE ANSWER: x"); add(ts(1, 0, 19), "check", "log-easy-6", "3", result="CORRECT")
    add(ts(1, 0, 10), "new", "simul", "easy", result="ID: simul-easy-7  (x)")                      # asked, never attempted
    add(ts(0, 3), "check", "perm-easy-8", "5", result="CORRECT"); add(ts(0, 3, 1), "reveal", "perm-easy-8", result="ID: perm-easy-8")
    add(ts(30), "check", "integ-easy-9", "1", result="INCORRECT"); add(ts(30, 0, 1), "reveal", "integ-easy-9", result="ID: integ-easy-9")
    add(ts(0, 0, -5), "hint", "stat-easy-10", "1", result="HINT 1")                                  # still open
    add(ts(3), "hint", "binom-easy-11", "1", result="HINT 1")                                        # abandoned
    add(ts(1), "check", "banana-easy-5", "1", result="CORRECT"); add(ts(1), "check", "nonsense", "1", result="GEN FAILED: Bad id")
    add(ts(0, 2), "check", "factor-easy-13", "1", result="CORRECT"); add(ts(0, 1), "check", "factor-easy-13", "2", result="INCORRECT")
    return L


@pytest.fixture
def progress(tmp_path, monkeypatch):
    p = tmp_path / "g.jsonl"
    p.write_text("\n".join(json.dumps(x) for x in events()) + "\nthis line is not json\n", encoding="utf-8")
    monkeypatch.setenv("EDITH_LOG", str(p))
    import progress as mod
    return importlib.reload(mod)


def questions(pr):
    evs = pr.load_events(); topics = pr.known_topics()
    return {q["id"]: q for q in pr.build_questions(evs, topics)}


def test_scores(progress):
    ids = questions(progress)
    want = {"diff-easy-1": 1.0, "diff-easy-2": 0.5, "diff-medium-3": 0.0, "quad-easy-4": 0.5, "trig-medium-5": 1.0, "log-easy-6": 1.0,
            "perm-easy-8": 1.0, "integ-easy-9": 0.0, "binom-easy-11": 0.0, "factor-easy-13": 1.0}
    for k, v in want.items():
        assert progress.score(ids[k], NOW) == v, k


def test_junk_is_ignored(progress):
    ids = questions(progress)
    for k in ("simul-easy-7", "banana-easy-5", "nonsense"):
        assert k not in ids, k
    assert progress.score(ids["stat-easy-10"], NOW) is None      # open question is not scored


def test_commands_run(progress, capsys):
    for args in (["stats"], ["stats", "diff"], ["next"], ["history", "6"], ["stats", "bogus"]):
        progress.main(args)
    out = capsys.readouterr().out
    assert out.strip()
    assert "RUN" in out                                          # next prints a command Edith can run
    assert "Traceback" not in out


def test_empty_log_is_fine(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("EDITH_LOG", str(tmp_path / "missing.jsonl"))
    import progress as mod
    importlib.reload(mod).main(["stats"])
    assert "Traceback" not in capsys.readouterr().out
