import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/db/client'
import { z } from 'zod'

const SaveCalculationSchema = z.object({
  model: z.string(),
  summary: z.object({
    productName: z.string(),
    month12: z.object({
      customers: z.number(),
      mrr: z.number(),
      arr: z.number(),
      profit: z.number(),
    }),
    month24: z.object({
      customers: z.number(),
      mrr: z.number(),
      arr: z.number(),
      profit: z.number(),
    }),
  }),
  monthlyData: z.array(z.object({
    month: z.number(),
    customers: z.number(),
    mrr: z.number(),
    profit: z.number(),
    cumulative: z.number(),
  })),
  projectId: z.string().uuid().optional(),
})

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const data = SaveCalculationSchema.parse(body)

    // Create a new calculation run
    const run = await prisma.run.create({
      data: {
        projectId: data.projectId || '00000000-0000-0000-0000-000000000000', // Default project ID
        kind: 'calc',
        step: `Financial calculation: ${data.model}`,
        status: 'success',
        startedAt: new Date(),
        finishedAt: new Date(),
        logs: `Calculation completed for ${data.summary.productName}`,
        artifacts: {
          model: data.model,
          summary: data.summary,
          monthlyData: data.monthlyData,
          timestamp: new Date().toISOString(),
        },
      },
    })

    return NextResponse.json({ success: true, runId: run.id })
  } catch (error) {
    console.error('Error saving calculation:', error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to save calculation' },
      { status: 400 }
    )
  }
}
