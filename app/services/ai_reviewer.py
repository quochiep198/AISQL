import json
import logging
import os
import re
from typing import Any

from pydantic import ValidationError

from app.services.ai_review_schema import SQLReviewResult
from app.services.prompt_builder import build_review_prompt
from app.services.rule_analyzer import build_summary
from app.utils.sanitizer import canonicalize_sql_for_comparison

logger = logging.getLogger(__name__)
ALLOWED_SEVERITIES = {"low", "medium", "high", "critical"}
ALLOWED_CATEGORIES = {
    "correctness",
    "performance",
    "maintainability",
    "security",
    "safety",
    "readability",
}
ALLOWED_DETECTED_TYPES = {"select", "insert", "update", "delete", "merge", "ddl", "unknown"}
SUPPORTED_PROVIDERS = ("gemini", "groq", "claude")


class AIReviewError(RuntimeError):
    pass


def _format_ai_exception(provider: str, model: str, exc: Exception) -> str:
    raw_message = str(exc)
    normalized = raw_message.lower()
    if "request too large" in normalized or "tokens per minute" in normalized or "rate_limit_exceeded" in normalized:
        return (
            f"Yeu cau gui toi {provider} voi model `{model}` qua lon so voi gioi han token hien tai. "
            "Hay rut gon query/context/schema/index hoac doi sang model/goi dich vu co gioi han lon hon."
        )
    if "all connection attempts failed" in normalized or "connecterror" in normalized:
        return (
            f"Khong the ket noi toi {provider} voi model `{model}`. "
            "May hien tai khong mo duoc ket noi HTTPS toi endpoint cua nha cung cap. "
            "Hay kiem tra firewall, DNS, proxy/VPN, hoac thu mang khac. "
            "Neu ban dang o mang cong ty, co the can cau hinh `HTTPS_PROXY`."
        )
    if "certificate" in normalized or "ssl" in normalized or "tls" in normalized:
        return (
            f"Ket noi TLS/SSL toi {provider} voi model `{model}` that bai. "
            "Hay kiem tra proxy doanh nghiep, chung chi CA noi bo, hoac bien moi truong `SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE`."
        )
    return f"{provider.capitalize()} tra loi khi phan tich truy van voi model `{model}`: {raw_message}"


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
    return canonicalize_sql_for_comparison(raw)


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
                "category": _normalize_category(item.get("category")),
                "title": title,
                "description": description or "AI review không cung cấp mô tả chi tiết.",
                "suggestion": suggestion or "Kiểm tra lại cấu trúc query và xác minh bằng EXPLAIN.",
            }
        )

    return issues


def _normalize_category(raw: Any) -> str:
    value = _first_string(raw, "performance").lower()
    return value if value in ALLOWED_CATEGORIES else "performance"


def _normalize_detected_type(raw: Any) -> str:
    value = _first_string(raw, "unknown").lower()
    return value if value in ALLOWED_DETECTED_TYPES else "unknown"


def _normalize_index_suggestions(raw: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if not isinstance(raw, list):
        return items

    for item in raw:
        if not isinstance(item, dict):
            continue
        index_name = _first_string(item.get("index_name") or item.get("name"))
        reason = _first_string(item.get("reason"))
        sql = _first_string(item.get("sql"))
        columns_raw = item.get("columns")
        columns = [part.strip() for part in columns_raw if isinstance(part, str) and part.strip()] if isinstance(columns_raw, list) else []
        if not index_name and not columns and not sql:
            continue
        items.append(
            {
                "index_name": index_name or "suggested_index",
                "columns": columns,
                "reason": reason or "AI đề xuất index dựa trên điều kiện lọc hoặc sắp xếp trong query.",
                "sql": sql or "",
            }
        )
    return items


def _normalize_identifier(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "", value.strip().lower())


def _parse_existing_indexes(index_info: str) -> tuple[set[str], set[tuple[str, ...]]]:
    names: set[str] = set()
    column_sets: set[tuple[str, ...]] = set()

    for raw_line in index_info.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        name_match = re.match(r"([A-Za-z0-9_]+)", line)
        if name_match:
            names.add(_normalize_identifier(name_match.group(1)))

        for raw_columns in re.findall(r"\(([^()]+)\)", line):
            columns = []
            for part in raw_columns.split(","):
                token = _normalize_identifier(part)
                if token:
                    columns.append(token)
            if columns:
                column_sets.add(tuple(columns))

    return names, column_sets


def _is_related_index(candidate: tuple[str, ...], existing: tuple[str, ...]) -> bool:
    if not candidate or not existing:
        return False
    if candidate == existing:
        return True
    shortest = min(len(candidate), len(existing))
    return candidate[:shortest] == existing[:shortest]


def _dedupe_index_suggestions(index_suggestions: list[dict[str, Any]], index_info: str) -> tuple[list[dict[str, Any]], list[str]]:
    existing_names, existing_column_sets = _parse_existing_indexes(index_info)
    filtered: list[dict[str, Any]] = []
    notes: list[str] = []

    for item in index_suggestions:
        normalized_name = _normalize_identifier(item.get("index_name", ""))
        normalized_columns = tuple(
            _normalize_identifier(column)
            for column in item.get("columns", [])
            if _normalize_identifier(column)
        )

        if normalized_name and normalized_name in existing_names:
            notes.append(f"Bỏ qua index suggestion `{item.get('index_name', '')}` vì index này đã tồn tại.")
            continue

        if normalized_columns and normalized_columns in existing_column_sets:
            notes.append(
                f"Bỏ qua index suggestion `{item.get('index_name', '')}` vì tập cột ({', '.join(item.get('columns', []))}) đã có index tương ứng."
            )
            continue

        related_existing = next((cols for cols in existing_column_sets if _is_related_index(normalized_columns, cols)), None)
        if related_existing:
            existing_cols_text = ", ".join(related_existing)
            item = {
                **item,
                "reason": (
                    f"{item.get('reason', '')} Lưu ý: đã tồn tại index gần giống trên ({existing_cols_text}); "
                    "cần kiểm tra thứ tự cột, điều kiện WHERE/ORDER BY và execution plan trước khi tạo index mới."
                ).strip(),
            }
            notes.append(
                f"Index suggestion `{item.get('index_name', '')}` không bị bỏ qua, nhưng hệ thống đã phát hiện index gần giống trên ({existing_cols_text})."
            )

        filtered.append(item)

    return filtered, notes


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
    assumptions = _string_list(raw.get("assumptions"))
    notes = _string_list(raw.get("notes") or raw.get("warnings"))
    optimized_query = raw.get("optimized_query") or raw.get("optimizedQuery") or raw.get("rewrite")
    index_suggestions = _normalize_index_suggestions(raw.get("index_suggestions"))

    if optimized_query is not None and not isinstance(optimized_query, str):
        optimized_query = str(optimized_query)

    score = _normalize_score(raw.get("score"), issues)
    summary = _first_string(raw.get("summary"))
    if not summary:
        summary = build_summary(score, [])
        if issues:
            summary = build_summary(score, [type("IssueLike", (), issue)() for issue in issues])

    candidate = {
        "detected_type": _normalize_detected_type(raw.get("detected_type") or raw.get("detectedType")),
        "score": score,
        "summary": summary,
        "issues": issues,
        "improvements": improvements,
        "optimized_query": optimized_query,
        "index_suggestions": index_suggestions,
        "assumptions": assumptions,
        "notes": notes,
    }

    if not candidate["improvements"]:
        candidate["improvements"] = ["AI review chưa đưa ra đề xuất cải thiện cụ thể."]
    if not candidate["assumptions"]:
        candidate["assumptions"] = ["Thiếu một phần schema, index hoặc EXPLAIN nên một số kết luận mang tính ước lượng."]
    if not candidate["notes"]:
        candidate["notes"] = ["AI review đã được chuẩn hóa từ schema linh hoạt."]

    try:
        validated = SQLReviewResult.model_validate(candidate)
    except ValidationError:
        logger.exception("AI review JSON failed SQLReviewResult validation for database_type=%s", database_type)
        return None

    normalized = validated.model_dump()
    normalized["notes"] = [*normalized.get("assumptions", []), *normalized.get("notes", [])]
    normalized["detected_type"] = normalized.get("detected_type") or database_type
    return normalized


def _get_provider(provider_override: str | None = None) -> str:
    if provider_override and provider_override.strip():
        return provider_override.strip().lower()
    return os.getenv("AI_PROVIDER", "groq").strip().lower()


def _model_matches_provider(model: str, provider: str) -> bool:
    normalized = model.strip().lower()
    if not normalized:
        return False
    if provider == "claude":
        return normalized.startswith("claude-")
    if provider == "gemini":
        return normalized.startswith("gemini-")
    return True


def _get_model(provider: str) -> str:
    if provider == "claude":
        default_model = "claude-sonnet-4-20250514"
        provider_specific_key = "CLAUDE_MODEL"
    elif provider == "gemini":
        default_model = "gemini-2.5-flash"
        provider_specific_key = "GEMINI_MODEL"
    else:
        default_model = "llama-3.3-70b-versatile"
        provider_specific_key = "GROQ_MODEL"
    legacy_model = os.getenv("AI_MODEL", "").strip()
    provider_model = os.getenv(provider_specific_key, "").strip()

    if provider_model:
        return provider_model

    if legacy_model and _model_matches_provider(legacy_model, provider):
        return legacy_model

    if legacy_model:
        logger.warning(
            "Ignoring AI_MODEL=%s because it does not match provider=%s; falling back to %s or default model",
            legacy_model,
            provider,
            provider_specific_key,
        )

    return default_model


def is_ai_enabled(provider_override: str | None = None) -> bool:
    enabled = os.getenv("ENABLE_AI_REVIEW", "false").lower() == "true"
    if not enabled:
        logger.info("AI review is disabled because ENABLE_AI_REVIEW is not set to true")
    return enabled


def _get_api_key_name(provider: str) -> str:
    if provider == "claude":
        return "ANTHROPIC_API_KEY"
    if provider == "gemini":
        return "GEMINI_API_KEY"
    return "GROQ_API_KEY"


def _has_provider_key(provider: str) -> bool:
    return bool(os.getenv(_get_api_key_name(provider), "").strip())


def _get_provider_order(provider_override: str | None = None) -> list[str]:
    preferred = _get_provider(provider_override)
    ordered = [preferred]
    for provider in SUPPORTED_PROVIDERS:
        if provider != preferred:
            ordered.append(provider)
    return ordered


def _ensure_ai_ready(provider: str) -> None:
    key_name = _get_api_key_name(provider)
    if not os.getenv(key_name):
        raise AIReviewError(f"AI provider `{provider}` chưa được cấu hình đầy đủ: thiếu biến môi trường {key_name}.")


async def _call_groq(model: str, prompt: str, timeout_seconds: float) -> str | None:
    try:
        from openai import AsyncOpenAI
    except Exception:
        logger.warning("Groq provider selected but openai package is not available")
        raise AIReviewError("Provider Groq chưa sẵn sàng vì môi trường Python đang thiếu package `openai`.")

    client = AsyncOpenAI(
        api_key=os.getenv("GROQ_API_KEY"),
        base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
        timeout=timeout_seconds,
    )

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
    except Exception as exc:
        logger.exception("Groq AI review request failed for model=%s", model)
        raise AIReviewError(_format_ai_exception("groq", model, exc)) from exc

    return response.choices[0].message.content or ""


async def _call_claude(model: str, prompt: str, timeout_seconds: float) -> str | None:
    try:
        from anthropic import AsyncAnthropic
    except Exception:
        logger.warning("Claude provider selected but anthropic package is not available")
        raise AIReviewError("Provider Claude chưa sẵn sàng vì môi trường Python đang thiếu package `anthropic`.")

    client = AsyncAnthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        timeout=timeout_seconds,
    )

    try:
        response = await client.messages.create(
            model=model,
            max_tokens=2048,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as exc:
        logger.exception("Claude AI review request failed for model=%s", model)
        raise AIReviewError(_format_ai_exception("claude", model, exc)) from exc

    parts: list[str] = []
    for block in getattr(response, "content", []):
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


async def _call_gemini(model: str, prompt: str, timeout_seconds: float) -> str | None:
    try:
        from google import genai
        from google.genai import types
    except Exception:
        logger.warning("Gemini provider selected but google-genai package is not available")
        raise AIReviewError("Provider Gemini chﾆｰa s蘯ｵn sﾃng vﾃｬ mﾃｴi trﾆｰ盻拵g Python ﾄ疎ng thi蘯ｿu package `google-genai`.")

    try:
        async with genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
            http_options=types.HttpOptions(timeout=timeout_seconds),
        ).aio as client:
            response = await client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=2048,
                ),
            )
    except Exception as exc:
        logger.exception("Gemini AI review request failed for model=%s", model)
        raise AIReviewError(_format_ai_exception("gemini", model, exc)) from exc

    return getattr(response, "text", None) or ""


async def _call_provider(provider: str, model: str, prompt: str, timeout_seconds: float) -> str | None:
    if provider == "claude":
        return await _call_claude(model, prompt, timeout_seconds)
    if provider == "gemini":
        return await _call_gemini(model, prompt, timeout_seconds)
    return await _call_groq(model, prompt, timeout_seconds)


async def review_with_ai(
    database_type: str,
    query: str,
    context: str,
    optimization_goal: str,
    schema_info: str = "",
    index_info: str = "",
    ai_provider: str | None = None,
) -> dict[str, Any] | None:
    if not is_ai_enabled(ai_provider):
        return None

    timeout_seconds = _get_timeout_seconds()
    prompt = build_review_prompt(
        database_type=database_type,
        query=query,
        context=context,
        optimization_goal=optimization_goal,
        schema_info=schema_info,
        index_info=index_info,
    )
    requested_provider = _get_provider(ai_provider)
    attempt_notes: list[str] = []
    last_error: AIReviewError | None = None

    for provider in _get_provider_order(ai_provider):
        if not _has_provider_key(provider):
            continue

        model = _get_model(provider)
        try:
            _ensure_ai_ready(provider)
            content = await _call_provider(provider, model, prompt, timeout_seconds)

            if not content:
                raise AIReviewError(f"Provider `{provider}` khong tra ve noi dung phan tich cho model `{model}`.")

            parsed = _extract_json(content)
            if parsed is None:
                logger.warning("%s AI review returned non-JSON content for model=%s", provider, model)
                raise AIReviewError(f"AI provider `{provider}` tra ve du lieu khong dung JSON cho model `{model}`.")

            normalized = _normalize_ai_result(parsed, database_type)
            if normalized is None:
                logger.warning("%s AI review returned JSON but could not be normalized for model=%s", provider, model)
                raise AIReviewError(f"AI provider `{provider}` tra ve JSON khong dung schema mong doi cho model `{model}`.")

            filtered_index_suggestions, dedupe_notes = _dedupe_index_suggestions(
                normalized.get("index_suggestions", []),
                index_info,
            )
            normalized["index_suggestions"] = filtered_index_suggestions
            normalized["notes"] = [*attempt_notes, *normalized.get("notes", []), *dedupe_notes]

            optimized_query = normalized.get("optimized_query")
            if isinstance(optimized_query, str) and optimized_query.strip():
                if _canonicalize_query(optimized_query) == _canonicalize_query(query):
                    normalized["optimized_query"] = None
                    normalized["notes"] = [
                        *normalized.get("notes", []),
                        "AI review khong dua ra ban rewrite thuc su khac biet so voi query goc, nen optimized_query duoc bo qua.",
                    ]
                    if not normalized.get("improvements"):
                        normalized["improvements"] = ["Can bo sung schema, index va muc tieu toi uu de nhan duoc de xuat rewrite tot hon."]

            if provider != requested_provider:
                normalized["notes"] = [
                    f"AI fallback da chuyen tu provider `{requested_provider}` sang `{provider}`.",
                    *normalized.get("notes", []),
                ]

            return normalized
        except AIReviewError as exc:
            last_error = exc
            logger.warning("AI review failed for provider=%s model=%s; trying next provider if available", provider, model)
            attempt_notes.append(str(exc))

    if last_error:
        raise AIReviewError("Tat ca AI provider deu that bai. He thong se fallback sang rule-based review.")

    return None

    if provider == "claude":
        content = await _call_claude(model, prompt, timeout_seconds)
    elif provider == "gemini":
        content = await _call_gemini(model, prompt, timeout_seconds)
    else:
        content = await _call_groq(model, prompt, timeout_seconds)

    if not content:
        raise AIReviewError(f"Provider `{provider}` không trả về nội dung phân tích cho model `{model}`.")

    parsed = _extract_json(content)
    if parsed is None:
        logger.warning("%s AI review returned non-JSON content for model=%s", provider, model)
        raise AIReviewError(f"AI provider `{provider}` trả về dữ liệu không đúng JSON cho model `{model}`.")

    normalized = _normalize_ai_result(parsed, database_type)
    if normalized is None:
        logger.warning("%s AI review returned JSON but could not be normalized for model=%s", provider, model)
        raise AIReviewError(f"AI provider `{provider}` trả về JSON không đúng schema mong đợi cho model `{model}`.")

    filtered_index_suggestions, dedupe_notes = _dedupe_index_suggestions(
        normalized.get("index_suggestions", []),
        index_info,
    )
    normalized["index_suggestions"] = filtered_index_suggestions
    normalized["notes"] = [*normalized.get("notes", []), *dedupe_notes]

    optimized_query = normalized.get("optimized_query")
    if isinstance(optimized_query, str) and optimized_query.strip():
        if _canonicalize_query(optimized_query) == _canonicalize_query(query):
            normalized["optimized_query"] = None
            normalized["notes"] = [
                *normalized.get("notes", []),
                "AI review không đưa ra được bản rewrite thực sự khác biệt so với query gốc, nên optimized_query đã được bỏ qua.",
            ]
            if not normalized.get("improvements"):
                normalized["improvements"] = ["Cần bổ sung schema, index và mục tiêu tối ưu để đề xuất rewrite tốt hơn."]

    return normalized
