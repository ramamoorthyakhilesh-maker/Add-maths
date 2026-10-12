import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (os.path.join(ROOT, "tools"), os.path.join(ROOT, "bench"), os.path.join(ROOT, "tests", "independent")):
    if p not in sys.path:
        sys.path.insert(0, p)

# Number of random seeds per topic and level. CI uses the default. Set EDITH_SEEDS=60 for the full run.
SEEDS = int(os.environ.get("EDITH_SEEDS", "12"))


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: slower tests (the full run uses more seeds)")
