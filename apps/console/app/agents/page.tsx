import { AgentStatusCard } from '@/components/AgentStatusCard'
import { prisma } from '@/lib/db/client'
import { formatDistanceToNow } from 'date-fns'

function getHeartbeat(lastHeartbeat: Date | null) {
  if (!lastHeartbeat) return 'never'
  return formatDistanceToNow(lastHeartbeat, { addSuffix: false })
}

export default async function AgentsPage() {
  const agents = await prisma.agent.findMany({
    orderBy: { name: 'asc' }
  })
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-base-900">Agents</h1>
        <p className="mt-1 text-base-600">Monitor and manage your autonomous agents</p>
      </div>

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
    </div>
  )
}
