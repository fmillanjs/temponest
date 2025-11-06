export default function ProjectDetailPage({
  params,
}: {
  params: { slug: string }
}) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-base-900 capitalize">
          {params.slug.replace(/-/g, ' ')} SaaS
        </h1>
        <p className="mt-1 text-base-600">Project details and build history</p>
      </div>

      <div className="grid gap-4 grid-cols-1 md:grid-cols-4">
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm text-base-600">Status</div>
          <div className="mt-2 text-lg font-semibold text-base-900">Building</div>
        </div>
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm text-base-600">Phase</div>
          <div className="mt-2 text-lg font-semibold text-base-900">Week 4</div>
        </div>
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm text-base-600">Build Runs</div>
          <div className="mt-2 text-lg font-semibold text-base-900">23</div>
        </div>
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm text-base-600">Est. MRR</div>
          <div className="mt-2 text-lg font-semibold text-base-900">$2.4k</div>
        </div>
      </div>

      <div className="rounded-2xl border border-base-200 bg-white p-6 shadow-soft">
        <h2 className="text-lg font-semibold text-base-900 mb-4">Recent Builds</h2>
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center justify-between border-b border-base-200 pb-3 last:border-0">
              <div>
                <div className="font-medium text-base-900">Build #{i}</div>
                <div className="text-sm text-base-600">Completed {i * 2}h ago</div>
              </div>
              <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700">
                Success
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
