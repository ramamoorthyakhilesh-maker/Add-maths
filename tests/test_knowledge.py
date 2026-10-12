"""The knowledge files must cover every generator topic, stay in sync with the build script, and stay inside the syllabus."""
import os, re, shutil, subprocess, sys
import gen
from conftest import ROOT

TOPICS_DIR = os.path.join(ROOT, "knowledge", "topics")


def index_rows():
    rows = {}
    for line in open(os.path.join(TOPICS_DIR, "INDEX.md"), encoding="utf-8"):
        m = re.match(r"\|\s*(\d\d-[\w-]+\.md)\s*\|(.*)\|(.*)\|\s*$", line)
        if m:
            rows[m.group(1)] = [t.strip() for t in m.group(3).split(",")]
    return rows


def test_index_lists_real_files_and_every_file():
    rows = index_rows()
    files = {f for f in os.listdir(TOPICS_DIR) if re.match(r"\d\d-.*\.md$", f)}
    assert set(rows) == files


def test_every_generator_topic_has_a_notes_file():
    covered = {t for ts in index_rows().values() for t in ts}
    assert covered == set(gen.GEN), set(gen.GEN) ^ covered


def test_every_notes_file_has_the_standard_sections():
    for f in index_rows():
        text = open(os.path.join(TOPICS_DIR, f), encoding="utf-8").read()
        assert text.startswith("# "), f
        assert "Not Cambridge text" in text, f
        for h in ("## What the syllabus asks", "## Core methods"):
            assert h in text, (f, h)
        assert "Answer:" in text, f"{f} has no worked example"


def test_syllabus_file_tags_every_generator_topic():
    text = open(os.path.join(ROOT, "knowledge", "syllabus.md"), encoding="utf-8").read()
    for t in gen.GEN:
        assert f"[{t}]" in text, f"syllabus.md has no [{t}] tag"
    assert "Not in the syllabus" in text


def test_notes_are_in_sync_with_the_build_script(tmp_path):
    """Rebuilding runs every worked example through sympy asserts. The result must match the committed files."""
    (tmp_path / "scripts").mkdir()
    shutil.copy(os.path.join(ROOT, "scripts", "build_knowledge.py"), tmp_path / "scripts" / "build_knowledge.py")
    r = subprocess.run([sys.executable, str(tmp_path / "scripts" / "build_knowledge.py")], capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stdout[-500:] + r.stderr[-1500:]
    built = tmp_path / "knowledge" / "topics"
    for f in os.listdir(TOPICS_DIR):
        if f.endswith(".md") and f != "INDEX.md":
            a = (built / f).read_text(encoding="utf-8").replace("\r\n", "\n")
            b = open(os.path.join(TOPICS_DIR, f), encoding="utf-8").read().replace("\r\n", "\n")
            assert a == b, f"{f} differs from what build_knowledge.py produces"
