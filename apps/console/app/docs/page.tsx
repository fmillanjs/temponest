export default function DocsPage() {
  const docs = [
    { title: 'Getting Started', category: 'Guide', updated: '2d ago' },
    { title: 'Agent System Overview', category: 'Architecture', updated: '5d ago' },
    { title: 'Building Your First SaaS', category: 'Tutorial', updated: '1w ago' },
    { title: 'Factory Setup', category: 'Guide', updated: '2w ago' },
    { title: 'API Reference', category: 'Reference', updated: '3w ago' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-base-900">Documentation</h1>
        <p className="mt-1 text-base-600">Browse guides, tutorials, and references</p>
      </div>

      <div className="rounded-2xl border border-base-200 bg-white shadow-soft">
        <div className="border-b border-base-200 p-4">
          <input
            type="text"
            placeholder="Search documentation..."
            className="w-full rounded-xl border border-base-300 bg-base-50 px-4 py-2 text-sm focus:border-accent-info focus:outline-none focus:ring-1 focus:ring-accent-info"
          />
        </div>
        <div className="divide-y divide-base-200">
          {docs.map((doc) => (
            <div
              key={doc.title}
              className="p-4 hover:bg-base-50 cursor-pointer transition-colors"
            >
              <h3 className="font-medium text-base-900">{doc.title}</h3>
              <div className="mt-1 flex items-center gap-3 text-sm text-base-600">
                <span className="rounded-full bg-base-100 px-2 py-0.5 text-xs">
                  {doc.category}
                </span>
                <span>Updated {doc.updated}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
