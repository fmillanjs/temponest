export default function FactoryWizardPage() {
  const phases = [
    { week: 1, title: 'Infrastructure & Agents', status: 'completed' },
    { week: 2, title: 'Pipeline & Automation', status: 'in_progress' },
    { week: 3, title: 'Templates & Patterns', status: 'pending' },
    { week: 4, title: 'Monitoring & Scaling', status: 'pending' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-base-900">Factory Setup Wizard</h1>
        <p className="mt-1 text-base-600">Initialize your SaaS portfolio factory</p>
      </div>

      <div className="space-y-4">
        {phases.map((phase) => (
          <div
            key={phase.week}
            className={`rounded-2xl border p-6 shadow-soft ${
              phase.status === 'completed'
                ? 'border-emerald-200 bg-emerald-50'
                : phase.status === 'in_progress'
                ? 'border-sky-200 bg-sky-50'
                : 'border-base-200 bg-white'
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-base-900">
                  Week {phase.week}: {phase.title}
                </h3>
              </div>
              <span
                className={`rounded-full px-3 py-1 text-xs font-medium ${
                  phase.status === 'completed'
                    ? 'bg-emerald-100 text-emerald-700'
                    : phase.status === 'in_progress'
                    ? 'bg-sky-100 text-sky-700'
                    : 'bg-base-200 text-base-700'
                }`}
              >
                {phase.status.replace('_', ' ')}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
