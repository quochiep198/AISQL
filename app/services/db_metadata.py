import os
import sqlite3
from dataclasses import dataclass
from urllib.parse import unquote, urlparse

from fastapi import HTTPException

from app.schemas import DatabaseInspectResponse, InspectableDatabaseType
from app.services.input_preview import build_input_preview


@dataclass
class _ParsedConnection:
    database_type: InspectableDatabaseType
    database_name: str
    schema_name: str
    notes: list[str]


def infer_database_type_from_connection_string(connection_string: str) -> InspectableDatabaseType:
    scheme = (urlparse(connection_string).scheme or "").lower()
    if scheme in {"postgres", "postgresql", "postgresql+psycopg", "postgresql+psycopg2"}:
        return "postgres"
    if scheme in {"mysql", "mysql+pymysql"}:
        return "mysql"
    if scheme == "sqlite":
        return "sqlite"
    raise HTTPException(
        status_code=400,
        detail="Unsupported connection string scheme. Use postgres/postgresql, mysql, or sqlite.",
    )


def inspect_database_metadata(
    connection_string: str,
    database_type: InspectableDatabaseType | None,
    schema_name: str,
    table_filter: str,
    limit_tables: int,
    table_names: list[str] | None = None,
) -> DatabaseInspectResponse:
    resolved_database_type = database_type or infer_database_type_from_connection_string(connection_string)
    if resolved_database_type == "sqlite":
        schema_text, index_text, parsed = _inspect_sqlite(connection_string, table_filter, limit_tables, table_names)
    elif resolved_database_type == "postgres":
        schema_text, index_text, parsed = _inspect_postgres(
            connection_string,
            schema_name,
            table_filter,
            limit_tables,
            table_names,
        )
    elif resolved_database_type == "mysql":
        schema_text, index_text, parsed = _inspect_mysql(
            connection_string,
            schema_name,
            table_filter,
            limit_tables,
            table_names,
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported database type for metadata inspection")

    preview = build_input_preview(schema_text, index_text)
    notes = [
        *parsed.notes,
        f"Loaded {preview.schema_line_count} schema lines and {preview.index_line_count} index lines from database metadata.",
    ]

    return DatabaseInspectResponse(
        database_type=resolved_database_type,
        database_name=parsed.database_name,
        schema_name=parsed.schema_name,
        schema=schema_text,
        indexes=index_text,
        input_preview=preview,
        notes=notes,
    )


def _inspect_sqlite(
    connection_string: str,
    table_filter: str,
    limit_tables: int,
    table_names: list[str] | None = None,
) -> tuple[str, str, _ParsedConnection]:
    parsed_url = urlparse(connection_string)
    if parsed_url.scheme != "sqlite":
        raise HTTPException(status_code=400, detail="SQLite connection string must start with sqlite:///")

    db_path = _sqlite_path_from_url(parsed_url)
    if not db_path:
        raise HTTPException(status_code=400, detail="Invalid SQLite path")

    if not os.path.exists(db_path):
        raise HTTPException(status_code=400, detail="SQLite database file does not exist")

    table_pattern = table_filter.strip()

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Cannot connect to SQLite database: {exc}") from exc

    try:
        table_query = """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
        """
        params: list[object] = []
        if table_names:
            placeholders = ", ".join("?" for _ in table_names)
            table_query += f" AND name IN ({placeholders})"
            params.extend(table_names)
        elif table_pattern:
            table_query += " AND name LIKE ?"
            params.append(f"%{table_pattern}%")
        table_query += " ORDER BY name LIMIT ?"
        params.append(limit_tables)

        table_names = [row["name"] for row in conn.execute(table_query, params).fetchall()]
        schema_lines: list[str] = []
        index_lines: list[str] = []

        for table_name in table_names:
            escaped_table_name = table_name.replace("'", "''")
            columns = conn.execute(f"PRAGMA table_info('{escaped_table_name}')").fetchall()
            column_parts = []
            for column in columns:
                pk_marker = " PK" if column["pk"] else ""
                null_marker = " NOT NULL" if column["notnull"] else ""
                default_marker = f" DEFAULT {column['dflt_value']}" if column["dflt_value"] is not None else ""
                column_parts.append(f"{column['name']} {column['type'] or 'TEXT'}{pk_marker}{null_marker}{default_marker}".strip())
            schema_lines.append(f"{table_name}({', '.join(column_parts)})")

            indexes = conn.execute(f"PRAGMA index_list('{escaped_table_name}')").fetchall()
            for index in indexes:
                index_name = index["name"]
                unique_marker = " UNIQUE" if index["unique"] else ""
                escaped_index_name = index_name.replace("'", "''")
                index_cols = conn.execute(f"PRAGMA index_info('{escaped_index_name}')").fetchall()
                column_names = [item["name"] for item in index_cols if item["name"]]
                index_lines.append(f"{index_name}{unique_marker} ON {table_name}({', '.join(column_names)})".strip())
    finally:
        conn.close()

    return (
        "\n".join(schema_lines),
        "\n".join(index_lines),
        _ParsedConnection(
            database_type="sqlite",
            database_name=os.path.basename(db_path),
            schema_name="main",
            notes=["SQLite metadata was loaded from the local database file."],
        ),
    )


def _inspect_postgres(
    connection_string: str,
    schema_name: str,
    table_filter: str,
    limit_tables: int,
    table_names: list[str] | None = None,
) -> tuple[str, str, _ParsedConnection]:
    try:
        import psycopg
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="PostgreSQL inspection requires psycopg. Add it to the environment before using this feature.",
        ) from exc

    parsed_url = urlparse(connection_string)
    resolved_schema = schema_name.strip() or "public"
    db_name = unquote(parsed_url.path.lstrip("/")) or "postgres"

    try:
        with psycopg.connect(connection_string) as conn:
            with conn.cursor() as cur:
                table_rows = _fetch_postgres_tables(cur, resolved_schema, table_filter, limit_tables, table_names)
                schema_lines = _format_postgres_schema(table_rows)
                index_lines = _fetch_postgres_indexes(cur, resolved_schema, table_filter, limit_tables, table_names)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Cannot connect to PostgreSQL database: {exc}") from exc

    return (
        "\n".join(schema_lines),
        "\n".join(index_lines),
        _ParsedConnection(
            database_type="postgres",
            database_name=db_name,
            schema_name=resolved_schema,
            notes=["PostgreSQL metadata was loaded from information_schema and pg_indexes."],
        ),
    )


def _fetch_postgres_tables(
    cur,
    schema_name: str,
    table_filter: str,
    limit_tables: int,
    table_names: list[str] | None = None,
):
    sql = """
        SELECT table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = %s
    """
    params: list[object] = [schema_name]
    if table_names:
        placeholders = ", ".join(["%s"] * len(table_names))
        sql += f" AND table_name IN ({placeholders})"
        params.extend(table_names)
    elif table_filter.strip():
        sql += " AND table_name ILIKE %s"
        params.append(f"%{table_filter.strip()}%")
    sql += " ORDER BY table_name, ordinal_position"
    cur.execute(sql, params)
    rows = cur.fetchall()

    grouped: dict[str, list[tuple[str, str, str]]] = {}
    for table_name, column_name, data_type, is_nullable in rows:
        grouped.setdefault(table_name, []).append((column_name, data_type, is_nullable))

    return list(grouped.items())[:limit_tables]


def _format_postgres_schema(table_rows) -> list[str]:
    lines: list[str] = []
    for table_name, columns in table_rows:
        parts = []
        for column_name, data_type, is_nullable in columns:
            nullable_marker = "" if is_nullable == "YES" else " NOT NULL"
            parts.append(f"{column_name} {data_type}{nullable_marker}".strip())
        lines.append(f"{table_name}({', '.join(parts)})")
    return lines


def _fetch_postgres_indexes(
    cur,
    schema_name: str,
    table_filter: str,
    limit_tables: int,
    table_names: list[str] | None = None,
) -> list[str]:
    sql = """
        SELECT tablename, indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = %s
    """
    params: list[object] = [schema_name]
    if table_names:
        placeholders = ", ".join(["%s"] * len(table_names))
        sql += f" AND tablename IN ({placeholders})"
        params.extend(table_names)
    elif table_filter.strip():
        sql += " AND tablename ILIKE %s"
        params.append(f"%{table_filter.strip()}%")
    sql += " ORDER BY tablename, indexname"
    cur.execute(sql, params)
    rows = cur.fetchall()

    allowed_tables: set[str] = set()
    lines: list[str] = []
    for table_name, index_name, index_def in rows:
        allowed_tables.add(table_name)
        if len(allowed_tables) > limit_tables:
            break
        lines.append(f"{index_name} ON {table_name}: {index_def}")
    return lines


def _inspect_mysql(
    connection_string: str,
    schema_name: str,
    table_filter: str,
    limit_tables: int,
    table_names: list[str] | None = None,
) -> tuple[str, str, _ParsedConnection]:
    try:
        import pymysql
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="MySQL inspection requires PyMySQL. Add it to the environment before using this feature.",
        ) from exc

    config = _parse_mysql_url(connection_string)
    resolved_schema = schema_name.strip() or config["database"]

    try:
        conn = pymysql.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            database=config["database"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.Cursor,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Cannot connect to MySQL database: {exc}") from exc

    try:
        with conn.cursor() as cur:
            table_rows = _fetch_mysql_tables(cur, resolved_schema, table_filter, limit_tables, table_names)
            schema_lines = _format_mysql_schema(table_rows)
            index_lines = _fetch_mysql_indexes(cur, resolved_schema, table_filter, limit_tables, table_names)
    finally:
        conn.close()

    return (
        "\n".join(schema_lines),
        "\n".join(index_lines),
        _ParsedConnection(
            database_type="mysql",
            database_name=config["database"],
            schema_name=resolved_schema,
            notes=["MySQL metadata was loaded from information_schema columns and statistics."],
        ),
    )


def _parse_mysql_url(connection_string: str) -> dict[str, object]:
    parsed = urlparse(connection_string)
    if parsed.scheme not in {"mysql", "mysql+pymysql"}:
        raise HTTPException(status_code=400, detail="MySQL connection string must start with mysql://")

    database = unquote(parsed.path.lstrip("/"))
    if not database:
        raise HTTPException(status_code=400, detail="MySQL connection string must include a database name")

    return {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": database,
    }


def _fetch_mysql_tables(
    cur,
    schema_name: str,
    table_filter: str,
    limit_tables: int,
    table_names: list[str] | None = None,
):
    sql = """
        SELECT table_name, column_name, column_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = %s
    """
    params: list[object] = [schema_name]
    if table_names:
        placeholders = ", ".join(["%s"] * len(table_names))
        sql += f" AND table_name IN ({placeholders})"
        params.extend(table_names)
    elif table_filter.strip():
        sql += " AND table_name LIKE %s"
        params.append(f"%{table_filter.strip()}%")
    sql += " ORDER BY table_name, ordinal_position"
    cur.execute(sql, params)
    rows = cur.fetchall()

    grouped: dict[str, list[tuple[str, str, str]]] = {}
    for table_name, column_name, column_type, is_nullable in rows:
        grouped.setdefault(table_name, []).append((column_name, column_type, is_nullable))

    return list(grouped.items())[:limit_tables]


def _format_mysql_schema(table_rows) -> list[str]:
    lines: list[str] = []
    for table_name, columns in table_rows:
        parts = []
        for column_name, column_type, is_nullable in columns:
            nullable_marker = "" if is_nullable == "YES" else " NOT NULL"
            parts.append(f"{column_name} {column_type}{nullable_marker}".strip())
        lines.append(f"{table_name}({', '.join(parts)})")
    return lines


def _fetch_mysql_indexes(
    cur,
    schema_name: str,
    table_filter: str,
    limit_tables: int,
    table_names: list[str] | None = None,
) -> list[str]:
    sql = """
        SELECT table_name, index_name, non_unique, seq_in_index, column_name
        FROM information_schema.statistics
        WHERE table_schema = %s
    """
    params: list[object] = [schema_name]
    if table_names:
        placeholders = ", ".join(["%s"] * len(table_names))
        sql += f" AND table_name IN ({placeholders})"
        params.extend(table_names)
    elif table_filter.strip():
        sql += " AND table_name LIKE %s"
        params.append(f"%{table_filter.strip()}%")
    sql += " ORDER BY table_name, index_name, seq_in_index"
    cur.execute(sql, params)
    rows = cur.fetchall()

    grouped: dict[tuple[str, str, int], list[str]] = {}
    table_order: list[str] = []
    for table_name, index_name, non_unique, _seq_in_index, column_name in rows:
        key = (table_name, index_name, non_unique)
        grouped.setdefault(key, []).append(column_name)
        if table_name not in table_order:
            table_order.append(table_name)

    allowed_tables = set(table_order[:limit_tables])
    lines: list[str] = []
    for (table_name, index_name, non_unique), columns in grouped.items():
        if table_name not in allowed_tables:
            continue
        unique_marker = "" if non_unique else " UNIQUE"
        lines.append(f"{index_name}{unique_marker} ON {table_name}({', '.join(columns)})")
    return lines


def _sqlite_path_from_url(parsed_url) -> str:
    if parsed_url.netloc and parsed_url.path:
        return unquote(f"{parsed_url.netloc}{parsed_url.path}")
    if parsed_url.path:
        path = unquote(parsed_url.path)
        if path.startswith("/") and len(path) >= 3 and path[2] == ":":
            return path.lstrip("/")
        return path
    return ""
