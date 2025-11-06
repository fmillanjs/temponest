import { FactoryMap } from '@/components/FactoryMap'

export default function FactoryMapPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-base-900">Factory Map</h1>
        <p className="mt-1 text-base-600">
          Visualize your products, pipelines, agents, and infrastructure
        </p>
      </div>

      <FactoryMap />

      <div className="grid gap-4 grid-cols-1 md:grid-cols-3">
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm font-medium text-base-600">Products</div>
          <div className="mt-2 text-2xl font-bold text-base-900">12</div>
        </div>
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm font-medium text-base-600">Active Pipelines</div>
          <div className="mt-2 text-2xl font-bold text-base-900">8</div>
        </div>
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm font-medium text-base-600">Infrastructure Nodes</div>
          <div className="mt-2 text-2xl font-bold text-base-900">15</div>
        </div>
      </div>
    </div>
  )
}
