import { cn } from '@/lib/utils'
import { Activity } from 'lucide-react'

type AgentStatus = 'healthy' | 'degraded' | 'down'

interface AgentStatusCardProps {
  name: string
  status: AgentStatus
  heartbeat: string
  version: string
  onOpen?: () => void
  onRestart?: () => void
}

export function AgentStatusCard({
  name,
  status,
  heartbeat,
  version,
  onOpen,
  onRestart,
}: AgentStatusCardProps) {
  const statusConfig = {
    healthy: {
      badge: 'bg-emerald-100 text-emerald-700',
      icon: 'text-emerald-500',
      label: 'Healthy',
    },
    degraded: {
      badge: 'bg-amber-100 text-amber-700',
      icon: 'text-amber-500',
      label: 'Degraded',
    },
    down: {
      badge: 'bg-rose-100 text-rose-700',
      icon: 'text-rose-500',
      label: 'Down',
    },
  }[status]

  return (
    <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft transition-shadow hover:shadow-soft-lg">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className={cn('h-5 w-5', statusConfig.icon)} />
          <h3 className="font-semibold text-base-800">{name}</h3>
        </div>
        <span className={cn('rounded-full px-2 py-1 text-xs font-medium', statusConfig.badge)}>
          {statusConfig.label}
        </span>
      </div>
      <div className="mt-3 text-sm text-base-600">
        <div className="flex items-center justify-between">
          <span>Heartbeat: {heartbeat}</span>
          <span>v{version}</span>
        </div>
      </div>
      <div className="mt-4 flex gap-2">
        <button
          onClick={onOpen}
          className="flex-1 rounded-xl bg-base-900 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-base-800"
        >
          Open
        </button>
        <button
          onClick={onRestart}
          className="flex-1 rounded-xl bg-base-200 px-3 py-1.5 text-sm font-medium text-base-800 transition-colors hover:bg-base-300"
        >
          Restart
        </button>
      </div>
    </div>
  )
}
