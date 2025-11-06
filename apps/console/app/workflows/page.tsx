export default function WorkflowsPage() {
  const columns = [
    { id: 'backlog', title: 'Backlog', count: 5 },
    { id: 'research', title: 'Research', count: 3 },
    { id: 'build', title: 'Build', count: 4 },
    { id: 'qa', title: 'QA', count: 2 },
    { id: 'deploy', title: 'Deploy', count: 1 },
    { id: 'live', title: 'Live', count: 8 },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-base-900">Workflows</h1>
        <p className="mt-1 text-base-600">Track your projects through the pipeline</p>
      </div>

      <div className="flex gap-4 overflow-x-auto pb-4">
        {columns.map((column) => (
          <div
            key={column.id}
            className="flex-shrink-0 w-80 rounded-2xl border border-base-200 bg-base-50 p-4"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-base-900">{column.title}</h3>
              <span className="rounded-full bg-base-200 px-2 py-1 text-xs font-medium text-base-700">
                {column.count}
              </span>
            </div>
            <div className="space-y-3">
              <div className="rounded-xl border border-base-200 bg-white p-3 shadow-sm">
                <div className="font-medium text-sm text-base-900">Example Project</div>
                <div className="mt-1 text-xs text-base-600">Last updated 2h ago</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
