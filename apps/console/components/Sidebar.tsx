'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  Network,
  KanbanSquare,
  FolderKanban,
  Bot,
  Wand2,
  Calculator,
  BookOpen,
  Activity,
  Settings,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Factory Map', href: '/factory-map', icon: Network },
  { name: 'Workflows', href: '/workflows', icon: KanbanSquare },
  { name: 'Projects', href: '/projects', icon: FolderKanban },
  { name: 'Agents', href: '/agents', icon: Bot },
  { name: 'Wizards', href: '/wizards', icon: Wand2 },
  { name: 'Financials', href: '/financials', icon: Calculator },
  { name: 'Docs', href: '/docs', icon: BookOpen },
  { name: 'Observability', href: '/observability', icon: Activity },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="flex h-full w-64 flex-col bg-base-900 text-white">
      {/* Logo */}
      <div className="flex h-16 items-center px-6">
        <h1 className="text-xl font-bold">SaaS Empire</h1>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/')
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'group flex items-center rounded-xl px-3 py-2.5 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-base-800 text-white'
                  : 'text-base-300 hover:bg-base-800 hover:text-white'
              )}
            >
              <item.icon
                className={cn(
                  'mr-3 h-5 w-5 flex-shrink-0',
                  isActive ? 'text-accent-info' : 'text-base-400 group-hover:text-base-300'
                )}
              />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-base-800 p-4">
        <div className="text-xs text-base-400">
          <p>v0.1.0</p>
          <p className="mt-1">Powered by Claude Code</p>
        </div>
      </div>
    </div>
  )
}
