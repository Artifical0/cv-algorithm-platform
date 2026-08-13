from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSIONS = ROOT / "database" / "migrations" / "versions"
EXPECTED_INITIAL_TABLES = {
    "users",
    "user_sessions",
    "projects",
    "project_memberships",
    "algorithm_versions",
    "build_jobs",
    "build_job_logs",
    "image_assets",
    "inference_tasks",
    "algorithm_comparisons",
    "comparison_tasks",
    "runtime_nodes",
    "runtime_instances",
    "media_sources",
    "media_inference_runs",
    "media_run_tasks",
    "workflows",
    "workflow_nodes",
    "workflow_node_dependencies",
    "workflow_runs",
    "workflow_run_tasks",
    "autoscaling_policies",
    "audit_events",
}


def assigned_constant(tree: ast.Module, name: str) -> str | None:
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == name:
                return ast.literal_eval(node.value)
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return ast.literal_eval(node.value)
    raise AssertionError(f"migration does not declare {name}")


def function_names(tree: ast.Module) -> set[str]:
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def called_tables(tree: ast.Module, operation: str) -> set[str]:
    tables: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != operation or not node.args:
            continue
        if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            tables.add(node.args[0].value)
    return tables


def foreign_key_targets(tree: ast.Module) -> set[str]:
    targets: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "ForeignKeyConstraint" or len(node.args) < 2:
            continue
        remote_columns = node.args[1]
        if not isinstance(remote_columns, (ast.List, ast.Tuple)):
            continue
        for element in remote_columns.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                targets.add(element.value.split(".", maxsplit=1)[0])
    return targets


def main() -> None:
    paths = sorted(VERSIONS.glob("*.py"))
    assert paths, "no database migrations found"
    revisions: dict[str, str | None] = {}
    all_tables: set[str] = set()
    all_dropped_tables: set[str] = set()
    all_foreign_key_targets: set[str] = set()
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        revision = assigned_constant(tree, "revision")
        parent = assigned_constant(tree, "down_revision")
        assert revision, f"{path.name} has an empty revision"
        assert revision not in revisions, f"duplicate migration revision: {revision}"
        assert {"upgrade", "downgrade"} <= function_names(tree), (
            f"{path.name} must define upgrade() and downgrade()"
        )
        revisions[revision] = parent
        all_tables |= called_tables(tree, "create_table")
        all_dropped_tables |= called_tables(tree, "drop_table")
        all_foreign_key_targets |= foreign_key_targets(tree)

    for revision, parent in revisions.items():
        assert parent is None or parent in revisions, (
            f"migration {revision} references missing parent {parent}"
        )
    parents = {parent for parent in revisions.values() if parent is not None}
    heads = set(revisions) - parents
    assert len(heads) == 1, f"expected one migration head, found {sorted(heads)}"

    for revision in revisions:
        visited: set[str] = set()
        cursor: str | None = revision
        while cursor is not None:
            assert cursor not in visited, f"cycle detected at migration {cursor}"
            visited.add(cursor)
            cursor = revisions[cursor]

    missing_tables = EXPECTED_INITIAL_TABLES - all_tables
    assert not missing_tables, f"initial migration is missing tables: {sorted(missing_tables)}"
    assert all_dropped_tables == all_tables, (
        "downgrade table set differs from upgrade: "
        f"missing={sorted(all_tables - all_dropped_tables)}, "
        f"unexpected={sorted(all_dropped_tables - all_tables)}"
    )
    missing_foreign_targets = all_foreign_key_targets - all_tables
    assert not missing_foreign_targets, (
        f"foreign keys reference missing tables: {sorted(missing_foreign_targets)}"
    )
    print(
        f"database migration chain valid: {len(revisions)} revision(s), "
        f"head={next(iter(heads))}, tables={len(all_tables)}"
    )


if __name__ == "__main__":
    main()
