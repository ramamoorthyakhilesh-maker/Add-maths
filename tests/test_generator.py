"""Every generated question must build, repeat exactly for the same ID, accept its own answer and reject wrong ones."""
import pytest
import gen
from conftest import SEEDS

CELLS = [(t, lv) for t in gen.GEN for lv in gen.LEVELS]
WRONG = {"expr": lambda s, q: s + " + x^2 + 1", "antider": lambda s, q: s + " + x^2", "int": lambda s, q: str(int(q["answer"]) + 1),
         "value": lambda s, q: "12345.678", "num3sf": lambda s, q: "12345.678", "set": lambda s, q: s + ", 999",
         "pairs": lambda s, q: "(999, 999)", "interval": lambda s, q: "x > 1000", "vec": lambda s, q: "999i + 999j",
         "eqn": lambda s, q: "x^2 + y^2 = 7"}


def test_there_are_24_topics():
    assert len(gen.GEN) == 24
    assert set(gen.LEVELS) == {"easy", "medium", "hard"}


@pytest.mark.parametrize("topic,level", CELLS)
def test_questions_build_and_are_stable(topic, level):
    for seed in range(1, SEEDS + 1):
        qid = f"{topic}-{level}-{seed}"
        q1, q2 = gen.build(qid), gen.build(qid)
        assert q1["question"] == q2["question"] and gen.ans_str(q1) == gen.ans_str(q2), qid
        assert q1["question"].strip() and q1["steps"], qid
        assert q1["topic"] == topic and q1["level"] == level and q1["id"] == qid


@pytest.mark.parametrize("topic,level", CELLS)
def test_own_answer_is_accepted(topic, level):
    for seed in range(1, SEEDS + 1):
        q = gen.build(f"{topic}-{level}-{seed}")
        a = q["ans_text"] if q["kind"] == "interval" else gen.ans_str(q)
        v = gen.verdict(q, a)
        assert v == "CORRECT" or v.startswith("NOT EXACT"), (q["id"], q["question"], a, v)


@pytest.mark.parametrize("topic,level", CELLS)
def test_wrong_answers_are_rejected(topic, level):
    for seed in range(1, SEEDS + 1):
        q = gen.build(f"{topic}-{level}-{seed}")
        s = q["ans_text"] if q["kind"] == "interval" else gen.ans_str(q)
        wrong = WRONG[q["kind"]](s, q)
        assert gen.verdict(q, wrong) != "CORRECT", (q["id"], q["question"], wrong)


def test_bad_ids_fail_cleanly():
    for bad in ("nonsense", "diff-easy", "banana-easy-5", "diff-silly-5", "diff-easy-x"):
        with pytest.raises(Exception):
            gen.build(bad)


def test_hints_end_with_a_stop_message(capsys):
    gen.main(["hint", "diff-easy-1", "99"])
    assert "No more hints" in capsys.readouterr().out
