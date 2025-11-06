import { KpiBar } from '@/components/KpiBar'
import { AgentStatusCard } from '@/components/AgentStatusCard'
import { QuickActions } from '@/components/QuickActions'
import { RecentActivity } from '@/components/RecentActivity'

const agents = [
  { name: 'Overseer', status: 'healthy' as const, heartbeat: '2m', version: '1.2.3' },
  { name: 'Developer', status: 'healthy' as const, heartbeat: '2m', version: '1.4.0' },
  { name: 'Designer', status: 'healthy' as const, heartbeat: '3m', version: '0.9.9' },
  { name: 'UX', status: 'healthy' as const, heartbeat: '1m', version: '0.4.2' },
  { name: 'QA', status: 'degraded' as const, heartbeat: '6m', version: '0.8.1' },
  { name: 'Security', status: 'healthy' as const, heartbeat: '4m', version: '0.5.0' },
  { name: 'DevOps', status: 'healthy' as const, heartbeat: '2m', version: '1.1.0' },
]

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-base-900">Dashboard</h1>
        <p className="mt-1 text-base-600">Monitor your SaaS building empire</p>
      </div>

      <KpiBar />

      <section>
        <h2 className="text-xl font-semibold mb-3 text-base-900">Agent Health</h2>
        <div className="grid gap-4 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
          {agents.map((agent) => (
            <AgentStatusCard
              key={agent.name}
              name={agent.name}
              status={agent.status}
              heartbeat={agent.heartbeat}
              version={agent.version}
            />
          ))}
        </div>
      </section>

      <section className="grid gap-6 grid-cols-1 lg:grid-cols-3">
        <QuickActions className="lg:col-span-2" />
        <RecentActivity />
      </section>
    </div>
  )
}
