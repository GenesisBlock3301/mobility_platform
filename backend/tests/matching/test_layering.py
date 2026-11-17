"""The matching engine must stay free of framework and database imports."""

import ast
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[2] / "app" / "matching"
FORBIDDEN = (
    "fastapi",
    "sqlalchemy",
    "asyncpg",
    "starlette",
    "pydantic",
    "app.routers",
    "app.services",
    "app.repositories",
    "app.models",
    "app.schemas",
    "app.infra",
)


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_engine_imports_nothing_forbidden():
    offenders = {}
    for path in ENGINE_DIR.glob("*.py"):
        bad = {n for n in _imports(path) if n.startswith(FORBIDDEN)}
        if bad:
            offenders[path.name] = bad
    assert offenders == {}
