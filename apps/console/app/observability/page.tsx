export default function ObservabilityPage() {
  const logs = [
    {
      timestamp: '2025-11-05 14:32:15',
      level: 'info',
      message: 'Build started for project: formbuilder',
      agent: 'Developer',
    },
    {
      timestamp: '2025-11-05 14:28:42',
      level: 'warn',
      message: 'QA agent response time degraded',
      agent: 'QA',
    },
    {
      timestamp: '2025-11-05 14:15:03',
      level: 'success',
      message: 'Deployment completed successfully',
      agent: 'DevOps',
    },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-base-900">Observability</h1>
        <p className="mt-1 text-base-600">Monitor logs, traces, and metrics</p>
      </div>

      <div className="grid gap-4 grid-cols-1 md:grid-cols-4">
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm text-base-600">Active Jobs</div>
          <div className="mt-2 text-2xl font-bold text-base-900">12</div>
        </div>
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm text-base-600">Queue Depth</div>
          <div className="mt-2 text-2xl font-bold text-base-900">8</div>
        </div>
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm text-base-600">Avg Duration</div>
          <div className="mt-2 text-2xl font-bold text-base-900">4.2m</div>
        </div>
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm text-base-600">Success Rate</div>
          <div className="mt-2 text-2xl font-bold text-base-900">96.4%</div>
        </div>
      </div>

      <div className="rounded-2xl border border-base-200 bg-white shadow-soft">
        <div className="border-b border-base-200 p-4">
          <h2 className="font-semibold text-base-900">Recent Logs</h2>
        </div>
        <div className="divide-y divide-base-200">
          {logs.map((log, i) => (
            <div key={i} className="p-4 font-mono text-sm">
              <div className="flex items-start gap-4">
                <span className="text-base-500">{log.timestamp}</span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                    log.level === 'info'
                      ? 'bg-sky-100 text-sky-700'
                      : log.level === 'warn'
                      ? 'bg-amber-100 text-amber-700'
                      : 'bg-emerald-100 text-emerald-700'
                  }`}
                >
                  {log.level.toUpperCase()}
                </span>
                <span className="flex-1 text-base-900">{log.message}</span>
                <span className="text-base-600">[{log.agent}]</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
