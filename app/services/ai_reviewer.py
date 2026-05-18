import json
import logging
import os
from typing import Any

from app.services.prompt_builder import build_review_prompt
from app.services.rule_analyzer import build_summary, calculate_score

logger = logging.getLogger(__name__)
ALLOWED_SEVERITIES = {"low", "medium", "high", "critical"}


def _extract_json(content: str) -> dict[str, Any] | None:
    text = content.strip()
    if not text:
        return None

    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        pass

    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            fenced = "\n".join(lines[1:-1]).strip()
            try:
                parsed = json.loads(fenced)
                return parsed if isinstance(parsed, dict) else None
            except Exception:
                pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and start < end:
        candidate = text[start : end + 1]
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None

    return None


def _get_timeout_seconds() -> float:
    raw = os.getenv("AI_TIMEOUT_SECONDS", "20")
    try:
        timeout = float(raw)
    except ValueError:
        logger.warning("Invalid AI_TIMEOUT_SECONDS=%r; falling back to 20 seconds", raw)
        return 20.0
    return max(1.0, timeout)


def _first_string(raw: Any, default: str = "") -> str:
    if isinstance(raw, str):
        return raw.strip()
    return default


def _canonicalize_query(raw: str) -> str:
    return " ".join(raw.lower().split())


def _string_list(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [item.strip() for item in raw if isinstance(item, str) and item.strip()]
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    return []


def _normalize_severity(raw: Any) -> str:
    value = _first_string(raw, "medium").lower()
    return value if value in ALLOWED_SEVERITIES else "medium"


def _normalize_issues(raw: Any) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    if not isinstance(raw, list):
        return issues

    for item in raw:
        if not isinstance(item, dict):
            continue
        title = _first_string(item.get("title") or item.get("name"))
        description = _first_string(item.get("description") or item.get("detail") or item.get("message"))
        suggestion = _first_string(item.get("suggestion") or item.get("fix") or item.get("recommendation"))

        if not title:
            continue

        issues.append(
            {
                "severity": _normalize_severity(item.get("severity")),
                "title": title,
                "description": description or "AI review khong cung cap mo ta chi tiet.",
                "suggestion": suggestion or "Kiem tra lai cau truc query va xac minh bang EXPLAIN.",
            }
        )

    return issues


def _normalize_score(raw: Any, issues: list[dict[str, str]]) -> int:
    if isinstance(raw, (int, float)):
        return max(0, min(100, int(raw)))

    if isinstance(raw, str):
        digits = "".join(char for char in raw if char.isdigit())
        if digits:
            return max(0, min(100, int(digits)))

    issue_weights = {"low": 8, "medium": 15, "high": 25, "critical": 40}
    score = 100
    for issue in issues:
        score -= issue_weights.get(issue["severity"], 10)
    return max(0, min(100, score))


def _normalize_ai_result(raw: dict[str, Any], database_type: str) -> dict[str, Any] | None:
    issues = _normalize_issues(raw.get("issues"))
    improvements = _string_list(raw.get("improvements") or raw.get("recommendations"))
    notes = _string_list(raw.get("notes") or raw.get("warnings") or raw.get("assumptions"))
    optimized_query = raw.get("optimized_query") or raw.get("optimizedQuery") or raw.get("rewrite")

    if optimized_query is not None and not isinstance(optimized_query, str):
        optimized_query = str(optimized_query)

    score = _normalize_score(raw.get("score"), issues)
    summary = _first_string(raw.get("summary"))
    if not summary:
        summary = build_summary(score, [])
        if issues:
            summary = build_summary(
                score,
                [
                    type("IssueLike", (), issue)()  # placeholder object with attributes
                    for issue in issues
                ],
            )

    normalized = {
        "detected_type": _first_string(raw.get("detected_type") or raw.get("detectedType"), database_type),
        "score": score,
        "summary": summary,
        "issues": issues,
        "improvements": improvements,
        "optimized_query": optimized_query,
        "notes": notes,
    }

    if not normalized["improvements"]:
        normalized["improvements"] = ["AI review chua dua ra de xuat cai thien cu the."]
    if not normalized["notes"]:
        normalized["notes"] = ["AI review da duoc chuan hoa tu schema linh hoat."]

    return normalized


def is_ai_enabled() -> bool:
    enabled = os.getenv("ENABLE_AI_REVIEW", "false").lower() == "true"
    has_key = bool(os.getenv("GROQ_API_KEY"))
    if not enabled:
        logger.info("AI review is disabled because ENABLE_AI_REVIEW is not set to true")
    elif not has_key:
        logger.warning("AI review is enabled but GROQ_API_KEY is missing")
    return enabled and has_key


async def review_with_ai(
    database_type: str,
    query: str,
    context: str,
    optimization_goal: str,
    schema_info: str = "",
    index_info: str = "",
) -> dict[str, Any] | None:
    """
    Optional AI review hook.

    Default flow remains rule-based. To enable AI review:
    - set ENABLE_AI_REVIEW=true
    - set GROQ_API_KEY
    - optional: set GROQ_BASE_URL
    - optional: set AI_MODEL
    - optional: set AI_TIMEOUT_SECONDS
    - install package openai
    """
    if not is_ai_enabled():
        return None

    try:
        from openai import AsyncOpenAI
    except Exception:
        logger.warning("AI review enabled but openai package is not available")
        return None

    model = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")
    timeout_seconds = _get_timeout_seconds()
    client = AsyncOpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        timeout=timeout_seconds,
    )
    prompt = build_review_prompt(
        database_type=database_type,
        query=query,
        context=context,
        optimization_goal=optimization_goal,
        schema_info=schema_info,
        index_info=index_info,
    )

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
    except Exception:
        logger.exception("Groq AI review request failed for database_type=%s model=%s", database_type, model)
        return None

    content = response.choices[0].message.content or ""
    parsed = _extract_json(content)
    if parsed is None:
        logger.warning("Groq AI review returned non-JSON content for model=%s", model)
        return None

    normalized = _normalize_ai_result(parsed, database_type)
    if normalized is None:
        logger.warning("Groq AI review returned JSON but could not be normalized for model=%s", model)
        return None

    optimized_query = normalized.get("optimized_query")
    if isinstance(optimized_query, str) and optimized_query.strip():
        if _canonicalize_query(optimized_query) == _canonicalize_query(query):
            normalized["optimized_query"] = None
            normalized["notes"] = [
                *normalized.get("notes", []),
                "AI review khong dua ra duoc ban rewrite thuc su khac biet so voi query goc, nen optimized_query da duoc bo qua.",
            ]
            if not normalized.get("improvements"):
                normalized["improvements"] = ["Can bo sung schema, index va muc tieu toi uu de de xuat rewrite tot hon."]

    return normalized
