export default function FinancialsPage() {
  const calculators = [
    { name: 'Form Builder', mrr: '$2.4k', arr: '$28.8k', payback: '8 months' },
    { name: 'Analytics Platform', mrr: '$5.1k', arr: '$61.2k', payback: '6 months' },
    { name: 'CRM System', mrr: '$8.9k', arr: '$106.8k', payback: '4 months' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-base-900">Financials</h1>
        <p className="mt-1 text-base-600">
          Model your SaaS financials and projections
        </p>
      </div>

      <div className="grid gap-4 grid-cols-1 md:grid-cols-3">
        <div className="rounded-2xl border border-base-200 bg-white p-6 shadow-soft">
          <div className="text-sm text-base-600">Total MRR</div>
          <div className="mt-2 text-3xl font-bold text-base-900">$18.4k</div>
          <div className="mt-1 text-sm text-accent-success">+14% this month</div>
        </div>
        <div className="rounded-2xl border border-base-200 bg-white p-6 shadow-soft">
          <div className="text-sm text-base-600">Total ARR</div>
          <div className="mt-2 text-3xl font-bold text-base-900">$220.8k</div>
          <div className="mt-1 text-sm text-accent-success">+12% this year</div>
        </div>
        <div className="rounded-2xl border border-base-200 bg-white p-6 shadow-soft">
          <div className="text-sm text-base-600">Avg. Payback</div>
          <div className="mt-2 text-3xl font-bold text-base-900">6 mo</div>
          <div className="mt-1 text-sm text-base-600">Across portfolio</div>
        </div>
      </div>

      <div className="rounded-2xl border border-base-200 bg-white shadow-soft">
        <div className="border-b border-base-200 p-6">
          <h2 className="text-lg font-semibold text-base-900">Product Projections</h2>
        </div>
        <div className="divide-y divide-base-200">
          {calculators.map((calc) => (
            <div key={calc.name} className="p-6">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-base-900">{calc.name}</h3>
                <button className="rounded-xl bg-base-100 px-4 py-2 text-sm font-medium text-base-900 hover:bg-base-200">
                  View Model
                </button>
              </div>
              <div className="mt-3 flex gap-6">
                <div>
                  <div className="text-xs text-base-600">MRR</div>
                  <div className="mt-1 font-semibold text-base-900">{calc.mrr}</div>
                </div>
                <div>
                  <div className="text-xs text-base-600">ARR</div>
                  <div className="mt-1 font-semibold text-base-900">{calc.arr}</div>
                </div>
                <div>
                  <div className="text-xs text-base-600">Payback</div>
                  <div className="mt-1 font-semibold text-base-900">{calc.payback}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
