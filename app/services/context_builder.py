def _clean_block(value: str) -> str:
    return value.strip()


def build_review_context(context: str, schema_info: str, index_info: str) -> str:
    sections: list[str] = []

    cleaned_context = _clean_block(context)
    cleaned_schema = _clean_block(schema_info)
    cleaned_indexes = _clean_block(index_info)

    if cleaned_schema:
        sections.append(f"Schema:\n{cleaned_schema}")
    if cleaned_indexes:
        sections.append(f"Indexes:\n{cleaned_indexes}")
    if cleaned_context:
        sections.append(f"Additional context:\n{cleaned_context}")

    return "\n\n".join(sections)
