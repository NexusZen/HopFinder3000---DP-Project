const STATUS = {
  SUPPORTED: { label: 'Evidence supports this claim', cls: 'status-good', icon: '✓' },
  CONTRADICTED: { label: 'Possible factual discrepancy', cls: 'status-bad', icon: '!' },
  NOT_ENOUGH_INFORMATION: { label: 'Not enough information to verify', cls: 'status-neutral', icon: '?' },
}

export default function EvidenceCard({ evidence, hopIndex }) {
  const meta = STATUS[evidence.status] || STATUS.NOT_ENOUGH_INFORMATION
  const rows = [
    ['Claim', evidence.claim],
    ['Claimed', evidence.claimed_value],
    ['Reference', evidence.supported_value],
  ].filter(([, v]) => v)

  return (
    <section className="evidence-card">
      <div className="evidence-head">
        <span className="small-label">Separate evidence check</span>
        <div className={`status-chip ${meta.cls}`}>
          <span className="status-dot">{meta.icon}</span>
          {meta.label}
        </div>
      </div>
      <p className="muted">Examining Hop {hopIndex}. This assessment is independent of the hidden-state probe score.</p>
      {rows.length > 0 && (
        <dl className="evidence-dl">
          {rows.map(([label, value]) => (
            <div className="evidence-row" key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      )}
      {evidence.evidence && <blockquote>{evidence.evidence}</blockquote>}
      <p className="muted">{evidence.explanation}</p>
    </section>
  )
}
