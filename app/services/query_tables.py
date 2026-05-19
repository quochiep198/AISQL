import re


_SQL_TABLE_PATTERNS = (
    r"\bfrom\s+([`\"\[]?[A-Za-z_][A-Za-z0-9_$]*(?:\s*\.\s*[`\"\[]?[A-Za-z_][A-Za-z0-9_$]*)?)",
    r"\bjoin\s+([`\"\[]?[A-Za-z_][A-Za-z0-9_$]*(?:\s*\.\s*[`\"\[]?[A-Za-z_][A-Za-z0-9_$]*)?)",
    r"\bupdate\s+([`\"\[]?[A-Za-z_][A-Za-z0-9_$]*(?:\s*\.\s*[`\"\[]?[A-Za-z_][A-Za-z0-9_$]*)?)",
    r"\binto\s+([`\"\[]?[A-Za-z_][A-Za-z0-9_$]*(?:\s*\.\s*[`\"\[]?[A-Za-z_][A-Za-z0-9_$]*)?)",
    r"\bdelete\s+from\s+([`\"\[]?[A-Za-z_][A-Za-z0-9_$]*(?:\s*\.\s*[`\"\[]?[A-Za-z_][A-Za-z0-9_$]*)?)",
)

_CTE_PATTERN = re.compile(r"\bwith\s+(.*?)\bselect\b", flags=re.IGNORECASE | re.DOTALL)
_CTE_NAME_PATTERN = re.compile(r"([A-Za-z_][A-Za-z0-9_$]*)\s+as\s*\(", flags=re.IGNORECASE)


def extract_table_names(query: str) -> list[str]:
    tables: list[str] = []
    seen: set[str] = set()
    compact = re.sub(r"\s+", " ", query or "").strip()
    cte_names = _extract_cte_names(compact)

    for pattern in _SQL_TABLE_PATTERNS:
        for raw_table in re.findall(pattern, compact, flags=re.IGNORECASE):
            table = _normalize_table_name(raw_table)
            if not table:
                continue
            key = table.lower()
            if key in cte_names:
                continue
            if key not in seen:
                seen.add(key)
                tables.append(table)

    return tables


def _extract_cte_names(query: str) -> set[str]:
    match = _CTE_PATTERN.search(query)
    if not match:
        return set()
    cte_block = match.group(1)
    return {name.lower() for name in _CTE_NAME_PATTERN.findall(cte_block)}


def _normalize_table_name(raw_table: str) -> str:
    cleaned = raw_table.strip().strip(",")
    if not cleaned or cleaned.startswith("("):
        return ""

    parts = []
    for part in cleaned.split("."):
        token = part.strip().strip("`\"[]")
        if token:
            parts.append(token)

    if not parts:
        return ""

    return parts[-1]
