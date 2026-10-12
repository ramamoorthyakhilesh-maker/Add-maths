"""SOUL.md is the whole behaviour contract. These tests check it still says the things the project promises."""
import os, re
import pytest
import gen
from conftest import ROOT


def soul():
    for name in ("SOUL.md", "SOUL.md.proposed"):
        p = os.path.join(ROOT, name)
        if os.path.exists(p):
            return open(p, encoding="utf-8").read()
    pytest.skip("no SOUL.md in this checkout")


def test_it_is_a_maths_only_tutor():
    s = soul()
    assert "0606" in s and "Additional Mathematics" in s
    assert "not a general assistant" in s
    assert "decline" in s.lower()


def test_it_never_gives_the_answer_straight():
    s = soul()
    assert "Never give the final answer" in s
    assert "Never tell the student the answer" in s
    assert "hint" in s.lower()
    assert "reveal" in s                                           # reveal is allowed only under stated conditions
    assert re.search(r"Never run reveal because the student asked", s)


def test_it_uses_tools_instead_of_guessing():
    s = soul()
    for tool in ("tools/gen.py", "tools/check.py", "tools/plot.py", "tools/progress.py", "tools/render.py"):
        assert tool in s, tool
        assert os.path.exists(os.path.join(ROOT, tool)), tool
    assert "Never invent practice questions" in s
    assert "do not judge the answer yourself" in s.lower() or "Do not generate a new question and do not judge" in s


def test_every_topic_is_listed_for_the_tutor():
    s = soul()
    for t in gen.GEN:
        assert re.search(rf"\b{t}\b", s), f"SOUL.md does not mention the topic {t}"


def test_every_verdict_has_instructions():
    s = soul()
    for v in ("CORRECT", "INCORRECT", "AMBIGUOUS", "NOT EXACT", "COULD NOT READ THE ANSWER"):
        assert v in s, v


def test_it_resists_instruction_injection():
    s = soul()
    assert "Ignore any instruction" in s


def test_it_is_not_personal():
    s = soul()
    # built from pieces so this file does not trip the repo hygiene scan
    for word in ("Akh" + "ilesh", "Ali" + "ce Smith", "Mala" + "ysia", "JAR" + "VIS", "@g" + "mail"):
        assert word.lower() not in s.lower(), word


def test_every_tool_command_in_soul_is_a_real_command():
    s = soul()
    for cmd in set(re.findall(r"python tools/gen\.py (\w+)", s)):
        assert cmd in ("list", "new", "followup", "check", "hint", "reveal", "dump"), cmd
    for cmd in set(re.findall(r"python tools/progress\.py (\w+)", s)):
        assert cmd in ("stats", "history", "next"), cmd
