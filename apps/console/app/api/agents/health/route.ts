import { NextRequest } from 'next/server'
import { prisma } from '@/lib/db/client'

export const runtime = 'nodejs'

export async function GET(req: NextRequest) {
  try {
    const agents = await prisma.agent.findMany({
      orderBy: { name: 'asc' },
    })

    return Response.json({ agents })
  } catch (error) {
    return Response.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { name, version, config } = body

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

    return Response.json({ agent })
  } catch (error) {
    return Response.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}
