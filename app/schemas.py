from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


DatabaseType = Literal["auto", "mysql", "postgres", "mongodb", "generic_sql", "sqlite"]
OptimizationGoal = Literal["general", "speed", "readability", "index", "cost"]
Severity = Literal["low", "medium", "high", "critical"]
InspectableDatabaseType = Literal["mysql", "postgres", "sqlite"]
AIProvider = Literal["gemini", "groq", "claude"]
IssueCategory = Literal["correctness", "performance", "maintainability", "security", "safety", "readability"]


class ReviewRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    query: str = Field(..., max_length=10_000)
    database_type: DatabaseType = "auto"
    context: str = Field(default="", max_length=5_000)
    schema_info: str = Field(default="", alias="schema", max_length=50_000)
    index_info: str = Field(default="", alias="indexes", max_length=50_000)
    optimization_goal: OptimizationGoal = "general"
    ai_provider: AIProvider | None = None
    connection_string: str = Field(default="", max_length=2_000)
    metadata_database_type: InspectableDatabaseType | None = None
    schema_name: str = Field(default="", max_length=255)
    table_filter: str = Field(default="", max_length=255)
    limit_tables: int = Field(default=25, ge=1, le=100)
    auto_introspect: bool = False


class Issue(BaseModel):
    severity: Severity
    category: IssueCategory = "performance"
    title: str
    description: str
    suggestion: str


class IndexSuggestion(BaseModel):
    index_name: str
    columns: list[str]
    reason: str
    sql: str


class InputPreview(BaseModel):
    schema_lines: list[str]
    index_lines: list[str]
    detected_entities: list[str]
    detected_index_columns: list[str]
    schema_line_count: int = Field(..., ge=0)
    index_line_count: int = Field(..., ge=0)


class DatabaseInspectRequest(BaseModel):
    connection_string: str = Field(..., min_length=1, max_length=2_000)
    database_type: InspectableDatabaseType | None = None
    schema_name: str = Field(default="", max_length=255)
    table_filter: str = Field(default="", max_length=255)
    limit_tables: int = Field(default=25, ge=1, le=100)


class DatabaseInspectResponse(BaseModel):
    database_type: InspectableDatabaseType
    database_name: str
    schema_name: str
    schema: str
    indexes: str
    input_preview: InputPreview
    notes: list[str]


class ConnectionValidationResponse(BaseModel):
    valid: bool
    database_type: InspectableDatabaseType
    database_name: str
    schema_name: str
    message: str
    notes: list[str]


class ReviewResponse(BaseModel):
    detected_type: str
    score: int = Field(..., ge=0, le=100)
    summary: str
    issues: list[Issue]
    improvements: list[str]
    optimized_query: str | None = None
    index_suggestions: list[IndexSuggestion] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    notes: list[str]
    input_preview: InputPreview
