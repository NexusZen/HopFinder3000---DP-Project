import { Fragment } from 'react'

const STAGES = [
  {
    title: 'Question + evidence',
    caption: 'You supply a question and reference text (or a document, TF-IDF-trimmed to fit).',
    icon: (
      <path d="M7 3h7l4 4v14a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
    ),
  },
  {
    title: 'Frozen model generates hops',
    caption: 'The base checkpoint writes a short chain of factual hops plus a final answer, as JSON.',
    icon: (
      <path d="M12 3v3M12 18v3M4.2 12H1M23 12h-3.2M6 6l2 2M18 18l-2-2M18 6l-2 2M6 18l2-2M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    ),
  },
  {
    title: 'Prefix built per hop',
    caption: 'For hop k, the model re-reads context + question + hops 1…k only — nothing later leaks in.',
    icon: (
      <path d="M4 6h16M4 12h16M4 18h10" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    ),
  },
  {
    title: 'Hidden state tapped',
    caption: 'One forward pass; the last token’s activation at a fixed transformer block is pulled out.',
    icon: (
      <path d="M4 5h16v4H4V5Zm0 10h16v4H4v-4Zm6-5h6" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
    ),
  },
  {
    title: 'Trained probe scores it',
    caption: 'A frozen classifier maps that single vector to an error-likelihood between 0 and 1.',
    icon: (
      <path d="M4 20V10m6 10V4m6 16v-7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    ),
  },
  {
    title: 'Flag + evidence check',
    caption: 'Highest-scoring hop crosses the threshold; a separate check compares it to the source text.',
    icon: (
      <path d="M9 12.5l2 2 4-4.5M12 3l8 4v5c0 5-3.4 8.4-8 10-4.6-1.6-8-5-8-10V7l8-4Z" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round" />
    ),
  },
]

const LAYER_COUNT = 24
const TAPPED_LAYER = 13

export default function HowItWorks() {
  return (
    <section className="how-it-works" id="how-it-works" aria-labelledby="how-title">
      <div className="how-intro">
        <span className="eyebrow">Under the hood</span>
        <h2 id="how-title">One frozen checkpoint, two jobs.</h2>
        <p>The same model that writes the reasoning chain also produces the activations the probe reads. No separate model, no fine-tuning at request time.</p>
      </div>

      <div className="flow-row" role="list">
        {STAGES.map((stage, i) => (
          <Fragment key={stage.title}>
            <div className="flow-node" role="listitem" style={{ '--i': i }}>
              <span className="flow-icon"><svg viewBox="0 0 24 24" width="20" height="20">{stage.icon}</svg></span>
              <strong>{stage.title}</strong>
              <p>{stage.caption}</p>
            </div>
            {i < STAGES.length - 1 && (
              <div className="flow-connector" aria-hidden="true" style={{ '--i': i }}>
                <span className="flow-dot" />
              </div>
            )}
          </Fragment>
        ))}
      </div>

      <div className="tap-diagram">
        <div className="tap-copy">
          <span className="small-label">Where the score comes from</span>
          <h3>Reading one layer, one token, one probe.</h3>
          <p>Every hop prefix runs through the same {LAYER_COUNT}-block frozen transformer. Only the final token&rsquo;s activation at block {TAPPED_LAYER} is kept &mdash; an 896-value vector. A scikit-learn classifier trained on clean vs. corrupted HotpotQA hops turns that vector into the error score shown per hop.</p>
        </div>
        <div className="tap-visual" aria-hidden="true">
          <div className="tap-stack">
            {Array.from({ length: LAYER_COUNT }, (_, i) => LAYER_COUNT - i).map((n) => (
              <div key={n} className={`tap-layer ${n === TAPPED_LAYER ? 'is-tapped' : ''}`}>
                {n === TAPPED_LAYER && <span className="tap-layer-label">block {n}</span>}
              </div>
            ))}
          </div>
          <svg className="tap-line" viewBox="0 0 60 10" preserveAspectRatio="none">
            <line x1="0" y1="5" x2="60" y2="5" stroke="var(--brand-2)" strokeWidth="1" strokeDasharray="3 3" />
          </svg>
          <div className="tap-vector">
            {Array.from({ length: 8 }, (_, i) => <span key={i} style={{ '--i': i }} />)}
            <em>×896</em>
          </div>
          <svg className="tap-line" viewBox="0 0 60 10" preserveAspectRatio="none">
            <line x1="0" y1="5" x2="60" y2="5" stroke="var(--brand-2)" strokeWidth="1" strokeDasharray="3 3" />
          </svg>
          <div className="tap-probe">probe</div>
          <svg className="tap-line" viewBox="0 0 60 10" preserveAspectRatio="none">
            <line x1="0" y1="5" x2="60" y2="5" stroke="var(--brand-2)" strokeWidth="1" strokeDasharray="3 3" />
          </svg>
          <div className="tap-gauge">
            <div className="tap-gauge-track">
              <div className="tap-gauge-fill" />
              <div className="tap-gauge-threshold" />
            </div>
            <span className="muted">error score</span>
          </div>
        </div>
      </div>
    </section>
  )
}
