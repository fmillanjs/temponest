import { NextResponse } from 'next/server'
import { prisma } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    // OPTIMIZED: Use database view to get all summary metrics in ONE query (was 6+ queries)
    const [metricsResult] = await prisma.$queryRaw<
      Array<{
        active_jobs: bigint;
        queue_depth: bigint;
        completed_last_hour: bigint;
        successful_last_hour: bigint;
        total_last_hour: bigint;
        runs_today: bigint;
        avg_duration_seconds: number | null;
      }>
    >`SELECT * FROM v_run_metrics_summary`

    const metrics = metricsResult || {
      active_jobs: 0n,
      queue_depth: 0n,
      completed_last_hour: 0n,
      successful_last_hour: 0n,
      total_last_hour: 0n,
      runs_today: 0n,
      avg_duration_seconds: 0,
    }

    const avgDuration = metrics.avg_duration_seconds || 0
    const successRate = Number(metrics.total_last_hour) > 0
      ? (Number(metrics.successful_last_hour) / Number(metrics.total_last_hour)) * 100
      : 0

    // OPTIMIZED: Use database view for status distribution (replaces GROUP BY query)
    const statusDistribution = await prisma.$queryRaw<
      Array<{ status: string; count: bigint; percentage: number }>
    >`SELECT * FROM v_run_status_distribution_24h`

    // OPTIMIZED: Use database view for agent metrics (replaces complex CASE query)
    const runsByAgent = await prisma.$queryRaw<
      Array<{ agent: string; count: bigint; successful: bigint; failed: bigint; avg_duration_seconds: number | null }>
    >`SELECT * FROM v_runs_by_agent_24h`

    // OPTIMIZED: Use database view for recent errors (includes project name)
    const recentErrors = await prisma.$queryRaw<
      Array<{
        id: string;
        project_id: string;
        project_name: string | null;
        step: string;
        finished_at: Date;
        log_preview: string | null;
      }>
    >`SELECT * FROM v_recent_failed_runs LIMIT 10`

    return NextResponse.json({
      summary: {
        activeJobs: Number(metrics.active_jobs),
        queueDepth: Number(metrics.queue_depth),
        avgDuration: Math.round(avgDuration),
        avgDurationFormatted: formatDuration(avgDuration),
        successRate: Math.round(successRate * 10) / 10,
        runsToday: Number(metrics.runs_today),
      },
      charts: {
        statusDistribution: statusDistribution.map((row) => ({
          status: row.status,
          count: Number(row.count),
          percentage: row.percentage,
        })),
        runsByAgent: runsByAgent.map((row) => ({
          agent: row.agent,
          count: Number(row.count),
          successful: Number(row.successful),
          failed: Number(row.failed),
          avgDuration: row.avg_duration_seconds ? Math.round(row.avg_duration_seconds) : 0,
        })),
      },
      recentErrors: recentErrors.map((error) => ({
        id: error.id,
        projectId: error.project_id,
        projectName: error.project_name,
        step: error.step,
        timestamp: error.finished_at?.toISOString(),
        preview: error.log_preview,
      })),
    })
  } catch (error) {
    console.error('Error fetching metrics:', error)
    return NextResponse.json(
      { error: 'Failed to fetch metrics' },
      { status: 500 }
    )
  }
}

function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`
  }
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.round(seconds % 60)
  if (minutes < 60) {
    return `${minutes}m ${remainingSeconds}s`
  }
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  return `${hours}h ${remainingMinutes}m`
}
