"""Lint what we changed in the plugin fork (`plugin/`, the branch checked out there) against
`upstream/main`. Files we own outright (`call_packages.py`, `calls/`) get the dev project's full
ruff rules and format check. Upstream's files (`adapter.py`, tests) use their own style, so only
bug-finding rules (F, B, E9, PLE) apply there, and only to lines we changed. Exit 1 on a finding.

    uv run python scripts/check_plugin.py [base]      # base defaults to upstream/main
"""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "plugin"
OWNED = ("call_packages.py", "calls/")


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
            if group is owned or line in changed[rel]:
                found.append(f"{rel}:{line}: {item['code']} {item['message']}")
    if owned and (bad := run([*ruff, "format", *config, "--check", *owned], PLUGIN)):
        found += [f"{name}: would be reformatted (ruff format)" for name in bad.splitlines()[:-1]]
    print("\n".join(sorted(set(found))) or f"plugin: clean against {base} ({len(files)} files)")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
