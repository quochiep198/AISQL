def _truncate_block(value: str, *, max_lines: int, max_chars: int) -> str:
    cleaned = value.strip()
    if not cleaned:
        return ""

    lines = [line.rstrip() for line in cleaned.splitlines() if line.strip()]
    truncated_by_lines = len(lines) > max_lines
    limited_lines = lines[:max_lines]
    limited = "\n".join(limited_lines)

    truncated_by_chars = len(limited) > max_chars
    if truncated_by_chars:
        limited = limited[: max_chars - 80].rstrip()

    if truncated_by_lines or truncated_by_chars:
        limited += "\n[Da rut gon metadata de tranh vuot gioi han token cua model.]"

    return limited


def build_review_prompt(
    database_type: str,
    query: str,
    context: str = "",
    optimization_goal: str = "",
    schema_info: str = "",
    index_info: str = "",
    explain_plan: str = "",
) -> str:
    query_block = _truncate_block(query, max_lines=120, max_chars=4000) or "Chua cung cap."
    schema_block = _truncate_block(schema_info, max_lines=24, max_chars=2500) or "Chua cung cap."
    index_block = _truncate_block(index_info, max_lines=18, max_chars=1800) or "Chua cung cap."
    context_block = _truncate_block(context, max_lines=12, max_chars=1200) or "Chua cung cap."
    explain_block = _truncate_block(explain_plan, max_lines=12, max_chars=1200) or "Chua cung cap."
    goal_block = optimization_goal.strip() or "Cai thien tinh dung dan, hieu nang, kha nang doc hieu va do an toan khi chay production."

    return f"""You are a senior database performance engineer and SQL reviewer.

Review the SQL query below.

Database type / SQL dialect:
{database_type}

SQL query:
{query_block}

Schema details:
{schema_block}

Index details:
{index_block}

EXPLAIN / execution plan:
{explain_block}

Additional context:
{context_block}

Optimization goal:
{goal_block}

Return ONLY valid JSON matching this exact schema:

{{
  "detected_type": "select | insert | update | delete | merge | ddl | unknown",
  "score": 0,
  "summary": "",
  "issues": [
    {{
      "severity": "low | medium | high | critical",
      "category": "correctness | performance | maintainability | security | safety | readability",
      "title": "",
      "description": "",
      "suggestion": ""
    }}
  ],
  "improvements": [
    ""
  ],
  "optimized_query": null,
  "index_suggestions": [
    {{
      "index_name": "",
      "columns": [""],
      "reason": "",
      "sql": ""
    }}
  ],
  "assumptions": [
    ""
  ],
  "notes": [
    ""
  ]
}}

Rules:
- Return JSON only.
- Do not use markdown fences.
- Do not add explanations outside JSON.
- All natural-language fields must be written in Vietnamese.
- Keep enum values in English.
- `score` must be an integer from 0 to 100.
- Do not execute the query.
- Do not invent schema, columns, indexes, constraints, or data distribution.
- If schema/index/explain information is missing, mention that limitation in `assumptions`.
- Use only syntax valid for the provided database type / SQL dialect.
- Review correctness, performance, maintainability, readability, security, locking risk, NULL handling, duplicate row risk, full scan risk, join risk, and production safety.
- Prefer safe, practical, low-risk suggestions.
- Only provide `optimized_query` when the rewrite is meaningfully better and safe.
- If no safe meaningful rewrite is possible, set `optimized_query` to null.
- Do not rewrite just to make the query look different.
- When `optimized_query` is provided, `improvements` must explain the exact improvements in that rewrite.
- When suggesting indexes, only suggest indexes based on columns visible in the query or schema.
"""
