import EmptyState from './EmptyState.jsx'
import ScoreChart from './ScoreChart.jsx'
import HopCard from './HopCard.jsx'
import EvidenceCard from './EvidenceCard.jsx'

export default function ResultsPanel({ data, onDownload }) {
  return (
    <section className="panel results-panel" aria-labelledby="results-title">
      <div className="panel-heading results-heading">
        <span className="step-number">02</span>
        <div>
          <h2 id="results-title">Reasoning analysis</h2>
          <p>Localization and evidence checking, shown separately.</p>
        </div>
        {data && (
          <button className="secondary" onClick={onDownload}>Download PDF</button>
        )}
      </div>

      {!data && <EmptyState />}

      {data && (
        <div className="results-body" aria-live="polite">
          <span className="small-label">Analyzed question</span>
          <p className="result-summary">{data.question}</p>

          <div className="answer-box">
            <span className="small-label">Generated answer</span>
            <p>{data.answer}</p>
            {data.answer_note && <div className="muted">{data.answer_note}</div>}
          </div>

          {data.controlled_error && (
            <div className="demo-result">
              <h3>Controlled test error</h3>
              <div>
                A test edit was inserted at Hop {data.controlled_error.hop_index}: {data.controlled_error.original_value} → {data.controlled_error.replacement_value}.
              </div>
              <div>
                Highest-scoring hop: {data.most_suspicious_hop}. {data.controlled_error.correct_localization ? 'The probe localized the edited hop.' : 'The probe did not localize the edited hop.'}
              </div>
              <div className="muted">This is an injected test, not a naturally occurring model error.</div>
            </div>
          )}

          <span className="small-label">Probe localization</span>
          <p className="result-summary">
            {data.first_flagged_hop === null
              ? 'No reasoning hop crossed the learned error threshold.'
              : `First threshold crossing: Hop ${data.first_flagged_hop}. This is a candidate error location.`}
          </p>

          <div className="metrics">
            <div className="metric">
              <span className="small-label">Highest-scoring</span>
              <strong>Hop {data.most_suspicious_hop}</strong>
            </div>
            <div className="metric">
              <span className="small-label">Hops analyzed</span>
              <strong>{data.hops.length}</strong>
            </div>
            <div className="metric">
              <span className="small-label">Threshold</span>
              <strong>{data.threshold.toFixed(2)}</strong>
            </div>
          </div>

          <ScoreChart rows={data.hops} threshold={data.threshold} highest={data.most_suspicious_hop} />

          <div className="hop-list">
            {data.hops.map((hop) => (
              <HopCard key={hop.index} hop={hop} isHighest={hop.index === data.most_suspicious_hop} />
            ))}
          </div>

          <EvidenceCard evidence={data.evidence_analysis} hopIndex={data.most_suspicious_hop} />

          <details className="reference-details">
            <summary>{data.retrieval.used ? `Evidence excerpts used · ${data.reference_source}` : `Reference used · ${data.reference_source}`}</summary>
            <p>{data.retrieval.used ? 'Only the displayed retrieved excerpts were analyzed; omitted text was not checked.' : 'The full supplied reference was analyzed.'}</p>
            <pre>{data.reference_context}</pre>
          </details>

          {(data.warnings || []).map((warning) => (
            <p className="muted" key={warning}>{warning}</p>
          ))}
        </div>
      )}
    </section>
  )
}
