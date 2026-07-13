export default function RefinementHistory({ history, finalReport, passed, regressed }) {
  if (!history || history.length === 0) {
    return <p className="text-text-secondary">No refinement history yet.</p>;
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <span
          className={`px-3 py-1 rounded-full text-sm font-semibold ${
            passed ? 'bg-green-900 text-green-300' : 'bg-yellow-900 text-yellow-300'
          }`}
        >
          {passed ? '✓ Passed threshold' : '✗ Did not reach threshold'}
        </span>
        {regressed && (
          <span className="px-3 py-1 rounded-full text-sm font-semibold bg-red-900 text-red-300">
            Rolled back to best iteration
          </span>
        )}
        {finalReport && (
          <span className="text-sm text-text-secondary">
           Final score: <span className="text-cyan-400 font-bold">{finalReport.total_score}</span> / 85 target          </span>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="bg-dark-bg border-b border-dark-hover">
              <th className="border border-dark-hover px-3 py-2 text-left text-text-primary">Iter</th>
              <th className="border border-dark-hover px-3 py-2 text-left text-text-primary">Total</th>
              <th className="border border-dark-hover px-3 py-2 text-left text-text-primary">ISO</th>
              <th className="border border-dark-hover px-3 py-2 text-left text-text-primary">Nielsen</th>
              <th className="border border-dark-hover px-3 py-2 text-left text-text-primary">WCAG</th>
              <th className="border border-dark-hover px-3 py-2 text-left text-text-primary">Threshold</th>
              <th className="border border-dark-hover px-3 py-2 text-left text-text-primary">Status</th>
              <th className="border border-dark-hover px-3 py-2 text-left text-text-primary">Fix applied</th>
            </tr>
          </thead>
          <tbody>
            {history.map((entry) => {
              const r = entry.report;
              return (
                <tr key={entry.iteration} className="hover:bg-dark-hover transition">
                  <td className="border border-dark-hover px-3 py-2 font-semibold text-text-primary">{entry.iteration}</td>
                  <td className="border border-dark-hover px-3 py-2 text-cyan-400 font-bold">{r.total_score}</td>
                  <td className="border border-dark-hover px-3 py-2 text-green-400">{r.iso_score}</td>
                  <td className="border border-dark-hover px-3 py-2 text-purple-400">{r.nielsen_score}</td>
                  <td className="border border-dark-hover px-3 py-2 text-blue-400">{r.wcag_score}</td>
                  <td className="border border-dark-hover px-3 py-2 text-text-secondary">{r.threshold}</td>
                  <td className="border border-dark-hover px-3 py-2">
                    {r.passed ? (
                      <span className="text-green-400 font-medium">Passed</span>
                    ) : (
                      <span className="text-yellow-400 font-medium">Refining</span>
                    )}
                  </td>
                  <td className="border border-dark-hover px-3 py-2 text-text-secondary">
                    {entry.appliedFix ? (
                      <span>
                        <span className="text-text-primary font-medium">{entry.appliedFix.weakest_standard}</span>
                        {' / '}
                        {entry.appliedFix.weakest_metric}
                      </span>
                    ) : (
                      <span className="text-neutral">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {history.some((e) => e.regressions && e.regressions.length > 0) && (
        <div className="bg-dark-bg border border-red-700 rounded-lg p-4">
          <h4 className="font-semibold text-red-400 mb-2">Regressions detected</h4>
          <ul className="space-y-1 text-sm text-text-secondary">
            {history.flatMap((e) =>
              (e.regressions || []).map((reg, idx) => (
                <li key={`${e.iteration}-${idx}`}>
                  Iteration {e.iteration}: <span className="text-text-primary">{reg.standard}</span> dropped{' '}
                  {reg.drop} pts ({reg.previous} → {reg.current})
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
}