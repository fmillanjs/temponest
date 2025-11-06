'use client'

import { Search, Bell } from 'lucide-react'
import { UserMenu } from './UserMenu'

export function Header() {
  return (
    <header className="flex h-16 items-center justify-between border-b border-base-200 bg-white px-6">
      {/* Search */}
      <div className="flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-base-400" />
          <input
            type="text"
            placeholder="Search projects, runs, docs..."
            className="w-full rounded-xl border border-base-300 bg-base-50 py-2 pl-10 pr-4 text-sm focus:border-accent-info focus:outline-none focus:ring-1 focus:ring-accent-info"
          />
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-4">
        <button className="rounded-xl p-2 text-base-600 hover:bg-base-100">
          <Bell className="h-5 w-5" />
        </button>
        <UserMenu />
      </div>
    </header>
  )
}
