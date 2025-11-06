import { NextRequest } from 'next/server'
import { FinancialRunRequestSchema } from '@/lib/schemas'
import { execStream } from '@/lib/server/exec'

export const runtime = 'nodejs'

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { model, args = [], workdir } = FinancialRunRequestSchema.parse(body)

    const child = execStream(
      'python3',
      ['tools/saas-calculator.py', model, ...args],
      { cwd: workdir }
    )

    const encoder = new TextEncoder()

    return new Response(
      new ReadableStream({
        start(controller) {
          child.stdout?.on('data', (chunk) => {
            controller.enqueue(encoder.encode(chunk.toString()))
          })

          child.stderr?.on('data', (chunk) => {
            controller.enqueue(encoder.encode(`ERROR: ${chunk.toString()}`))
          })

          child.on('close', (code) => {
            if (code !== 0) {
              controller.enqueue(
                encoder.encode(`\nProcess exited with code ${code}`)
              )
            }
            controller.close()
          })

          child.on('error', (error) => {
            controller.enqueue(
              encoder.encode(`\nERROR: ${error.message}`)
            )
            controller.close()
          })
        },
      }),
      {
        headers: {
          'Content-Type': 'text/plain; charset=utf-8',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
      }
    )
  } catch (error) {
    return Response.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 400 }
    )
  }
}
