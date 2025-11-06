import { NextResponse } from 'next/server'
import { prisma } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

export async function GET() {
  try {
    // Get active jobs (running runs)
    const activeJobs = await prisma.run.count({
      where: { status: 'running' },
    })

    // Get queue depth (pending runs)
    const queueDepth = await prisma.run.count({
      where: { status: 'pending' },
    })

    // Get completed runs from last hour for duration calculation
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000)
    const completedRuns = await prisma.run.findMany({
      where: {
        status: { in: ['success', 'failed'] },
        finishedAt: { gte: oneHourAgo },
      },
      select: {
        startedAt: true,
        finishedAt: true,
      },
    })

    // Calculate average duration
    let avgDuration = 0
    if (completedRuns.length > 0) {
      const totalDuration = completedRuns.reduce((acc, run) => {
        if (run.startedAt && run.finishedAt) {
          return acc + (run.finishedAt.getTime() - run.startedAt.getTime())
        }
        return acc
      }, 0)
      avgDuration = totalDuration / completedRuns.length / 1000 // Convert to seconds
    }

    // Calculate success rate
    const totalRuns = await prisma.run.count({
      where: { finishedAt: { gte: oneHourAgo } },
    })
    const successfulRuns = await prisma.run.count({
      where: {
        status: 'success',
        finishedAt: { gte: oneHourAgo },
      },
    })
    const successRate = totalRuns > 0 ? (successfulRuns / totalRuns) * 100 : 0

    // Get run status distribution
    const statusDistribution = await prisma.$queryRaw<
      Array<{ status: string; count: bigint }>
    >`
      SELECT status::text, COUNT(*) as count
      FROM runs
      WHERE created_at >= NOW() - INTERVAL '24 hours'
      GROUP BY status
    `

    // Get runs by agent (from logs)
    const runsByAgent = await prisma.$queryRaw<
      Array<{ agent: string; count: bigint }>
    >`
      SELECT
        CASE
          WHEN step LIKE '%Developer%' THEN 'Developer'
          WHEN step LIKE '%QA%' THEN 'QA'
          WHEN step LIKE '%DevOps%' THEN 'DevOps'
          WHEN step LIKE '%Designer%' THEN 'Designer'
          WHEN step LIKE '%Security%' THEN 'Security'
          WHEN step LIKE '%Overseer%' THEN 'Overseer'
          WHEN step LIKE '%UX%' THEN 'UX'
          ELSE 'Other'
        END as agent,
        COUNT(*) as count
      FROM runs
      WHERE created_at >= NOW() - INTERVAL '24 hours'
      GROUP BY agent
    `

    // Recent errors
    const recentErrors = await prisma.run.findMany({
      where: {
        status: 'failed',
        finishedAt: { gte: oneHourAgo },
      },
      select: {
        id: true,
        step: true,
        finishedAt: true,
        logs: true,
      },
      orderBy: { finishedAt: 'desc' },
      take: 10,
    })

    return NextResponse.json({
      summary: {
        activeJobs,
        queueDepth,
        avgDuration: Math.round(avgDuration),
        avgDurationFormatted: formatDuration(avgDuration),
        successRate: Math.round(successRate * 10) / 10,
      },
      charts: {
        statusDistribution: statusDistribution.map((row) => ({
          status: row.status,
          count: Number(row.count),
        })),
        runsByAgent: runsByAgent.map((row) => ({
          agent: row.agent,
          count: Number(row.count),
        })),
      },
      recentErrors: recentErrors.map((error) => ({
        id: error.id,
        step: error.step,
        timestamp: error.finishedAt?.toISOString(),
        preview: error.logs?.substring(0, 200),
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
