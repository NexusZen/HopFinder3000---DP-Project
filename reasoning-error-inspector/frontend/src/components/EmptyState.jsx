export default function EmptyState() {
  return (
    <div className="empty-state">
      <div className="empty-symbol" aria-hidden="true"><span /><span /><span /></div>
      <h3>A clear view of every step.</h3>
      <p>Your question will produce a fresh reasoning chain. The trained probe will score each hop, then a separate evidence check will examine the highest-scoring claim.</p>
      <div className="empty-flow">
        <span>Generate</span>
        <span className="empty-flow-arrow">→</span>
        <span>Probe</span>
        <span className="empty-flow-arrow">→</span>
        <span>Compare evidence</span>
      </div>
    </div>
  )
}
