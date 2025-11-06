'use client'

import { useState } from 'react'
import {
  DndContext,
  DragEndEvent,
  DragOverlay,
  DragStartEvent,
  PointerSensor,
  useSensor,
  useSensors,
  closestCorners
} from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical, ExternalLink, MoreVertical } from 'lucide-react'
import Link from 'next/link'
import { formatDistanceToNow } from 'date-fns'

type Project = {
  id: string
  name: string
  slug: string
  status: string
  type: string
  updatedAt: Date
}

type KanbanBoardProps = {
  projects: Project[]
  onStatusChange?: (projectId: string, newStatus: string) => Promise<void>
}

type Column = {
  id: string
  title: string
  color: string
}

const columns: Column[] = [
  { id: 'idle', title: 'Idle', color: 'slate' },
  { id: 'research', title: 'Research', color: 'sky' },
  { id: 'build', title: 'Build', color: 'sky' },
  { id: 'qa', title: 'QA', color: 'amber' },
  { id: 'deploy', title: 'Deploy', color: 'amber' },
  { id: 'live', title: 'Live', color: 'emerald' },
]

function ProjectCard({ project }: { project: Project }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging
  } = useSortable({ id: project.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="group rounded-xl border border-base-200 bg-white p-3 shadow-sm hover:shadow-md transition-shadow"
    >
      <div className="flex items-start gap-2">
        <button
          {...attributes}
          {...listeners}
          className="mt-1 cursor-grab active:cursor-grabbing text-base-400 hover:text-base-600"
        >
          <GripVertical className="h-4 w-4" />
        </button>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1">
              <Link
                href={`/projects/${project.slug}`}
                className="font-medium text-sm text-base-900 hover:text-base-700 line-clamp-1"
              >
                {project.name}
              </Link>
              <div className="mt-1 flex items-center gap-2 text-xs text-base-600">
                <span className="capitalize">{project.type}</span>
                <span>•</span>
                <span>{formatDistanceToNow(project.updatedAt, { addSuffix: true })}</span>
              </div>
            </div>
            <button className="opacity-0 group-hover:opacity-100 p-1 hover:bg-base-100 rounded transition-opacity">
              <MoreVertical className="h-4 w-4 text-base-600" />
            </button>
          </div>
          <div className="mt-2 flex items-center gap-2">
            <Link
              href={`/projects/${project.slug}`}
              className="text-xs text-accent-info hover:text-accent-info-dark flex items-center gap-1"
            >
              View <ExternalLink className="h-3 w-3" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

function DroppableColumn({ column, projects }: { column: Column; projects: Project[] }) {
  return (
    <div className="flex-shrink-0 w-80 rounded-2xl border border-base-200 bg-base-50 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold text-base-900">{column.title}</h3>
        <span className="rounded-full bg-base-200 px-2 py-1 text-xs font-medium text-base-700">
          {projects.length}
        </span>
      </div>
      <SortableContext items={projects.map(p => p.id)} strategy={verticalListSortingStrategy}>
        <div className="space-y-3 min-h-[200px]">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
          {projects.length === 0 && (
            <div className="text-center py-8 text-sm text-base-500">
              No projects
            </div>
          )}
        </div>
      </SortableContext>
    </div>
  )
}

export function KanbanBoard({ projects, onStatusChange }: KanbanBoardProps) {
  const [activeId, setActiveId] = useState<string | null>(null)
  const [localProjects, setLocalProjects] = useState(projects)

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  )

  const handleDragStart = (event: DragStartEvent) => {
    setActiveId(event.active.id as string)
  }

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event

    if (!over) {
      setActiveId(null)
      return
    }

    const activeProject = localProjects.find(p => p.id === active.id)
    if (!activeProject) {
      setActiveId(null)
      return
    }

    // Find the column the project was dropped into
    const overProject = localProjects.find(p => p.id === over.id)
    const newStatus = overProject?.status || (over.id as string)

    // Check if dropped in a valid column
    const validStatuses = columns.map(c => c.id)
    if (!validStatuses.includes(newStatus)) {
      setActiveId(null)
      return
    }

    if (activeProject.status !== newStatus) {
      // Optimistically update UI
      const updatedProjects = localProjects.map(p =>
        p.id === activeProject.id ? { ...p, status: newStatus } : p
      )
      setLocalProjects(updatedProjects)

      // Call the server to update
      if (onStatusChange) {
        try {
          await onStatusChange(activeProject.id, newStatus)
        } catch (error) {
          // Revert on error
          setLocalProjects(localProjects)
          console.error('Failed to update project status:', error)
        }
      }
    }

    setActiveId(null)
  }

  const getColumnProjects = (columnId: string) => {
    return localProjects.filter(p => p.status === columnId)
  }

  const activeProject = localProjects.find(p => p.id === activeId)

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="flex gap-4 overflow-x-auto pb-4">
        {columns.map((column) => (
          <DroppableColumn
            key={column.id}
            column={column}
            projects={getColumnProjects(column.id)}
          />
        ))}
      </div>

      <DragOverlay>
        {activeProject ? (
          <div className="rounded-xl border border-base-200 bg-white p-3 shadow-lg opacity-90 w-80">
            <div className="font-medium text-sm text-base-900">{activeProject.name}</div>
            <div className="mt-1 text-xs text-base-600">
              {formatDistanceToNow(activeProject.updatedAt, { addSuffix: true })}
            </div>
          </div>
        ) : null}
      </DragOverlay>
    </DndContext>
  )
}
