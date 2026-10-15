"""Give one OpenClaw agent its own model chain, and register a custom OpenAI-compatible provider for it.

Dry run by default: it prints what it would change and writes nothing. Add --apply to write.
It backs up openclaw.json first, never prints your API key, and changes only:
  - models.providers.<provider>            (added or extended, existing models kept)
  - agents.defaults.models                 (adds the refs so OpenClaw knows them)
  - agents.list[<agent>].model             (primary + fallbacks for that agent only)
Other agents, channels, tokens and settings are left exactly as they are.

Usage:
  python scripts/configure_models.py --chain scripts/edith_chain.txt                 # preview
  python scripts/configure_models.py --chain scripts/edith_chain.txt --apply         # write

The chain file has one model ref per line, "provider/model". The first line is the primary and the rest are fallbacks,
in order. Blank lines and lines starting with # are ignored.

The provider key is read from the environment variable named by --key-env when you run this (default UNOROUTER_API_KEY).
By default it is written into openclaw.json, the same way your other keys are stored. Use --env-ref to write ${VAR}
instead, but then the gateway process itself must have that variable set.
"""
import argparse, copy, datetime, json, os, shutil, sys

DEFAULT_CONFIG = os.path.join(os.path.expanduser("~"), ".openclaw", "openclaw.json")


def read_chain(path):
    refs = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#"):
            if "/" not in line:
                raise SystemExit(f"Bad model ref {line!r}: use provider/model")
            refs.append(line)
    if not refs:
        raise SystemExit("The chain file has no models.")
    if len(set(refs)) != len(refs):
        raise SystemExit("The chain file lists the same model twice.")
    return refs


def model_entry(model_id):
    return {"id": model_id, "name": model_id, "reasoning": False, "input": ["text"],
            "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0}, "contextWindow": 32768, "maxTokens": 8192}


def plan(cfg, refs, agent, provider, base_url, api_key):
    """Return a modified copy of the config. Raises SystemExit if the agent does not exist."""
    new = copy.deepcopy(cfg)
    agents = new.get("agents", {})
    entry = next((a for a in agents.get("list", []) if a.get("id") == agent), None)
    if entry is None:
        raise SystemExit(f"No agent with id {agent!r} in agents.list.")
    # provider
    models = new.setdefault("models", {})
    models.setdefault("mode", "merge")
    prov = models.setdefault("providers", {}).setdefault(provider, {})
    prov["baseUrl"] = base_url
    prov["apiKey"] = api_key
    prov.setdefault("api", "openai-completions")
    have = {m.get("id") for m in prov.setdefault("models", [])}
    for ref in refs:
        p, _, mid = ref.partition("/")
        if p == provider and mid not in have:
            prov["models"].append(model_entry(mid)); have.add(mid)
    # catalogue
    catalogue = agents.setdefault("defaults", {}).setdefault("models", {})
    for ref in refs:
        catalogue.setdefault(ref, {})
    # the agent's own chain
    entry["model"] = {"primary": refs[0], "fallbacks": refs[1:]}
    return new


def describe(old, new, agent, provider, shown_key):
    lines = []
    old_models = {m.get("id") for m in old.get("models", {}).get("providers", {}).get(provider, {}).get("models", [])}
    new_models = [m["id"] for m in new["models"]["providers"][provider]["models"]]
    lines.append(f"provider {provider}: {new['models']['providers'][provider]['baseUrl']}  key: {shown_key}")
    lines.append("  models added: " + (", ".join(m for m in new_models if m not in old_models) or "none"))
    cat_old = set(old.get("agents", {}).get("defaults", {}).get("models", {}))
    cat_new = [r for r in new["agents"]["defaults"]["models"] if r not in cat_old]
    lines.append("catalogue entries added: " + (", ".join(cat_new) or "none"))
    chain = next(a for a in new["agents"]["list"] if a.get("id") == agent)["model"]
    lines.append(f"agent {agent} chain:")
    lines.append(f"  primary:   {chain['primary']}")
    for i, f in enumerate(chain["fallbacks"], 1):
        lines.append(f"  fallback {i}: {f}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=DEFAULT_CONFIG)
    ap.add_argument("--chain", required=True)
    ap.add_argument("--agent", default="addmath")
    ap.add_argument("--provider", default="unorouter")
    ap.add_argument("--base-url", default="https://api.unorouter.com/v1")
    ap.add_argument("--key-env", default="UNOROUTER_API_KEY")
    ap.add_argument("--env-ref", action="store_true", help="write ${VAR} instead of the key itself")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args(argv)

    if not os.path.exists(a.config):
        raise SystemExit(f"Config not found: {a.config}")
    try:
        cfg = json.load(open(a.config, encoding="utf-8"))
    except ValueError as e:
        raise SystemExit(f"{a.config} is not plain JSON ({e}). Nothing was changed.")
    refs = read_chain(a.chain)
    uses_provider = any(r.startswith(a.provider + "/") for r in refs)
    key = os.environ.get(a.key_env, "")
    if uses_provider and not a.env_ref and not key and a.apply:
        raise SystemExit(f"Set {a.key_env} in this window first, or use --env-ref.")
    api_key = "${" + a.key_env + "}" if a.env_ref else (key or "<from " + a.key_env + ">")
    new = plan(cfg, refs, a.agent, a.provider, a.base_url, api_key)
    shown = "${" + a.key_env + "}" if a.env_ref else ("set from " + a.key_env if key else f"NOT SET ({a.key_env} is empty)")
    print(describe(cfg, new, a.agent, a.provider, shown))
    if not a.apply:
        print("\nDry run. Nothing was written. Add --apply to make this change.")
        return 0
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"{a.config}.bak-{stamp}"
    shutil.copyfile(a.config, backup)
    tmp = a.config + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(new, fh, indent=2, ensure_ascii=False); fh.write("\n")
    json.load(open(tmp, encoding="utf-8"))          # must parse before it replaces the real file
    os.replace(tmp, a.config)
    print(f"\nWritten. Backup of the old file: {backup}")
    print("Next: openclaw gateway restart    then    openclaw models status")
    return 0


if __name__ == "__main__":
    sys.exit(main())
