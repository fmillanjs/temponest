import { prisma } from '@/lib/db/client'
import { formatDistanceToNow } from 'date-fns'
import { notFound } from 'next/navigation'
import {
  Play,
  XCircle,
  CheckCircle,
  Clock,
  Ban,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  FileJson
} from 'lucide-react'
import Link from 'next/link'

const statusIcons = {
  pending: Clock,
  running: Play,
  success: CheckCircle,
  failed: XCircle,
  cancelled: Ban,
}

const statusColors = {
  pending: 'bg-slate-100 text-slate-700',
  running: 'bg-sky-100 text-sky-700',
  success: 'bg-emerald-100 text-emerald-700',
  failed: 'bg-rose-100 text-rose-700',
  cancelled: 'bg-amber-100 text-amber-700',
}

export default async function ProjectDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const project = await prisma.project.findUnique({
    where: { slug },
    include: {
      runs: {
        orderBy: { createdAt: 'desc' },
        include: {
          approvals: true
        }
      }
    }
  })

  if (!project) {
    notFound()
  }

  const totalRuns = project.runs.length
  const successfulRuns = project.runs.filter(r => r.status === 'success').length
  const failedRuns = project.runs.filter(r => r.status === 'failed').length
  const successRate = totalRuns > 0 ? ((successfulRuns / totalRuns) * 100).toFixed(0) : '0'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-base-900">{project.name}</h1>
          <p className="mt-1 text-base-600">Project details and build history</p>
        </div>
        <div className="flex gap-2">
          <button className="rounded-xl bg-base-900 px-4 py-2 text-sm font-medium text-white hover:bg-base-800">
            Start New Run
          </button>
          {project.repoUrl && (
            <Link
              href={project.repoUrl}
              target="_blank"
              className="rounded-xl border border-base-200 bg-white px-4 py-2 text-sm font-medium text-base-900 hover:bg-base-50 flex items-center gap-2"
            >
              Repository <ExternalLink className="h-4 w-4" />
            </Link>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 grid-cols-1 md:grid-cols-4">
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm text-base-600">Status</div>
          <div className="mt-2 text-lg font-semibold text-base-900 capitalize">
            {project.status}
          </div>
        </div>
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm text-base-600">Total Runs</div>
          <div className="mt-2 text-lg font-semibold text-base-900">{totalRuns}</div>
        </div>
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm text-base-600">Success Rate</div>
          <div className="mt-2 text-lg font-semibold text-base-900">{successRate}%</div>
        </div>
        <div className="rounded-2xl border border-base-200 bg-white p-4 shadow-soft">
          <div className="text-sm text-base-600">Type</div>
          <div className="mt-2 text-lg font-semibold text-base-900 capitalize">
            {project.type}
          </div>
        </div>
      </div>

      {/* Run History */}
      <div className="rounded-2xl border border-base-200 bg-white shadow-soft">
        <div className="border-b border-base-200 p-6">
          <h2 className="text-lg font-semibold text-base-900">Run History</h2>
        </div>
        <div className="divide-y divide-base-200">
          {project.runs.length === 0 ? (
            <div className="p-8 text-center text-base-600">
              No runs yet. Start your first run to see it here.
            </div>
          ) : (
            project.runs.map((run) => {
              const StatusIcon = statusIcons[run.status as keyof typeof statusIcons]
              const duration = run.startedAt && run.finishedAt
                ? Math.round((run.finishedAt.getTime() - run.startedAt.getTime()) / 1000)
                : null

              return (
                <details key={run.id} className="group">
                  <summary className="cursor-pointer p-4 hover:bg-base-50 transition-colors">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 flex-1">
                        <ChevronRight className="h-4 w-4 text-base-600 group-open:rotate-90 transition-transform" />
                        <StatusIcon className="h-5 w-5 text-base-600" />
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-base-900">
                            {run.kind.toUpperCase()} • {run.step}
                          </div>
                          <div className="text-sm text-base-600">
                            Started {formatDistanceToNow(run.createdAt, { addSuffix: true })}
                            {duration && ` • ${duration}s`}
                          </div>
                        </div>
                      </div>
                      <span className={`rounded-full px-3 py-1 text-xs font-medium ${statusColors[run.status as keyof typeof statusColors]}`}>
                        {run.status.toUpperCase()}
                      </span>
                    </div>
                  </summary>

                  {/* Expanded content */}
                  <div className="border-t border-base-200 bg-base-50 p-4 space-y-4">
                    {/* Logs */}
                    {run.logs && (
                      <div>
                        <h4 className="text-sm font-medium text-base-900 mb-2">Logs</h4>
                        <div className="rounded-lg bg-base-900 p-4 font-mono text-xs text-emerald-400 overflow-x-auto max-h-60 overflow-y-auto">
                          <pre className="whitespace-pre-wrap">{run.logs}</pre>
                        </div>
                      </div>
                    )}

                    {/* Artifacts */}
                    {run.artifacts && (
                      <div>
                        <h4 className="text-sm font-medium text-base-900 mb-2 flex items-center gap-2">
                          <FileJson className="h-4 w-4" />
                          Artifacts
                        </h4>
                        <div className="rounded-lg bg-base-900 p-4 font-mono text-xs text-sky-300 overflow-x-auto max-h-60 overflow-y-auto">
                          <pre>{JSON.stringify(run.artifacts, null, 2)}</pre>
                        </div>
                      </div>
                    )}

                    {/* Approvals */}
                    {run.approvals.length > 0 && (
                      <div>
                        <h4 className="text-sm font-medium text-base-900 mb-2">Approvals</h4>
                        <div className="space-y-2">
                          {run.approvals.map((approval) => (
                            <div key={approval.id} className="rounded-lg border border-base-200 bg-white p-3">
                              <div className="flex items-center justify-between">
                                <div className="text-sm font-medium text-base-900">
                                  {approval.step}
                                </div>
                                <span className={`rounded-full px-2 py-1 text-xs font-medium ${
                                  approval.status === 'approved'
                                    ? 'bg-emerald-100 text-emerald-700'
                                    : approval.status === 'changes_requested'
                                    ? 'bg-amber-100 text-amber-700'
                                    : 'bg-slate-100 text-slate-700'
                                }`}>
                                  {approval.status.toUpperCase().replace('_', ' ')}
                                </span>
                              </div>
                              {approval.comment && (
                                <div className="mt-2 text-sm text-base-600">{approval.comment}</div>
                              )}
                              {approval.decidedBy && (
                                <div className="mt-2 text-xs text-base-500">
                                  By {approval.decidedBy} • {formatDistanceToNow(approval.createdAt, { addSuffix: true })}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Quick Actions */}
                    <div className="flex gap-2 pt-2">
                      <button className="text-sm text-accent-info hover:text-accent-info-dark font-medium">
                        Rerun
                      </button>
                      <button className="text-sm text-base-600 hover:text-base-900 font-medium">
                        Download Logs
                      </button>
                      {run.status === 'running' && (
                        <button className="text-sm text-accent-danger hover:text-accent-danger-dark font-medium">
                          Cancel
                        </button>
                      )}
                    </div>
                  </div>
                </details>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}
