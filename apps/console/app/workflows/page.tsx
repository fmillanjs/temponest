import { KanbanBoard } from '@/components/KanbanBoard'
import { prisma } from '@/lib/db/client'
import { revalidatePath } from 'next/cache'

async function updateProjectStatus(projectId: string, newStatus: string) {
  'use server'
  await prisma.project.update({
    where: { id: projectId },
    data: { status: newStatus as any }
  })
  revalidatePath('/workflows')
}

export default async function WorkflowsPage() {
  const projects = await prisma.project.findMany({
    select: {
      id: true,
      name: true,
      slug: true,
      status: true,
      type: true,
      updatedAt: true
    },
    orderBy: { updatedAt: 'desc' }
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-base-900">Workflows</h1>
        <p className="mt-1 text-base-600">Track your projects through the pipeline</p>
      </div>

      <KanbanBoard projects={projects} onStatusChange={updateProjectStatus} />
    </div>
  )
}
