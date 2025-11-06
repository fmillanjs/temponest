import { formatRelativeTime } from '@/lib/utils'
import { GitCommit, Play, AlertTriangle } from 'lucide-react'

const activities = [
  {
    type: 'commit',
    message: 'Add user authentication',
    project: 'FormBuilder SaaS',
    time: new Date(Date.now() - 2 * 60 * 1000),
    icon: GitCommit,
    iconColor: 'text-base-600',
  },
  {
    type: 'run',
    message: 'Build completed successfully',
    project: 'Analytics Platform',
    time: new Date(Date.now() - 15 * 60 * 1000),
    icon: Play,
    iconColor: 'text-accent-success',
  },
  {
    type: 'alert',
    message: 'QA agent degraded performance',
    project: 'System',
    time: new Date(Date.now() - 32 * 60 * 1000),
    icon: AlertTriangle,
    iconColor: 'text-accent-warn',
  },
]

export function RecentActivity() {
  return (
    <div>
      <h2 className="text-xl font-semibold mb-3 text-base-900">Recent Activity</h2>
      <div className="rounded-2xl border border-base-200 bg-white shadow-soft">
        <div className="divide-y divide-base-200">
          {activities.map((activity, idx) => (
            <div key={idx} className="p-4">
              <div className="flex gap-3">
                <div className="flex-shrink-0">
                  <activity.icon className={`h-5 w-5 ${activity.iconColor}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-base-900">{activity.message}</p>
                  <p className="text-xs text-base-600 mt-1">
                    {activity.project} · {formatRelativeTime(activity.time)}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
        <div className="border-t border-base-200 p-3">
          <button className="text-sm text-accent-info hover:text-accent-info-dark font-medium">
            View all activity →
          </button>
        </div>
      </div>
    </div>
  )
}
