import React, { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import axios from 'axios'

const API_BASE = 'http://127.0.0.1:8001'

export default function ReportPage() {
  const { screenId } = useParams()
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!screenId) return

    const loadReport = async () => {
      try {
        setLoading(true)
        const response = await axios.get(`${API_BASE}/api/reports`)
        const data = response.data
        const screenReport = data.reports?.find((r) => r.screenId === screenId)
        if (!screenReport) {
          throw new Error('Report not found for this screen.')
        }
        setReport(screenReport.report)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load report.')
      } finally {
        setLoading(false)
      }
    }

    loadReport()
  }, [screenId])

  if (loading) {
    return (
      <div className="min-h-screen bg-dark-bg text-text-primary flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-text-secondary">Loading report...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-dark-bg text-text-primary flex items-center justify-center">
        <div className="bg-red-900 text-red-200 border border-red-700 p-6 rounded-lg max-w-md">
          <h2 className="text-lg font-bold mb-2">Error</h2>
          <p>{error}</p>
          <Link to="/" className="inline-block mt-4 text-primary hover:underline">
            Back to Home
          </Link>
        </div>
      </div>
    )
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-dark-bg text-text-primary flex items-center justify-center">
        <div className="text-center">
          <p className="text-text-secondary mb-4">No report available for this screen.</p>
          <Link to="/" className="text-primary hover:underline">
            Back to Home
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-dark-bg text-text-primary">
      <div className="max-w-6xl mx-auto p-6">
        <div className="mb-6">
          <Link to="/" className="text-primary hover:underline mb-4 inline-block">
            ← Back to Home
          </Link>
          <h1 className="text-3xl font-bold text-primary">Evaluation Report: {screenId}</h1>
          <p className="text-text-secondary mt-2">Detailed usability evaluation breakdown</p>
        </div>

        <div className="bg-dark-card border border-dark-hover rounded-lg shadow-sm p-6 mb-6">
          <h2 className="text-xl font-bold text-primary mb-4">Overall Scores</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-dark-bg border border-cyan-700 rounded-lg">
              <div className="text-3xl font-bold text-cyan-400">{report.total_score || 0}</div>
              <div className="text-sm text-text-secondary">Total Score</div>
            </div>
            <div className="text-center p-4 bg-dark-bg border border-green-700 rounded-lg">
              <div className="text-3xl font-bold text-green-400">{report.iso_score || 0}</div>
              <div className="text-sm text-text-secondary">ISO 9241-11</div>
            </div>
            <div className="text-center p-4 bg-dark-bg border border-purple-700 rounded-lg">
              <div className="text-3xl font-bold text-purple-400">{report.nielsen_score || 0}</div>
              <div className="text-sm text-text-secondary">Nielsen</div>
            </div>
            <div className="text-center p-4 bg-dark-bg border border-blue-700 rounded-lg">
              <div className="text-3xl font-bold text-blue-400">{report.wcag_score || 0}</div>
              <div className="text-sm text-text-secondary">WCAG 2.2</div>
            </div>
          </div>
          <div className="mt-4 p-3 bg-dark-bg border border-yellow-700 rounded-lg">
            <p className="text-sm text-text-secondary">
              <strong className="text-text-primary">Weakest Standard:</strong> {report.weakest_standard || 'N/A'}
            </p>
          </div>
        </div>

        {report.iso_details && (
          <div className="bg-dark-card border border-dark-hover rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-xl font-bold text-primary mb-4">ISO 9241-11 Details</h2>
            <div className="mb-4">
              <p className="text-lg font-semibold text-text-primary">Score: {report.iso_details.iso_score || 0}/100</p>
              <p className="text-sm text-text-secondary">Weakest Metric: {report.iso_details.weakest_metric || 'N/A'}</p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {Object.entries(report.iso_details.sub_scores || {}).map(([metric, score]) => (
                <div key={metric} className="p-3 bg-dark-bg border border-green-700 rounded-lg">
                  <div className="font-medium text-text-primary capitalize">{metric.replace(/_/g, ' ')}</div>
                  <div className="text-2xl font-bold text-green-400">{score}/4</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {report.nielsen_details && (
          <div className="bg-dark-card border border-dark-hover rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-xl font-bold text-primary mb-4">Nielsen Heuristics Details</h2>
            <div className="mb-4">
              <p className="text-lg font-semibold text-text-primary">Score: {report.nielsen_details.nielsen_score || 0}/100</p>
              <p className="text-sm text-text-secondary">Weakest Metric: {report.nielsen_details.weakest_metric || 'N/A'}</p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(report.nielsen_details.sub_scores || {}).map(([metric, score]) => (
                <div key={metric} className="p-3 bg-dark-bg border border-purple-700 rounded-lg">
                  <div className="font-medium text-text-primary capitalize">{metric.replace(/_/g, ' ')}</div>
                  <div className="text-2xl font-bold text-purple-400">{score}/4</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {report.wcag_details && (
          <div className="bg-dark-card border border-dark-hover rounded-lg shadow-sm p-6 mb-6">
            <h2 className="text-xl font-bold text-primary mb-4">WCAG 2.2 Details</h2>
            <div className="mb-4">
              <p className="text-lg font-semibold text-text-primary">Score: {report.wcag_details.wcag_score ?? 0}/100</p>
              <p className="text-sm text-text-secondary">
                Reliability: {report.wcag_details.reliability ?? 'N/A'}
                {report.wcag_details.weakest_pour && report.wcag_details.weakest_pour !== 'unavailable'
                  ? ` | Weakest POUR: ${report.wcag_details.weakest_pour}`
                  : ''}
              </p>
            </div>

            {report.wcag_details.reliability === 'partial' && (
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-yellow-600 bg-yellow-900/20 px-3 py-1 text-xs font-semibold text-yellow-300">
                Partial WCAG mode — axe-core unavailable. Install it with: npm install -g @axe-core/cli
              </div>
            )}

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              {[
                { label: 'Alt Text', value: report.wcag_details.alt_score },
                { label: 'Landmarks', value: report.wcag_details.landmark_score },
                { label: 'Contrast', value: report.wcag_details.contrast_score },
                { label: 'Language', value: report.wcag_details.lang_score },
              ].map(({ label, value }) => (
                <div key={label} className="p-3 bg-dark-bg border border-blue-700 rounded-lg">
                  <div className="font-medium text-text-primary">{label}</div>
                  <div className="text-2xl font-bold text-blue-400">
                    {value != null ? `${Math.round(value)}%` : '—'}
                  </div>
                </div>
              ))}
            </div>

            {report.wcag_details.axe_score != null && (
              <div className="mb-6">
                <div className="p-3 bg-dark-bg border border-blue-700 rounded-lg inline-block">
                  <div className="font-medium text-text-primary">Axe-core Score</div>
                  <div className="text-2xl font-bold text-blue-400">{Math.round(report.wcag_details.axe_score)}/100</div>
                  {report.wcag_details.violations_count != null && (
                    <div className="text-xs text-text-secondary mt-1">{report.wcag_details.violations_count} violation(s) found</div>
                  )}
                </div>
              </div>
            )}

            {(() => {
              const pour = report.wcag_details.pour_scores ?? {}
              const validPour = Object.entries(pour).filter(([, v]) => v != null)
              if (validPour.length === 0) {
                return (
                  <div className="mt-2 p-3 bg-dark-bg border border-dark-hover rounded text-sm text-text-secondary">
                    POUR principle breakdown requires axe-core.{' '}
                    <span className="text-yellow-300">Run: npm install -g @axe-core/cli</span>
                  </div>
                )
              }
              return (
                <div className="mt-4">
                  <h3 className="font-semibold text-text-primary mb-2">POUR Scores (out of 25)</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {validPour.map(([principle, score]) => (
                      <div key={principle} className="p-3 bg-dark-bg border border-blue-700 rounded-lg">
                        <div className="font-medium text-text-primary">{principle}</div>
                        <div className="text-xl font-bold text-blue-400">{score}/25</div>
                      </div>
                    ))}
                  </div>
                </div>
              )
            })()}
          </div>
        )}

        <div className="bg-dark-card border border-dark-hover rounded-lg shadow-sm p-6">
          <Link
            to={`/preview/${screenId}`}
            className="inline-flex items-center px-4 py-2 bg-primary text-black rounded-lg hover:bg-primary/90 transition-colors font-semibold"
          >
            View Screen Preview
          </Link>
        </div>
      </div>
    </div>
  )
}