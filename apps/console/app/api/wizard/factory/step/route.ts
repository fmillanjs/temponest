import { NextRequest } from 'next/server'
import { WizardStepRequestSchema } from '@/lib/schemas'
import { execStream } from '@/lib/server/exec'

export const runtime = 'nodejs'

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { step, args = [], workdir } = WizardStepRequestSchema.parse(body)

    const child = execStream(
      '/bin/bash',
      ['-lc', `./cli/saas-factory-init.sh ${step} ${args.join(' ')}`],
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
            controller.enqueue(encoder.encode(chunk.toString()))
          })

          child.on('close', (code) => {
            if (code !== 0) {
              controller.enqueue(
                encoder.encode(`\n\nProcess exited with code ${code}`)
              )
            }
            controller.close()
          })

          child.on('error', (error) => {
            controller.enqueue(
              encoder.encode(`\n\nERROR: ${error.message}`)
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
