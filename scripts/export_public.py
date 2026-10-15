"""Copy the shareable parts of this workspace into a clean folder for the public repository.

Usage:
  python scripts/export_public.py <destination folder> --repo OWNER/REPO [--with-report]

Only files on the allow list are copied, so private files (USER.md, memory/, logs/, plots/, API keys, benchmark
results) cannot leak by accident. The script then runs the repository hygiene tests on the copy and fails if they fail.
Run it again whenever you want to publish changes. It overwrites files in the destination but never deletes anything,
and it never touches a .git folder.
"""
import argparse, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (source relative to the workspace, destination relative to the repo)
COPY_FILES = [
    ("SOUL.md", "SOUL.md"),
    ("public/README.md", "README.md"),
    ("public/LICENSE", "LICENSE"),
    (".gitignore", ".gitignore"),
    ("pytest.ini", "pytest.ini"),
    ("requirements.txt", "requirements.txt"),
    ("requirements-dev.txt", "requirements-dev.txt"),
    (".github/workflows/ci.yml", ".github/workflows/ci.yml"),
    ("bench/bench.py", "bench/bench.py"),
    ("bench/leak.py", "bench/leak.py"),
    ("bench/mock_server.py", "bench/mock_server.py"),
    ("bench/models.example.txt", "bench/models.example.txt"),
]
COPY_TREES = [
    ("tools", "tools", (".py",)),
    ("scripts", "scripts", (".py",)),
    ("knowledge", "knowledge", (".md",)),
    ("tests", "tests", (".py",)),
    ("public/docs", "docs", (".md", ".png")),
]
SKIP_NAMES = {"__pycache__", ".pytest_cache"}


def copy_file(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dest")
    ap.add_argument("--repo", help="OWNER/REPO, used in the README badge and clone links")
    ap.add_argument("--with-report", action="store_true", help="also publish bench/REPORT.md as docs/BENCHMARK_RESULTS.md and bench/LEAK.md as docs/LEAK_RESULTS.md")
    a = ap.parse_args()
    dest = os.path.abspath(a.dest)
    if os.path.abspath(ROOT) == dest or dest.startswith(os.path.abspath(ROOT) + os.sep):
        sys.exit("Choose a destination OUTSIDE the workspace, for example a new folder next to it.")
    os.makedirs(dest, exist_ok=True)
    soul = os.path.join(ROOT, "SOUL.md")
    if not os.path.exists(soul):
        sys.exit("SOUL.md not found in the workspace.")
    n = 0
    for src, dst in COPY_FILES:
        s = os.path.join(ROOT, src)
        if not os.path.exists(s):
            print("skip (missing):", src); continue
        copy_file(s, os.path.join(dest, dst)); n += 1
    for src, dst, exts in COPY_TREES:
        base = os.path.join(ROOT, src)
        for folder, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in SKIP_NAMES]
            for f in files:
                if f.endswith(exts):
                    rel = os.path.relpath(os.path.join(folder, f), base)
                    copy_file(os.path.join(folder, f), os.path.join(dest, dst, rel)); n += 1
    if a.with_report:
        rep = os.path.join(ROOT, "bench", "REPORT.md")
        if os.path.exists(rep) and os.path.getsize(rep) > 0:
            copy_file(rep, os.path.join(dest, "docs", "BENCHMARK_RESULTS.md")); n += 1
        else:
            print("No bench/REPORT.md with content yet, so no results were published.")
        leak = os.path.join(ROOT, "bench", "LEAK.md")
        if os.path.exists(leak) and os.path.getsize(leak) > 0:
            copy_file(leak, os.path.join(dest, "docs", "LEAK_RESULTS.md")); n += 1
        else:
            print("No bench/LEAK.md with content yet, so no leak results were published.")
    if a.repo:
        for rel in ("README.md", os.path.join("docs", "SETUP.md")):
            p = os.path.join(dest, rel)
            t = open(p, encoding="utf-8").read().replace("OWNER/REPO", a.repo)
            t = t.replace("OWNER", a.repo.split("/")[0]).replace("REPO.git", a.repo.split("/")[1] + ".git")
            t = re.sub(r"cd REPO\b", "cd " + a.repo.split("/")[1], t)
            open(p, "w", encoding="utf-8", newline="\n").write(t)
    print(f"Copied {n} files into {dest}")
    print("Running the hygiene checks on the copy...")
    r = subprocess.run([sys.executable, "-m", "pytest", "-o", "addopts=", "-q", "tests/test_repo_hygiene.py", "tests/test_persona.py"], cwd=dest)
    if r.returncode != 0:
        sys.exit("FAILED: the copy contains something private or the persona rules are broken. Do not push. Fix the cause and run again.")
    print("Clean. Next, in that folder:  git add -A  then  git commit -m \"...\"  then  git push")


if __name__ == "__main__":
    main()
