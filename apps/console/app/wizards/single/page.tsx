export default function SingleSaasWizardPage() {
  const steps = [
    { week: 1, title: 'Foundation & Setup', status: 'completed' },
    { week: 2, title: 'Research & Validation', status: 'completed' },
    { week: 3, title: 'Design System', status: 'in_progress' },
    { week: 4, title: 'Core Features', status: 'pending' },
    { week: 5, title: 'Authentication & Auth', status: 'pending' },
    { week: 6, title: 'Testing & QA', status: 'pending' },
    { week: 7, title: 'Deploy & Monitor', status: 'pending' },
    { week: 8, title: 'Launch & Iterate', status: 'pending' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-base-900">Single-SaaS Wizard</h1>
        <p className="mt-1 text-base-600">Build a complete SaaS product in 8 weeks</p>
      </div>

      <div className="space-y-4">
        {steps.map((step) => (
          <div
            key={step.week}
            className={`rounded-2xl border p-6 shadow-soft ${
              step.status === 'completed'
                ? 'border-emerald-200 bg-emerald-50'
                : step.status === 'in_progress'
                ? 'border-sky-200 bg-sky-50'
                : 'border-base-200 bg-white'
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-base-900">
                  Week {step.week}: {step.title}
                </h3>
              </div>
              <span
                className={`rounded-full px-3 py-1 text-xs font-medium ${
                  step.status === 'completed'
                    ? 'bg-emerald-100 text-emerald-700'
                    : step.status === 'in_progress'
                    ? 'bg-sky-100 text-sky-700'
                    : 'bg-base-200 text-base-700'
                }`}
              >
                {step.status.replace('_', ' ')}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
