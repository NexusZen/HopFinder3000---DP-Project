export default function ScoreChart({ rows, threshold, highest }) {
  const width = 100
  const left = 13
  const right = 15
  const rowHeight = 15
  const plotWidth = width - left - right
  const top = 4
  const height = top + rows.length * rowHeight + 10
  const x = left + threshold * plotWidth

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="score-chart"
      role="img"
      aria-label={`Hop error scores with threshold ${threshold.toFixed(2)}`}
    >
      {rows.map((r, i) => {
        const y = top + i * rowHeight
        const barColor = r.index === highest ? 'url(#barHighest)' : r.flagged ? 'var(--amber)' : 'var(--bar-idle)'
        return (
          <g key={r.index}>
            <text x={0} y={y + 6.5} className="chart-label">H{r.index}</text>
            <rect x={left} y={y} width={plotWidth} height={9} rx={2.2} className="chart-track" />
            <rect x={left} y={y} width={Math.max(0.6, r.error_score * plotWidth)} height={9} rx={2.2} fill={barColor} />
            <text x={width - 1} y={y + 6.5} className="chart-value" textAnchor="end">{r.error_score.toFixed(2)}</text>
          </g>
        )
      })}
      <line x1={x} x2={x} y1={top - 2} y2={height - 8} className="chart-threshold" />
      <defs>
        <linearGradient id="barHighest" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="var(--brand-2)" />
          <stop offset="100%" stopColor="var(--brand-1)" />
        </linearGradient>
      </defs>
    </svg>
  )
}
