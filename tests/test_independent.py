"""A second, separate solver re-derives each answer from the question TEXT. If the generator's key and this solver
disagree, the test fails. The solver shares no formulas with the generator."""
import pytest
import gen
import core, new
from conftest import SEEDS

OLD = ["diff", "integ", "stat", "quad", "log", "binom", "simul", "factor", "trig", "tangent", "func", "circ", "perm"]
NEW = ["mod", "ineq", "prog", "vec", "kin", "rates", "area", "lin", "line", "cgeo", "tgraph"]


def test_every_topic_has_an_independent_verifier():
    assert set(OLD) | set(NEW) == set(gen.GEN)


@pytest.mark.parametrize("topic", OLD)
def test_original_topics(topic):
    problems = []
    for lv in gen.LEVELS:
        for seed in range(1, SEEDS + 1):
            q = gen.build(f"{topic}-{lv}-{seed}")
            r = core.verify(q)
            if r:
                problems.append((q["id"], q["question"], r))
    assert not problems, problems[:3]


@pytest.mark.parametrize("topic", NEW)
def test_newer_topics(topic):
    new.bad.clear()
    for lv in gen.LEVELS:
        for seed in range(1, SEEDS + 1):
            q = gen.build(f"{topic}-{lv}-{seed}")
            new.verify(q)
    assert not new.bad, new.bad[:3]
