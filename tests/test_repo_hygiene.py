"""Nothing private may reach a public repository: keys, tokens, the student's name, school, email or chat logs."""
import os, re
import pytest
from conftest import ROOT

SKIP_DIRS = {".git", "__pycache__", "plots", "logs", ".pytest_cache", "node_modules", ".venv", "venv"}
SKIP_FILES = {"test_repo_hygiene.py", "gen_calls.jsonl"}
TEXT = (".py", ".md", ".txt", ".json", ".jsonl", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".proposed", ".bak", ".bak2", ".gitignore", "")
PATTERNS = {
    "OpenRouter key": r"sk-or-v1-[A-Za-z0-9]{16,}",
    "generic secret key": r"\bsk-[A-Za-z0-9]{32,}",
    "Telegram bot token": r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b",
    "Anthropic key": r"sk-ant-[A-Za-z0-9_-]{20,}",
    "GitHub token": r"\bgh[pousr]_[A-Za-z0-9]{30,}",
    "Windows user path": r"C:\\Users\\[A-Za-z0-9._-]+\\",
    "email address": r"[A-Za-z0-9._%+-]+@(?:gmail|outlook|hotmail|yahoo|icloud)\.com",
}
PRIVATE_WORDS = ["akh" + "ilesh", "ram" + "am", "ali" + "ce smith"]

# These checks are for the PUBLIC copy of the project. Your live workspace holds private files by design, so skip it there.
if os.path.exists(os.path.join(ROOT, "USER.md")) or os.path.isdir(os.path.join(ROOT, "memory")):
    if not os.environ.get("EDITH_CHECK_PRIVATE"):
        pytest.skip("private workspace: run these tests in the public repo copy", allow_module_level=True)


def text_files():
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f in SKIP_FILES or not f.endswith(TEXT) and "." in f:
                continue
            yield os.path.join(base, f)


def read(p):
    try:
        return open(p, encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        return ""


@pytest.mark.parametrize("label,pattern", PATTERNS.items())
def test_no_secrets(label, pattern):
    hits = [os.path.relpath(p, ROOT) for p in text_files() if re.search(pattern, read(p))]
    assert not hits, f"{label} found in {hits}"


def test_no_personal_names():
    hits = []
    for p in text_files():
        low = read(p).lower()
        for w in PRIVATE_WORDS:
            if w in low:
                hits.append((os.path.relpath(p, ROOT), w))
    assert not hits, hits


def test_private_workspace_files_are_not_in_the_repo():
    for name in ("USER.md", "MEMORY.md", "IDENTITY.md", "openclaw.json", ".env"):
        assert not os.path.exists(os.path.join(ROOT, name)), name
    assert not os.path.isdir(os.path.join(ROOT, "memory"))


def test_gitignore_covers_private_output():
    p = os.path.join(ROOT, ".gitignore")
    assert os.path.exists(p), "add a .gitignore"
    g = read(p)
    for entry in ("logs/", "plots/", "bench/results.jsonl", ".env", "__pycache__/"):
        assert entry in g, entry
