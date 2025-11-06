import { AgentStatusCard } from '@/components/AgentStatusCard'

const agents = [
  { name: 'Overseer', status: 'healthy' as const, heartbeat: '2m', version: '1.2.3' },
  { name: 'Developer', status: 'healthy' as const, heartbeat: '2m', version: '1.4.0' },
  { name: 'Designer', status: 'healthy' as const, heartbeat: '3m', version: '0.9.9' },
  { name: 'UX', status: 'healthy' as const, heartbeat: '1m', version: '0.4.2' },
  { name: 'QA', status: 'degraded' as const, heartbeat: '6m', version: '0.8.1' },
  { name: 'Security', status: 'healthy' as const, heartbeat: '4m', version: '0.5.0' },
  { name: 'DevOps', status: 'healthy' as const, heartbeat: '2m', version: '1.1.0' },
]

export default function AgentsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-base-900">Agents</h1>
        <p className="mt-1 text-base-600">Monitor and manage your autonomous agents</p>
      </div>

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
    </div>
  )
}
