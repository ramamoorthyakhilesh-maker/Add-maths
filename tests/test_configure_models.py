"""scripts/configure_models.py edits openclaw.json. It must touch only what it says and never lose anything else."""
import copy, json, os, subprocess, sys
import pytest
from conftest import ROOT

SCRIPT = os.path.join(ROOT, "scripts", "configure_models.py")

CONFIG = {
    "agents": {
        "defaults": {"workspace": "W", "model": {"primary": "openrouter/a:free", "fallbacks": ["openrouter/b:free"]},
                     "models": {"openrouter/a:free": {}, "openrouter/b:free": {"alias": "B"}}},
        "list": [{"id": "main"}, {"id": "addmath", "name": "addmath", "workspace": "W2"}],
    },
    "channels": {"telegram": {"accounts": {"addmath": {"botToken": "TOKEN-KEEP"}}}},
    "bindings": [{"type": "route", "agentId": "addmath"}],
    "auth": {"profiles": {"openrouter:default": {"provider": "openrouter", "mode": "api_key"}}},
}
CHAIN = "# comment\nopenrouter/a:free\nopenrouter/c:free\nunorouter/m1:free\nunorouter/m2:free\n"


def run(tmp_path, *extra, key="SECRET-KEY-123", cfg=None):
    c = tmp_path / "openclaw.json"
    c.write_text(json.dumps(CONFIG if cfg is None else cfg), encoding="utf-8")
    ch = tmp_path / "chain.txt"
    ch.write_text(CHAIN, encoding="utf-8")
    env = dict(os.environ, UNOROUTER_API_KEY=key)
    if key is None:
        env.pop("UNOROUTER_API_KEY")
    p = subprocess.run([sys.executable, SCRIPT, "--config", str(c), "--chain", str(ch), *extra], capture_output=True, text=True, env=env, timeout=60)
    return p, c


def test_dry_run_changes_nothing_and_hides_the_key(tmp_path):
    p, c = run(tmp_path)
    assert p.returncode == 0, p.stderr
    assert json.loads(c.read_text(encoding="utf-8")) == CONFIG
    assert "SECRET-KEY-123" not in p.stdout + p.stderr
    assert "Dry run" in p.stdout and "unorouter/m1:free" in p.stdout


def test_apply_sets_only_the_agents_chain(tmp_path):
    p, c = run(tmp_path, "--apply")
    assert p.returncode == 0, p.stderr
    new = json.loads(c.read_text(encoding="utf-8"))
    agent = next(a for a in new["agents"]["list"] if a["id"] == "addmath")
    assert agent["model"] == {"primary": "openrouter/a:free", "fallbacks": ["openrouter/c:free", "unorouter/m1:free", "unorouter/m2:free"]}
    assert agent["workspace"] == "W2"                                            # other fields kept
    assert next(a for a in new["agents"]["list"] if a["id"] == "main") == {"id": "main"}   # other agents untouched
    assert new["agents"]["defaults"]["model"] == CONFIG["agents"]["defaults"]["model"]     # shared default untouched
    for k in ("channels", "bindings", "auth"):
        assert new[k] == CONFIG[k], k
    assert new["agents"]["defaults"]["models"]["openrouter/b:free"] == {"alias": "B"}      # existing alias kept
    for ref in ("openrouter/c:free", "unorouter/m1:free", "unorouter/m2:free"):
        assert ref in new["agents"]["defaults"]["models"]


def test_provider_is_registered(tmp_path):
    p, c = run(tmp_path, "--apply")
    new = json.loads(c.read_text(encoding="utf-8"))
    prov = new["models"]["providers"]["unorouter"]
    assert new["models"]["mode"] == "merge"
    assert prov["baseUrl"] == "https://api.unorouter.com/v1" and prov["api"] == "openai-completions"
    assert prov["apiKey"] == "SECRET-KEY-123"
    assert [m["id"] for m in prov["models"]] == ["m1:free", "m2:free"]
    assert all(m["input"] == ["text"] for m in prov["models"])


def test_backup_is_made_and_matches_the_old_file(tmp_path):
    p, c = run(tmp_path, "--apply")
    backups = [f for f in os.listdir(tmp_path) if f.startswith("openclaw.json.bak-")]
    assert len(backups) == 1
    assert json.loads((tmp_path / backups[0]).read_text(encoding="utf-8")) == CONFIG


def test_env_ref_keeps_the_key_out_of_the_file(tmp_path):
    p, c = run(tmp_path, "--apply", "--env-ref")
    assert "SECRET-KEY-123" not in c.read_text(encoding="utf-8")
    assert json.loads(c.read_text(encoding="utf-8"))["models"]["providers"]["unorouter"]["apiKey"] == "${UNOROUTER_API_KEY}"


def test_running_twice_gives_the_same_result(tmp_path):
    run(tmp_path, "--apply")
    first = json.loads((tmp_path / "openclaw.json").read_text(encoding="utf-8"))
    ch = tmp_path / "chain.txt"
    env = dict(os.environ, UNOROUTER_API_KEY="SECRET-KEY-123")
    subprocess.run([sys.executable, SCRIPT, "--config", str(tmp_path / "openclaw.json"), "--chain", str(ch), "--apply"], env=env, check=True, capture_output=True, timeout=60)
    assert json.loads((tmp_path / "openclaw.json").read_text(encoding="utf-8")) == first


def test_missing_key_stops_before_writing(tmp_path):
    p, c = run(tmp_path, "--apply", key=None)
    assert p.returncode != 0 and "UNOROUTER_API_KEY" in p.stderr + p.stdout
    assert json.loads(c.read_text(encoding="utf-8")) == CONFIG


def test_unknown_agent_is_an_error(tmp_path):
    p, c = run(tmp_path, "--apply", "--agent", "nobody")
    assert p.returncode != 0 and "nobody" in p.stderr + p.stdout
    assert json.loads(c.read_text(encoding="utf-8")) == CONFIG


def test_broken_config_is_not_touched(tmp_path):
    c = tmp_path / "openclaw.json"
    c.write_text("{ not json", encoding="utf-8")
    ch = tmp_path / "chain.txt"; ch.write_text(CHAIN, encoding="utf-8")
    p = subprocess.run([sys.executable, SCRIPT, "--config", str(c), "--chain", str(ch), "--apply"], capture_output=True, text=True, timeout=60, env=dict(os.environ, UNOROUTER_API_KEY="x"))
    assert p.returncode != 0
    assert c.read_text(encoding="utf-8") == "{ not json"
