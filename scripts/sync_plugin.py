"""Copy the call library into the plugin fork as `plugin/calls/` (source of truth: src/xmpp_calls)
and its engine tests as `plugin/tests/calls_engine/` (imports rewritten to the plugin layout).

devtools/ stays out. Run `python scripts/sync_plugin.py` after changing src/ or tests/, or with
`--check` to fail when the copy is stale.
"""

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC, DST = ROOT / "src" / "xmpp_calls", ROOT / "plugin" / "calls"
SKIP = {"devtools", "__pycache__"}
TESTS, TESTS_DST = ROOT / "tests", ROOT / "plugin" / "tests" / "calls_engine"
CAPTURES = ROOT / "RESEARCH" / "evidence" / "jmi-jingle-captures"
NOT_PORTED = {"__init__.py", "test_env.py", "test_layers.py", "test_leaks.py"}


PRIVATE_NAMES = (
    ROOT / ".scratch" / "private_names.json"
)  # git-ignored [[pattern, replacement], ...]
PRIVATE = json.loads(PRIVATE_NAMES.read_text()) if PRIVATE_NAMES.exists() else []


def neutral(text: str) -> str:
    for pattern, replacement in PRIVATE:
        text = re.sub(pattern, replacement, text)
    return text


def port(source: str) -> bytes:
    """The dev tree imports `xmpp_calls`; the plugin ships the same code as `calls`."""
    source = neutral(re.sub(r"\bxmpp_calls\b", "calls", source))
    source = source.replace("from tests.", "from .")
    source = source.replace(
        'Path(__file__).parent.parent / "RESEARCH/evidence/jmi-jingle-captures"',
        'Path(__file__).parent / "captures"',
    )
    return source.encode()


def files() -> dict[Path, Path]:
    return {
        path.relative_to(SRC): path
        for path in SRC.rglob("*.py")
        if not SKIP & set(path.relative_to(SRC).parts)
    }


def sync_tests(check: bool) -> list[str]:
    wanted: dict[Path, bytes] = {
        TESTS_DST / path.name: port(path.read_text())
        for path in TESTS.glob("*.py")
        if path.name not in NOT_PORTED
    }
    wanted |= {
        TESTS_DST / "captures" / path.name: neutral(path.read_text()).encode()
        for path in CAPTURES.iterdir()
        if path.suffix in {".xml", ".txt"}
    }
    keep = {TESTS_DST / "__init__.py", TESTS_DST / "conftest.py"}
    stale = [
        str(p.relative_to(TESTS_DST))
        for p, data in wanted.items()
        if not p.exists() or p.read_bytes() != data
    ]
    extra = [
        p
        for p in TESTS_DST.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p not in wanted and p not in keep
    ]
    if not check:
        for p, data in wanted.items():
            if str(p.relative_to(TESTS_DST)) in stale:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(data)
                print(f"synced: tests/calls_engine/{p.relative_to(TESTS_DST)}")
        for p in extra:
            p.unlink()
    return stale + [str(p.relative_to(TESTS_DST)) for p in extra]


def main() -> int:
    wanted = files()
    stale = [
        rel
        for rel, src in wanted.items()
        if not (DST / rel).exists() or (DST / rel).read_bytes() != src.read_bytes()
    ]
    extra = [
        p.relative_to(DST)
        for p in DST.rglob("*.py")
        if "__pycache__" not in p.parts and p.relative_to(DST) not in wanted
    ]
    if "--check" in sys.argv:
        tests = sync_tests(check=True)
        for rel in [*stale, *extra, *tests]:
            print(f"stale: {rel}")
        return 1 if stale or extra or tests else 0
    for rel in extra:
        (DST / rel).unlink()
    for rel in stale:
        (DST / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(wanted[rel], DST / rel)
        print(f"synced: {rel}")
    sync_tests(check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
