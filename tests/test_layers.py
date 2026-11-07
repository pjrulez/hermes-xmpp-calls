"""The Jingle layer stays pure: no network, no media, no Hermes."""

import ast
from pathlib import Path

FORBIDDEN = {"aiortc", "slixmpp", "hermes", "asyncio", "socket"}


def test_jingle_imports_nothing_heavy() -> None:
    for path in (Path(__file__).parent.parent / "src/xmpp_calls/jingle").glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            names = (
                [a.name for a in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
                if isinstance(node, ast.ImportFrom) and node.level == 0
                else []
            )
            assert not FORBIDDEN & {n.split(".")[0] for n in names}, (path.name, names)
