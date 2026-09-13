import { useEffect, useRef, useState } from 'react'
import Header from './components/Header.jsx'
import InputPanel from './components/InputPanel.jsx'
import ResultsPanel from './components/ResultsPanel.jsx'
import HowItWorks from './components/HowItWorks.jsx'
import { getHealth, analyze, fetchReportBlob } from './api.js'

export default function App() {
  const [status, setStatus] = useState('loading')
  const [setupMessage, setSetupMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [elapsed, setElapsed] = useState(0)
  const timerRef = useRef(null)
  const pollRef = useRef(null)

  useEffect(() => {
    let cancelled = false
    async function poll() {
      try {
        const data = await getHealth()
        if (cancelled) return
        setStatus(data.status)
        setSetupMessage(data.message || '')
        if (data.status === 'loading') {
          pollRef.current = setTimeout(poll, 4000)
        }
      } catch {
        if (cancelled) return
        setStatus('offline')
        setSetupMessage('Start the FastAPI backend and reload this page.')
      }
    }
    poll()
    return () => {
      cancelled = true
      clearTimeout(pollRef.current)
    }
  }, [])

  async function handleSubmit({ question, context, injectTestError, sourceName }) {
    setError('')
    setBusy(true)
    setElapsed(0)
    const started = Date.now()
    timerRef.current = setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1000)
    try {
      const data = await analyze({ question, context, injectTestError, sourceName })
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      clearInterval(timerRef.current)
      setBusy(false)
    }
  }

  async function handleDownload() {
    if (!result?.report_id) return
    try {
      const blob = await fetchReportBlob(result.report_id)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'reasoning-diagnostic.pdf'
      a.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (err) {
      setError(err.message)
    }
  }

  const ready = status === 'ready'

  return (
    <>
      <div className="bg-mesh" aria-hidden="true" />
      <Header status={status} />
      <main>
        <div className="intro">
          <span className="eyebrow">From evidence to explanation</span>
          <h1>Catch the wrong hop before it becomes the wrong answer.</h1>
          <p>Generate a fresh multi-hop reasoning chain, score every hop with a trained hidden-state probe, and cross-check the most suspicious claim against the source.</p>
          <div className="trust-strip">
            <span><span className="trust-dot" />Hidden-state probing</span>
            <span><span className="trust-dot" />Independent evidence check</span>
            <span><span className="trust-dot" />Transparent retrieval</span>
          </div>
        </div>

        {setupMessage && status !== 'ready' && <div className="notice">{setupMessage}</div>}

        <HowItWorks />

        <div className="workspace" id="workspace">
          <InputPanel ready={ready} busy={busy} onSubmit={handleSubmit} elapsed={elapsed} />
          <ResultsPanel data={result} onDownload={handleDownload} />
        </div>

        {error && <div className="error toast" role="alert">{error}</div>}

        <footer>
          Experimental factual reasoning diagnostic. The probe was trained on HotpotQA-style controlled corruptions and may not generalize to unrelated domains. Error scores are uncalibrated and are not proof of factual incorrectness.
        </footer>
      </main>
    </>
  )
}
