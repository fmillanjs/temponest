'use client'

import { useState } from 'react'
import dynamic from 'next/dynamic'

// Dynamically import chart components to reduce initial bundle size
const FinancialsCharts = dynamic(
  () => import('@/components/financials/FinancialsCharts').then((mod) => ({ default: mod.FinancialsCharts })),
  {
    loading: () => (
      <div className="rounded-2xl border border-base-200 bg-white p-6 shadow-soft">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-base-200 rounded w-1/3"></div>
          <div className="h-64 bg-base-200 rounded"></div>
        </div>
      </div>
    ),
    ssr: false,
  }
)

type CalculatorModel = 'formbuilder' | 'analytics' | 'crm' | 'scheduler' | 'emailbuilder'

interface CalculatorOption {
  value: CalculatorModel
  label: string
  description: string
}

const CALCULATOR_OPTIONS: CalculatorOption[] = [
  { value: 'formbuilder', label: 'FormFlow', description: 'Form Builder SaaS' },
  { value: 'analytics', label: 'SimpleAnalytics', description: 'Web Analytics Platform' },
  { value: 'crm', label: 'MicroCRM', description: 'Simple CRM System' },
  { value: 'scheduler', label: 'QuickSchedule', description: 'Appointment Booking' },
  { value: 'emailbuilder', label: 'EmailCraft', description: 'Email Template Builder' },
]

interface MonthlyData {
  month: number
  customers: number
  mrr: number
  profit: number
  cumulative: number
}

export default function FinancialsPage() {
  const [selectedModel, setSelectedModel] = useState<CalculatorModel>('formbuilder')
  const [isRunning, setIsRunning] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [output, setOutput] = useState('')
  const [monthlyData, setMonthlyData] = useState<MonthlyData[]>([])
  const [saveMessage, setSaveMessage] = useState('')
  const [summary, setSummary] = useState<{
    productName: string
    month12: { customers: number; mrr: number; arr: number; profit: number }
    month24: { customers: number; mrr: number; arr: number; profit: number }
  } | null>(null)

  const runCalculation = async () => {
    setIsRunning(true)
    setOutput('')
    setMonthlyData([])
    setSummary(null)

    try {
      const response = await fetch('/api/financials/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: selectedModel,
          args: ['--monthly'],
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to run calculation')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (reader) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        buffer += chunk
        setOutput((prev) => prev + chunk)

        // Parse monthly data from output
        parseOutputData(buffer)
      }
    } catch (error) {
      setOutput(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setIsRunning(false)
    }
  }

  const parseOutputData = (text: string) => {
    // Extract product name
    const productMatch = text.match(/SaaS Financial Projection: (.+)/)
    if (productMatch) {
      const productName = productMatch[1].trim()

      // Try to extract month 12 and 24 summaries
      const month12Match = text.match(/MONTH 12 PROJECTION:\s+Customers: ([\d,]+)\s+MRR: \$([\d,]+)\s+ARR: \$([\d,]+)\s+Monthly Profit: \$([\d,\-]+)/)
      const month24Match = text.match(/MONTH 24 PROJECTION:\s+Customers: ([\d,]+)\s+MRR: \$([\d,]+)\s+ARR: \$([\d,]+)\s+Monthly Profit: \$([\d,\-]+)/)

      if (month12Match && month24Match) {
        setSummary({
          productName,
          month12: {
            customers: parseInt(month12Match[1].replace(/,/g, '')),
            mrr: parseInt(month12Match[2].replace(/,/g, '')),
            arr: parseInt(month12Match[3].replace(/,/g, '')),
            profit: parseInt(month24Match[4].replace(/,/g, '')),
          },
          month24: {
            customers: parseInt(month24Match[1].replace(/,/g, '')),
            mrr: parseInt(month24Match[2].replace(/,/g, '')),
            arr: parseInt(month24Match[3].replace(/,/g, '')),
            profit: parseInt(month24Match[4].replace(/,/g, '')),
          },
        })
      }
    }

    // Extract monthly breakdown data
    const monthlyPattern = /^(\d+)\s+([\d,]+)\s+\$([\d,]+)\s+\$([\d,\-]+)\s+\$([\d,\-]+)/gm
    const matches = Array.from(text.matchAll(monthlyPattern))

    if (matches.length > 0) {
      const data = matches.map(match => ({
        month: parseInt(match[1]),
        customers: parseInt(match[2].replace(/,/g, '')),
        mrr: parseInt(match[3].replace(/,/g, '')),
        profit: parseInt(match[4].replace(/,/g, '')),
        cumulative: parseInt(match[5].replace(/,/g, '')),
      }))
      setMonthlyData(data)
    }
  }

  const exportToJSON = () => {
    const data = {
      model: selectedModel,
      summary,
      monthlyData,
      timestamp: new Date().toISOString(),
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${selectedModel}-projection-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const exportToCSV = () => {
    if (monthlyData.length === 0) return

    const headers = ['Month', 'Customers', 'MRR', 'Profit', 'Cumulative Profit']
    const rows = monthlyData.map(d => [d.month, d.customers, d.mrr, d.profit, d.cumulative])
    const csv = [headers, ...rows].map(row => row.join(',')).join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${selectedModel}-projection-${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  const saveToDatabase = async () => {
    if (!summary || monthlyData.length === 0) return

    setIsSaving(true)
    setSaveMessage('')

    try {
      const response = await fetch('/api/financials/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: selectedModel,
          summary,
          monthlyData,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to save calculation')
      }

      const data = await response.json()
      setSaveMessage(`Saved successfully! Run ID: ${data.runId}`)
      setTimeout(() => setSaveMessage(''), 5000)
    } catch (error) {
      setSaveMessage(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-base-900">Financial Calculator</h1>
        <p className="mt-1 text-base-600">
          Model your SaaS financials and projections
        </p>
      </div>

      {/* Calculator Selection */}
      <div className="rounded-2xl border border-base-200 bg-white p-6 shadow-soft">
        <h2 className="text-lg font-semibold text-base-900 mb-4">Select Calculator Model</h2>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {CALCULATOR_OPTIONS.map((option) => (
            <button
              key={option.value}
              onClick={() => setSelectedModel(option.value)}
              className={`rounded-xl border-2 p-4 text-left transition-all ${
                selectedModel === option.value
                  ? 'border-accent-primary bg-accent-primary/5'
                  : 'border-base-200 hover:border-base-300'
              }`}
            >
              <div className="font-semibold text-base-900">{option.label}</div>
              <div className="mt-1 text-sm text-base-600">{option.description}</div>
            </button>
          ))}
        </div>

        <div className="mt-6 flex gap-3">
          <button
            onClick={runCalculation}
            disabled={isRunning}
            className="rounded-xl bg-accent-primary px-6 py-3 font-medium text-white hover:bg-accent-primary/90 disabled:opacity-50"
          >
            {isRunning ? 'Running...' : 'Run Calculation'}
          </button>

          {monthlyData.length > 0 && (
            <>
              <button
                onClick={saveToDatabase}
                disabled={isSaving}
                className="rounded-xl bg-accent-success px-6 py-3 font-medium text-white hover:bg-accent-success/90 disabled:opacity-50"
              >
                {isSaving ? 'Saving...' : 'Save to Database'}
              </button>
              <button
                onClick={exportToJSON}
                className="rounded-xl border border-base-300 bg-white px-6 py-3 font-medium text-base-900 hover:bg-base-50"
              >
                Export JSON
              </button>
              <button
                onClick={exportToCSV}
                className="rounded-xl border border-base-300 bg-white px-6 py-3 font-medium text-base-900 hover:bg-base-50"
              >
                Export CSV
              </button>
            </>
          )}
        </div>

        {saveMessage && (
          <div className={`mt-4 rounded-xl px-4 py-3 text-sm ${
            saveMessage.startsWith('Error')
              ? 'bg-accent-error/10 text-accent-error border border-accent-error/20'
              : 'bg-accent-success/10 text-accent-success border border-accent-success/20'
          }`}>
            {saveMessage}
          </div>
        )}
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
          <div className="rounded-2xl border border-base-200 bg-white p-6 shadow-soft">
            <h3 className="text-sm font-semibold text-base-600 uppercase mb-4">Month 12 Projection</h3>
            <div className="space-y-3">
              <div>
                <div className="text-sm text-base-600">Customers</div>
                <div className="text-2xl font-bold text-base-900">{summary.month12.customers.toLocaleString()}</div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-base-600">MRR</div>
                  <div className="text-lg font-bold text-base-900">${(summary.month12.mrr / 1000).toFixed(1)}k</div>
                </div>
                <div>
                  <div className="text-sm text-base-600">ARR</div>
                  <div className="text-lg font-bold text-base-900">${(summary.month12.arr / 1000).toFixed(1)}k</div>
                </div>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-base-200 bg-white p-6 shadow-soft">
            <h3 className="text-sm font-semibold text-base-600 uppercase mb-4">Month 24 Projection</h3>
            <div className="space-y-3">
              <div>
                <div className="text-sm text-base-600">Customers</div>
                <div className="text-2xl font-bold text-base-900">{summary.month24.customers.toLocaleString()}</div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-base-600">MRR</div>
                  <div className="text-lg font-bold text-base-900">${(summary.month24.mrr / 1000).toFixed(1)}k</div>
                </div>
                <div>
                  <div className="text-sm text-base-600">ARR</div>
                  <div className="text-lg font-bold text-base-900">${(summary.month24.arr / 1000).toFixed(1)}k</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts - Dynamically loaded to reduce initial bundle size */}
      {monthlyData.length > 0 && <FinancialsCharts monthlyData={monthlyData} />}

      {/* Output Log */}
      {output && (
        <div className="rounded-2xl border border-base-200 bg-white shadow-soft">
          <div className="border-b border-base-200 p-4">
            <h3 className="font-semibold text-base-900">Calculation Output</h3>
          </div>
          <div className="p-4">
            <pre className="whitespace-pre-wrap font-mono text-sm text-base-700 bg-base-50 p-4 rounded-xl overflow-x-auto max-h-96">
              {output}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
