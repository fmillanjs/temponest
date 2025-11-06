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
import { CheckCircle2, Circle, PlayCircle, SkipForward, RotateCcw, Loader2 } from 'lucide-react'

// Step configuration
const wizardSteps = [
  { id: 1, week: 1, title: 'Foundation & Setup', description: 'Initialize project structure' },
  { id: 2, week: 2, title: 'Research & Validation', description: 'Market research and validation' },
  { id: 3, week: 3, title: 'Design System', description: 'Create UI/UX design system' },
  { id: 4, week: 4, title: 'Core Features', description: 'Build main functionality' },
  { id: 5, week: 5, title: 'Authentication & Auth', description: 'Implement auth system' },
  { id: 6, week: 6, title: 'Testing & QA', description: 'Comprehensive testing' },
  { id: 7, week: 7, title: 'Deploy & Monitor', description: 'Production deployment' },
  { id: 8, week: 8, title: 'Launch & Iterate', description: 'Launch and gather feedback' },
]

// Form schema for step configuration
const stepSchema = z.object({
  projectName: z.string().min(1, 'Project name is required'),
  repositoryUrl: z.string().url('Valid URL required').optional().or(z.literal('')),
  workdir: z.string().min(1, 'Working directory is required'),
})

type StepFormData = z.infer<typeof stepSchema>

type StepStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped'

interface StepState {
  status: StepStatus
  logs: string[]
  error?: string
}

const STORAGE_KEY = 'single-saas-wizard-state'

export default function SingleSaasWizardPage() {
  const [currentStep, setCurrentStep] = useState(0)
  const [stepStates, setStepStates] = useState<Record<number, StepState>>(() => {
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
  const logsEndRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  const form = useForm<StepFormData>({
    resolver: zodResolver(stepSchema),
    defaultValues: {
      projectName: '',
      repositoryUrl: '',
      workdir: process.env.NEXT_PUBLIC_WORKDIR || '/home/doctor/temponest',
    },
  })

  // Auto-save to localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stepStates))
  }, [stepStates])

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
  }, [stepStates])

  const getCurrentStepStatus = (): StepStatus => {
    return stepStates[currentStep]?.status || 'pending'
  }

  const runStep = async (stepId: number, skipMode: boolean = false) => {
    const step = wizardSteps[stepId]
    if (!step) return

    const formData = form.getValues()

    if (skipMode) {
      setStepStates(prev => ({
        ...prev,
        [stepId]: { status: 'skipped', logs: ['Step skipped by user'] }
      }))
      if (stepId < wizardSteps.length - 1) {
        setCurrentStep(stepId + 1)
      }
      return
    }

    // Initialize step state
    setStepStates(prev => ({
      ...prev,
      [stepId]: { status: 'running', logs: [] }
    }))
    setIsStreaming(true)

    // Create abort controller for this request
    const controller = new AbortController()
    abortControllerRef.current = controller

    try {
      const response = await fetch('/api/wizard/single/step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          step: step.id,
          args: [formData.projectName, formData.repositoryUrl].filter(Boolean),
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

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n').filter(line => line.trim())

        logs = [...logs, ...lines]

        setStepStates(prev => ({
          ...prev,
          [stepId]: { status: 'running', logs }
        }))
      }

      // Mark as completed
      setStepStates(prev => ({
        ...prev,
        [stepId]: { status: 'completed', logs }
      }))

      // Move to next step automatically
      if (stepId < wizardSteps.length - 1) {
        setTimeout(() => setCurrentStep(stepId + 1), 1000)
      }

    } catch (error: unknown) {
      if (error instanceof Error && error.name === 'AbortError') {
        setStepStates(prev => ({
          ...prev,
          [stepId]: {
            status: 'failed',
            logs: [...(prev[stepId]?.logs || []), 'Execution aborted by user'],
            error: 'Aborted'
          }
        }))
      } else {
        setStepStates(prev => ({
          ...prev,
          [stepId]: {
            status: 'failed',
            logs: prev[stepId]?.logs || [],
            error: error instanceof Error ? error.message : 'Unknown error'
          }
        }))
      }
    } finally {
      setIsStreaming(false)
      abortControllerRef.current = null
    }
  }

  const retryStep = () => {
    runStep(currentStep, false)
  }

  const skipStep = () => {
    runStep(currentStep, true)
  }

  const stopExecution = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
  }

  const resetWizard = () => {
    if (confirm('Are you sure you want to reset the wizard? All progress will be lost.')) {
      setStepStates({})
      setCurrentStep(0)
      localStorage.removeItem(STORAGE_KEY)
      localStorage.removeItem(`${STORAGE_KEY}-form`)
      form.reset()
    }
  }

  const getProgress = () => {
    const completed = Object.values(stepStates).filter(s => s.status === 'completed').length
    return (completed / wizardSteps.length) * 100
  }

  const getStatusIcon = (status: StepStatus) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-emerald-600" />
      case 'running':
        return <Loader2 className="h-5 w-5 text-sky-600 animate-spin" />
      case 'failed':
        return <Circle className="h-5 w-5 text-rose-600" />
      case 'skipped':
        return <SkipForward className="h-5 w-5 text-amber-600" />
      default:
        return <Circle className="h-5 w-5 text-slate-400" />
    }
  }

  const getStatusBadge = (status: StepStatus) => {
    const variants: Record<StepStatus, string> = {
      pending: 'bg-slate-100 text-slate-700',
      running: 'bg-sky-100 text-sky-700',
      completed: 'bg-emerald-100 text-emerald-700',
      failed: 'bg-rose-100 text-rose-700',
      skipped: 'bg-amber-100 text-amber-700',
    }
    return (
      <Badge className={variants[status]}>
        {status}
      </Badge>
    )
  }

  const currentStepData = wizardSteps[currentStep]
  const currentStatus = getCurrentStepStatus()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Single-SaaS Wizard</h1>
          <p className="mt-1 text-slate-600">Build a complete SaaS product in 8 weeks</p>
        </div>
        <Button variant="outline" onClick={resetWizard}>
          Reset Wizard
        </Button>
      </div>

      {/* Overall Progress */}
      <Card>
        <CardHeader>
          <CardTitle>Overall Progress</CardTitle>
          <CardDescription>
            {Object.values(stepStates).filter(s => s.status === 'completed').length} of {wizardSteps.length} steps completed
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Progress value={getProgress()} className="h-2" />
        </CardContent>
      </Card>

      {/* Configuration Form */}
      <Card>
        <CardHeader>
          <CardTitle>Project Configuration</CardTitle>
          <CardDescription>Configure your SaaS project settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Project Name</label>
            <Input {...form.register('projectName')} placeholder="my-saas-project" />
            {form.formState.errors.projectName && (
              <p className="text-sm text-rose-600 mt-1">{form.formState.errors.projectName.message}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Repository URL (Optional)</label>
            <Input {...form.register('repositoryUrl')} placeholder="https://github.com/username/repo" />
            {form.formState.errors.repositoryUrl && (
              <p className="text-sm text-rose-600 mt-1">{form.formState.errors.repositoryUrl.message}</p>
            )}
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
        {/* Steps List */}
        <Card>
          <CardHeader>
            <CardTitle>Workflow Steps</CardTitle>
            <CardDescription>Track progress through each phase</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {wizardSteps.map((step, index) => {
                const state = stepStates[index]
                const status = state?.status || 'pending'
                const isActive = index === currentStep

                return (
                  <div
                    key={step.id}
                    className={`flex items-center gap-3 p-3 rounded-lg border transition-all cursor-pointer ${
                      isActive
                        ? 'border-sky-300 bg-sky-50 shadow-sm'
                        : 'border-slate-200 bg-white hover:border-slate-300'
                    }`}
                    onClick={() => setCurrentStep(index)}
                  >
                    {getStatusIcon(status)}
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-slate-900">
                        Week {step.week}: {step.title}
                      </div>
                      <div className="text-sm text-slate-600 truncate">{step.description}</div>
                    </div>
                    {getStatusBadge(status)}
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>

        {/* Current Step Execution */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Week {currentStepData.week}: {currentStepData.title}</CardTitle>
                <CardDescription>{currentStepData.description}</CardDescription>
              </div>
              {getStatusBadge(currentStatus)}
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Action Buttons */}
            <div className="flex gap-2">
              {currentStatus === 'pending' || currentStatus === 'failed' ? (
                <>
                  <Button
                    onClick={() => runStep(currentStep, false)}
                    disabled={isStreaming || !form.formState.isValid}
                    className="flex-1"
                  >
                    <PlayCircle className="mr-2 h-4 w-4" />
                    {currentStatus === 'failed' ? 'Retry' : 'Start Step'}
                  </Button>
                  <Button
                    variant="outline"
                    onClick={skipStep}
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
              ) : currentStatus === 'completed' ? (
                <Button
                  variant="outline"
                  onClick={retryStep}
                  disabled={isStreaming}
                  className="flex-1"
                >
                  <RotateCcw className="mr-2 h-4 w-4" />
                  Re-run Step
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
              <ScrollArea className="h-[400px]">
                <div className="p-3 font-mono text-xs space-y-1">
                  {stepStates[currentStep]?.logs.length ? (
                    stepStates[currentStep].logs.map((log, i) => (
                      <div key={i} className="whitespace-pre-wrap break-all">
                        {log}
                      </div>
                    ))
                  ) : (
                    <div className="text-slate-500 italic">
                      No logs yet. Start the step to see execution output.
                    </div>
                  )}
                  <div ref={logsEndRef} />
                </div>
              </ScrollArea>
            </div>

            {/* Error Display */}
            {stepStates[currentStep]?.error && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg">
                <p className="text-sm font-medium text-rose-900">Error</p>
                <p className="text-sm text-rose-700 mt-1">
                  {stepStates[currentStep].error}
                </p>
              </div>
            )}

            {/* Navigation */}
            <div className="flex justify-between pt-4 border-t">
              <Button
                variant="outline"
                onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
                disabled={currentStep === 0}
              >
                Previous
              </Button>
              <Button
                variant="outline"
                onClick={() => setCurrentStep(Math.min(wizardSteps.length - 1, currentStep + 1))}
                disabled={currentStep === wizardSteps.length - 1}
              >
                Next
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
