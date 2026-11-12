"""Lint what we changed in the plugin fork (`plugin/`, the branch checked out there) against
`upstream/main`: only the lines that differ, so a branch that is behind the dev repo is not flagged
for code it does not have. Files we own outright (`call_packages.py`, `calls/`) get the dev
project's rule set and a format check; upstream's files (`adapter.py`, tests) use their own style,
so only bug-finding rules (F, B, E9, PLE) apply there. Pyrefly runs against the real Hermes source
(`HERMES_SRC`, default ~/.hermes/hermes-agent). Exit 1 on a finding."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugin"
OWNED = ("call_packages.py", "calls/")
# Hermes' own source, so pyrefly sees the real gateway classes the plugin subclasses and calls.
HERMES_SRC = Path(os.environ.get("HERMES_SRC", "~/.hermes/hermes-agent")).expanduser()


def run(cmd: list[str], cwd: Path) -> str:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False).stdout


def changed_lines(base: str) -> dict[str, set[int]]:
    """{file: lines added or changed since `base`} for Python files, from `git diff -U0`."""
    out: dict[str, set[int]] = {}
    name = ""
    for line in run(["git", "diff", "-U0", "--no-color", base, "--", "*.py"], PLUGIN).splitlines():
        if line.startswith("+++ b/"):
            name = line[6:]
            out[name] = set()
        elif m := re.match(r"@@ -\S+ \+(\d+)(?:,(\d+))? @@", line):
            start, count = int(m[1]), int(m[2] or 1)
            out[name].update(range(start, start + count))
    return out


def pyrefly(files: list[str], owned: list[str], changed: dict[str, set[int]]) -> list[str]:
    """Type errors against the real Hermes source; missing imports (Hermes' own dependencies, the
    optional OMEMO libraries) are not reported. Skipped when no Hermes source is found."""
    if not HERMES_SRC.is_dir():
        print(f"pyrefly: no Hermes source at {HERMES_SRC} (set HERMES_SRC): skipped")
        return []
    cmd = ["uv", "run", "--frozen", "pyrefly", "check", "--output-format", "json"]
    raw = run([*cmd, "--search-path", str(HERMES_SRC), *(f"plugin/{f}" for f in files)], ROOT)
    try:
        errors = json.loads(raw[: raw.rindex("}") + 1])["errors"]
    except (ValueError, KeyError):
        return ["pyrefly: unreadable output (is the plugin importable?)"]
    out = []
    for item in errors:
        rel = Path(item["path"]).as_posix().removeprefix("plugin/")
        if item["name"] == "missing-import":
            continue
        if item["line"] in changed.get(rel, set()):
            what = item["description"].splitlines()[0]
            out.append(f"{rel}:{item['line']}: pyrefly {item['name']}: {what}")
    return out


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "upstream/main"
    if not PLUGIN.is_dir():
        print("no plugin/ checkout: nothing to check")
        return 0
    changed = changed_lines(base)
    files = sorted(f for f in changed if (PLUGIN / f).exists())
    if not files:
        print(f"no Python changes against {base}")
        return 0
    ruff = ["uv", "run", "--frozen", "ruff"]
    config = ["--config", str(ROOT / "pyproject.toml")]
    owned = [f for f in files if f.startswith(OWNED)]
    found: list[str] = []
    # Upstream's files use their own style (Optional[...], other wrapping): there only the rules
    # that find bugs apply, and only on lines we changed. Our own files get the full rule set.
    for group, extra in ((files, ["--select", "F,B,E9,PLE"]), (owned, [])):
        if not group:
            continue
        raw = run([*ruff, "check", *config, *extra, "--output-format", "json", *group], PLUGIN)
        for item in json.loads(raw or "[]"):
            rel = str(Path(item["filename"]).relative_to(PLUGIN))
            line = item["location"]["row"]
            if line in changed[rel]:
                found.append(f"{rel}:{line}: {item['code']} {item['message']}")
    if owned and (bad := run([*ruff, "format", *config, "--check", *owned], PLUGIN)):
        found += [f"{name}: would be reformatted (ruff format)" for name in bad.splitlines()[:-1]]
    found += pyrefly(files, owned, changed)
    print("\n".join(sorted(set(found))) or f"plugin: clean against {base} ({len(files)} files)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
