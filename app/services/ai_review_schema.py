from typing import Literal

from pydantic import BaseModel, Field


class Issue(BaseModel):
    severity: Literal["low", "medium", "high", "critical"]
    category: Literal[
        "correctness",
        "performance",
        "maintainability",
        "security",
        "safety",
        "readability",
    ]
    title: str
    description: str
    suggestion: str


class IndexSuggestion(BaseModel):
    index_name: str
    columns: list[str]
    reason: str
    sql: str


class SQLReviewResult(BaseModel):
    detected_type: Literal["select", "insert", "update", "delete", "merge", "ddl", "unknown"]
    score: int = Field(ge=0, le=100)
    summary: str
    issues: list[Issue]
    improvements: list[str]
    optimized_query: str | None
    index_suggestions: list[IndexSuggestion]
    assumptions: list[str]
    notes: list[str]
