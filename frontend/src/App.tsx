import { useEffect, useMemo, useRef, useState } from "react";
import {
  checkHealth,
  inspectDatabase,
  reviewQuery,
  validateConnection,
  type ConnectionValidationResponse,
  type DatabaseInspectRequest,
  type ReviewRequest,
  type ReviewResponse
} from "./api/review";
import "./styles.css";

const PROFILE_IMAGE =
  "https://lh3.googleusercontent.com/aida-public/AB6AXuDNyQtT0XGScO0IUEeamA43oWXWEiCyypLx_P9nVdBxKSLTo79IuOMZl59MiSLPtPsd2b0K7e0BqtIxYYpMx4HKjnKPapRPQ0MVz7heebznM5GA8YJqr8vl2R3DnDel2ii1zF3VniOHKDs2YwPjE3QvF6Qsp0YBrJ0SHhWg43prcsDI-7IRrNgpXjrMUy3mI3wszQmW-0ykJa3Kg1gjT1j8tmE13crL6GmQ4LGBcNnISG4qpYUAyoh45Vexuo0tbNkPGAm1hBKxXsRw";

const initialPayload: ReviewRequest = {
  query: [
    
  ].join("\n"),
  database_type: "mysql",
  context: "",
  schema: "",
  indexes: "",
  optimization_goal: "speed",
  ai_provider: null,
  connection_string: "",
  metadata_database_type: null,
  schema_name: "",
  table_filter: "",
  limit_tables: 25,
  auto_introspect: true
};

const initialInspectConfig: DatabaseInspectRequest = {
  connection_string: "",
  database_type: null,
  schema_name: "",
  table_filter: "",
  limit_tables: 25
};

function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function highlightSql(query: string) {
  const escaped = escapeHtml(query);

  return escaped
    .replace(/(--.*)$/gm, '<span class="syntax-comment">$1</span>')
    .replace(/('(?:[^'\\]|\\.)*')/g, '<span class="syntax-string">$1</span>')
    .replace(/\b(\d+(?:\.\d+)?)\b/g, '<span class="syntax-number">$1</span>')
    .replace(
      /\b(SELECT|FROM|JOIN|INNER|LEFT|RIGHT|ON|WHERE|AND|OR|GROUP BY|ORDER BY|DESC|ASC|AS|LIMIT|OFFSET|CREATE INDEX|CREATE|INDEX|FILTER)\b/gi,
      '<span class="syntax-keyword">$1</span>'
    )
    .replace(/\b(SUM|COUNT|AVG|MIN|MAX)\b/gi, '<span class="syntax-function">$1</span>');
}

function formatSql(query: string) {
  const compact = query.replace(/\s+/g, " ").trim();
  if (!compact) return "";

  return compact
    .replace(/\bSELECT\b/gi, "SELECT")
    .replace(/\bFROM\b/gi, "\nFROM")
    .replace(/\bWHERE\b/gi, "\nWHERE")
    .replace(/\bGROUP BY\b/gi, "\nGROUP BY")
    .replace(/\bORDER BY\b/gi, "\nORDER BY")
    .replace(/\bLIMIT\b/gi, "\nLIMIT")
    .replace(/\bOFFSET\b/gi, "\nOFFSET")
    .replace(/\bHAVING\b/gi, "\nHAVING")
    .replace(/\bINNER JOIN\b/gi, "\nINNER JOIN")
    .replace(/\bLEFT JOIN\b/gi, "\nLEFT JOIN")
    .replace(/\bRIGHT JOIN\b/gi, "\nRIGHT JOIN")
    .replace(/\bFULL JOIN\b/gi, "\nFULL JOIN")
    .replace(/\bJOIN\b/gi, "\nJOIN")
    .replace(/\bUNION ALL\b/gi, "\nUNION ALL\n")
    .replace(/\bUNION\b/gi, "\nUNION\n")
    .replace(/\bON\b/gi, "\n  ON")
    .replace(/\bAND\b/gi, "\n  AND")
    .replace(/\bOR\b/gi, "\n  OR")
    .replace(/,\s*/g, ",\n  ")
    .replace(/\n{2,}/g, "\n")
    .trim();
}

function getLatency(score: number) {
  if (score >= 80) return "180ms";
  if (score >= 60) return "820ms";
  if (score >= 40) return "2.4s";
  return "4.2s";
}

function getCpu(score: number) {
  if (score >= 80) return "28%";
  if (score >= 60) return "47%";
  if (score >= 40) return "68%";
  return "82%";
}

function getImprovementEstimate(score: number) {
  if (score >= 80) return "~12%";
  if (score >= 60) return "~35%";
  if (score >= 40) return "~68%";
  return "~95%";
}

function getHealthClass(health: "checking" | "online" | "offline") {
  if (health === "online") return "health-online";
  if (health === "offline") return "health-offline";
  return "health-checking";
}

function getSeverityLabel(severity: ReviewResponse["issues"][number]["severity"]) {
  switch (severity) {
    case "critical":
      return "nghiêm trọng";
    case "high":
      return "cao";
    case "medium":
      return "trung bình";
    case "low":
      return "thấp";
    default:
      return severity;
  }
}

function getCategoryLabel(category: ReviewResponse["issues"][number]["category"]) {
  switch (category) {
    case "correctness":
      return "độ chính xác";
    case "performance":
      return "hiệu năng";
    case "maintainability":
      return "bảo trì";
    case "security":
      return "bảo mật";
    case "safety":
      return "an toàn";
    case "readability":
      return "dễ đọc";
    default:
      return category;
  }
}

function getDetectedTypeLabel(detectedType: string) {
  switch (detectedType) {
    case "select":
      return "SELECT";
    case "insert":
      return "INSERT";
    case "update":
      return "UPDATE";
    case "delete":
      return "DELETE";
    case "merge":
      return "MERGE";
    case "ddl":
      return "DDL";
    case "unknown":
      return "không xác định";
    default:
      return detectedType;
  }
}

export default function App() {
  const [payload, setPayload] = useState<ReviewRequest>(initialPayload);
  const [inspectConfig, setInspectConfig] = useState<DatabaseInspectRequest>(initialInspectConfig);
  const [inspectNotes, setInspectNotes] = useState<string[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<"idle" | "checking" | "valid" | "invalid">("idle");
  const [connectionInfo, setConnectionInfo] = useState<ConnectionValidationResponse | null>(null);
  const [isDatabasePanelOpen, setIsDatabasePanelOpen] = useState(true);
  const [result, setResult] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [inspecting, setInspecting] = useState(false);
  const [error, setError] = useState("");
  const [warningPopup, setWarningPopup] = useState("");
  const [health, setHealth] = useState<"checking" | "online" | "offline">("checking");
  const schemaSectionRef = useRef<HTMLElement | null>(null);
  const benchmarksSectionRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    let active = true;

    checkHealth()
      .then(() => {
        if (active) {
          setHealth("online");
        }
      })
      .catch(() => {
        if (active) {
          setHealth("offline");
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const hasConnectionString = Boolean(inspectConfig.connection_string.trim());
  const requiresValidatedConnection = hasConnectionString && connectionStatus !== "valid";

  async function handleSubmit() {
    if (!payload.query.trim()) {
      setError("Vui lòng nhập câu truy vấn cần phân tích.");
      setResult(null);
      return;
    }

    if (requiresValidatedConnection) {
      setError("Vui lòng kiểm tra connection string hợp lệ trước khi phân tích.");
      return;
    }

    setLoading(true);
    setError("");
    setWarningPopup("");
    setResult(null);

    try {
      const reviewPayload: ReviewRequest = {
        ...payload,
        schema: hasConnectionString ? "" : payload.schema,
        indexes: hasConnectionString ? "" : payload.indexes,
        connection_string: inspectConfig.connection_string,
        metadata_database_type: inspectConfig.database_type,
        schema_name: inspectConfig.schema_name,
        table_filter: inspectConfig.table_filter,
        limit_tables: inspectConfig.limit_tables,
        auto_introspect: Boolean(inspectConfig.connection_string.trim())
      };
      const data = await reviewQuery(reviewPayload);
      setResult(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Đã xảy ra lỗi không mong muốn.";
      setError(message);
      setWarningPopup(message);
    } finally {
      setLoading(false);
    }
  }

  async function handleInspectDatabase() {
    setInspecting(true);
    setError("");

    try {
      const data = await inspectDatabase(inspectConfig);
      setPayload((current) => ({
        ...current,
        database_type: data.database_type,
        schema: data.schema,
        indexes: data.indexes
      }));
      setInspectNotes(data.notes);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đã xảy ra lỗi không mong muốn.");
    } finally {
      setInspecting(false);
    }
  }

  async function handleValidateConnection() {
    if (!inspectConfig.connection_string.trim()) {
      setError("Vui lòng nhập connection string.");
      setConnectionStatus("invalid");
      setConnectionInfo(null);
      return;
    }

    setConnectionStatus("checking");
    setConnectionInfo(null);
    setError("");

    try {
      const data = await validateConnection(inspectConfig);
      setConnectionInfo(data);
      const nextConfig = {
        ...inspectConfig,
        schema_name: inspectConfig.schema_name || data.schema_name
      };
      setInspectConfig(nextConfig);
      setConnectionStatus("valid");
      setInspectNotes(data.notes);
      setInspecting(true);
      try {
        const metadata = await inspectDatabase(nextConfig);
        setPayload((current) => ({
          ...current,
          database_type: metadata.database_type,
          schema: metadata.schema,
          indexes: metadata.indexes
        }));
        setInspectNotes(metadata.notes);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Đã xảy ra lỗi không mong muốn.");
      } finally {
        setInspecting(false);
      }
    } catch (err) {
      setConnectionStatus("invalid");
      setConnectionInfo(null);
      setError(err instanceof Error ? err.message : "Đã xảy ra lỗi không mong muốn.");
    }
  }

  async function handleCopy() {
    const content = hasResult && result?.optimized_query?.trim() ? formatSql(result.optimized_query) : null;
    if (!content) return;

    try {
      await navigator.clipboard.writeText(content);
    } catch {
      setError("Không thể sao chép nội dung SQL.");
    }
  }

  function scrollToSection(section: "schema" | "benchmarks") {
    const target = section === "schema" ? schemaSectionRef.current : benchmarksSectionRef.current;
    target?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  const hasResult = result !== null;
  const isNoSql = payload.database_type === "mongodb";
  const issueCount = result?.issues.length ?? 0;
  const lineCount = Math.max(payload.query.split(/\r?\n/).length, 12);
  const lineNumbers = Array.from({ length: lineCount }, (_, index) => index + 1);
  const editorHtml = useMemo(() => highlightSql(payload.query), [payload.query]);
  const displayOptimizedQuery = useMemo(() => {
    if (!hasResult) return "-- Chưa có SQL đề xuất";
    if (result?.optimized_query?.trim()) return result.optimized_query;
    return payload.query || "-- Chưa có SQL đề xuất";
  }, [hasResult, payload.query, result?.optimized_query]);
  const formattedOptimizedQuery = useMemo(
    () => (result?.optimized_query?.trim() ? formatSql(displayOptimizedQuery) : ""),
    [displayOptimizedQuery, result?.optimized_query]
  );
  const optimizedHtml = useMemo(
    () => (formattedOptimizedQuery ? highlightSql(formattedOptimizedQuery) : ""),
    [formattedOptimizedQuery]
  );

  return (
    <div className="shell">
      <header className="topbar">
        <div className="topbar-brand">
          <span className="brand-wordmark">SQL Performance Optimization</span>
        </div>

        {/* <div className="topbar-actions">
          <div className="topbar-search">
            <span className="material-symbols-outlined icon-muted">search</span>
            <input placeholder="Tﾃｬm ki蘯ｿm tﾃi li盻㎡..." type="text" />
          </div>
          <button className="icon-button" type="button">
            <span className="material-symbols-outlined">notifications</span>
          </button>
          <button className="icon-button" type="button">
            <span className="material-symbols-outlined">settings</span>
          </button>
          <div className="profile-avatar">
            <img alt="User profile" src={PROFILE_IMAGE} />
          </div>
        </div> */}
      </header>

      <div className="workspace-shell">
        <aside className="sidebar">
          <div className="sidebar-brand">
            <div className="sidebar-icon">
              <span className="material-symbols-outlined filled">terminal</span>
            </div>
            <div>
              <h2>SQL/NoSQL</h2>
              <p>Optimization Engine</p>
            </div>
          </div>

          {/* <button className="sidebar-primary-button" type="button">
            <span className="material-symbols-outlined">add</span>
            <span>New Workspace</span>
          </button> */}

          { <nav className="sidebar-nav">
            <button
              className={`sidebar-nav-link ${isDatabasePanelOpen ? "active" : ""}`}
              onClick={() => setIsDatabasePanelOpen((current) => !current)}
              type="button"
            >
              <span className="material-symbols-outlined">database</span>
              <span>Database</span>
              <span className="material-symbols-outlined sidebar-nav-expand">
                {isDatabasePanelOpen ? "expand_less" : "expand_more"}
              </span>
            </button>
            </nav>
          }
          {/* {
            <button className="sidebar-nav-link" onClick={() => scrollToSection("benchmarks")} type="button">
              <span className="material-symbols-outlined">speed</span>
              <span>Benchmarks</span>
            </button>
          </nav> } */}

          <section className={`sidebar-db-panel custom-scrollbar ${isDatabasePanelOpen ? "open" : "collapsed"}`}>
            <div className="db-inspector-card db-inspector-card-sidebar">
              <div className="analysis-section-header">
                <h3 className="analysis-title sidebar-panel-title">Database connection</h3>
              </div>

              <label className="pane-label">
                <span>Connection string</span>
                <textarea
                  className="pane-textarea sidebar-pane-textarea"
                  rows={4}
                  value={inspectConfig.connection_string}
                  placeholder="postgresql://user:password@host:5432/app_db or mysql://user:password@host:3306/app_db or sqlite:///C:/data/app.db"
                  onChange={(event) => {
                    setInspectConfig((current) => ({ ...current, connection_string: event.target.value }));
                    setConnectionStatus("idle");
                    setConnectionInfo(null);
                  }}
                />
              </label>

              <div className="analysis-section-header">
                <button className="link-button" disabled={connectionStatus === "checking" || !inspectConfig.connection_string.trim()} onClick={handleValidateConnection} type="button">
                  <span className="material-symbols-outlined">link</span>
                  <span>{connectionStatus === "checking" ? "Checking..." : "Check connection"}</span>
                </button>
                <span className="subtle-badge">
                  {connectionStatus === "valid"
                    ? "connection valid"
                    : connectionStatus === "invalid"
                      ? "connection invalid"
                      : "not checked"}
                </span>
              </div>

              {connectionInfo ? (
                <div className="notes-block notes-block-muted">
                  <p>{connectionInfo.message}</p>
                  <p>
                    Type: {connectionInfo.database_type} | Database: {connectionInfo.database_name} | Schema: {connectionInfo.schema_name}
                  </p>
                </div>
              ) : null}

              <div className="db-inspector-grid db-inspector-grid-sidebar">
                <label className="pane-label">
                  <span>Metadata source</span>
                  <input className="pane-input" type="text" value="auto from connection string" readOnly />
                </label>

                <label className="pane-label">
                  <span>Schema name (optional)</span>
                  <input
                    className="pane-input"
                    type="text"
                    value={inspectConfig.schema_name}
                    placeholder="public, analytics, ...; MySQL/SQLite can leave empty"
                    onChange={(event) => setInspectConfig((current) => ({ ...current, schema_name: event.target.value }))}
                  />
                </label>

                <label className="pane-label">
                  <span>Table filter</span>
                  <input
                    className="pane-input"
                    type="text"
                    value={inspectConfig.table_filter}
                    placeholder="orders"
                    onChange={(event) => setInspectConfig((current) => ({ ...current, table_filter: event.target.value }))}
                  />
                </label>

                <label className="pane-label">
                  <span>Table limit</span>
                  <input
                    className="pane-input"
                    type="number"
                    min={1}
                    max={100}
                    value={inspectConfig.limit_tables}
                    onChange={(event) =>
                      setInspectConfig((current) => ({
                        ...current,
                        limit_tables: Number(event.target.value) || 25
                      }))
                    }
                  />
                </label>
              </div>

              {inspectNotes.length > 0 ? (
                <div className="notes-block notes-block-muted">
                  {inspectNotes.map((note, index) => (
                    <p key={`${note}-${index}`}>{note}</p>
                  ))}
                </div>
              ) : null}
            </div>
          </section>

          <div className="sidebar-footer">
            <a href="#support">
              <span className="material-symbols-outlined">help</span>
              <span>Support</span>
            </a>
            <a href="#logs">
              <span className="material-symbols-outlined">description</span>
              <span>Logs</span>
            </a>
          </div>
        </aside>

        <main className="workspace">
          <div className="workspace-toolbar">
            <div className="toolbar-left">
              <div className="mode-tabs">
                <button
                  className={!isNoSql ? "mode-tab active" : "mode-tab"}
                  onClick={() => setPayload((current) => ({ ...current, database_type: current.database_type === "mongodb" ? "mysql" : current.database_type }))}
                  type="button"
                >
                  SQL
                </button>
                <button
                  className={isNoSql ? "mode-tab active" : "mode-tab"}
                  onClick={() => setPayload((current) => ({ ...current, database_type: "mongodb" }))}
                  type="button"
                >
                  NoSQL
                </button>
              </div>

              <div className="toolbar-meta">
                <span>Database:</span>
                <div className="toolbar-chip">
                  <span className="material-symbols-outlined chip-icon">storage</span>
                  <select
                    value={payload.database_type}
                    onChange={(event) => setPayload((current) => ({ ...current, database_type: event.target.value as ReviewRequest["database_type"] }))}
                  >
                    <option value="auto">auto</option>
                    <option value="mysql">mysql</option>
                    <option value="postgres">postgres</option>
                    <option value="mongodb">mongodb</option>
                    <option value="generic_sql">generic_sql</option>
                    <option value="sqlite">sqlite</option>
                  </select>
                  <span className="material-symbols-outlined chip-expand">expand_more</span>
                </div>
              </div>

              <div className="toolbar-meta toolbar-meta-goal">
                <span>Goal:</span>
                <div className="toolbar-chip">
                  <span className="material-symbols-outlined chip-icon">tune</span>
                  <select
                    value={payload.optimization_goal}
                    onChange={(event) => setPayload((current) => ({ ...current, optimization_goal: event.target.value as ReviewRequest["optimization_goal"] }))}
                  >
                    <option value="general">general</option>
                    <option value="speed">speed</option>
                    <option value="readability">readability</option>
                    <option value="index">index</option>
                    <option value="cost">cost</option>
                  </select>
                  <span className="material-symbols-outlined chip-expand">expand_more</span>
                </div>
              </div>

              <div className="toolbar-meta">
                <span>AI:</span>
                <div className="toolbar-chip">
                  <span className="material-symbols-outlined chip-icon">smart_toy</span>
                  <select
                    value={payload.ai_provider ?? "groq"}
                    onChange={(event) => setPayload((current) => ({ ...current, ai_provider: event.target.value as ReviewRequest["ai_provider"] }))}
                  >
                    <option value="groq">groq</option>
                    <option value="claude">claude</option>
                  </select>
                  <span className="material-symbols-outlined chip-expand">expand_more</span>
                </div>
              </div>
            </div>

            <div className="toolbar-right">
              <span className={`health-badge ${getHealthClass(health)}`}>API {health}</span>
              <button className="analyze-button" disabled={loading || requiresValidatedConnection} onClick={handleSubmit} type="button">
                <span className="material-symbols-outlined">bolt</span>
                <span>{loading ? "Phân tích..." : requiresValidatedConnection ? "Kiểm tra kết nối trước" : "Phân tích & Tối ưu"}</span>
              </button>
            </div>
          </div>

          <div className="workspace-body">
            <section className="editor-pane">
              <div className="editor-scroll custom-scrollbar">
                <div className="editor-grid">
                  <div className="editor-lines" aria-hidden="true">
                    {lineNumbers.map((line) => (
                      <span key={line}>{line}</span>
                    ))}
                  </div>

                  <div className="editor-layer">
                    <pre className="editor-highlight" dangerouslySetInnerHTML={{ __html: editorHtml || " " }} />
                    <textarea
                      className="editor-textarea"
                      spellCheck={false}
                      value={payload.query}
                      onChange={(event) => setPayload((current) => ({ ...current, query: event.target.value }))}
                    />
                  </div>
                </div>
                <div className="editor-ruler" aria-hidden="true" />
              </div>
            </section>

            <aside className="analysis-pane custom-scrollbar">
              {error && <div className="analysis-error">{error}</div>}

              <section className="analysis-section">
                <div className="analysis-section-header">
                  <h3 className="analysis-title">
                    <span className="material-symbols-outlined section-icon section-icon-error">report</span>
                    <span>Điểm chậm và vấn đề cần sửa</span>
                  </h3>
                  <span className="warning-pill">{issueCount} vấn đề</span>
                </div>

                <div className="issue-stack">
                  {hasResult && result.issues.length > 0 ? (
                    result.issues.map((issue, index) => (
                      <article className="risk-card" key={`${issue.title}-${index}`}>
                        <span className={`material-symbols-outlined risk-icon risk-${issue.severity}`}>
                          {issue.severity === "medium" || issue.severity === "low" ? "warning" : "error"}
                        </span>
                        <div>
                          <p className="risk-title">{issue.title}</p>
                          <p className="risk-meta">{getSeverityLabel(issue.severity)} · {getCategoryLabel(issue.category)}</p>
                          <p className="risk-copy">{issue.description}</p>
                          <p className="risk-suggestion">Cách sửa: {issue.suggestion}</p>
                        </div>
                      </article>
                    ))
                  ) : (
                    <article className="risk-card risk-card-empty">
                      <div>
                        <p className="risk-title">Chưa phát hiện điểm nghẽn rõ ràng</p>
                        <p className="risk-copy">Nhập query để kiểm tra chỗ chậm, đoạn viết chưa tối ưu và rủi ro có thể lặp lại trong tương lai.</p>
                      </div>
                    </article>
                  )}
                </div>
              </section>

              <section className="analysis-section" ref={benchmarksSectionRef}>
                <h3 className="analysis-title">Ước lượng tác động hiệu năng</h3>

                <div className="estimate-grid">
                  <article className="estimate-card">
                    <p className="estimate-label">Độ trễ(Latency)</p>
                    <p className="estimate-value estimate-value-error">{hasResult ? getLatency(result.score) : "--"}</p>
                    <p className="estimate-caption">Cao</p>
                  </article>
                  <article className="estimate-card">
                    <p className="estimate-label">Tải CPU</p>
                    <p className="estimate-value estimate-value-tertiary">{hasResult ? getCpu(result.score) : "--"}</p>
                    <p className="estimate-caption">Cao</p>
                  </article>
                </div>

                <div className="improvement-banner">
                  <div className="improvement-copy">
                    <span className="material-symbols-outlined filled">trending_up</span>
                    <span>Cải thiện tiềm  năng:</span>
                  </div>
                  <strong>{hasResult ? getImprovementEstimate(result.score) : "--"}</strong>
                </div>
              </section>

              <section className="analysis-section" ref={schemaSectionRef}>
                <div className="analysis-section-header">
                  <h3 className="analysis-title analysis-title-primary">SQL đề xuất để cải thiện</h3>
                  <button className="link-button" onClick={handleCopy} type="button">
                    <span className="material-symbols-outlined">content_copy</span>
                    <span>Sao chép</span>
                  </button>
                </div>

                {result?.optimized_query ? (
                  <div className="optimized-block">
                    <pre dangerouslySetInnerHTML={{ __html: optimizedHtml }} />
                  </div>
                ) : null}

                {hasResult && !result.optimized_query ? (
                  <div className="notes-block notes-block-muted">
                    <p>Chưa có bản rewrite an toàn được tạo tự động. Đang hiển thị query hiện tại để coder tiếp tục chỉnh tay theo các vấn đề đã phát hiện.</p>
                  </div>
                ) : null}

                {hasResult && result.index_suggestions.length > 0 ? (
                  <div className="notes-block">
                    <p><strong>Index đề xuất</strong></p>
                    {result.index_suggestions.map((item, index) => (
                      <div className="index-suggestion-card" key={`${item.index_name}-${index}`}>
                        <p><strong>{item.index_name}</strong></p>
                        <p>Cột: {item.columns.join(", ") || "không có"}</p>
                        <p>{item.reason}</p>
                        <pre>{item.sql || "-- chưa có câu lệnh SQL được cung cấp"}</pre>
                      </div>
                    ))}
                  </div>
                ) : null}

                <div className="analysis-actions">
                  <button className="secondary-run-button" type="button">
                    <span className="material-symbols-outlined">play_circle</span>
                    <span>Chạy truy vấn tối ưu</span>
                  </button>
                </div>
              </section>

              <section className="analysis-section">
                <div className="analysis-section-header">
                  <h3 className="analysis-title">Tóm tắt cho coder</h3>
                  <span className="subtle-badge">{getDetectedTypeLabel(result?.detected_type ?? payload.database_type)}</span>
                </div>

                <div className="notes-block">
                  <p>{result?.summary ?? "Chưa có kết luận phân tích."}</p>
                </div>

                {/* <label className="pane-label">
                  <span>Schema</span>
                  <textarea
                    className="pane-textarea"
                    rows={4}
                    value={payload.schema}
                    placeholder="users(id PK, email, status, created_at)"
                    onChange={(event) => setPayload((current) => ({ ...current, schema: event.target.value }))}
                  />
                </label>

                <label className="pane-label">
                  <span>Indexes</span>
                  <textarea
                    className="pane-textarea"
                    rows={3}
                    value={payload.indexes}
                    placeholder="idx_users_email(email), idx_users_status_created(status, created_at)"
                    onChange={(event) => setPayload((current) => ({ ...current, indexes: event.target.value }))}
                  />
                </label>

                <label className="pane-label">
                  <span>Additional context</span>
                  <textarea
                    className="pane-textarea"
                    rows={4}
                    value={payload.context}
                    placeholder="Row count, cardinality, workload pattern, SLA..."
                    onChange={(event) => setPayload((current) => ({ ...current, context: event.target.value }))}
                  />
                </label>

                {hasResult ? (
                  <div className="notes-block">
                    <p><strong>Input preview</strong></p>
                    <p>
                      Schema lines: {result.input_preview.schema_line_count} | Index lines: {result.input_preview.index_line_count}
                    </p>
                    <p>
                      Entities: {result.input_preview.detected_entities.length > 0 ? result.input_preview.detected_entities.join(", ") : "none"}
                    </p>
                    <p>
                      Indexed columns: {result.input_preview.detected_index_columns.length > 0 ? result.input_preview.detected_index_columns.join(", ") : "none"}
                    </p>
                  </div>
                ) : null} */}

                <div className="notes-block">
                  {hasResult && result.input_preview.detected_entities.length > 0 ? (
                    <p><strong>Bảng liên quan:</strong> {result.input_preview.detected_entities.join(", ")}</p>
                  ) : null}
                  {hasResult && result.improvements.length > 0 ? (
                    result.improvements.map((item, index) => (
                      <p key={`${item}-${index}`}>{item}</p>
                    ))
                  ) : (
                    ""
                  )}
                </div>

                <div className="notes-block notes-block-muted">
                  {hasResult && result.assumptions.length > 0 ? <p><strong>Giả định phân tích:</strong></p> : null}
                  {hasResult && result.assumptions.length > 0 ? (
                    result.assumptions.map((item, index) => (
                      <p key={`${item}-${index}`}>{item}</p>
                    ))
                  ) : null}
                  {hasResult ? <p><strong>Ghi chú để tránh lặp lại:</strong></p> : null}
                  {hasResult && result.notes.length > 0 ? (
                    result.notes.map((note, index) => (
                      <p key={`${note}-${index}`}>{note}</p>
                    ))
                  ) : (
                    ""
                  )}
                </div>
              </section>
            </aside>
          </div>
        </main>
      </div>

      <button className="fab-button" type="button">
        <span className="material-symbols-outlined filled">auto_fix_high</span>
      </button>

      {warningPopup ? (
        <div className="popup-backdrop" role="dialog" aria-modal="true" aria-labelledby="ai-warning-title">
          <div className="warning-popup">
            <div className="warning-popup-header">
              <span className="material-symbols-outlined warning-popup-icon">warning</span>
              <h3 id="ai-warning-title">Không thể phân tích bằng AI</h3>
            </div>
            <p>{warningPopup}</p>
            <button className="warning-popup-button" onClick={() => setWarningPopup("")} type="button">
              Đóng
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
