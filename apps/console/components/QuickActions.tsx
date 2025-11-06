import { Rocket, Factory, Calculator } from 'lucide-react'
import Link from 'next/link'

interface QuickActionsProps {
  className?: string
}

const actions = [
  {
    title: 'Start Single-SaaS Wizard',
    description: 'Launch a new SaaS product in 1-8 weeks',
    icon: Rocket,
    href: '/wizards/single',
    color: 'bg-sky-100 text-sky-600',
  },
  {
    title: 'Initialize Factory',
    description: 'Set up your complete 4-week factory system',
    icon: Factory,
    href: '/wizards/factory',
    color: 'bg-emerald-100 text-emerald-600',
  },
  {
    title: 'Run Calculator',
    description: 'Model financials and projections',
    icon: Calculator,
    href: '/financials',
    color: 'bg-amber-100 text-amber-600',
  },
]

export function QuickActions({ className }: QuickActionsProps) {
  return (
    <div className={className}>
      <h2 className="text-xl font-semibold mb-3 text-base-900">Quick Actions</h2>
      <div className="grid gap-4 grid-cols-1 md:grid-cols-3">
        {actions.map((action) => (
          <Link
            key={action.title}
            href={action.href}
            className="group rounded-2xl border border-base-200 bg-white p-5 shadow-soft transition-all hover:shadow-soft-lg hover:border-base-300"
          >
            <div className={`inline-flex rounded-xl p-3 ${action.color}`}>
              <action.icon className="h-6 w-6" />
            </div>
            <h3 className="mt-4 font-semibold text-base-900 group-hover:text-base-700">
              {action.title}
            </h3>
            <p className="mt-1 text-sm text-base-600">{action.description}</p>
          </Link>
        ))}
      </div>
    </div>
  )
}
