def _clean_block(value: str) -> str:
    return value.strip()


def build_review_context(context: str, schema_info: str, index_info: str) -> str:
    cleaned_context = _clean_block(context)
    return cleaned_context
