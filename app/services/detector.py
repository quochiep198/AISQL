import json
import re

SQL_KEYWORDS = (
    "select", "insert", "update", "delete", "with", "create", "alter", "drop"
)


def detect_query_type(query: str, requested_type: str = "auto") -> str:
    if requested_type and requested_type != "auto":
        return requested_type

    text = query.strip()
    lower = text.lower()

    if _looks_like_mongodb(text, lower):
        return "mongodb"

    if lower.startswith(SQL_KEYWORDS) or re.search(r"\bfrom\b|\bwhere\b|\bjoin\b", lower):
        return "generic_sql"

    return "unknown"


def _looks_like_mongodb(text: str, lower: str) -> bool:
    if any(token in lower for token in ("db.", "aggregate(", "find(", "$match", "$lookup", "$project")):
        return True

    try:
        parsed = json.loads(text)
        return isinstance(parsed, (dict, list))
    except Exception:
        return False
