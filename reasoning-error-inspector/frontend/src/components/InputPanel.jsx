import { useState } from 'react'
import { uploadDocument } from '../api.js'
import { EXAMPLES } from '../examples.js'

export default function InputPanel({ ready, busy, onSubmit, elapsed }) {
  const [question, setQuestion] = useState('')
  const [context, setContext] = useState('')
  const [demo, setDemo] = useState(false)
  const [sourceName, setSourceName] = useState(null)
  const [sourceStatus, setSourceStatus] = useState('or paste text above')
  const [uploadError, setUploadError] = useState('')

  async function handleFile(e) {
    const file = e.target.files[0]
    e.target.value = ''
    if (!file) return
    if (file.size > 10 * 1024 * 1024) {
      setUploadError('Choose a document smaller than 10 MB.')
      return
    }
    setUploadError('')
    setSourceStatus('Extracting document text…')
    try {
      const data = await uploadDocument(file)
      setContext(data.text)
      setSourceName(data.name)
      setSourceStatus(`${data.name} · ${data.characters.toLocaleString()} characters`)
    } catch (err) {
      setUploadError(err.message)
      setSourceStatus('Upload failed; pasted text is unchanged')
    }
  }

  function handleSubmit(e) {
    e.preventDefault()
    if (busy || !ready) return
    onSubmit({ question, context, injectTestError: demo, sourceName })
  }

  function loadExample(example) {
    if (busy) return
    setQuestion(example.question)
    setContext(example.context)
    setSourceName(null)
    setSourceStatus('or paste text above')
    setUploadError('')
  }

  return (
    <section className="panel input-panel" aria-labelledby="input-title">
      <div className="panel-heading">
        <span className="step-number">01</span>
        <div>
          <h2 id="input-title">Question &amp; evidence</h2>
          <p>Start with a question and its reference material.</p>
        </div>
      </div>
      {EXAMPLES.length > 0 && (
        <div className="example-row">
          <span className="small-label">Try an example</span>
          <div className="example-chips">
            {EXAMPLES.map((example) => (
              <button
                type="button"
                key={example.label}
                className="example-chip"
                onClick={() => loadExample(example)}
                disabled={busy}
              >
                {example.label}
              </button>
            ))}
          </div>
        </div>
      )}
      <form onSubmit={handleSubmit}>
        <label htmlFor="question">Your question</label>
        <textarea
          id="question"
          rows={3}
          maxLength={1500}
          required
          placeholder="Who founded the university where this person taught?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <div className="field-heading">
          <label htmlFor="context">Reference context / evidence</label>
          <span>{context.length.toLocaleString()} characters</span>
        </div>
        <textarea
          id="context"
          rows={12}
          maxLength={250000}
          required
          placeholder="Paste the source text the model should use to answer your question…"
          value={context}
          onChange={(e) => setContext(e.target.value)}
        />
        <div className="upload-row">
          <label className="upload-button" htmlFor="document">
            Upload document <span>TXT or PDF</span>
          </label>
          <input type="file" id="document" accept=".txt,.pdf" className="visually-hidden" onChange={handleFile} disabled={busy} />
          <span className="source-name">{sourceStatus}</span>
        </div>
        {uploadError && <div className="error" role="alert">{uploadError}</div>}
        <p className="helper">Long documents use relevant excerpts. You can inspect the exact evidence used with the results.</p>
        <label className="demo-toggle">
          <span className="switch">
            <input type="checkbox" checked={demo} onChange={(e) => setDemo(e.target.checked)} />
            <span className="switch-track"><span className="switch-thumb" /></span>
          </span>
          <span>
            <strong>Inject controlled test error</strong>
            <small>Change one supported value after generation for a labeled demonstration.</small>
          </span>
        </label>
        <button type="submit" className="primary" disabled={!ready || busy}>
          <span>Analyze reasoning</span>
          <span aria-hidden="true">{busy ? '···' : '↗'}</span>
        </button>
        {busy && (
          <div className="activity" role="status">
            <span className="spinner" />
            <span>Generating and analyzing… {elapsed}s</span>
          </div>
        )}
      </form>
    </section>
  )
}
