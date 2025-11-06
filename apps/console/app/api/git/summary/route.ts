import { NextRequest } from 'next/server'
import { execCollect } from '@/lib/server/exec'

export const runtime = 'nodejs'

export async function GET(req: NextRequest) {
  try {
    const workdir = req.nextUrl.searchParams.get('workdir') || '/home/doctor/temponest'

    const [status, branch, lastCommit] = await Promise.all([
      execCollect('git', ['status', '--short'], { cwd: workdir }),
      execCollect('git', ['branch', '--show-current'], { cwd: workdir }),
      execCollect('git', ['log', '-1', '--oneline'], { cwd: workdir }),
    ])

    return Response.json({
      status: status.stdout,
      branch: branch.stdout.trim(),
      lastCommit: lastCommit.stdout.trim(),
      hasChanges: status.stdout.length > 0,
    })
  } catch (error) {
    return Response.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}
