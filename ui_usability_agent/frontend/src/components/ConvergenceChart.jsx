export default function ConvergenceChart({ history }) {
  if (!history || history.length === 0) {
    return <p className="text-text-secondary">No convergence data yet.</p>
  }

  const width = 640
  const height = 280
  const padding = { top: 20, right: 20, bottom: 40, left: 40 }
  const plotW = width - padding.left - padding.right
  const plotH = height - padding.top - padding.bottom

  const n = history.length
  const xStep = n > 1 ? plotW / (n - 1) : 0
  const xFor = (i) => padding.left + i * xStep
  const yFor = (score) => padding.top + plotH - (score / 100) * plotH

  const series = [
    { key: 'total_score', label: 'Total', color: '#22d3ee' },
    { key: 'iso_score', label: 'ISO', color: '#4ade80' },
    { key: 'nielsen_score', label: 'Nielsen', color: '#c084fc' },
    { key: 'wcag_score', label: 'WCAG', color: '#60a5fa' },
  ]

  const pathFor = (key) =>
    history.map((e, i) => `${i === 0 ? 'M' : 'L'} ${xFor(i)} ${yFor(e.report[key])}`).join(' ')

  const thresholdY = yFor(history[0]?.report?.threshold ?? 85)

  return (
    <div className="bg-dark-bg border border-dark-hover rounded-lg p-4">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto">
        {[0, 25, 50, 75, 100].map((tick) => (
          <g key={tick}>
            <line x1={padding.left} x2={width - padding.right} y1={yFor(tick)} y2={yFor(tick)} stroke="#334155" strokeWidth="1" />
            <text x={padding.left - 8} y={yFor(tick) + 4} fontSize="10" textAnchor="end" fill="#94a3b8">{tick}</text>
          </g>
        ))}

        <line x1={padding.left} x2={width - padding.right} y1={thresholdY} y2={thresholdY} stroke="#facc15" strokeWidth="1.5" strokeDasharray="6 4" />
        <text x={width - padding.right} y={thresholdY - 6} fontSize="10" textAnchor="end" fill="#facc15">
          Threshold {history[0]?.report?.threshold ?? 85}
        </text>

        {series.map((s) => (
          <path key={s.key} d={pathFor(s.key)} fill="none" stroke={s.color} strokeWidth="2.5" />
        ))}

        {history.map((e, i) => (
          <g key={e.iteration}>
            {series.map((s) => (
              <circle key={s.key} cx={xFor(i)} cy={yFor(e.report[s.key])} r="3.5" fill={s.color} />
            ))}
            <text x={xFor(i)} y={height - padding.bottom + 16} fontSize="10" textAnchor="middle" fill="#94a3b8">
              Iter {e.iteration}
            </text>
          </g>
        ))}
      </svg>

      <div className="flex flex-wrap gap-4 mt-2 text-xs">
        {series.map((s) => (
          <div key={s.key} className="flex items-center gap-1.5">
            <span className="inline-block w-3 h-3 rounded-sm" style={{ backgroundColor: s.color }} />
            <span className="text-text-secondary">{s.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}