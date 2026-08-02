import React, { useState, useEffect } from 'react'
import axios from 'axios'
import InputForm from '../components/InputForm'
import UIOutput from '../components/UIOutput'
import DocumentationTabs from '../components/DocumentationTabs'
import RefinementHistory from '../components/RefinementHistory'
import ConvergenceChart from '../components/ConvergenceChart'

const API_BASE = 'http://127.0.0.1:8001'

export default function Home() {
  const [activeStep, setActiveStep] = useState('plan')
  const [requirements, setRequirements] = useState('')
  const [planScreens, setPlanScreens] = useState([])
  const [selectedScreenId, setSelectedScreenId] = useState('')
  const [generatedUI, setGeneratedUI] = useState('')
  const [evaluationReports, setEvaluationReports] = useState([])
  const [loading, setLoading] = useState({ plan: false, generate: false, evaluate: false ,refine: false})
  const [error, setError] = useState('')
  const [logs, setLogs] = useState('')
  const [outputScreens, setOutputScreens] = useState([])
  const [outputsLoading, setOutputsLoading] = useState(false)
  const [reportsLoading, setReportsLoading] = useState(false)
  const [selectedScreensForEval, setSelectedScreensForEval] = useState([])
  const [selectedScreenForRefine, setSelectedScreenForRefine] = useState('')
  const [refinementResult, setRefinementResult] = useState(null)
  const [restoring, setRestoring] = useState(true)

  useEffect(() => {
    const restore = async () => {
      try {
        const [outputsRes, planRes, reportsRes] = await Promise.all([
          axios.get(`${API_BASE}/api/outputs`),
          axios.get(`${API_BASE}/api/plan-status`),
          axios.get(`${API_BASE}/api/reports`),
        ])

        const outputsData = outputsRes.data
        const screens = outputsData.screens || []
        setOutputScreens(screens)
        if (screens.length > 0) {
          setActiveStep('evaluate')
        }

        const planData = planRes.data
        if (planData.screens && planData.screens.length > 0) {
          setPlanScreens(planData.screens)
          setSelectedScreenId(planData.screens[0]?.screen_id || '')
        }

        const reportsData = reportsRes.data
        if (reportsData.reports && reportsData.reports.length > 0) {
          setEvaluationReports(reportsData.reports)
        }

        if (screens.length > 0) {
          const historyRes = await axios.get(`${API_BASE}/api/history`, { params: { screenId: screens[0] } }).catch(() => ({ data: { history: [] } }))
          if (historyRes.data.history?.length > 0) {
            setRefinementResult({
              screenId: screens[0],
              history: historyRes.data.history,
              finalReport: historyRes.data.history.find((h) => h.isFinal)?.report,
              passed: historyRes.data.history.find((h) => h.isFinal)?.report?.total_score >= 85,
              regressed: false,
            })
            setSelectedScreenForRefine(screens[0])
          }
        }
      } catch (err) {
        console.warn('[restore] Could not restore state:', err)
      } finally {
        setRestoring(false)
      }
    }

    restore()
  }, [])

  const formatLogs = (logData) => {
    if (!logData) return ''
    const stdout = logData.stdout ? `STDOUT:\n${logData.stdout}` : ''
    const stderr = logData.stderr ? `STDERR:\n${logData.stderr}` : ''
    return [stdout, stderr].filter(Boolean).join('\n\n')
  }

  const loadOutputs = async () => {
    try {
      setOutputsLoading(true)
      const response = await axios.get(`${API_BASE}/api/outputs`)
      const data = response.data
      setOutputScreens(data.screens || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load outputs.')
    } finally {
      setOutputsLoading(false)
    }
  }

  const previewOutput = async (screenId) => {
    try {
      setError('')
      const response = await axios.get(`${API_BASE}/api/outputs`, {
        params: { screenId },
      })
      const data = response.data
      setGeneratedUI(data.html || '')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load output.')
    }
  }

  const loadReports = async () => {
    try {
      setReportsLoading(true)
      const response = await axios.get(`${API_BASE}/api/reports`)
      const data = response.data
      setEvaluationReports(data.reports || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load reports.')
    } finally {
      setReportsLoading(false)
    }
  }

  const handlePlan = async () => {
    try {
      setError('')
      setLoading((prev) => ({ ...prev, plan: true }))
      if (!requirements.trim()) {
        throw new Error('Please provide requirements JSON or upload a file.')
      }

      let parsedRequirements
      try {
        parsedRequirements = JSON.parse(requirements)
      } catch (parseError) {
        throw new Error('Requirements must be valid JSON.')
      }

      const response = await axios.post(`${API_BASE}/api/plan`, { requirements: parsedRequirements })
      const data = response.data

      setPlanScreens(data.screens || [])
      setSelectedScreenId(data.screens?.[0]?.screen_id || '')
      setLogs(formatLogs(data.logs))
      setActiveStep('generate')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Planning failed.')
    } finally {
      setLoading((prev) => ({ ...prev, plan: false }))
    }
  }

  const handleGenerate = async () => {
    try {
      setError('')
      if (!selectedScreenId) {
        setError('Select a screen to generate.')
        return
      }

      setLoading((prev) => ({ ...prev, generate: true }))
      const response = await axios.post(`${API_BASE}/api/generate`, { screenId: selectedScreenId })
      const data = response.data

      setGeneratedUI(data.html || '')
      setLogs(formatLogs(data.logs))
      setActiveStep('evaluate')
      loadOutputs()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Generation failed.')
    } finally {
      setLoading((prev) => ({ ...prev, generate: false }))
    }
  }

  const handleEvaluate = async () => {
    try {
      setError('')
      setLoading((prev) => ({ ...prev, evaluate: true }))

      const body = selectedScreensForEval.length > 0 ? { screenIds: selectedScreensForEval } : {}
      const response = await axios.post(`${API_BASE}/api/evaluate`, body)
      const data = response.data

      setEvaluationReports(data.reports || [])
      setLogs(formatLogs(data.logs))
      loadReports()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Evaluation failed.')
    } finally {
      setLoading((prev) => ({ ...prev, evaluate: false }))
    }
  }
  
  const handleRefine = async () => {
    try {
      setError('')
      if (!selectedScreenForRefine) {
        setError('Select a screen to refine.')
        return
      }

      setLoading((prev) => ({ ...prev, refine: true }))
      const response = await axios.post(`${API_BASE}/api/refine`, { screenId: selectedScreenForRefine })
      const data = response.data

      setGeneratedUI(data.html || '')
      setRefinementResult(data)
      setLogs(formatLogs(data.logs))
      loadOutputs()
      loadReports()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Refinement failed.')
    } finally {
      setLoading((prev) => ({ ...prev, refine: false }))
    }
  }

  const handleClearSession = async () => {
    if (!confirm('Clear all session data? This removes the screen plan, generated screens, and score reports.')) return
    try {
      await axios.post(`${API_BASE}/api/clear-session`)
      setRequirements('')
      setPlanScreens([])
      setSelectedScreenId('')
      setGeneratedUI('')
      setEvaluationReports([])
      setLogs('')
      setOutputScreens([])
      setSelectedScreensForEval([])
      setSelectedScreenForRefine('')
      setRefinementResult(null)
      setError('')
      setActiveStep('plan')
    } catch (err) {
      setError('Failed to clear session.')
    }
  };

  if (restoring) {
    return (
      <div className="min-h-screen bg-dark-bg text-text-primary flex items-center justify-center">
        <p className="text-text-secondary animate-pulse">Restoring session...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-dark-bg text-text-primary">
      <div className="flex items-center justify-between bg-dark-card border-b border-dark-hover shadow-lg px-6 py-4">
        <div>
          <h1 className="text-3xl font-bold text-primary">UI/UX Usability Agent</h1>
          <p className="text-text-secondary text-sm mt-1">Generate and Evaluate UI Prototypes</p>
        </div>
        <button
          onClick={handleClearSession}
          className="px-4 py-2 text-sm rounded-md border border-red-700 text-red-400 hover:bg-red-900 transition"
        >
          New Session
        </button>
      </div>
      <main className="container mx-auto p-6">
        <div className="flex flex-wrap gap-3 mb-6">
          <button
            className={`px-4 py-2 rounded-full border transition ${activeStep === 'plan' ? 'bg-primary-dark text-dark-bg font-semibold' : 'bg-dark-card border-dark-hover text-text-primary hover:border-primary'}`}
            onClick={() => setActiveStep('plan')}
          >
            1. Planning
          </button>
          <button
            className={`px-4 py-2 rounded-full border transition ${activeStep === 'generate' ? 'bg-primary-dark text-dark-bg font-semibold' : 'bg-dark-card border-dark-hover text-text-primary hover:border-primary'}`}
            onClick={() => setActiveStep('generate')}
          >
            2. Generation
          </button>
          <button
            className={`px-4 py-2 rounded-full border transition ${activeStep === 'evaluate' ? 'bg-primary-dark text-dark-bg font-semibold' : 'bg-dark-card border-dark-hover text-text-primary hover:border-primary'}`}
            onClick={() => setActiveStep('evaluate')}
          >
            3. Evaluation
          </button>
          <button
            className={`px-4 py-2 rounded-full border transition ${activeStep === 'refine' ? 'bg-primary-dark text-dark-bg font-semibold' : 'bg-dark-card border-dark-hover text-text-primary hover:border-primary'}`}
            onClick={() => setActiveStep('refine')}
          >
            4. Refinement
          </button>
        </div>

        {error && (
          <div className="mb-4 bg-red-900 text-red-100 border border-red-700 p-3 rounded">
            {error}
          </div>
        )}

        {activeStep === 'plan' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <InputForm
              requirements={requirements}
              onRequirementsChange={setRequirements}
              onPlan={handlePlan}
              loading={loading.plan}
            />
            <div className="bg-dark-card p-6 rounded-lg shadow-md border border-dark-hover">
              <h2 className="text-xl font-semibold mb-4 text-primary">Planned Screens</h2>
              {planScreens.length === 0 ? (
                <p className="text-text-secondary">No screen plan yet.</p>
              ) : (
                <ul className="space-y-3">
                  {planScreens.map((screen) => (
                    <li key={screen.screen_id} className="border border-dark-hover rounded-md p-3 bg-dark-bg hover:bg-dark-hover transition">
                      <div className="font-semibold text-primary">{screen.screen_name}</div>
                      <div className="text-sm text-text-secondary">{screen.screen_id} · {screen.screen_type}</div>
                      <div className="text-sm text-neutral mt-1">{screen.purpose}</div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        )}

        {activeStep === 'generate' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-dark-card p-6 rounded-lg shadow-md border border-dark-hover">
              <h2 className="text-xl font-semibold mb-4 text-primary">Generate UI</h2>
              <label className="block text-sm font-medium text-text-secondary mb-2">Select screen</label>
              <select
                className="w-full p-2 border border-dark-hover bg-dark-bg text-text-primary rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                value={selectedScreenId}
                onChange={(e) => setSelectedScreenId(e.target.value)}
              >
                <option value="">Choose a screen</option>
                {planScreens.map((screen) => (
                  <option key={screen.screen_id} value={screen.screen_id}>
                    {screen.screen_name} ({screen.screen_id})
                  </option>
                ))}
              </select>
              <button
                className="mt-4 bg-primary text-black px-6 py-2 rounded-md hover:bg-primary-light transition font-semibold"
                onClick={handleGenerate}
                disabled={loading.generate}
              >
                {loading.generate ? 'Generating...' : 'Generate Screen'}
              </button>
              <div className="mt-6 border-t border-dark-hover pt-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-primary">Generated Files</h3>
                  <button
                    className="text-sm text-primary hover:text-primary-light transition"
                    onClick={loadOutputs}
                    disabled={outputsLoading}
                  >
                    {outputsLoading ? 'Refreshing...' : 'Refresh'}
                  </button>
                </div>
                {outputScreens.length === 0 ? (
                  <p className="text-text-secondary">No generated files yet.</p>
                ) : (
                  <ul className="space-y-2">
                    {outputScreens.map((screenId) => (
                      <li key={screenId} className="flex items-center justify-between border border-dark-hover rounded-md px-3 py-2 bg-dark-bg hover:bg-dark-hover transition">
                        <span className="text-sm text-text-secondary">{screenId}</span>
                        <div className="flex gap-3">
                          <button
                            className="text-sm text-primary hover:text-primary-light transition"
                            onClick={() => previewOutput(screenId)}
                          >
                            Preview
                          </button>
                          <button
                            className="text-sm text-primary hover:text-primary-light transition"
                            onClick={() => window.open(`/preview/${screenId}`, '_blank')}
                          >
                            Open
                          </button>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
            <UIOutput generatedUI={generatedUI} />
          </div>
        )}

        {activeStep === 'evaluate' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-dark-card p-6 rounded-lg shadow-md border border-dark-hover">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-primary">Evaluate Screens</h2>
                <button
                  className="text-sm text-primary hover:text-primary-light transition"
                  onClick={() => {
                    loadOutputs()
                    loadReports()
                  }}
                >
                  Refresh lists
                </button>
              </div>
              <p className="text-text-secondary mb-4">Select screens to evaluate (or leave empty to evaluate all).</p>
              <button
                className="bg-primary text-black px-6 py-2 rounded-md hover:bg-primary-light transition font-semibold"
                onClick={handleEvaluate}
                disabled={loading.evaluate}
              >
                {loading.evaluate ? 'Evaluating...' : 'Run Evaluation'}
              </button>
              <div className="mt-6 border-t border-dark-hover pt-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-primary">Generated Screens</h3>
                  <button
                    className="text-sm text-primary hover:text-primary-light transition"
                    onClick={loadOutputs}
                    disabled={outputsLoading}
                  >
                    {outputsLoading ? 'Refreshing...' : 'Refresh'}
                  </button>
                </div>
                {outputScreens.length === 0 ? (
                  <p className="text-text-secondary">No generated files yet.</p>
                ) : (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 mb-3">
                      <input
                        type="checkbox"
                        id="select-all"
                        checked={selectedScreensForEval.length === outputScreens.length}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedScreensForEval(outputScreens)
                          } else {
                            setSelectedScreensForEval([])
                          }
                        }}
                        className="bg-dark-bg border border-dark-hover"
                      />
                      <label htmlFor="select-all" className="text-sm text-text-secondary">Select All</label>
                    </div>
                    {outputScreens.map((screenId) => (
                      <div key={screenId} className="flex items-center justify-between border border-dark-hover rounded-md px-3 py-2 bg-dark-bg hover:bg-dark-hover transition">
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            id={`screen-${screenId}`}
                            checked={selectedScreensForEval.includes(screenId)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedScreensForEval((prev) => [...prev, screenId])
                              } else {
                                setSelectedScreensForEval((prev) => prev.filter((id) => id !== screenId))
                              }
                            }}
                            className="bg-dark-bg border border-dark-hover"
                          />
                          <label htmlFor={`screen-${screenId}`} className="text-sm text-text-secondary">{screenId}</label>
                        </div>
                        <div className="flex gap-3">
                          <button
                            className="text-sm text-primary hover:text-primary-light transition"
                            onClick={() => previewOutput(screenId)}
                          >
                            Preview
                          </button>
                          <button
                            className="text-sm text-primary hover:text-primary-light transition"
                            onClick={() => window.open(`/preview/${screenId}`, '_blank')}
                          >
                            Open
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div className="bg-dark-card p-6 rounded-lg shadow-md border border-dark-hover">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-primary">Score Reports</h2>
                <button
                  className="text-sm text-primary hover:text-primary-light transition"
                  onClick={loadReports}
                  disabled={reportsLoading}
                >
                  {reportsLoading ? 'Refreshing...' : 'Refresh'}
                </button>
              </div>
              {evaluationReports.length === 0 ? (
                <p className="text-text-secondary">No reports yet.</p>
              ) : (
                <div className="space-y-4">
                  {evaluationReports.map(({ screenId, report }) => (
                    <a
                      key={screenId}
                      href={`/reports/${screenId}`}
                      className="block border border-dark-hover rounded-md p-3 bg-dark-bg hover:bg-dark-hover transition-colors cursor-pointer"
                    >
                      <div className="font-semibold text-primary">{screenId}</div>
                      <div className="text-sm text-text-secondary">Total: {report.total_score} · ISO: {report.iso_score} · Nielsen: {report.nielsen_score} · WCAG: {report.wcag_score}</div>
                      <div className="text-sm text-neutral">Weakest: {report.weakest_standard} / {report.weakest_metric}</div>
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
        {activeStep === 'refine' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-dark-card p-6 rounded-lg shadow-md border border-dark-hover">
              <h2 className="text-xl font-semibold mb-4 text-primary">Run Refinement Loop</h2>
              <p className="text-text-secondary mb-4">
                Evaluates the selected screen, fixes its weakest sub-metric, re-evaluates, and
                repeats up to 5 iterations or until the threshold is reached.
              </p>
              <label className="block text-sm font-medium text-text-secondary mb-2">Select screen</label>
              <select
                className="w-full p-2 border border-dark-hover bg-dark-bg text-text-primary rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                value={selectedScreenForRefine}
                onChange={(e) => setSelectedScreenForRefine(e.target.value)}
              >
                <option value="">Choose a screen</option>
                {outputScreens.map((screenId) => (
                  <option key={screenId} value={screenId}>
                    {screenId}
                  </option>
                ))}
              </select>
              <button
                className="mt-4 bg-primary text-black px-6 py-2 rounded-md hover:bg-primary-light transition font-semibold"
                onClick={handleRefine}
                disabled={loading.refine}
              >
                {loading.refine ? 'Refining (this can take a while)...' : 'Run Refinement'}
              </button>
              {refinementResult && (
                <div className="mt-4 flex gap-3">
                  <button
                    className="text-sm text-primary hover:text-primary-light transition"
                    onClick={() => window.open(`/preview/${refinementResult.screenId}`, '_blank')}
                  >
                    Open refined preview
                  </button>
                  <button
                    className="text-sm text-primary hover:text-primary-light transition"
                    onClick={() => window.open(`/reports/${refinementResult.screenId}`, '_blank')}
                  >
                    Open full report
                  </button>
                </div>
              )}
            </div>
            <UIOutput generatedUI={generatedUI} />
          </div>
        )}
        
        {activeStep === 'refine' && refinementResult && (
          <div className="bg-dark-card p-6 rounded-lg shadow-md mt-6 border border-dark-hover">
            <h2 className="text-xl font-semibold mb-4 text-primary">Convergence — {refinementResult.screenId}</h2>
            <ConvergenceChart history={refinementResult.history} />
          </div>
        )}

        {activeStep === 'refine' && refinementResult && (
          <div className="bg-dark-card p-6 rounded-lg shadow-md mt-6 border border-dark-hover">
            <h2 className="text-xl font-semibold mb-4 text-primary">Refinement History — {refinementResult.screenId}</h2>
            <RefinementHistory
              history={refinementResult.history}
              finalReport={refinementResult.finalReport}
              passed={refinementResult.passed}
              regressed={refinementResult.regressed}
            />
          </div>
        )}

        <div className="bg-dark-card p-6 rounded-lg shadow-md mt-6 border border-dark-hover">
          <h2 className="text-xl font-semibold mb-4 text-primary">Pipeline Logs</h2>
          <pre className="text-xs text-text-secondary whitespace-pre-wrap bg-dark-bg border border-dark-hover rounded-md p-3 min-h-[120px] overflow-auto">
            {logs || 'No logs yet.'}
          </pre>
        </div>

        <div className="mt-8">
          <DocumentationTabs />
        </div>
      </main>
    </div>
  )
}