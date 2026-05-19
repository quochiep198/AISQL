import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import ConnectionValidationResponse, DatabaseInspectRequest, DatabaseInspectResponse, ReviewRequest, ReviewResponse
from app.services.ai_reviewer import AIReviewError, review_with_ai
from app.services.context_builder import build_review_context
from app.services.db_metadata import infer_database_type_from_connection_string, inspect_database_metadata
from app.services.detector import detect_query_type
from app.services.input_preview import build_input_preview
from app.services.query_tables import extract_table_names
from app.services.rule_analyzer import analyze_rules, build_summary, calculate_score
from app.services.sql_syntax import validate_sql_syntax
from app.utils.sanitizer import has_meaningful_sql_change, normalize_query

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="SQL Query Review API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/database/introspect", response_model=DatabaseInspectResponse)
def introspect_database(payload: DatabaseInspectRequest) -> DatabaseInspectResponse:
    return inspect_database_metadata(
        connection_string=payload.connection_string,
        database_type=payload.database_type,
        schema_name=payload.schema_name,
        table_filter=payload.table_filter,
        limit_tables=payload.limit_tables,
    )


@app.post("/api/database/validate", response_model=ConnectionValidationResponse)
def validate_database_connection(payload: DatabaseInspectRequest) -> ConnectionValidationResponse:
    metadata = inspect_database_metadata(
        connection_string=payload.connection_string,
        database_type=payload.database_type,
        schema_name=payload.schema_name,
        table_filter=payload.table_filter,
        limit_tables=1,
    )
    return ConnectionValidationResponse(
        valid=True,
        database_type=metadata.database_type,
        database_name=metadata.database_name,
        schema_name=metadata.schema_name,
        message="Connection string is valid and the database connection succeeded.",
        notes=metadata.notes,
    )


@app.post("/api/review", response_model=ReviewResponse)
async def review(payload: ReviewRequest) -> ReviewResponse:
    query = normalize_query(payload.query)
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")

    detected_type = detect_query_type(query, payload.database_type)
    schema_info = payload.schema_info
    index_info = payload.index_info
    auto_notes: list[str] = []

    if payload.auto_introspect and payload.connection_string.strip():
        inspect_type = payload.metadata_database_type
        if not inspect_type:
            inspect_type = infer_database_type_from_connection_string(payload.connection_string)
        if inspect_type in {"mysql", "postgres", "sqlite"}:
            table_names = extract_table_names(query)
            metadata = inspect_database_metadata(
                connection_string=payload.connection_string,
                database_type=inspect_type,
                schema_name=payload.schema_name,
                table_filter=payload.table_filter,
                limit_tables=payload.limit_tables,
                table_names=table_names or None,
            )
            schema_info = metadata.schema
            index_info = metadata.indexes
            if table_names:
                auto_notes.append(f"Auto-loaded schema/index for tables found in query: {', '.join(table_names[:8])}.")
            else:
                auto_notes.append("Auto-loaded schema/index from database before review.")
            auto_notes.extend(metadata.notes)

    input_preview = build_input_preview(schema_info=schema_info, index_info=index_info)
    review_context = build_review_context(
        context=payload.context,
        schema_info=schema_info,
        index_info=index_info,
    )

    syntax_issues = validate_sql_syntax(query, detected_type)
    if syntax_issues:
        syntax_notes = [
            *auto_notes,
            "Phát hiện lỗi cú pháp SQL trước khi chạy review tối ưu.",
            "Cần sửa lỗi syntax trước, sau đó mới đánh giá chính xác về hiệu năng và index.",
        ]
        syntax_improvements = [
            "Sửa toàn bộ lỗi cú pháp đang được chỉ ra trong phần vấn đề.",
            "Sau khi query chạy được, chạy lại review để nhận gợi ý tối ưu và index chính xác hơn.",
        ]
        syntax_score = calculate_score(syntax_issues)
        return ReviewResponse(
            detected_type=detected_type,
            score=syntax_score,
            summary="Query đang có lỗi cú pháp, nên chưa thể phân tích tối ưu một cách đáng tin cậy.",
            issues=syntax_issues,
            improvements=syntax_improvements,
            optimized_query=None,
            index_suggestions=[],
            assumptions=["Chưa thực hiện AI review hoặc rule-based optimization sâu vì query chưa hợp lệ về cú pháp."],
            notes=syntax_notes,
            input_preview=input_preview,
        )

    ai_error_note: str | None = None
    try:
        ai_result = await review_with_ai(
            database_type=detected_type,
            query=query,
            context=review_context,
            optimization_goal=payload.optimization_goal,
            schema_info=schema_info,
            index_info=index_info,
            ai_provider=payload.ai_provider,
        )
    except AIReviewError as exc:
        ai_result = None
        ai_error_note = str(exc)

    if ai_result:
        try:
            if not has_meaningful_sql_change(query, ai_result.get("optimized_query")):
                ai_result["optimized_query"] = None
            ai_result["input_preview"] = input_preview.model_dump()
            ai_result["notes"] = [*auto_notes, *ai_result.get("notes", [])]
            return ReviewResponse(**ai_result)
        except Exception:
            pass

    issues, improvements, notes, optimized_query = analyze_rules(
        query=query,
        detected_type=detected_type,
        schema_info=schema_info,
        index_info=index_info,
    )
    score = calculate_score(issues)
    if not has_meaningful_sql_change(query, optimized_query):
        optimized_query = None

    if ai_result:
        notes.append("AI review response was invalid; using rule-based result.")
    if ai_error_note:
        notes.append(ai_error_note)
        notes.append("AI review khong kha dung; da fallback sang rule-based review.")

    return ReviewResponse(
        detected_type=detected_type,
        score=score,
        summary=build_summary(score, issues),
        issues=issues,
        improvements=improvements,
        optimized_query=optimized_query,
        index_suggestions=[],
        assumptions=[],
        notes=[*auto_notes, *notes],
        input_preview=input_preview,
    )
