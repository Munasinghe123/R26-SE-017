import { useState, useEffect, useCallback } from "react";
import "./App.css";
import { checkHealth, generateLLD, generateSample } from "./api";
import type {
  GenerateRequest,
  GenerateResponse,
  HealthResponse,
} from "./types";

// ============================================================
// Sub-components
// ============================================================

function Header({ health }: { health: HealthResponse | null }) {
  const statusClass = health === null ? "checking" : health.status === "healthy" ? "" : "offline";
  const statusText = health === null ? "Checking..." : health.status === "healthy" ? `v${health.version} · ${health.llm_provider}` : "Offline";

  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="header-logo">🏗️</div>
        <div>
          <div className="header-title">LLD Agent</div>
          <div className="header-subtitle">Detailed System Design Generator</div>
        </div>
      </div>
      <div className="header-status">
        <span className={`status-dot ${statusClass}`} />
        <span>{statusText}</span>
      </div>
    </header>
  );
}

function LoadingOverlay({ step }: { step: number }) {
  const steps = [
    "Parsing requirements & architecture",
    "Generating Class diagram",
    "Generating Sequence diagram",
    "Generating ER diagram",
    "Cross-validating diagrams",
    "Rendering PNG / SVG exports",
  ];

  return (
    <div className="loading-overlay">
      <div className="loading-spinner" />
      <div className="loading-text">Generating LLD Diagrams</div>
      <div className="loading-subtext">This may take a minute...</div>
      <div className="loading-steps">
        {steps.map((label, i) => {
          const cls = i < step ? "done" : i === step ? "active" : "";
          return (
            <div key={i} className={`loading-step ${cls}`}>
              <span className="step-icon">{i < step ? "✓" : i === step ? "●" : "○"}</span>
              {label}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================
// Input Form Page
// ============================================================

function InputPage({
  form,
  onGenerate,
  onSample,
  loading,
}: {
  form: GenerateRequest;
  setForm: React.Dispatch<React.SetStateAction<GenerateRequest>>;
  onGenerate: () => void;
  onSample: (sampleId: number) => void;
  loading: boolean;
}) {




  return (
    <div className="input-page">
      {/* Hero */}
      <section className="hero-section">
        <h1>
          Generate <span>LLD Diagrams</span>
        </h1>
        <p className="hero-description">
          Provide your high-level architecture and functional requirements. The multi-agent pipeline will generate
          cross-validated Class, Sequence, and ER diagrams with educational feedback.
        </p>
        <div className="hero-actions">
          <button className="btn btn-secondary" onClick={() => onSample(1)} disabled={loading} id="sample-btn-1">
            📦 Use Sample Data 1
          </button>
          <button className="btn btn-secondary" onClick={() => onSample(2)} disabled={loading} id="sample-btn-2">
            📦 Use Sample Data 2
          </button>
          <button className="btn btn-secondary" onClick={() => onSample(3)} disabled={loading} id="sample-btn-3">
            📦 Use Sample Data 3
          </button>
          <button className="btn btn-secondary" onClick={() => onSample(4)} disabled={loading} id="sample-btn-4">
            📦 Use Sample Data 4
          </button>
        </div>
      </section>
    </div>
  );
}

// ============================================================
// Results Page
// ============================================================

function ResultsPage({
  result,
  onBack,
}: {
  result: GenerateResponse;
  onBack: () => void;
}) {
  const [activeTab, setActiveTab] = useState<"diagrams" | "validation" | "traceability" | "summary">("diagrams");
  const vr = result.validation_report;
  //const consistencyScore = Math.max(0, Math.min(100, vr.consistency_score));

  return (
    <div className="results-page">
      {/* Header */}
      <div className="results-header">
        <div>
          <h2>📊 {result.project_name}</h2>
        </div>
        <button className="btn btn-secondary" onClick={onBack} id="back-btn">
          ← New Generation
        </button>
      </div>

      {/* Meta chips */}
      <div className="results-meta">
        {/*<div className="meta-chip">
          <span className="label">Status</span>
          <span className={`score-badge ${result.success ? "pass" : "fail"}`}>
            {result.success ? "✓ Success" : "✗ Failed"}
          </span>
        </div> */}
        {/*<div className="meta-chip">
          <span className="label">Consistency</span>
          <span className={`score-badge ${consistencyScore >= 85 ? "pass" : "fail"}`}>
            {consistencyScore.toFixed(0)}%
          </span>
        </div> */}
        <div className="meta-chip">
          <span className="label">Checks</span>
          <span className="value">{vr.passed_checks}/{vr.total_checks}</span>
        </div>
        <div className="meta-chip">
          <span className="label">Iterations</span>
          <span className="value">{result.iterations_used}</span>
        </div>
        <div className="meta-chip">
          <span className="label">Diagrams</span>
          <span className="value">{result.diagrams.length}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        {(
          [
            ["diagrams", "📐 Diagrams"],
            ["validation", "🔍 Validation"],
            ["traceability", "🔗 Traceability"],
            ["summary", "📚 Summary"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            className={`tab-btn ${activeTab === key ? "active" : ""}`}
            onClick={() => setActiveTab(key)}
            id={`tab-${key}`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Tab: Diagrams */}
      {activeTab === "diagrams" && (
        <div className="diagrams-grid animate-fade-in">
          {result.diagrams.length === 0 && (
            <div className="card" style={{ textAlign: "center", padding: 40 }}>
              <p style={{ color: "var(--text-muted)" }}>No diagrams were generated.</p>
            </div>
          )}
          {result.diagrams.map((diag, i) => (
            <div className="diagram-card" key={i}>
              <div className="diagram-card-header">
                <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span className="diagram-type-badge">{diag.diagram_type}</span>
                  {diag.name && <span style={{ fontSize: "0.9rem", fontWeight: 600 }}>{diag.name}</span>}
                </div>
              </div>
              <div className="diagram-card-body">
                {/* Rendered image */}
                {diag.png_base64 ? (
                  <div className="diagram-image-container">
                    <img
                      src={`data:image/png;base64,${diag.png_base64}`}
                      alt={`${diag.diagram_type} diagram`}
                    />
                  </div>
                ) : diag.svg_content ? (
                  <div
                    className="diagram-image-container"
                    dangerouslySetInnerHTML={{ __html: diag.svg_content }}
                  />
                ) : (
                  <div className="diagram-image-container" style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
                    No rendered image available
                  </div>
                )}

                {/* Source code collapse */}
                {(diag.plantuml_syntax || diag.mermaid_syntax) && (
                  <details className="diagram-source">
                    <summary>View source code</summary>
                    {diag.plantuml_syntax && (
                      <div>
                        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 8, marginBottom: 4 }}>PlantUML</div>
                        <pre>{diag.plantuml_syntax}</pre>
                      </div>
                    )}
                    {diag.mermaid_syntax && (
                      <div>
                        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 8, marginBottom: 4 }}>Mermaid</div>
                        <pre>{diag.mermaid_syntax}</pre>
                      </div>
                    )}
                  </details>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tab: Validation */}
      {activeTab === "validation" && (
        <div className="validation-section animate-fade-in">
          {/* Errors */}
          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-header">
              <div className="card-title">
                <span className="icon">⚠️</span> Validation Issues ({vr.errors.length})
              </div>
            </div>
            {vr.errors.length === 0 ? (
              <p style={{ color: "var(--accent-success)", fontSize: "0.9rem" }}>✓ No validation issues found</p>
            ) : (
              <div className="validation-errors">
                {vr.errors.map((err, i) => (
                  <div className={`validation-error-item ${err.severity}`} key={i}>
                    <div>
                      <span className="error-severity">{err.severity}</span>
                    </div>
                    <div>
                      <div className="error-message">{err.message}</div>
                      <div className="error-suggestion">💡 {err.suggestion}</div>
                      {err.educational_feedback && (
                        <div className="error-feedback">📖 {err.educational_feedback}</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Naming Violations */}
          {vr.naming_violations.length > 0 && (
            <div className="card" style={{ marginBottom: 24 }}>
              <div className="card-header">
                <div className="card-title">
                  <span className="icon">📛</span> Naming Violations ({vr.naming_violations.length})
                  {vr.naming_violations_fixed > 0 && (
                    <span className="score-badge pass" style={{ fontSize: "0.72rem" }}>
                      {vr.naming_violations_fixed} auto-fixed
                    </span>
                  )}
                </div>
              </div>
              <div className="trace-table-wrapper">
                <table className="trace-table">
                  <thead>
                    <tr>
                      <th>Location</th>
                      <th>Current</th>
                      <th>Expected</th>
                      <th>Convention</th>
                      <th>Fixed</th>
                    </tr>
                  </thead>
                  <tbody>
                    {vr.naming_violations.map((nv, i) => (
                      <tr key={i}>
                        <td>{nv.location}</td>
                        <td><code>{nv.current_name}</code></td>
                        <td><code>{nv.expected_name}</code></td>
                        <td>{nv.convention}</td>
                        <td>
                          <span className={`covered-badge ${nv.auto_fixed ? "yes" : "no"}`}>
                            {nv.auto_fixed ? "Yes" : "No"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Over-design flags */}
          {vr.overdesign_flags.length > 0 && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <span className="icon">🔬</span> Over-Design Flags ({vr.overdesign_flags.length})
                </div>
              </div>
              <div className="validation-errors">
                {vr.overdesign_flags.map((flag, i) => (
                  <div className="validation-error-item MEDIUM" key={i}>
                    <div>
                      <span className="error-severity">{flag.element_type}</span>
                    </div>
                    <div>
                      <div className="error-message">
                        <code>{flag.element_name}</code> — {flag.reason}
                      </div>
                      {flag.educational_feedback && (
                        <div className="error-feedback">📖 {flag.educational_feedback}</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab: Traceability */}
      {activeTab === "traceability" && (
        <div className="animate-fade-in">
          <div className="card">
            <div className="card-header">
              <div className="card-title">
                <span className="icon">🔗</span> Requirement Traceability Matrix
              </div>
            </div>
            {vr.traceability_matrix.length === 0 ? (
              <p style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>No traceability data available.</p>
            ) : (
              <div className="trace-table-wrapper">
                <table className="trace-table">
                  <thead>
                    <tr>
                      <th>Requirement</th>
                      <th>Classes</th>
                      <th>Sequences</th>
                      <th>Entities</th>
                      <th>Covered</th>
                    </tr>
                  </thead>
                  <tbody>
                    {vr.traceability_matrix.map((entry, i) => (
                      <tr key={i}>
                        <td><code>{entry.requirement_id}</code></td>
                        <td>{entry.mapped_classes.join(", ") || "—"}</td>
                        <td>{entry.mapped_sequences.join(", ") || "—"}</td>
                        <td>{entry.mapped_entities.join(", ") || "—"}</td>
                        <td>
                          <span className={`covered-badge ${entry.is_covered ? "yes" : "no"}`}>
                            {entry.is_covered ? "✓ Yes" : "✗ No"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab: Summary */}
      {activeTab === "summary" && (
        <div className="animate-fade-in">
          <div className="educational-summary">
            <h3>📚 Educational Summary</h3>
            <div className="content">
              {result.educational_summary || "No educational summary was generated."}
            </div>
          </div>

          {/* Exported files */}
          {result.exported_files.length > 0 && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">
                  <span className="icon">📁</span> Exported Files
                </div>
              </div>
              <div className="req-list">
                {result.exported_files.map((file, i) => (
                  <div className="req-item" key={i} style={{ fontFamily: "var(--font-mono)", fontSize: "0.82rem" }}>
                    {file}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================
// Main App
// ============================================================

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [form, setForm] = useState<GenerateRequest>({
    project_name: "",
    project_description: "",
    high_level_architecture: { pattern: "", layers: [], architectural_constraints: [] },
    functional_requirements: [],
    export_formats: ["png"],
  });
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Health check on mount
  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: "offline", llm_provider: "unknown", rag_enabled: false, kroki_url: "", version: "?" }));
  }, []);

  // Simulate loading steps
  useEffect(() => {
    if (!loading) return;
    setLoadingStep(0);
    const interval = setInterval(() => {
      setLoadingStep((s) => {
        if (s >= 5) {
          clearInterval(interval);
          return s;
        }
        return s + 1;
      });
    }, 3000);
    return () => clearInterval(interval);
  }, [loading]);

  const handleGenerate = useCallback(async () => {
    setError(null);
    setLoading(true);
    try {
      const res = await generateLLD(form);
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [form]);

  const handleSample = useCallback(async (sampleId: number) => {
    setError(null);
    setLoading(true);
    try {
      const res = await generateSample(sampleId);
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleBack = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return (
    <div className="app-container">
      <Header health={health} />

      {error && (
        <div className="error-banner">
          <span className="error-icon">❌</span>
          <span className="error-text">{error}</span>
          <button className="btn btn-ghost btn-sm" onClick={() => setError(null)} style={{ marginLeft: "auto" }}>
            Dismiss
          </button>
        </div>
      )}

      {loading && <LoadingOverlay step={loadingStep} />}

      {result ? (
        <ResultsPage result={result} onBack={handleBack} />
      ) : (
        <InputPage
          form={form}
          setForm={setForm}
          onGenerate={handleGenerate}
          onSample={handleSample}
          loading={loading}
        />
      )}
    </div>
  );
}

export default App;
