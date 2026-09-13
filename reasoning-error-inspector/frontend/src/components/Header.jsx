const LABELS = { ready: 'Model ready', loading: 'Loading model…', error: 'Setup needs attention' }

export default function Header({ status }) {
  const label = LABELS[status] || 'Connecting…'
  return (
    <header className="masthead">
      <div className="brand">
        <span className="brand-mark">R<span>i</span></span>
        <div className="brand-text">
          <span className="brand-name">Reasoning Error Inspector</span>
          <span className="brand-tag">Experimental diagnostic</span>
        </div>
      </div>
      <nav className="masthead-nav" aria-label="Primary">
        <a href="#workspace">Workspace</a>
        <a href="#how-it-works">How it works</a>
      </nav>
      <div className={`status-pill status-${status}`} role="status">
        <span className="status-dot-ping" />
        {label}
      </div>
    </header>
  )
}
