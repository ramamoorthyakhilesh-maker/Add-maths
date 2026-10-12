"""Question cards: the plain-text question must become valid maths, and a PNG must be written."""
import os, re, subprocess, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest
import gen, render
from conftest import SEEDS, ROOT


def body(s):
    return render.to_mathtext(s)


@pytest.mark.parametrize("plain,expect", [
    ("x^2 + 3x - 1", "x^{2}+3x-1"),
    ("x^(3/2)", "x^{\\frac{3}{2}}"),
    ("sqrt(x)", "\\sqrt{x}"),
    ("(4x + 4)/(x + 4)", "\\frac{4x+4}{x+4}"),
    ("f^-1(x)", "f^{-1}(x)"),
    ("e^(-2x)", "e^{{-}2x}"),
    ("|x - 4| >= 2", "\\left|x-4\\right|\\geq 2"),
    ("0 <= x <= 360 degrees", "0\\leq x\\leq 360^{\\circ}"),
    ("3i - 4j", "3\\mathbf{i}-4\\mathbf{j}"),
    ("12 cm", "12\\ \\mathrm{cm}"),
    ("log base 5 of x", "\\log_{5}(x)"),
])
def test_conversions(plain, expect):
    if plain.startswith("log base"):
        chunks = render.build_chunks("Solve " + plain + " = 3.")
        assert any(expect in c[1] for c in chunks if c[0] == "m")
    else:
        assert expect in body(plain)


def test_prose_stays_prose():
    kinds = {w: k for k, w, _ in render.split_sentence("A sector of a circle has radius 12 cm and angle 3/2 radians.")}
    assert kinds["A"] == "t" if "A" in kinds else True
    assert not any(k == "m" and "sector" in w for k, w, _ in render.split_sentence("A sector of a circle has radius 12 cm."))


def test_a_is_a_variable_only_when_it_is_one():
    spans = [w for k, w, _ in render.split_sentence("Find a, b and c where a > 0.") if k == "m"]
    assert any(w.startswith("a") for w in spans)
    text_only = [w for k, w, _ in render.split_sentence("a straight line") if k == "m"]
    assert text_only == []


def test_every_generated_question_draws():
    fig = plt.figure(figsize=(5, 3), dpi=100)
    r = fig.canvas.get_renderer()
    for t in gen.GEN:
        for lv in gen.LEVELS:
            for seed in range(1, SEEDS + 1):
                q = gen.build(f"{t}-{lv}-{seed}")
                for kind, drawable, _, plain in render.build_chunks(q["question"]):
                    if kind == "m":
                        fig.text(0, 0, drawable, fontsize=15, transform=None).get_window_extent(r)   # raises if mathtext rejects it
                        fig.texts[-1].remove()
    plt.close(fig)


def test_no_maths_falls_back_to_plain_text():
    for t in gen.GEN:
        for lv in gen.LEVELS:
            for seed in range(1, SEEDS + 1):
                q = gen.build(f"{t}-{lv}-{seed}")
                for kind, plain, _ in render.split_sentence(q["question"]):
                    if kind == "m":
                        render.to_mathtext(plain)       # raises render.Bad if the converter gave up


def test_cli_writes_a_png(tmp_path):
    out = tmp_path / "card.png"
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "render.py"), "vec-hard-256687", "--out", str(out)],
                       capture_output=True, text=True, timeout=120)
    assert out.exists() and out.stat().st_size > 5000, r.stdout + r.stderr
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_cli_prints_media_line():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "render.py"), "diff-easy-1"], capture_output=True, text=True, timeout=120)
    assert re.fullmatch(r"MEDIA:plots/q_diff-easy-1\.png", r.stdout.strip()), r.stdout + r.stderr
    path = os.path.join(ROOT, "plots", "q_diff-easy-1.png")
    assert os.path.exists(path)
    os.remove(path)


def test_cli_fails_cleanly_on_bad_id():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "render.py"), "nonsense-1"], capture_output=True, text=True, timeout=120)
    assert r.stdout.startswith("RENDER FAILED") and "Traceback" not in r.stderr


def test_card_never_shows_the_answer():
    src = open(os.path.join(ROOT, "tools", "render.py"), encoding="utf-8").read()
    assert "ans_str" not in src and '["answer"]' not in src and "steps" not in src
