def normalize_query(query: str) -> str:
    return query.strip()


def compact_whitespace(value: str) -> str:
    return " ".join(value.strip().split())
