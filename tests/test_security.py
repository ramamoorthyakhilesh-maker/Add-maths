"""The student's answer is typed into a parser. It must never run code, and never hang."""
import os, subprocess, sys, time
import pytest
import gen

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")
HOSTILE = ["9**9**9**9", "9^9^9^9", "9^(9^9)", "(9^99)^99", "2^(3^(4^5))", "x^99999", "__import__('os').getcwd()",
           "x.__class__", "lambda: 1", "[c for c in 'ab']", "open('f')", "x^pi", "exec('1')", "eval('1')", "().__class__",
           "x[0]", "{1: 2}", "x if 1 else 2", "print(1)"]


@pytest.mark.parametrize("bad", HOSTILE)
def test_hostile_input_is_refused_quickly(bad):
    q = gen.build("diff-easy-1")
    t0 = time.time()
    v = gen.verdict(q, bad)
    assert time.time() - t0 < 3.0, bad
    assert v != "CORRECT", bad


def test_normal_power_forms_still_work():
    q = gen.build("diff-easy-1")
    for ok in ("2^x", "e^(2x)", "3x^2+4x^3", "x^(3/2)"):
        assert not gen.verdict(q, ok).startswith("GEN FAILED"), ok


@pytest.mark.parametrize("bad", ["9**9**9**9", "__import__('os').system('echo hi')", "x.__class__"])
def test_check_cli_refuses_hostile_input(bad):
    t0 = time.time()
    r = subprocess.run([sys.executable, os.path.join(TOOLS, "check.py"), "eval", bad], capture_output=True, text=True, timeout=20)
    assert time.time() - t0 < 10
    assert "hi" != r.stdout.strip()
    assert r.returncode == 0 or r.stdout or r.stderr
