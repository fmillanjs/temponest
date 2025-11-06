import { NextRequest } from 'next/server'
import { prisma } from '@/lib/db/client'
import { withAuth, withPermission, withRateLimit, compose, jsonResponse, errorResponse } from '@/lib/server/api-helpers'
import { Permission } from '@/lib/permissions'

export const runtime = 'nodejs'

// GET - View agents (requires auth and view permission)
export const GET = compose(
  withAuth,
  withPermission(Permission.AGENT_VIEW),
  withRateLimit(30, 60000) // 30 requests per minute
)(async (req: NextRequest) => {
  try {
    const agents = await prisma.agent.findMany({
      orderBy: { name: 'asc' },
    })

    return jsonResponse({ agents })
  } catch (error) {
    return errorResponse(
      error instanceof Error ? error.message : 'Unknown error',
      500
    )
  }
})

// POST - Update agent heartbeat (requires auth and configure permission)
export const POST = compose(
  withAuth,
  withPermission(Permission.AGENT_CONFIGURE),
  withRateLimit(60, 60000) // 60 requests per minute
)(async (req: NextRequest) => {
  try {
    const body = await req.json()
    const { name, version, config } = body

    if (!name || !version) {
      return errorResponse('Name and version are required', 400)
    }

    const agent = await prisma.agent.upsert({
      where: { name },
      update: {
        lastHeartbeat: new Date(),
        version,
        config: config || {},
        status: 'healthy',
      },
      create: {
        name,
        version,
        config: config || {},
        status: 'healthy',
      },
    })

    return jsonResponse({ agent })
  } catch (error) {
    return errorResponse(
      error instanceof Error ? error.message : 'Unknown error',
      500
    )
  }
})
