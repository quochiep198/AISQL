export type DatabaseType = "auto" | "mysql" | "postgres" | "mongodb" | "generic_sql" | "sqlite";
export type OptimizationGoal = "general" | "speed" | "readability" | "index" | "cost";
export type InspectableDatabaseType = "mysql" | "postgres" | "sqlite";
export type AIProvider = "gemini" | "groq" | "claude";

export type ReviewRequest = {
  query: string;
  database_type: DatabaseType;
  context: string;
  schema: string;
  indexes: string;
  optimization_goal: OptimizationGoal;
  ai_provider: AIProvider | null;
  connection_string: string;
  metadata_database_type: InspectableDatabaseType | null;
  schema_name: string;
  table_filter: string;
  limit_tables: number;
  auto_introspect: boolean;
};

export type Issue = {
  severity: "low" | "medium" | "high" | "critical";
  category: "correctness" | "performance" | "maintainability" | "security" | "safety" | "readability";
  title: string;
  description: string;
  suggestion: string;
};

export type IndexSuggestion = {
  index_name: string;
  columns: string[];
  reason: string;
  sql: string;
};

export type InputPreview = {
  schema_lines: string[];
  index_lines: string[];
  detected_entities: string[];
  detected_index_columns: string[];
  schema_line_count: number;
  index_line_count: number;
};

export type DatabaseInspectRequest = {
  connection_string: string;
  database_type: InspectableDatabaseType | null;
  schema_name: string;
  table_filter: string;
  limit_tables: number;
};

export type DatabaseInspectResponse = {
  database_type: InspectableDatabaseType;
  database_name: string;
  schema_name: string;
  schema: string;
  indexes: string;
  input_preview: InputPreview;
  notes: string[];
};

export type ConnectionValidationResponse = {
  valid: boolean;
  database_type: InspectableDatabaseType;
  database_name: string;
  schema_name: string;
  message: string;
  notes: string[];
};

export type ReviewResponse = {
  detected_type: string;
  score: number;
  summary: string;
  issues: Issue[];
  improvements: string[];
  optimized_query: string | null;
  index_suggestions: IndexSuggestion[];
  assumptions: string[];
  notes: string[];
  input_preview: InputPreview;
};

export type HealthResponse = {
  status: string;
};

export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch("/api/health");

  if (!response.ok) {
    throw new Error("Health check failed");
  }

  return response.json();
}

export async function reviewQuery(payload: ReviewRequest): Promise<ReviewResponse> {
  const response = await fetch("/api/review", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || "Request failed");
  }

  return response.json();
}

export async function inspectDatabase(payload: DatabaseInspectRequest): Promise<DatabaseInspectResponse> {
  const response = await fetch("/api/database/introspect", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || "Request failed");
  }

  return response.json();
}

export async function validateConnection(payload: DatabaseInspectRequest): Promise<ConnectionValidationResponse> {
  const response = await fetch("/api/database/validate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || "Request failed");
  }

  return response.json();
}
