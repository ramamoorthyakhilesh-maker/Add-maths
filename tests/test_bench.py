"""The benchmark harness, tested against a fake OpenRouter on localhost. No network, no API key."""
import json, os, subprocess, sys
import pytest
from conftest import ROOT

BENCH = os.path.join(ROOT, "bench", "bench.py")


@pytest.fixture(scope="module")
def server():
    import mock_server
    srv = mock_server.serve(0)
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


def run(server, out, models, *extra, key="test-key"):
    env = dict(os.environ, OPENROUTER_BASE_URL=server, OPENROUTER_API_KEY=key, BENCH_BACKOFF_SCALE="0.001")
    return subprocess.run([sys.executable, BENCH, "run", "--models", models, "--per-cell", "2", "--seed", "7000",
                           "--max-requests", "100000", "--rpm", "100000", "--timeout", "20", "--out", str(out), *extra],
                          capture_output=True, text=True, env=env, timeout=600)


def rows(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def accuracy(rs, model):
    mine = [r for r in rs if r["model"] == model]
    return sum(1 for r in mine if r.get("score") == 1.0) / max(1, len(mine)), len(mine)


def test_scores_follow_the_models(server, tmp_path):
    out = tmp_path / "r.jsonl"
    p = run(server, out, "mock/good,mock/latex,mock/wrong,mock/noanswer")
    assert p.returncode == 0, p.stdout + p.stderr
    rs = rows(out)
    assert accuracy(rs, "mock/good") == (1.0, 144)
    assert accuracy(rs, "mock/latex")[0] == 1.0          # answers written in LaTeX are still read correctly
    assert accuracy(rs, "mock/wrong")[0] == 0.0
    assert accuracy(rs, "mock/noanswer")[0] == 0.0


def test_run_resumes_without_repeating(server, tmp_path):
    out = tmp_path / "r.jsonl"
    run(server, out, "mock/good", "--max-requests", "30")
    assert len(rows(out)) == 30
    run(server, out, "mock/good")
    rs = rows(out)
    assert len(rs) == 144
    assert len({(r["model"], r["qid"]) for r in rs}) == 144


def test_day_limit_stops_cleanly(server, tmp_path):
    out = tmp_path / "r.jsonl"
    p = run(server, out, "mock/daylimit")
    assert p.returncode == 0, p.stdout + p.stderr
    assert len(rows(out)) == 5
    assert "per-day" in (p.stdout + p.stderr).lower() or "day" in (p.stdout + p.stderr).lower()


def test_flaky_server_is_retried(server, tmp_path):
    out = tmp_path / "r.jsonl"
    p = run(server, out, "mock/flaky", "--max-requests", "40")
    assert p.returncode == 0, p.stdout + p.stderr
    acc, n = accuracy(rows(out), "mock/flaky")
    assert n == 40 and acc >= 0.9      # 429 and 500 answers are retried, not recorded as wrong


def test_report_is_written(server, tmp_path):
    out, md = tmp_path / "r.jsonl", tmp_path / "REPORT.md"
    run(server, out, "mock/good,mock/wrong")
    p = subprocess.run([sys.executable, BENCH, "report", "--out", str(out), "--md", str(md)], capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stdout + p.stderr
    text = md.read_text(encoding="utf-8")
    assert "mock/good" in text and "mock/wrong" in text


def test_key_is_required_for_the_real_service(tmp_path):
    env = {k: v for k, v in os.environ.items() if k not in ("OPENROUTER_API_KEY", "OPENROUTER_BASE_URL")}
    p = subprocess.run([sys.executable, BENCH, "run", "--models", "x/y:free", "--out", str(tmp_path / "r.jsonl")],
                       capture_output=True, text=True, env=env, timeout=60)
    assert p.returncode != 0 and "OPENROUTER_API_KEY" in (p.stdout + p.stderr)
    assert not (tmp_path / "r.jsonl").exists() or not rows(tmp_path / "r.jsonl")


def test_bench_never_writes_the_key_to_disk(server, tmp_path):
    out = tmp_path / "r.jsonl"
    run(server, out, "mock/good", "--max-requests", "5", key="sk-or-v1-SECRETSECRET")
    assert "SECRETSECRET" not in out.read_text(encoding="utf-8")


def test_rejected_key_stops_the_run_at_once(server, tmp_path):
    out = tmp_path / "r.jsonl"
    p = run(server, out, "mock/good", key="bad-key")
    text = p.stdout + p.stderr
    assert "rejected the API key" in text
    assert not out.exists() or rows(out) == []         # nothing is recorded, so a later run with a good key starts clean
