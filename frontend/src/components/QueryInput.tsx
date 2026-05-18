import type { DatabaseType, OptimizationGoal, ReviewRequest } from "../api/review";

type Props = {
  value: ReviewRequest;
  loading: boolean;
  onChange: (value: ReviewRequest) => void;
  onSubmit: () => void;
};

export function QueryInput({ value, loading, onChange, onSubmit }: Props) {
  const setField = <K extends keyof ReviewRequest>(key: K, fieldValue: ReviewRequest[K]) => {
    onChange({ ...value, [key]: fieldValue });
  };

  const queryLength = value.query.length;
  const contextLength = value.context.length;
  const schemaLength = value.schema.length;
  const indexesLength = value.indexes.length;

  return (
    <section className="card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Workspace</p>
          <h2>Review query input</h2>
        </div>
        <span className="meta-pill">POST /api/review</span>
      </div>

      <label>
        Query
        <textarea
          rows={10}
          value={value.query}
          placeholder="SELECT * FROM users WHERE email LIKE '%gmail.com'"
          onChange={(event) => setField("query", event.target.value)}
        />
      </label>
      <div className="field-meta">
        <span>SQL / MongoDB text input</span>
        <span>{queryLength}/10000</span>
      </div>

      <div className="grid">
        <label>
          Database type
          <select
            value={value.database_type}
            onChange={(event) => setField("database_type", event.target.value as DatabaseType)}
          >
            <option value="auto">auto</option>
            <option value="mysql">mysql</option>
            <option value="postgres">postgres</option>
            <option value="mongodb">mongodb</option>
            <option value="generic_sql">generic_sql</option>
          </select>
        </label>

        <label>
          Optimization goal
          <select
            value={value.optimization_goal}
            onChange={(event) => setField("optimization_goal", event.target.value as OptimizationGoal)}
          >
            <option value="general">general</option>
            <option value="speed">speed</option>
            <option value="readability">readability</option>
            <option value="index">index</option>
            <option value="cost">cost</option>
          </select>
        </label>
      </div>

      <label>
        Schema optional
        <textarea
          rows={4}
          value={value.schema}
          placeholder="users(id, email, status, created_at)"
          onChange={(event) => setField("schema", event.target.value)}
        />
      </label>
      <div className="field-meta">
        <span>Table/collection schema</span>
        <span>{schemaLength}/5000</span>
      </div>

      <label>
        Indexes optional
        <textarea
          rows={3}
          value={value.indexes}
          placeholder="idx_users_email(email), idx_users_status_created(status, created_at)"
          onChange={(event) => setField("indexes", event.target.value)}
        />
      </label>
      <div className="field-meta">
        <span>Known indexes and sort keys</span>
        <span>{indexesLength}/5000</span>
      </div>

      <label>
        Additional context optional
        <textarea
          rows={4}
          value={value.context}
          placeholder="Vi du: users co khoang 2 trieu records, workload doc nhieu hon ghi"
          onChange={(event) => setField("context", event.target.value)}
        />
      </label>
      <div className="field-meta">
        <span>Row count / cardinality / workload notes</span>
        <span>{contextLength}/5000</span>
      </div>

      <div className="actions-row">
        <div className="helper-copy">
          <strong>MVP</strong>
          <span>Rule-based + optional AI review</span>
        </div>
        <button disabled={loading || !value.query.trim()} onClick={onSubmit}>
          {loading ? "Reviewing..." : "Review Query"}
        </button>
      </div>
    </section>
  );
}
