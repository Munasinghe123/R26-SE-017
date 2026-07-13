import React, { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import axios from 'axios'

const API_BASE = 'http://127.0.0.1:8001'

export default function PreviewPage() {
  const { screenId } = useParams()
  const [html, setHtml] = useState('')
  const [error, setError] = useState('')
  const [screens, setScreens] = useState([])
  const [loading, setLoading] = useState(true)
  const [report, setReport] = useState(null)
  const [reportLoading, setReportLoading] = useState(false)

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
      const data = response.data
      setScreens(data.screens || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load screens.')
    }
  }

  useEffect(() => {
    if (!screenId) return

    const loadPreview = async () => {
      try {
        setLoading(true)
        setError('')
        const response = await axios.get(`${API_BASE}/api/outputs`, {
          params: { screenId },
        })
        const data = response.data
        setHtml(data.html || '')
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load preview.')
      } finally {
        setLoading(false)
      }
    }

    loadScreens()
    loadPreview()
    loadReport()
  }, [screenId])

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
              <a
                key={id}
                href={`/preview/${id}`}
                className={`block rounded-md border px-3 py-2 text-sm transition ${id === screenId ? 'border-primary bg-primary bg-opacity-20 text-black' : 'border-dark-hover text-text-secondary hover:border-primary'}`}
              >
                {id}
              </a>
            ))
          )}
        </div>
        <Link className="mt-6 inline-flex text-sm text-primary hover:underline" to="/">
          Back to Wizard
        </Link>
      </aside>
      <main className="flex-1 p-6 overflow-auto">
        <div className="mb-4">
          <h2 className="text-2xl font-bold text-primary">Preview: {screenId}</h2>
          <p className="text-sm text-text-secondary">Full-screen render of the generated HTML</p>
        </div>
        {error ? (
          <div className="bg-red-900 text-red-200 border border-red-700 p-4 rounded">
            {error}
          </div>
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
                />
              ) : (
                <p className="text-text-secondary p-4">No HTML available for this screen.</p>
              )}
            </div>

            {report && (
              <div className="bg-dark-card border border-dark-hover rounded-lg shadow-sm p-6">
                <h3 className="text-xl font-bold text-primary mb-4">Usability Evaluation Report</h3>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="text-center p-4 bg-dark-bg border border-green-700 rounded-lg">
                    <div className="text-3xl font-bold text-green-400">{report.report?.iso_score || 0}</div>
                    <div className="text-sm text-text-secondary">ISO 9241-11</div>
                  </div>
                  <div className="text-center p-4 bg-dark-bg border border-purple-700 rounded-lg">
                    <div className="text-3xl font-bold text-purple-400">{report.report?.nielsen_score || 0}</div>
                    <div className="text-sm text-text-secondary">Nielsen</div>
                  </div>
                  <div className="text-center p-4 bg-dark-bg border border-blue-700 rounded-lg">
                    <div className="text-3xl font-bold text-blue-400">{report.report?.wcag_score || 0}</div>
                    <div className="text-sm text-text-secondary">WCAG 2.2</div>
                  </div>
                  <div className="text-center p-4 bg-dark-bg border border-cyan-700 rounded-lg">
                    <div className="text-3xl font-bold text-cyan-400">{report.report?.total_score || 0}</div>
                    <div className="text-sm text-text-secondary">Composite</div>
                  </div>
                </div>

                <div className="grid md:grid-cols-3 gap-6">
                  <div>
                    <h4 className="font-semibold text-text-primary mb-3">ISO 9241-11 Details</h4>
                    <div className="space-y-2">
                      {report.report?.iso_details?.sub_scores
                        && Object.entries(report.report.iso_details.sub_scores).map(([key, value]) => (
                        <div key={key} className="flex justify-between text-sm">
                          <span className="text-text-secondary">{key.replace(/_/g, ' ')}</span>
                          <span className="font-medium text-text-primary">{value}/4</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-text-primary mb-3">Nielsen Heuristics Details</h4>
                    <div className="space-y-2">
                      {report.report?.nielsen_details?.sub_scores
                        && Object.entries(report.report.nielsen_details.sub_scores).map(([key, value]) => (
                        <div key={key} className="flex justify-between text-sm">
                          <span className="text-text-secondary">{key.replace(/_/g, ' ')}</span>
                          <span className="font-medium text-text-primary">{value}/4</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-text-primary mb-3">WCAG 2.2 Details</h4>
                    <div className="space-y-2">
                      {report.report?.wcag_details
                        && Object.entries(report.report.wcag_details).map(([key, value]) => (
                        <div key={key} className="flex justify-between text-sm">
                          <span className="text-text-secondary">{key.replace(/_/g, ' ')}</span>
                          <span className="font-medium text-text-primary">{value ? '✓' : '✗'}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {report.status && (
                  <div className="mt-6 p-4 rounded-lg bg-dark-bg border border-green-700">
                    <div className="flex items-center">
                      <span className="text-green-400 font-medium">✓ PASSED</span>
                      <span className="ml-2 text-sm text-text-secondary">
                        Score: {report.report?.total_score || 0} / Threshold: {report.report?.threshold || 65}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {reportLoading && (
              <div className="bg-dark-card border border-dark-hover rounded-lg shadow-sm p-6">
                <p className="text-text-secondary">Loading evaluation report...</p>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}