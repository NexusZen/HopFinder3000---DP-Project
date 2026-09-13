async function responseJSON(response) {
  const data = await response.json()
  if (!response.ok) {
    throw new Error(typeof data.detail === 'string' ? data.detail : data.detail?.message || 'The request could not be completed.')
  }
  return data
}

export async function getHealth() {
  return responseJSON(await fetch('/api/health'))
}

export async function analyze({ question, context, injectTestError, sourceName }) {
  return responseJSON(
    await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        context,
        inject_test_error: injectTestError,
        source_name: sourceName,
      }),
    }),
  )
}

export async function uploadDocument(file) {
  const form = new FormData()
  form.append('file', file)
  return responseJSON(await fetch('/api/documents', { method: 'POST', body: form }))
}

export async function fetchReportBlob(reportId) {
  const res = await fetch(`/api/reports/${reportId}.pdf`)
  if (!res.ok) {
    await responseJSON(res)
  }
  return res.blob()
}
