'use client'

import { Search, Bell, CheckCircle, AlertCircle, Clock } from 'lucide-react'
import { UserMenu } from './UserMenu'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

// Mock notifications - in production, this would come from API
const mockNotifications = [
  {
    id: '1',
    type: 'success' as const,
    title: 'Build completed',
    message: 'Sample SaaS build finished successfully',
    time: '2 min ago',
  },
  {
    id: '2',
    type: 'info' as const,
    title: 'Wizard progress',
    message: 'Single-SaaS wizard is 60% complete',
    time: '15 min ago',
  },
  {
    id: '3',
    type: 'warning' as const,
    title: 'Agent degraded',
    message: 'Designer agent status is degraded',
    time: '1 hour ago',
  },
]

export function Header() {
  const hasUnread = mockNotifications.length > 0

  return (
    <header className="flex h-16 items-center justify-between border-b border-base-200 bg-white px-6">
      {/* Search */}
      <div className="flex-1 max-w-md">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-base-400" />
          <input
            type="text"
            placeholder="Search projects, runs, docs... (⌘K)"
            className="w-full rounded-xl border border-base-300 bg-base-50 py-2 pl-10 pr-4 text-sm focus:border-accent-info focus:outline-none focus:ring-1 focus:ring-accent-info"
          />
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-4">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="relative rounded-xl p-2 text-base-600 hover:bg-base-100 focus:outline-none focus:ring-2 focus:ring-accent-info">
              <Bell className="h-5 w-5" />
              {hasUnread && (
                <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-rose-500" />
              )}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-80">
            <DropdownMenuLabel>Notifications</DropdownMenuLabel>
            <DropdownMenuSeparator />
            {mockNotifications.length === 0 ? (
              <div className="py-6 text-center text-sm text-base-500">
                No new notifications
              </div>
            ) : (
              mockNotifications.map((notification) => (
                <DropdownMenuItem key={notification.id} className="flex flex-col items-start py-3">
                  <div className="flex items-start gap-2 w-full">
                    {notification.type === 'success' && (
                      <CheckCircle className="h-4 w-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                    )}
                    {notification.type === 'warning' && (
                      <AlertCircle className="h-4 w-4 text-amber-500 mt-0.5 flex-shrink-0" />
                    )}
                    {notification.type === 'info' && (
                      <Clock className="h-4 w-4 text-sky-500 mt-0.5 flex-shrink-0" />
                    )}
                    <div className="flex-1">
                      <div className="font-medium text-sm">{notification.title}</div>
                      <div className="text-xs text-base-500 mt-0.5">
                        {notification.message}
                      </div>
                      <div className="text-xs text-base-400 mt-1">
                        {notification.time}
                      </div>
                    </div>
                  </div>
                </DropdownMenuItem>
              ))
            )}
          </DropdownMenuContent>
        </DropdownMenu>
        <UserMenu />
      </div>
    </header>
  )
}
