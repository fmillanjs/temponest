import { KpiBar } from '@/components/KpiBar'
import { AgentStatusCard } from '@/components/AgentStatusCard'
import { QuickActions } from '@/components/QuickActions'
import { RecentActivity } from '@/components/RecentActivity'
import { prisma } from '@/lib/db/client'
import { formatDistanceToNow } from 'date-fns'

function getHeartbeat(lastHeartbeat: Date | null) {
  if (!lastHeartbeat) return 'never'
  return formatDistanceToNow(lastHeartbeat, { addSuffix: false })
}

export default async function DashboardPage() {
  const agents = await prisma.agent.findMany({
    orderBy: { name: 'asc' }
  })
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
              key={agent.id}
              name={agent.name}
              status={agent.status}
              heartbeat={getHeartbeat(agent.lastHeartbeat)}
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
