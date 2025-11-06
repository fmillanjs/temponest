export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-base-900">Settings</h1>
        <p className="mt-1 text-base-600">Configure your SaaS Empire Console</p>
      </div>

      <div className="grid gap-6">
        <div className="rounded-2xl border border-base-200 bg-white p-6 shadow-soft">
          <h2 className="text-lg font-semibold text-base-900 mb-4">Paths</h2>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-base-700">Working Directory</label>
              <input
                type="text"
                defaultValue="/home/doctor/temponest"
                className="mt-2 w-full rounded-xl border border-base-300 bg-base-50 px-4 py-2 text-sm"
              />
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-base-200 bg-white p-6 shadow-soft">
          <h2 className="text-lg font-semibold text-base-900 mb-4">Risk Controls</h2>
          <div className="space-y-3">
            <label className="flex items-center gap-3">
              <input type="checkbox" defaultChecked className="rounded" />
              <span className="text-sm text-base-700">Require approval for deployments</span>
            </label>
            <label className="flex items-center gap-3">
              <input type="checkbox" defaultChecked className="rounded" />
              <span className="text-sm text-base-700">Enable dry-run mode by default</span>
            </label>
            <label className="flex items-center gap-3">
              <input type="checkbox" defaultChecked className="rounded" />
              <span className="text-sm text-base-700">Audit all destructive actions</span>
            </label>
          </div>
        </div>

        <div className="rounded-2xl border border-base-200 bg-white p-6 shadow-soft">
          <h2 className="text-lg font-semibold text-base-900 mb-4">API Tokens</h2>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-base-700">GitHub Token</label>
              <input
                type="password"
                placeholder="ghp_••••••••••••••••"
                className="mt-2 w-full rounded-xl border border-base-300 bg-base-50 px-4 py-2 text-sm"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-base-700">Langfuse API Key</label>
              <input
                type="password"
                placeholder="lf_••••••••••••••••"
                className="mt-2 w-full rounded-xl border border-base-300 bg-base-50 px-4 py-2 text-sm"
              />
            </div>
          </div>
        </div>

        <button className="rounded-xl bg-base-900 px-6 py-3 text-sm font-medium text-white hover:bg-base-800">
          Save Changes
        </button>
      </div>
    </div>
  )
}
