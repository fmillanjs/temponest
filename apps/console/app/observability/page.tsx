'use client'

import { useEffect, useState, useRef } from 'react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Search, RefreshCw, Download, Pause, Play } from 'lucide-react'

interface Log {
  id: string
  timestamp: string
  level: string
  message: string
  agent: string
  resource: string
  details?: any
}

interface Metrics {
  summary: {
    activeJobs: number
    queueDepth: number
    avgDuration: number
    avgDurationFormatted: string
    successRate: number
  }
  charts: {
    statusDistribution: Array<{ status: string; count: number }>
    runsByAgent: Array<{ agent: string; count: number }>
  }
  recentErrors: Array<{
    id: string
    step: string
    timestamp: string
    preview: string
  }>
}

export default function ObservabilityPage() {
  const [logs, setLogs] = useState<Log[]>([])
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [autoScroll, setAutoScroll] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [agentFilter, setAgentFilter] = useState('all')
  const [levelFilter, setLevelFilter] = useState('all')
  const logsEndRef = useRef<HTMLDivElement>(null)

  const fetchLogs = async () => {
    try {
      const params = new URLSearchParams()
      if (searchQuery) params.append('search', searchQuery)
      if (agentFilter !== 'all') params.append('agent', agentFilter)
      if (levelFilter !== 'all') params.append('level', levelFilter)
      params.append('limit', '100')

      const response = await fetch(`/api/observability/logs?${params}`)
      const data = await response.json()
      setLogs(data.logs || [])
    } catch (error) {
      console.error('Failed to fetch logs:', error)
    }
  }

  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/observability/metrics')
      const data = await response.json()
      setMetrics(data)
    } catch (error) {
      console.error('Failed to fetch metrics:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
    fetchMetrics()
  }, [searchQuery, agentFilter, levelFilter])

  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      fetchLogs()
      fetchMetrics()
    }, 5000) // Refresh every 5 seconds

    return () => clearInterval(interval)
  }, [autoRefresh, searchQuery, agentFilter, levelFilter])

  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs, autoScroll])

  const exportLogs = () => {
    const dataStr = JSON.stringify(logs, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `logs-${new Date().toISOString()}.json`
    link.click()
  }

  const getLevelBadgeClass = (level: string) => {
    switch (level) {
      case 'error':
        return 'bg-rose-100 text-rose-700 border-rose-200'
      case 'warn':
        return 'bg-amber-100 text-amber-700 border-amber-200'
      case 'success':
        return 'bg-emerald-100 text-emerald-700 border-emerald-200'
      default:
        return 'bg-sky-100 text-sky-700 border-sky-200'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-base-600">Loading observability data...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-base-900">Observability</h1>
        <p className="mt-1 text-base-600">
          Real-time logs, metrics, and system health monitoring
        </p>
      </div>

      {/* Metrics Summary */}
      <div className="grid gap-4 grid-cols-1 md:grid-cols-4">
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm text-base-600">Active Jobs</div>
          <div className="mt-2 text-2xl font-bold text-base-900">
            {metrics?.summary.activeJobs || 0}
          </div>
          <div className="mt-1 text-xs text-emerald-600">Running now</div>
        </div>
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm text-base-600">Queue Depth</div>
          <div className="mt-2 text-2xl font-bold text-base-900">
            {metrics?.summary.queueDepth || 0}
          </div>
          <div className="mt-1 text-xs text-sky-600">Pending execution</div>
        </div>
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm text-base-600">Avg Duration</div>
          <div className="mt-2 text-2xl font-bold text-base-900">
            {metrics?.summary.avgDurationFormatted || '0s'}
          </div>
          <div className="mt-1 text-xs text-base-600">Last hour</div>
        </div>
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm text-base-600">Success Rate</div>
          <div className="mt-2 text-2xl font-bold text-base-900">
            {metrics?.summary.successRate.toFixed(1) || '0'}%
          </div>
          <div className="mt-1 text-xs text-emerald-600">Last hour</div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
        {/* Status Distribution */}
        <div className="rounded-2xl border border-base-200 bg-white p-6 shadow-soft">
          <h3 className="font-semibold text-base-900 mb-4">
            Status Distribution (24h)
          </h3>
          <div className="space-y-3">
            {metrics?.charts.statusDistribution.map((item) => (
              <div key={item.status} className="flex items-center gap-3">
                <div className="w-24 text-sm text-base-600 capitalize">
                  {item.status}
                </div>
                <div className="flex-1 bg-base-100 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      item.status === 'success'
                        ? 'bg-emerald-500'
                        : item.status === 'failed'
                        ? 'bg-rose-500'
                        : item.status === 'running'
                        ? 'bg-sky-500'
                        : 'bg-amber-500'
                    }`}
                    style={{
                      width: `${
                        (item.count /
                          metrics.charts.statusDistribution.reduce(
                            (sum, s) => sum + s.count,
                            0
                          )) *
                        100
                      }%`,
                    }}
                  />
                </div>
                <div className="w-12 text-sm font-medium text-base-900">
                  {item.count}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Runs by Agent */}
        <div className="rounded-2xl border border-base-200 bg-white p-6 shadow-soft">
          <h3 className="font-semibold text-base-900 mb-4">
            Runs by Agent (24h)
          </h3>
          <div className="space-y-3">
            {metrics?.charts.runsByAgent
              .filter((item) => item.agent !== 'Other')
              .map((item) => (
                <div key={item.agent} className="flex items-center gap-3">
                  <div className="w-24 text-sm text-base-600">{item.agent}</div>
                  <div className="flex-1 bg-base-100 rounded-full h-2">
                    <div
                      className="bg-sky-500 h-2 rounded-full"
                      style={{
                        width: `${
                          (item.count /
                            metrics.charts.runsByAgent.reduce(
                              (sum, s) => sum + s.count,
                              0
                            )) *
                          100
                        }%`,
                      }}
                    />
                  </div>
                  <div className="w-12 text-sm font-medium text-base-900">
                    {item.count}
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Log Viewer */}
      <div className="rounded-2xl border border-base-200 bg-white shadow-soft">
        {/* Controls */}
        <div className="border-b border-base-200 p-4">
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-base-400" />
                <Input
                  placeholder="Search logs..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>

            <Select value={agentFilter} onValueChange={setAgentFilter}>
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="All Agents" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Agents</SelectItem>
                <SelectItem value="Developer">Developer</SelectItem>
                <SelectItem value="QA">QA</SelectItem>
                <SelectItem value="DevOps">DevOps</SelectItem>
                <SelectItem value="Designer">Designer</SelectItem>
                <SelectItem value="Security">Security</SelectItem>
                <SelectItem value="Overseer">Overseer</SelectItem>
              </SelectContent>
            </Select>

            <Select value={levelFilter} onValueChange={setLevelFilter}>
              <SelectTrigger className="w-[130px]">
                <SelectValue placeholder="All Levels" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Levels</SelectItem>
                <SelectItem value="info">Info</SelectItem>
                <SelectItem value="success">Success</SelectItem>
                <SelectItem value="warn">Warning</SelectItem>
                <SelectItem value="error">Error</SelectItem>
              </SelectContent>
            </Select>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setAutoRefresh(!autoRefresh)}
            >
              {autoRefresh ? (
                <Pause className="h-4 w-4 mr-1" />
              ) : (
                <Play className="h-4 w-4 mr-1" />
              )}
              {autoRefresh ? 'Pause' : 'Resume'}
            </Button>

            <Button variant="outline" size="sm" onClick={() => fetchLogs()}>
              <RefreshCw className="h-4 w-4 mr-1" />
              Refresh
            </Button>

            <Button variant="outline" size="sm" onClick={exportLogs}>
              <Download className="h-4 w-4 mr-1" />
              Export
            </Button>
          </div>

          <div className="mt-2 flex items-center gap-2 text-sm text-base-600">
            <span>{logs.length} logs</span>
            <span>•</span>
            <button
              onClick={() => setAutoScroll(!autoScroll)}
              className="hover:text-base-900"
            >
              Auto-scroll: {autoScroll ? 'ON' : 'OFF'}
            </button>
            {autoRefresh && (
              <>
                <span>•</span>
                <span className="text-emerald-600">
                  Auto-refreshing every 5s
                </span>
              </>
            )}
          </div>
        </div>

        {/* Logs */}
        <div className="divide-y divide-base-200 max-h-[600px] overflow-y-auto">
          {logs.length === 0 ? (
            <div className="p-8 text-center text-base-500">
              No logs found matching your filters
            </div>
          ) : (
            logs.map((log) => (
              <div key={log.id} className="p-4 font-mono text-sm hover:bg-base-50">
                <div className="flex items-start gap-4">
                  <span className="text-base-500 text-xs">
                    {new Date(log.timestamp).toLocaleString()}
                  </span>
                  <Badge
                    variant="outline"
                    className={`${getLevelBadgeClass(log.level)} text-xs`}
                  >
                    {log.level.toUpperCase()}
                  </Badge>
                  <span className="flex-1 text-base-900">{log.message}</span>
                  <span className="text-base-600 text-xs">[{log.agent}]</span>
                </div>
                {log.details && (
                  <div className="mt-2 ml-4 text-xs text-base-500">
                    Resource: {log.resource}
                  </div>
                )}
              </div>
            ))
          )}
          <div ref={logsEndRef} />
        </div>
      </div>

      {/* Recent Errors */}
      {metrics?.recentErrors && metrics.recentErrors.length > 0 && (
        <div className="rounded-2xl border border-base-200 bg-white shadow-soft">
          <div className="border-b border-base-200 p-4">
            <h2 className="font-semibold text-base-900">Recent Errors</h2>
          </div>
          <div className="divide-y divide-base-200">
            {metrics.recentErrors.map((error) => (
              <div key={error.id} className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="font-medium text-base-900">{error.step}</div>
                    <div className="mt-1 text-sm text-base-600">
                      {error.preview}...
                    </div>
                  </div>
                  <div className="text-xs text-base-500">
                    {new Date(error.timestamp).toLocaleString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Langfuse Integration */}
      <div className="rounded-2xl border border-base-200 bg-gradient-to-br from-sky-50 to-emerald-50 p-6 shadow-soft">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-semibold text-base-900">
              Langfuse Tracing
            </h3>
            <p className="mt-1 text-sm text-base-600">
              View detailed LLM traces and performance metrics
            </p>
          </div>
          <Button
            onClick={() =>
              window.open(
                process.env.NEXT_PUBLIC_LANGFUSE_URL || 'http://localhost:3000',
                '_blank'
              )
            }
          >
            Open Langfuse →
          </Button>
        </div>
      </div>
    </div>
  )
}
