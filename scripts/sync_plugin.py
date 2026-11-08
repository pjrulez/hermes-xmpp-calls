"""Copy the call library into the plugin fork as `plugin/calls/` (source of truth: src/xmpp_calls).

devtools/ stays out. Run `python scripts/sync_plugin.py` after changing src/, or with `--check`
to fail when the copy is stale.
"""

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC, DST = ROOT / "src" / "xmpp_calls", ROOT / "plugin" / "calls"
SKIP = {"devtools", "__pycache__"}


def files() -> dict[Path, Path]:
    return {
        path.relative_to(SRC): path
        for path in SRC.rglob("*.py")
        if not SKIP & set(path.relative_to(SRC).parts)
    }


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
        for rel in [*stale, *extra]:
            print(f"stale: {rel}")
        return 1 if stale or extra else 0
    for rel in extra:
        (DST / rel).unlink()
    for rel in stale:
        (DST / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(wanted[rel], DST / rel)
        print(f"synced: {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
