from dataclasses import dataclass

from sqlalchemy import Engine, inspect
from sqlmodel import SQLModel


@dataclass(frozen=True)
class SchemaReport:
    status: str
    missing_tables: list[str]
    missing_columns: dict[str, list[str]]


def check_database_schema(engine: Engine) -> SchemaReport:
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    expected_tables = {table.name: table for table in SQLModel.metadata.sorted_tables}

    missing_tables = sorted(table_name for table_name in expected_tables if table_name not in existing_tables)
    missing_columns: dict[str, list[str]] = {}

    for table_name, table in expected_tables.items():
        if table_name in missing_tables:
            continue
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        expected_columns = {column.name for column in table.columns}
        missing = sorted(expected_columns - existing_columns)
        if missing:
            missing_columns[table_name] = missing

    status = "ok" if not missing_tables and not missing_columns else "mismatch"
    return SchemaReport(status=status, missing_tables=missing_tables, missing_columns=missing_columns)
