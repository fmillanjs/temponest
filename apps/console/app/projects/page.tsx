import Link from 'next/link'
import { FolderKanban, ArrowRight } from 'lucide-react'

const projects = [
  {
    id: '1',
    name: 'FormBuilder SaaS',
    slug: 'formbuilder',
    status: 'build',
    phase: 'Week 4 - Core Features',
    mrr: '$2.4k',
    updated: '2h ago',
  },
  {
    id: '2',
    name: 'Analytics Platform',
    slug: 'analytics',
    status: 'qa',
    phase: 'Week 6 - Testing',
    mrr: '$5.1k',
    updated: '5h ago',
  },
  {
    id: '3',
    name: 'CRM System',
    slug: 'crm',
    status: 'live',
    phase: 'Live - Iteration',
    mrr: '$8.9k',
    updated: '1d ago',
  },
]

const statusColors = {
  build: 'bg-sky-100 text-sky-700',
  qa: 'bg-amber-100 text-amber-700',
  live: 'bg-emerald-100 text-emerald-700',
}

export default function ProjectsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-base-900">Projects</h1>
          <p className="mt-1 text-base-600">Manage your SaaS products</p>
        </div>
        <button className="rounded-xl bg-base-900 px-4 py-2 text-sm font-medium text-white hover:bg-base-800">
          New Project
        </button>
      </div>

      <div className="grid gap-4">
        {projects.map((project) => (
          <Link
            key={project.id}
            href={`/projects/${project.slug}`}
            className="group rounded-2xl border border-base-200 bg-white p-6 shadow-soft transition-all hover:shadow-soft-lg hover:border-base-300"
          >
            <div className="flex items-start justify-between">
              <div className="flex gap-4">
                <div className="rounded-xl bg-base-100 p-3">
                  <FolderKanban className="h-6 w-6 text-base-700" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-base-900 group-hover:text-base-700">
                    {project.name}
                  </h3>
                  <p className="mt-1 text-sm text-base-600">{project.phase}</p>
                  <div className="mt-3 flex items-center gap-3">
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-medium ${
                        statusColors[project.status as keyof typeof statusColors]
                      }`}
                    >
                      {project.status.toUpperCase()}
                    </span>
                    <span className="text-sm text-base-600">Updated {project.updated}</span>
                  </div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-base-600">Projected MRR</div>
                <div className="mt-1 text-xl font-bold text-base-900">{project.mrr}</div>
                <ArrowRight className="mt-2 ml-auto h-5 w-5 text-base-400 group-hover:text-base-600" />
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
