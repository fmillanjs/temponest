'use client'

import { useState, useEffect, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { CheckCircle2, Circle, PlayCircle, SkipForward, RotateCcw, Loader2, AlertCircle } from 'lucide-react'

// Phase configuration for Factory setup
const factoryPhases = [
  {
    id: 1,
    week: 1,
    title: 'Infrastructure & Agents',
    description: 'Set up core infrastructure and autonomous agents',
    tasks: ['Configure PostgreSQL', 'Deploy Coolify', 'Set up 7 core agents', 'Configure message queue']
  },
  {
    id: 2,
    week: 2,
    title: 'Pipeline & Automation',
    description: 'Build automated SaaS generation pipeline',
    tasks: ['Create template repository', 'Set up CI/CD', 'Configure deployment automation', 'Test full workflow']
  },
  {
    id: 3,
    week: 3,
    title: 'Templates & Patterns',
    description: 'Design reusable SaaS templates',
    tasks: ['Create base template', 'Add template variants', 'Document patterns', 'Test template generation']
  },
  {
    id: 4,
    week: 4,
    title: 'Monitoring & Scaling',
    description: 'Implement observability and scaling',
    tasks: ['Set up Langfuse', 'Configure metrics', 'Add alerting', 'Load testing']
  },
]

// Form schema for factory configuration
const factorySchema = z.object({
  factoryName: z.string().min(1, 'Factory name is required'),
  githubOrg: z.string().min(1, 'GitHub organization required'),
  coolifyUrl: z.string().url('Valid URL required'),
  workdir: z.string().min(1, 'Working directory is required'),
  agentCount: z.number().min(1).max(10),
})

type FactoryFormData = z.infer<typeof factorySchema>

type PhaseStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped' | 'approval_required'

interface PhaseState {
  status: PhaseStatus
  logs: string[]
  error?: string
  approvalComment?: string
  completedTasks: number
  totalTasks: number
}

const STORAGE_KEY = 'factory-wizard-state'

export default function FactoryWizardPage() {
  const [currentPhase, setCurrentPhase] = useState(0)
  const [phaseStates, setPhaseStates] = useState<Record<number, PhaseState>>(() => {
    const saved = typeof window !== 'undefined' ? localStorage.getItem(STORAGE_KEY) : null
    if (saved) {
      try {
        return JSON.parse(saved)
      } catch {
        return {}
      }
    }
    return {}
  })
  const [isStreaming, setIsStreaming] = useState(false)
  const [showApprovalModal, setShowApprovalModal] = useState(false)
  const [approvalComment, setApprovalComment] = useState('')
  const logsEndRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  const form = useForm<FactoryFormData>({
    resolver: zodResolver(factorySchema),
    defaultValues: {
      factoryName: 'SaaS-Empire-Factory',
      githubOrg: '',
      coolifyUrl: '',
      workdir: process.env.NEXT_PUBLIC_WORKDIR || '/home/doctor/temponest',
      agentCount: 7,
    },
  })

  // Auto-save to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(phaseStates))
  }, [phaseStates])

  // Load saved form data
  useEffect(() => {
    const savedForm = localStorage.getItem(`${STORAGE_KEY}-form`)
    if (savedForm) {
      try {
        const data = JSON.parse(savedForm)
        form.reset(data)
      } catch {}
    }
  }, [form])

  // Save form data on change
  useEffect(() => {
    const subscription = form.watch((value) => {
      localStorage.setItem(`${STORAGE_KEY}-form`, JSON.stringify(value))
    })
    return () => subscription.unsubscribe()
  }, [form])

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [phaseStates])

  const getCurrentPhaseStatus = (): PhaseStatus => {
    return phaseStates[currentPhase]?.status || 'pending'
  }

  const runPhase = async (phaseId: number, skipMode: boolean = false) => {
    const phase = factoryPhases[phaseId]
    if (!phase) return

    const formData = form.getValues()

    if (skipMode) {
      setPhaseStates(prev => ({
        ...prev,
        [phaseId]: {
          status: 'skipped',
          logs: ['Phase skipped by user'],
          completedTasks: 0,
          totalTasks: phase.tasks.length
        }
      }))
      if (phaseId < factoryPhases.length - 1) {
        setCurrentPhase(phaseId + 1)
      }
      return
    }

    // Initialize phase state
    setPhaseStates(prev => ({
      ...prev,
      [phaseId]: {
        status: 'running',
        logs: [],
        completedTasks: 0,
        totalTasks: phase.tasks.length
      }
    }))
    setIsStreaming(true)

    // Create abort controller for this request
    const controller = new AbortController()
    abortControllerRef.current = controller

    try {
      const response = await fetch('/api/wizard/factory/step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          step: phase.id,
          args: [
            formData.factoryName,
            formData.githubOrg,
            formData.coolifyUrl,
            formData.agentCount.toString()
          ].filter(Boolean),
          workdir: formData.workdir,
        }),
        signal: controller.signal,
      })

      if (!response.ok || !response.body) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let logs: string[] = []
      let completedTasks = 0

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n').filter(line => line.trim())

        // Count completed tasks based on log patterns
        lines.forEach(line => {
          if (line.includes('✓') || line.includes('completed') || line.includes('success')) {
            completedTasks = Math.min(completedTasks + 1, phase.tasks.length)
          }
        })

        logs = [...logs, ...lines]

        setPhaseStates(prev => ({
          ...prev,
          [phaseId]: {
            status: 'running',
            logs,
            completedTasks,
            totalTasks: phase.tasks.length
          }
        }))
      }

      // For critical phases, require approval
      if ([1, 4].includes(phase.id)) {
        setPhaseStates(prev => ({
          ...prev,
          [phaseId]: {
            status: 'approval_required',
            logs,
            completedTasks: phase.tasks.length,
            totalTasks: phase.tasks.length
          }
        }))
        setShowApprovalModal(true)
      } else {
        // Mark as completed
        setPhaseStates(prev => ({
          ...prev,
          [phaseId]: {
            status: 'completed',
            logs,
            completedTasks: phase.tasks.length,
            totalTasks: phase.tasks.length
          }
        }))

        // Move to next phase automatically
        if (phaseId < factoryPhases.length - 1) {
          setTimeout(() => setCurrentPhase(phaseId + 1), 1500)
        }
      }

    } catch (error: unknown) {
      if (error instanceof Error && error.name === 'AbortError') {
        setPhaseStates(prev => ({
          ...prev,
          [phaseId]: {
            status: 'failed',
            logs: [...(prev[phaseId]?.logs || []), 'Execution aborted by user'],
            error: 'Aborted',
            completedTasks: prev[phaseId]?.completedTasks || 0,
            totalTasks: phase.tasks.length
          }
        }))
      } else {
        setPhaseStates(prev => ({
          ...prev,
          [phaseId]: {
            status: 'failed',
            logs: prev[phaseId]?.logs || [],
            error: error instanceof Error ? error.message : 'Unknown error',
            completedTasks: prev[phaseId]?.completedTasks || 0,
            totalTasks: phase.tasks.length
          }
        }))
      }
    } finally {
      setIsStreaming(false)
      abortControllerRef.current = null
    }
  }

  const approvePhase = () => {
    setPhaseStates(prev => ({
      ...prev,
      [currentPhase]: {
        ...prev[currentPhase],
        status: 'completed',
        approvalComment: approvalComment || 'Approved'
      }
    }))
    setShowApprovalModal(false)
    setApprovalComment('')

    // Move to next phase
    if (currentPhase < factoryPhases.length - 1) {
      setTimeout(() => setCurrentPhase(currentPhase + 1), 500)
    }
  }

  const rejectPhase = () => {
    setPhaseStates(prev => ({
      ...prev,
      [currentPhase]: {
        ...prev[currentPhase],
        status: 'failed',
        error: 'Rejected during approval',
        approvalComment: approvalComment || 'Rejected'
      }
    }))
    setShowApprovalModal(false)
    setApprovalComment('')
  }

  const retryPhase = () => {
    runPhase(currentPhase, false)
  }

  const skipPhase = () => {
    runPhase(currentPhase, true)
  }

  const stopExecution = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
  }

  const resetWizard = () => {
    if (confirm('Are you sure you want to reset the factory wizard? All progress will be lost.')) {
      setPhaseStates({})
      setCurrentPhase(0)
      localStorage.removeItem(STORAGE_KEY)
      localStorage.removeItem(`${STORAGE_KEY}-form`)
      form.reset()
    }
  }

  const getProgress = () => {
    const completed = Object.values(phaseStates).filter(s => s.status === 'completed').length
    return (completed / factoryPhases.length) * 100
  }

  const getStatusIcon = (status: PhaseStatus) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-emerald-600" />
      case 'running':
        return <Loader2 className="h-5 w-5 text-sky-600 animate-spin" />
      case 'failed':
        return <Circle className="h-5 w-5 text-rose-600" />
      case 'skipped':
        return <SkipForward className="h-5 w-5 text-amber-600" />
      case 'approval_required':
        return <AlertCircle className="h-5 w-5 text-amber-600" />
      default:
        return <Circle className="h-5 w-5 text-slate-400" />
    }
  }

  const getStatusBadge = (status: PhaseStatus) => {
    const variants: Record<PhaseStatus, string> = {
      pending: 'bg-slate-100 text-slate-700',
      running: 'bg-sky-100 text-sky-700',
      completed: 'bg-emerald-100 text-emerald-700',
      failed: 'bg-rose-100 text-rose-700',
      skipped: 'bg-amber-100 text-amber-700',
      approval_required: 'bg-amber-100 text-amber-700',
    }
    return (
      <Badge className={variants[status]}>
        {status.replace('_', ' ')}
      </Badge>
    )
  }

  const currentPhaseData = factoryPhases[currentPhase]
  const currentStatus = getCurrentPhaseStatus()
  const currentState = phaseStates[currentPhase]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Factory Setup Wizard</h1>
          <p className="mt-1 text-slate-600">Initialize your autonomous SaaS factory</p>
        </div>
        <Button variant="outline" onClick={resetWizard}>
          Reset Wizard
        </Button>
      </div>

      {/* Overall Progress */}
      <Card>
        <CardHeader>
          <CardTitle>Factory Setup Progress</CardTitle>
          <CardDescription>
            {Object.values(phaseStates).filter(s => s.status === 'completed').length} of {factoryPhases.length} phases completed
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Progress value={getProgress()} className="h-2" />
        </CardContent>
      </Card>

      {/* Configuration Form */}
      <Card>
        <CardHeader>
          <CardTitle>Factory Configuration</CardTitle>
          <CardDescription>Configure your SaaS factory infrastructure</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Factory Name</label>
              <Input {...form.register('factoryName')} placeholder="SaaS-Empire-Factory" />
              {form.formState.errors.factoryName && (
                <p className="text-sm text-rose-600 mt-1">{form.formState.errors.factoryName.message}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">GitHub Organization</label>
              <Input {...form.register('githubOrg')} placeholder="your-org" />
              {form.formState.errors.githubOrg && (
                <p className="text-sm text-rose-600 mt-1">{form.formState.errors.githubOrg.message}</p>
              )}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Coolify URL</label>
              <Input {...form.register('coolifyUrl')} placeholder="https://coolify.yourdomain.com" />
              {form.formState.errors.coolifyUrl && (
                <p className="text-sm text-rose-600 mt-1">{form.formState.errors.coolifyUrl.message}</p>
              )}
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Agent Count</label>
              <Input
                type="number"
                {...form.register('agentCount', { valueAsNumber: true })}
                placeholder="7"
                min="1"
                max="10"
              />
              {form.formState.errors.agentCount && (
                <p className="text-sm text-rose-600 mt-1">{form.formState.errors.agentCount.message}</p>
              )}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Working Directory</label>
            <Input {...form.register('workdir')} placeholder="/home/doctor/temponest" />
            {form.formState.errors.workdir && (
              <p className="text-sm text-rose-600 mt-1">{form.formState.errors.workdir.message}</p>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Phases List */}
        <Card>
          <CardHeader>
            <CardTitle>Setup Phases</CardTitle>
            <CardDescription>4-week factory initialization</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {factoryPhases.map((phase, index) => {
                const state = phaseStates[index]
                const status = state?.status || 'pending'
                const isActive = index === currentPhase

                return (
                  <div
                    key={phase.id}
                    className={`rounded-lg border p-4 transition-all cursor-pointer ${
                      isActive
                        ? 'border-sky-300 bg-sky-50 shadow-sm'
                        : 'border-slate-200 bg-white hover:border-slate-300'
                    }`}
                    onClick={() => setCurrentPhase(index)}
                  >
                    <div className="flex items-start gap-3">
                      {getStatusIcon(status)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <div className="font-medium text-slate-900">
                            Week {phase.week}: {phase.title}
                          </div>
                          {getStatusBadge(status)}
                        </div>
                        <div className="text-sm text-slate-600 mb-2">{phase.description}</div>

                        {/* Task Progress */}
                        {state && (
                          <div className="space-y-1">
                            <div className="flex justify-between text-xs text-slate-500">
                              <span>Tasks: {state.completedTasks}/{state.totalTasks}</span>
                              <span>{Math.round((state.completedTasks / state.totalTasks) * 100)}%</span>
                            </div>
                            <Progress
                              value={(state.completedTasks / state.totalTasks) * 100}
                              className="h-1"
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Current Phase Execution */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Week {currentPhaseData.week}: {currentPhaseData.title}</CardTitle>
                <CardDescription>{currentPhaseData.description}</CardDescription>
              </div>
              {getStatusBadge(currentStatus)}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Task Checklist */}
            <div className="border rounded-lg p-3 bg-slate-50">
              <div className="text-sm font-medium text-slate-700 mb-2">Phase Tasks:</div>
              <div className="space-y-1">
                {currentPhaseData.tasks.map((task, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    {currentState && i < currentState.completedTasks ? (
                      <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    ) : (
                      <Circle className="h-4 w-4 text-slate-400" />
                    )}
                    <span className={currentState && i < currentState.completedTasks ? 'text-emerald-700' : 'text-slate-600'}>
                      {task}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              {currentStatus === 'pending' || currentStatus === 'failed' ? (
                <>
                  <Button
                    onClick={() => runPhase(currentPhase, false)}
                    disabled={isStreaming || !form.formState.isValid}
                    className="flex-1"
                  >
                    <PlayCircle className="mr-2 h-4 w-4" />
                    {currentStatus === 'failed' ? 'Retry Phase' : 'Start Phase'}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={skipPhase}
                    disabled={isStreaming}
                  >
                    <SkipForward className="h-4 w-4" />
                  </Button>
                </>
              ) : currentStatus === 'running' ? (
                <Button
                  variant="destructive"
                  onClick={stopExecution}
                  className="flex-1"
                >
                  Stop Execution
                </Button>
              ) : currentStatus === 'approval_required' ? (
                <div className="flex-1 space-y-2">
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                    <p className="text-sm font-medium text-amber-900 flex items-center gap-2">
                      <AlertCircle className="h-4 w-4" />
                      Approval Required
                    </p>
                    <p className="text-sm text-amber-700 mt-1">
                      This phase requires manual approval before proceeding.
                    </p>
                  </div>
                </div>
              ) : currentStatus === 'completed' ? (
                <Button
                  variant="outline"
                  onClick={retryPhase}
                  disabled={isStreaming}
                  className="flex-1"
                >
                  <RotateCcw className="mr-2 h-4 w-4" />
                  Re-run Phase
                </Button>
              ) : null}
            </div>

            {/* Logs Viewer */}
            <div className="border rounded-lg bg-slate-950 text-slate-50">
              <div className="px-3 py-2 border-b border-slate-800 flex items-center justify-between">
                <span className="text-xs font-mono">Execution Logs</span>
                {isStreaming && (
                  <Loader2 className="h-3 w-3 animate-spin text-sky-400" />
                )}
              </div>
              <ScrollArea className="h-[300px]">
                <div className="p-3 font-mono text-xs space-y-1">
                  {phaseStates[currentPhase]?.logs.length ? (
                    phaseStates[currentPhase].logs.map((log, i) => (
                      <div key={i} className="whitespace-pre-wrap break-all">
                        {log}
                      </div>
                    ))
                  ) : (
                    <div className="text-slate-500 italic">
                      No logs yet. Start the phase to see execution output.
                    </div>
                  )}
                  <div ref={logsEndRef} />
                </div>
              </ScrollArea>
            </div>

            {/* Error Display */}
            {phaseStates[currentPhase]?.error && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg">
                <p className="text-sm font-medium text-rose-900">Error</p>
                <p className="text-sm text-rose-700 mt-1">
                  {phaseStates[currentPhase].error}
                </p>
              </div>
            )}

            {/* Navigation */}
            <div className="flex justify-between pt-4 border-t">
              <Button
                variant="outline"
                onClick={() => setCurrentPhase(Math.max(0, currentPhase - 1))}
                disabled={currentPhase === 0}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                onClick={() => setCurrentPhase(Math.min(factoryPhases.length - 1, currentPhase + 1))}
                disabled={currentPhase === factoryPhases.length - 1}
              >
                Next
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Approval Modal */}
      {showApprovalModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-lg w-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-amber-600" />
                Approval Required
              </CardTitle>
              <CardDescription>
                Week {currentPhaseData.week}: {currentPhaseData.title} requires your approval to proceed
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Comment (Optional)
                </label>
                <textarea
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                  rows={3}
                  value={approvalComment}
                  onChange={(e) => setApprovalComment(e.target.value)}
                  placeholder="Add a comment about this approval..."
                />
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={approvePhase}
                  className="flex-1 bg-emerald-600 hover:bg-emerald-700"
                >
                  <CheckCircle2 className="mr-2 h-4 w-4" />
                  Approve
                </Button>
                <Button
                  variant="destructive"
                  onClick={rejectPhase}
                  className="flex-1"
                >
                  Reject
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
