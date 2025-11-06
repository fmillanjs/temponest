import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const agent = searchParams.get('agent')
    const project = searchParams.get('project')
    const level = searchParams.get('level')
    const search = searchParams.get('search')
    const limit = parseInt(searchParams.get('limit') || '50')

    // Get audit logs
    let auditWhere: any = {}

    if (search) {
      auditWhere.OR = [
        { action: { contains: search, mode: 'insensitive' } },
        { resource: { contains: search, mode: 'insensitive' } },
      ]
    }

    if (agent) {
      auditWhere.action = { contains: agent, mode: 'insensitive' }
    }

    if (project) {
      auditWhere.resource = { contains: project, mode: 'insensitive' }
    }

    const auditLogs = await prisma.auditLog.findMany({
      where: auditWhere,
      orderBy: { createdAt: 'desc' },
      take: limit,
    })

    // Transform audit logs to unified format
    const logs = auditLogs.map((log) => {
      // Extract agent name from action
      const actionParts = log.action.split('.')
      const agentName = actionParts[0] || 'System'

      // Determine level from action
      let logLevel = 'info'
      if (log.action.includes('error') || log.action.includes('failed')) {
        logLevel = 'error'
      } else if (log.action.includes('warn') || log.action.includes('degraded')) {
        logLevel = 'warn'
      } else if (log.action.includes('success') || log.action.includes('completed')) {
        logLevel = 'success'
      }

      return {
        id: log.id,
        timestamp: log.createdAt.toISOString(),
        level: logLevel,
        message: log.action,
        agent: agentName,
        resource: log.resource,
        details: log.details,
        userId: log.userId,
      }
    })

    // Apply level filter after transformation
    const filteredLogs = level
      ? logs.filter(log => log.level === level)
      : logs

    return NextResponse.json({
      logs: filteredLogs,
      total: filteredLogs.length,
    })
  } catch (error) {
    console.error('Error fetching logs:', error)
    return NextResponse.json(
      { error: 'Failed to fetch logs' },
      { status: 500 }
    )
  }
}
