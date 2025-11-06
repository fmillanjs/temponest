import { TrendingUp, Zap, CheckCircle, Clock, DollarSign } from 'lucide-react'
import { prisma } from '@/lib/db/client'

export async function KpiBar() {
  // Fetch real-time metrics from database
  const [
    totalProjects,
    activeProjects,
    runsToday,
    queueDepth,
    healthyAgents,
    totalAgents
  ] = await Promise.all([
    prisma.project.count(),
    prisma.project.count({ where: { status: { notIn: ['idle'] } } }),
    prisma.run.count({
      where: {
        createdAt: { gte: new Date(new Date().setHours(0, 0, 0, 0)) }
      }
    }),
    prisma.run.count({ where: { status: 'pending' } }),
    prisma.agent.count({ where: { status: 'healthy' } }),
    prisma.agent.count()
  ])

  const uptime = totalAgents > 0 ? ((healthyAgents / totalAgents) * 100).toFixed(1) : '0.0'

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
