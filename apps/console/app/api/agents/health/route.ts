import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/db/client'

export const runtime = 'nodejs'

// GET - View agents
export async function GET(req: NextRequest) {
  try {
    const agents = await prisma.agent.findMany({
      orderBy: { name: 'asc' },
    })

    return NextResponse.json({ agents })
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}

// POST - Update agent heartbeat
export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { name, version, config } = body

    if (!name || !version) {
      return NextResponse.json(
        { error: 'Name and version are required' },
        { status: 400 }
      )
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

    return NextResponse.json({ agent })
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}
