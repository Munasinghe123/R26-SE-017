import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ReferenceLine, ResponsiveContainer,
} from 'recharts'

const SERIES = [
  { key: 'total_score', label: 'Total', color: '#22d3ee' },
  { key: 'iso_score', label: 'ISO', color: '#4ade80' },
  { key: 'nielsen_score', label: 'Nielsen', color: '#c084fc' },
  { key: 'wcag_score', label: 'WCAG', color: '#60a5fa' },
]

export default function ConvergenceChart({ history }) {
  if (!history || history.length === 0) {
    return <p className="text-text-secondary">No convergence data yet.</p>
  }

  const threshold = history[0]?.report?.threshold ?? 85
  const data = history.map((e) => ({
    name: `Iter ${e.iteration}`,
    total_score: e.report.total_score,
    iso_score: e.report.iso_score,
    nielsen_score: e.report.nielsen_score,
    wcag_score: e.report.wcag_score,
  }))

  return (
    <div className="bg-dark-bg border border-dark-hover rounded-lg p-4">
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid stroke="#1e293b" />
          <XAxis dataKey="name" stroke="#94a3b8" tick={{ fontSize: 12 }} />
          <YAxis domain={[0, 100]} stroke="#94a3b8" tick={{ fontSize: 12 }} />
          <Tooltip
            contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
            labelStyle={{ color: '#f1f5f9' }}
          />
          <Legend wrapperStyle={{ fontSize: 12, color: '#cbd5e1' }} />
          <ReferenceLine
            y={threshold}
            stroke="#facc15"
            strokeDasharray="6 4"
            label={{ value: `Threshold ${threshold}`, position: 'insideTopRight', fill: '#facc15', fontSize: 12 }}
          />
          {SERIES.map((s) => (
            <Line
              key={s.key}
              type="monotone"
              dataKey={s.key}
              name={s.label}
              stroke={s.color}
              strokeWidth={2.5}
              dot={{ r: 4, fill: s.color, strokeWidth: 0 }}
              isAnimationActive={false}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      {data.length === 1 && (
        <p className="text-xs text-text-secondary mt-2 text-center">
          Converged on the first pass — showing single-iteration result.
        </p>
      )}
    </div>
  )
}