import re


_SQL_TABLE_PATTERNS = (
    r"\bfrom\s+([`\"\[]?[A-Za-z_][A-Za-z0-9_$]*(?:\.[`\"\[]?[A-Za-z_][A-Za-z0-9_$]*)?)",
    r"\bjoin\s+([`\"\[]?[A-Za-z_][A-Za-z0-9_$]*(?:\.[`\"\[]?[A-Za-z_][A-Za-z0-9_$]*)?)",
    r"\bupdate\s+([`\"\[]?[A-Za-z_][A-Za-z0-9_$]*(?:\.[`\"\[]?[A-Za-z_][A-Za-z0-9_$]*)?)",
    r"\binto\s+([`\"\[]?[A-Za-z_][A-Za-z0-9_$]*(?:\.[`\"\[]?[A-Za-z_][A-Za-z0-9_$]*)?)",
    r"\bdelete\s+from\s+([`\"\[]?[A-Za-z_][A-Za-z0-9_$]*(?:\.[`\"\[]?[A-Za-z_][A-Za-z0-9_$]*)?)",
)


def extract_table_names(query: str) -> list[str]:
    tables: list[str] = []
    seen: set[str] = set()
    compact = re.sub(r"\s+", " ", query or "")

    for pattern in _SQL_TABLE_PATTERNS:
        for raw_table in re.findall(pattern, compact, flags=re.IGNORECASE):
            table = _normalize_table_name(raw_table)
            if not table:
                continue
            key = table.lower()
            if key not in seen:
                seen.add(key)
                tables.append(table)

    return tables


def _normalize_table_name(raw_table: str) -> str:
    cleaned = raw_table.strip().strip(",")
    if not cleaned:
        return ""

    parts = [part.strip("`\"[]]") for part in cleaned.split(".") if part.strip("`\"[]]")]
    if not parts:
        return ""

    return parts[-1]
