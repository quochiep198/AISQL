import type { ReviewResponse } from "../api/review";
import { ScoreBadge } from "./ScoreBadge";

type Props = {
  result: ReviewResponse;
};

export function ReviewResult({ result }: Props) {
  const highRiskCount = result.issues.filter((issue) => issue.severity === "high" || issue.severity === "critical").length;

  return (
    <section className="card">
      <div className="result-header">
        <div>
          <p className="eyebrow">Detected type</p>
          <h2>{result.detected_type}</h2>
        </div>
        <ScoreBadge score={result.score} />
      </div>

      <div className="stats-grid">
        <article className="stat-card">
          <span className="stat-label">Issues</span>
          <strong>{result.issues.length}</strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">High risk</span>
          <strong>{highRiskCount}</strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">Improvements</span>
          <strong>{result.improvements.length}</strong>
        </article>
        <article className="stat-card">
          <span className="stat-label">Notes</span>
          <strong>{result.notes.length}</strong>
        </article>
      </div>

      <h3>Summary</h3>
      <p className="section-copy">{result.summary}</p>

      <h3>Issues</h3>
      {result.issues.length ? (
        <div className="issue-list">
          {result.issues.map((issue, index) => (
            <article className="issue" key={`${issue.title}-${index}`}>
              <span className={`severity severity-${issue.severity}`}>{issue.severity}</span>
              <h4>{issue.title}</h4>
              <p>{issue.description}</p>
              <p><strong>Suggestion:</strong> {issue.suggestion}</p>
            </article>
          ))}
        </div>
      ) : (
        <p>Khﾃｴng cﾃｳ issue rule-based rﾃｵ rﾃng.</p>
      )}

      <h3>Recommended improvements</h3>
      <ul className="plain-list">
        {result.improvements.map((item, index) => (
          <li key={`${item}-${index}`}>{item}</li>
        ))}
      </ul>

      <h3>Optimized query</h3>
      {result.optimized_query ? <pre>{result.optimized_query}</pre> : <p>Chﾆｰa ﾄ黛ｻｧ thﾃｴng tin ﾄ黛ｻ・ﾄ黛ｻ・xu蘯･t query t盻訴 ﾆｰu an toﾃn.</p>}

      <h3>Notes / warnings</h3>
      <ul className="plain-list">
        {result.notes.map((item, index) => (
          <li key={`${item}-${index}`}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
