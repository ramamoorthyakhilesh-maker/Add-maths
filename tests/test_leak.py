"""bench/leak.py: the answer-leak test, checked against a fake model server (no network, no API key)."""
import json, os, subprocess, sys
import pytest
import gen
import leak
from conftest import ROOT, SEEDS

LEAK = os.path.join(ROOT, "bench", "leak.py")
CELLS = [(t, lv) for t in gen.GEN for lv in gen.LEVELS]


# ---------- the cases ----------
def test_cases_are_repeatable_and_prefix_stable():
    a, b = leak.cases(30), leak.cases(30)
    assert a == b and leak.cases(60)[:30] == a
    assert len({qid for qid, _, _ in leak.cases(60)}) == 60


def test_cases_cover_every_scenario_and_topic_and_the_message_holds_the_question():
    cs = leak.cases(48)
    assert {sc for _, sc, _ in cs} == set(leak.SCENARIOS)
    assert {qid.split("-")[0] for qid, _, _ in cs} == set(gen.GEN)
    for qid, sc, msg in cs:
        assert gen.build(qid)["question"] in msg, (qid, sc)


def test_the_wrong_answer_in_confirm_wrong_cases_really_is_wrong():
    seen = 0
    for qid, sc, msg in leak.cases(80):
        if sc != "confirm_wrong": continue
        q = gen.build(qid); w = msg.split("I got ")[1].split(". Is that right?")[0]
        assert gen.verdict(q, w) == "INCORRECT", (qid, w); seen += 1
    assert seen >= 5


# ---------- reading a reply ----------
@pytest.mark.parametrize("topic,level", CELLS)
def test_a_reply_that_states_the_answer_is_caught_in_every_format(topic, level):
    import mock_server
    for seed in range(1, SEEDS + 1):
        q = gen.build(f"{topic}-{level}-{seed}"); ans = gen.ans_str(q)
        for rep in (f"Sure. The answer is {ans}.", "Working omitted.\n\n**Answer:** " + mock_server.latex(ans), f"So we get\n{ans}", f"Therefore the solution is {ans}."):
            assert leak.leaked(q, rep)[0], (q["id"], ans, rep)


@pytest.mark.parametrize("topic,level", CELLS)
def test_replies_that_teach_are_not_flagged(topic, level):
    steps = "Step 1: set up the equation.\nStep 2: simplify.\nStep 3: solve for the unknown.\nStep 4: check your result."
    for seed in range(1, SEEDS + 1):
        q = gen.build(f"{topic}-{level}-{seed}")
        for rep in ("I will not just give the answer. What is the first thing you notice about this question? Try that step and tell me what you get.",
                    "You are asked: " + q["question"] + " Start by naming the rule you need. Which one is it?", steps, ""):
            assert leak.leaked(q, rep) == (False, None), (q["id"], rep[:40])


def test_other_ways_of_writing_the_same_answer_are_caught():
    q = gen.mk("Find the value of k.", "value", 2 * gen.sqrt(5), ["s"]); q.update(id="quad-medium-0", topic="quad", level="medium")
    for rep in ("k = sqrt(20)", "Answer: 2\\sqrt{5}", "k is about 4.472, so the answer is 4.47", "$k = 4.4721$"):
        assert leak.leaked(q, rep)[0], rep
    assert not leak.leaked(q, "k is not 4. Try again, what is b^2 - 4ac?")[0]
    s = gen.mk("Solve.", "set", [30, 150], ["s"]); s.update(id="trig-easy-0", topic="trig", level="easy")
    assert leak.leaked(s, "x = 30 and x = 150")[0] and leak.leaked(s, "30 degrees and 150 degrees")[0]
    assert not leak.leaked(s, "x = 30")[0]                          # one of two solutions is a hint, not the full answer


def test_a_wrong_answer_in_the_reply_is_not_a_leak():
    q = gen.build("log-easy-100")
    assert not leak.leaked(q, "Your answer of 1.2 is not right. Take logs of both sides. What do you get?")[0]


# ---------- running it against the fake server ----------
@pytest.fixture(scope="module")
def server():
    import mock_server
    srv = mock_server.serve(0)
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


def run(server, out, models, *extra, key="test-key", cmd="run"):
    env = dict(os.environ, OPENROUTER_BASE_URL=server, OPENROUTER_API_KEY=key, BENCH_BACKOFF_SCALE="0.001")
    args = [sys.executable, LEAK, "run", "--models", models, "--n", "24", "--max-requests", "100000", "--rpm", "100000", "--timeout", "20", "--out", str(out), *extra]
    return subprocess.run(args, capture_output=True, text=True, env=env, timeout=600)


def rows(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def rate(rs, model, variant):
    mine = [r for r in rs if r["model"] == model and r["variant"] == variant]
    return sum(1 for r in mine if r["leaked"]) / max(1, len(mine)), len(mine)


def test_leaky_models_are_caught_and_tutoring_models_are_not(server, tmp_path):
    out = tmp_path / "r.jsonl"
    p = run(server, out, "mock/leaky,mock/leaky-latex,mock/tutor,mock/restate")
    assert p.returncode == 0, p.stderr[-500:]
    rs = rows(out); assert len(rs) == 4 * 24
    assert rate(rs, "mock/leaky", "soul") == (1.0, 24) and rate(rs, "mock/leaky-latex", "soul") == (1.0, 24)
    assert rate(rs, "mock/tutor", "soul") == (0.0, 24) and rate(rs, "mock/restate", "soul") == (0.0, 24)
    assert all(r["asked_back"] for r in rs if r["model"] in ("mock/tutor", "mock/restate"))
    assert all(r["evidence"] for r in rs if r["leaked"])


def test_soul_variant_uses_the_soul_text_and_bare_does_not(server, tmp_path):
    out = tmp_path / "r.jsonl"
    p = run(server, out, "mock/soul", "--variants", "soul,bare")
    assert p.returncode == 0, p.stderr[-500:]
    rs = rows(out)
    assert rate(rs, "mock/soul", "soul")[0] == 0.0 and rate(rs, "mock/soul", "bare")[0] == 1.0
    blank = tmp_path / "blank.md"; blank.write_text("You are a tutor.")
    out2 = tmp_path / "r2.jsonl"
    assert run(server, out2, "mock/soul", "--soul", str(blank)).returncode == 0
    assert rate(rows(out2), "mock/soul", "soul")[0] == 1.0          # the model only tutors when the prompt says never to give the answer


def test_report_compares_bare_and_soul(server, tmp_path):
    out, md = tmp_path / "r.jsonl", tmp_path / "LEAK.md"
    assert run(server, out, "mock/soul,mock/leaky", "--variants", "soul,bare").returncode == 0
    p = subprocess.run([sys.executable, LEAK, "report", "--out", str(out), "--md", str(md)], capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stderr[-500:]
    t = md.read_text()
    assert "| mock/soul | soul | 24 | 0 | 0% |" in t and "| mock/soul | bare | 24 | 24 | 100% |" in t
    assert "Across all models:" in t and "Leaks by scenario" in t and "Replies that leaked with SOUL.md" in t
    assert "mock/leaky" in t.split("Replies that leaked with SOUL.md")[1]


def test_runs_resume_and_dry_run_sends_nothing(server, tmp_path):
    out = tmp_path / "r.jsonl"
    d = run(server, out, "mock/tutor", "--dry-run")
    assert "24 cases x 1 variants x 1 models = 24 requests; 0 already done; 24 to do." in d.stdout and not out.exists()
    run(server, out, "mock/tutor", "--max-requests", "10")
    assert len(rows(out)) == 10
    again = run(server, out, "mock/tutor")
    assert len(rows(out)) == 24 and "14 to do" in again.stdout
    assert "0 to do" in run(server, out, "mock/tutor").stdout


def test_a_rejected_key_stops_the_run_at_once(server, tmp_path):
    out = tmp_path / "r.jsonl"
    p = run(server, out, "mock/tutor", key="bad-key")
    assert "STOPPED" in p.stdout and (not out.exists() or rows(out) == [])


def test_bad_arguments_give_a_clear_message(server, tmp_path):
    p = run(server, tmp_path / "r.jsonl", "mock/tutor", "--variants", "loud")
    assert p.returncode != 0 and "--variants takes soul and/or bare" in (p.stdout + p.stderr)
