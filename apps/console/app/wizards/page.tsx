import Link from 'next/link'
import { Rocket, Factory } from 'lucide-react'

const wizards = [
  {
    title: 'Single-SaaS Wizard',
    description: 'Build a complete SaaS product in 1-8 weeks',
    href: '/wizards/single',
    icon: Rocket,
    color: 'bg-sky-100 text-sky-600',
    duration: '1-8 weeks',
  },
  {
    title: 'Factory Setup Wizard',
    description: 'Initialize your complete portfolio factory system',
    href: '/wizards/factory',
    icon: Factory,
    color: 'bg-emerald-100 text-emerald-600',
    duration: '4 weeks',
  },
]

export default function WizardsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-base-900">Wizards</h1>
        <p className="mt-1 text-base-600">Interactive setup guides for your SaaS empire</p>
      </div>

      <div className="grid gap-6 grid-cols-1 md:grid-cols-2">
        {wizards.map((wizard) => (
          <Link
            key={wizard.title}
            href={wizard.href}
            className="group rounded-2xl border border-base-200 bg-white p-8 shadow-soft transition-all hover:shadow-soft-lg hover:border-base-300"
          >
            <div className={`inline-flex rounded-xl p-4 ${wizard.color}`}>
              <wizard.icon className="h-8 w-8" />
            </div>
            <h3 className="mt-6 text-xl font-semibold text-base-900 group-hover:text-base-700">
              {wizard.title}
            </h3>
            <p className="mt-2 text-base-600">{wizard.description}</p>
            <div className="mt-4 text-sm font-medium text-accent-info">
              Duration: {wizard.duration}
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
