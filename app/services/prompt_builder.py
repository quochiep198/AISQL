def build_review_prompt(
    database_type: str,
    query: str,
    context: str,
    optimization_goal: str,
    schema_info: str = "",
    index_info: str = "",
) -> str:
    schema_block = schema_info.strip() or "Not provided."
    index_block = index_info.strip() or "Not provided."
    context_block = context.strip() or "Not provided."

    return f"""You are a senior database performance engineer.

Review the following query:

Database type:
{database_type}

Query:
{query}

Schema details:
{schema_block}

Index details:
{index_block}

Additional context:
{context_block}

Optimization goal:
{optimization_goal}

Return JSON only with:
- detected_type
- score from 0 to 100
- summary
- issues: severity, title, description, suggestion
- improvements
- optimized_query
- notes

Rules:
- Do not invent schema details.
- If schema/index information is missing, clearly mention assumptions.
- When schema/index information is provided, use it directly in your reasoning and rewrite.
- Prefer safe suggestions.
- Do not execute the query.
- All natural-language fields must be written in Vietnamese.
- Keep `severity` in English only, using one of: low, medium, high, critical.
- `optimized_query` must be a genuinely improved rewrite, not a copy of the original query.
- If you cannot produce a meaningfully better and safer rewrite, set `optimized_query` to null and explain why in `notes`.
- When you provide `optimized_query`, also make `improvements` specific to the exact rewrite you proposed.
- Return valid JSON only. Do not use markdown fences. Do not add explanations outside JSON.
"""
