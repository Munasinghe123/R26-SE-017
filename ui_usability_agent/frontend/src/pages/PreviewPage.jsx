import React, { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import axios from 'axios'

const API_BASE = 'http://127.0.0.1:8001'

const highlightScript = (frId) => `
<script>
(function() {
  function run() {
    var targets = document.querySelectorAll('[data-fr]');
    var match = null;
    targets.forEach(function(el) {
      var ids = (el.getAttribute('data-fr') || '').split(',').map(function(s){ return s.trim(); });
      if (!match && ids.indexOf(${JSON.stringify(frId)}) !== -1) match = el;
    });
    if (match) {
      match.scrollIntoView({ behavior: 'smooth', block: 'center' });
      match.style.outline = '3px solid #facc15';
      match.style.outlineOffset = '2px';
      match.style.transition = 'outline-color 0.6s ease';
      setTimeout(function() { match.style.outlineColor = '#22d3ee'; }, 1200);
    }
  }
  if (document.readyState === 'complete' || document.readyState === 'interactive') {
    setTimeout(run, 50);
  } else {
    document.addEventListener('DOMContentLoaded', run);
  }
})();
</script>
`

export default function PreviewPage() {
  const { screenId } = useParams()
  const [searchParams] = useSearchParams()
  const highlightFr = searchParams.get('highlight')
  const [html, setHtml] = useState('')
  const [error, setError] = useState('')
  const [screens, setScreens] = useState([])
  const [loading, setLoading] = useState(true)
  const [report, setReport] = useState(null)
  const [reportLoading, setReportLoading] = useState(false)

  const downloadHtml = () => {
    if (!html) return
    const blob = new Blob([html], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${screenId}.html`
    a.click()
    URL.revokeObjectURL(url)
  }

  const loadReport = async () => {
    try {
      setReportLoading(true)
      const response = await axios.get(`${API_BASE}/api/reports`)
      const data = response.data
      const screenReport = data.reports?.find((r) => r.screenId === screenId)
      setReport(screenReport || null)
    } catch (err) {
      console.error('Failed to load report:', err)
    } finally {
      setReportLoading(false)
    }
  }

  const loadScreens = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/outputs`)
      setScreens(response.data.screens || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load screens.')
    }
  }

  useEffect(() => {
    if (!screenId) return

   if (rawHtml) {
  const targetFr = highlightFr || "";
  rawHtml = rawHtml.includes('</body>')
    ? rawHtml.replace('</body>', `${highlightScript(targetFr)}</body>`)
    : rawHtml + highlightScript(targetFr);
}

    loadScreens()
    loadPreview()
    loadReport()
  }, [screenId, highlightFr])

  return (
    <div className="min-h-screen bg-dark-bg text-text-primary flex">
      <aside className="w-full max-w-xs bg-dark-card border-r border-dark-hover p-6 overflow-y-auto">
        <div className="mb-6">
          <h1 className="text-xl font-bold text-primary">Generated Screens</h1>
          <p className="text-sm text-text-secondary">Pick a screen to preview</p>
        </div>
        <div className="space-y-2">
          {screens.length === 0 ? (
            <p className="text-text-secondary text-sm">No generated screens yet.</p>
          ) : (
            screens.map((id) => (
              <Link
                key={id}
                to={`/preview/${id}`}
                className={`block rounded-md border px-3 py-2 text-sm transition ${id === screenId ? 'border-primary bg-primary bg-opacity-20 text-black' : 'border-dark-hover text-text-secondary hover:border-primary'}`}
              >
                {id}
              </Link>
            ))
          )}
        </div>
        <Link className="mt-6 inline-flex text-sm text-primary hover:underline" to="/">
          Back to Wizard
        </Link>
      </aside>
      <main className="flex-1 p-6 overflow-auto">
        <div className="mb-4 flex items-center gap-3">
          <div>
            <h2 className="text-2xl font-bold text-primary">Preview: {screenId}</h2>
            <p className="text-sm text-text-secondary">Full-screen render of the generated HTML</p>
          </div>
          {highlightFr && (
            <span className="text-xs px-2 py-1 rounded-full bg-yellow-900 text-yellow-300">
              Highlighting {highlightFr}
            </span>
          )}
          <button
            onClick={downloadHtml}
            disabled={!html}
            className="ml-auto text-sm px-3 py-1.5 rounded-md border border-dark-hover text-text-primary hover:border-primary transition disabled:opacity-40"
          >
            Download HTML
          </button>
        </div>
        {error ? (
          <div className="bg-red-900 text-red-200 border border-red-700 p-4 rounded">{error}</div>
        ) : (
          <div className="space-y-6">
            <div className="bg-dark-card border border-dark-hover rounded-lg shadow-sm p-0 min-h-[70vh] overflow-hidden">
              {loading ? (
                <p className="text-text-secondary p-4">Loading preview...</p>
              ) : html ? (
                <iframe
                  title={`Preview ${screenId}`}
                  className="w-full h-[70vh]"
                  srcDoc={html}
                  sandbox="allow-scripts allow-same-origin"
                  // MINIMAL FIX: Block clicks from escaping the window frame
                  onLoad={(e) => {
                    e.target.contentWindow.document.addEventListener('click', (evt) => {
                      const el = evt.target.closest('a, button');
                      if (el) {
                        evt.preventDefault();
                        evt.stopPropagation();
                      }
                    }, true);
                  }}
                />

              ) : (
                <p className="text-text-secondary p-4">No HTML available for this screen.</p>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}