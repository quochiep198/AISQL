import re

from app.schemas import InputPreview


def build_input_preview(schema_info: str, index_info: str) -> InputPreview:
    schema_lines = _non_empty_lines(schema_info)
    index_lines = _non_empty_lines(index_info)

    detected_entities = _extract_entities(schema_lines)
    detected_index_columns = _extract_index_columns(index_lines)

    return InputPreview(
        schema_lines=schema_lines[:8],
        index_lines=index_lines[:8],
        detected_entities=detected_entities[:12],
        detected_index_columns=detected_index_columns[:12],
        schema_line_count=len(schema_lines),
        index_line_count=len(index_lines),
    )


def _non_empty_lines(raw: str) -> list[str]:
    return [line.strip() for line in raw.splitlines() if line.strip()]


def _extract_entities(lines: list[str]) -> list[str]:
    entities: list[str] = []
    seen: set[str] = set()

    for line in lines:
        match = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\s*[\(:]", line)
        if not match:
            continue
        entity = match.group(1)
        key = entity.lower()
        if key not in seen:
            seen.add(key)
            entities.append(entity)

    return entities


def _extract_index_columns(lines: list[str]) -> list[str]:
    columns: list[str] = []
    seen: set[str] = set()

    for line in lines:
        for raw_column in re.findall(r"\(([^()]+)\)", line):
            for part in raw_column.split(","):
                token_match = re.search(r"[A-Za-z_][A-Za-z0-9_]*", part.strip())
                if not token_match:
                    continue
                column = token_match.group(0)
                key = column.lower()
                if key not in seen:
                    seen.add(key)
                    columns.append(column)

    return columns
