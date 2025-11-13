import { TrendingUp, Zap, CheckCircle, Clock, DollarSign } from 'lucide-react'
import { prisma } from '@/lib/db/client'

export async function KpiBar() {
  // OPTIMIZED: Use database views for faster queries
  // Get all metrics in parallel (3 queries instead of 6+)
  const [projectMetrics, runMetrics, agentHealth] = await Promise.all([
    // Projects: total and active count
    prisma.$queryRaw<Array<{ total: bigint; active: bigint }>>`
      SELECT
        COUNT(*) as total,
        COUNT(*) FILTER (WHERE status != 'idle') as active
      FROM projects
    `,
    // Runs: use the optimized metrics view
    prisma.$queryRaw<Array<{ runs_today: bigint; queue_depth: bigint }>>`
      SELECT runs_today, queue_depth FROM v_run_metrics_summary
    `,
    // Agents: use the health summary view
    prisma.$queryRaw<Array<{ total_agents: bigint; healthy_count: bigint; health_percentage: number }>>`
      SELECT * FROM v_agent_health_summary
    `,
  ])

  const totalProjects = Number(projectMetrics[0]?.total || 0)
  const activeProjects = Number(projectMetrics[0]?.active || 0)
  const runsToday = Number(runMetrics[0]?.runs_today || 0)
  const queueDepth = Number(runMetrics[0]?.queue_depth || 0)
  const uptime = agentHealth[0]?.health_percentage?.toFixed(1) || '0.0'

  const kpis = [
    { label: 'Active Projects', value: activeProjects.toString(), icon: Zap, change: '', trend: 'up' as const },
    { label: 'Build Runs Today', value: runsToday.toString(), icon: CheckCircle, change: '', trend: 'up' as const },
    { label: 'Agent Uptime', value: `${uptime}%`, icon: TrendingUp, change: '', trend: 'up' as const },
    { label: 'Queue Depth', value: queueDepth.toString(), icon: Clock, change: '', trend: 'up' as const },
    { label: 'Total Projects', value: totalProjects.toString(), icon: DollarSign, change: '', trend: 'up' as const },
  ]
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
