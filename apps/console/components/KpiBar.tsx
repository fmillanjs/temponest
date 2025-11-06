import { TrendingUp, Zap, CheckCircle, Clock, DollarSign } from 'lucide-react'

const kpis = [
  { label: 'Active Projects', value: '12', icon: Zap, change: '+3', trend: 'up' },
  { label: 'Build Runs Today', value: '47', icon: CheckCircle, change: '+12', trend: 'up' },
  { label: 'Agent Uptime', value: '99.2%', icon: TrendingUp, change: '-0.1%', trend: 'down' },
  { label: 'Queue Depth', value: '8', icon: Clock, change: '-4', trend: 'up' },
  { label: 'Est. MRR', value: '$18.4k', icon: DollarSign, change: '+$2.1k', trend: 'up' },
]

export function KpiBar() {
  return (
    <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-5">
      {kpis.map((kpi) => (
        <div
          key={kpi.label}
          className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft"
        >
          <div className="flex items-center justify-between">
            <div className="rounded-xl bg-base-100 p-2">
              <kpi.icon className="h-5 w-5 text-base-700" />
            </div>
            <span
              className={`text-xs font-medium ${
                kpi.trend === 'up' ? 'text-accent-success' : 'text-accent-danger'
              }`}
            >
              {kpi.change}
            </span>
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold text-base-900">{kpi.value}</div>
            <div className="mt-1 text-sm text-base-600">{kpi.label}</div>
          </div>
        </div>
      ))}
    </div>
  )
}
