import re


def normalize_query(query: str) -> str:
    return query.strip()


def compact_whitespace(value: str) -> str:
    return " ".join(value.strip().split())


def strip_sql_comments(value: str) -> str:
    without_block_comments = re.sub(r"/\*.*?\*/", " ", value, flags=re.DOTALL)
    without_line_comments = re.sub(r"(^|[\r\n])\s*--.*?(?=$|[\r\n])", r"\1", without_block_comments)
    return without_line_comments


def canonicalize_sql_for_comparison(value: str) -> str:
    without_comments = strip_sql_comments(value or "")
    without_semicolon = re.sub(r";+\s*$", "", without_comments)
    return compact_whitespace(without_semicolon).lower()


def has_meaningful_sql_change(original: str, candidate: str | None) -> bool:
    if not candidate or not candidate.strip():
        return False
    return canonicalize_sql_for_comparison(original) != canonicalize_sql_for_comparison(candidate)
