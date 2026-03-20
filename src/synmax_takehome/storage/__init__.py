"""Persistence layer: use `synmax_takehome.storage.schema` and `synmax_takehome.storage.repository` directly."""

from synmax_takehome.storage.schema import TABLE_COLUMNS, TABLE_NAME, create_table_ddl

__all__ = ["TABLE_COLUMNS", "TABLE_NAME", "create_table_ddl"]
