export default function HopCard({ hop, isHighest }) {
  const cls = ['hop-card', isHighest && 'highest', hop.flagged && 'flagged'].filter(Boolean).join(' ')
  return (
    <article className={cls}>
      <div className="hop-top">
        <span className="hop-index">{String(hop.index).padStart(2, '0')}</span>
        <div className="hop-top-tags">
          {isHighest && <span className="pill pill-brand">Highest score</span>}
          <span className={`pill ${hop.flagged ? 'pill-amber' : 'pill-quiet'}`}>{hop.flagged ? 'Flagged' : 'Not flagged'}</span>
        </div>
      </div>
      <p className="hop-text">{hop.text}</p>
      <div className="hop-meter">
        <div className="hop-meter-track">
          <div
            className={`hop-meter-fill ${hop.flagged ? 'is-flagged' : ''}`}
            style={{ width: `${Math.max(2, hop.error_score * 100)}%` }}
          />
        </div>
        <span className="hop-score">{hop.error_score.toFixed(3)}</span>
      </div>
    </article>
  )
}
