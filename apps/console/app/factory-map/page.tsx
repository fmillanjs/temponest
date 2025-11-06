import { FactoryMap } from '@/components/FactoryMap'
import { prisma } from '@/lib/db/client'

export default async function FactoryMapPage() {
  // Fetch real data from database
  const [projects, agents, activeProjects] = await Promise.all([
    prisma.project.findMany({
      select: { id: true, name: true, status: true },
      orderBy: { createdAt: 'desc' }
    }),
    prisma.agent.findMany({
      select: { id: true, name: true, status: true, version: true },
      orderBy: { name: 'asc' }
    }),
    prisma.project.count({
      where: { status: { notIn: ['idle'] } }
    })
  ])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-base-900">Factory Map</h1>
        <p className="mt-1 text-base-600">
          Visualize your products, pipelines, agents, and infrastructure
        </p>
      </div>

      <FactoryMap projects={projects} agents={agents} />

      <div className="grid gap-4 grid-cols-1 md:grid-cols-3">
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm font-medium text-base-600">Products</div>
          <div className="mt-2 text-2xl font-bold text-base-900">{projects.length}</div>
        </div>
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm font-medium text-base-600">Active Projects</div>
          <div className="mt-2 text-2xl font-bold text-base-900">{activeProjects}</div>
        </div>
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm font-medium text-base-600">Total Agents</div>
          <div className="mt-2 text-2xl font-bold text-base-900">{agents.length}</div>
        </div>
      </div>
    </div>
  )
}
