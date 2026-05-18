type Props = {
  score: number;
};

export function ScoreBadge({ score }: Props) {
  const label = score >= 80 ? "Good" : score >= 50 ? "Needs review" : "High risk";
  const tone = score >= 80 ? "score-good" : score >= 50 ? "score-medium" : "score-high";

  return (
    <div className={`score-badge ${tone}`}>
      <strong>{score}</strong>
      <span>{label}</span>
    </div>
  );
}
