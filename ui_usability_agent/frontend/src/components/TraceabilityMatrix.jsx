export default function TraceabilityMatrix({ traceability, screenId }) {
  if (!traceability || traceability.total_frs === 0) {
    return <p className="text-text-secondary">No traceability data for this screen.</p>
  }

  const { matrix, coverage_pct, covered_frs, total_frs, untagged_elements, total_interactive_elements } = traceability

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <span className={`px-3 py-1 rounded-full text-sm font-semibold ${coverage_pct === 100 ? 'bg-green-900 text-green-300' : 'bg-yellow-900 text-yellow-300'}`}>
          {coverage_pct}% FR coverage
        </span>
        <span className="text-sm text-text-secondary">
          {covered_frs}/{total_frs} functional requirements traced to UI elements
        </span>
        <span className="text-sm text-neutral">
          · {total_interactive_elements - untagged_elements}/{total_interactive_elements} interactive elements tagged
        </span>
      </div>

      <div className="w-full h-2 bg-dark-bg border border-dark-hover rounded-full overflow-hidden">
        <div
          className={`h-full ${coverage_pct === 100 ? 'bg-green-500' : 'bg-yellow-500'}`}
          style={{ width: `${coverage_pct}%` }}
        />
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="bg-dark-bg border-b border-dark-hover">
              <th className="border border-dark-hover px-3 py-2 text-left text-text-primary">FR ID</th>
              <th className="border border-dark-hover px-3 py-2 text-left text-text-primary">Title</th>
              <th className="border border-dark-hover px-3 py-2 text-left text-text-primary">Status</th>
              <th className="border border-dark-hover px-3 py-2 text-left text-text-primary">UI Elements</th>
            </tr>
          </thead>
          <tbody>
            {matrix.map((row) => (
              <tr key={row.fr_id} className="hover:bg-dark-hover transition">
                <td className="border border-dark-hover px-3 py-2 font-semibold text-text-primary">{row.fr_id}</td>
                <td className="border border-dark-hover px-3 py-2 text-text-secondary">{row.title || '—'}</td>
                <td className="border border-dark-hover px-3 py-2">
                  {row.covered ? (
                    <span className="text-green-400 font-medium">✓ Traced</span>
                  ) : (
                    <span className="text-red-400 font-medium">✗ Missing</span>
                  )}
                </td>
                <td className="border border-dark-hover px-3 py-2 text-text-secondary">
                  {row.elements.length === 0 ? (
                    <span className="text-neutral">none</span>
                  ) : (
                    <ul className="space-y-1">
                      {row.elements.map((el, i) => (
                        <li key={i} className="flex items-center gap-2">
                          <span className="text-cyan-400 font-mono text-xs">&lt;{el.tag}&gt;</span>
                          <span>{el.label}</span>
                          {screenId && (
                            <a
                              href={`/preview/${screenId}?highlight=${encodeURIComponent(row.fr_id)}`}
                              target="_blank"
                              rel="noreferrer"
                              className="text-xs text-primary hover:underline ml-1"
                            >
                              View →
                            </a>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}