import ast
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


ROOT_MIGRATION = Path(
    "libs/db/migrations/alembic/versions/5cf84776dfef_auto_schema_sync.py"
)
STANDALONE_VERSIONS = Path("apps/bilgeapi/migrations/versions")


def _upgrade_operation_names(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    upgrade = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "upgrade"
    )
    return [
        node.func.attr
        for node in ast.walk(upgrade)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "op"
    ]


def test_root_reconciliation_migration_is_additive_only():
    operations = _upgrade_operation_names(ROOT_MIGRATION)
    destructive = {
        "alter_column",
        "drop_column",
        "drop_constraint",
        "drop_index",
        "drop_table",
    }

    assert destructive.isdisjoint(operations)

    source = ROOT_MIGRATION.read_text(encoding="utf-8").upper()
    assert source.count("_ADD_COLUMN_IF_MISSING(") >= 13
    assert "DROP TABLE" not in source


def test_standalone_migration_history_is_preserved():
    assert (STANDALONE_VERSIONS / "0001_initial_schema.py").is_file()
    assert (STANDALONE_VERSIONS / "e1f8a846b9c9_add_tenant_id_scoping.py").is_file()
    assert not (STANDALONE_VERSIONS / "2744482ce0d0_bilgeapi_baseline.py").exists()


def test_standalone_alembic_has_one_canonical_head():
    config = Config("apps/bilgeapi/alembic.ini")
    script = ScriptDirectory.from_config(config)

    assert script.get_heads() == ["e1f8a846b9c9"]
