'use client'

import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface MonthlyData {
  month: number
  customers: number
  mrr: number
  profit: number
  cumulative: number
}

interface FinancialsChartsProps {
  monthlyData: MonthlyData[]
}

export function FinancialsCharts({ monthlyData }: FinancialsChartsProps) {
  return (
    <div className="grid gap-6 md:grid-cols-2">
      {/* Revenue Chart */}
      <div className="rounded-2xl border border-base-200 bg-white p-6 shadow-soft">
        <h3 className="text-lg font-semibold text-base-900 mb-4">Monthly Recurring Revenue</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={monthlyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" label={{ value: 'Month', position: 'insideBottom', offset: -5 }} />
            <YAxis label={{ value: 'MRR ($)', angle: -90, position: 'insideLeft' }} />
            <Tooltip formatter={(value) => `$${Number(value).toLocaleString()}`} />
            <Legend />
            <Line type="monotone" dataKey="mrr" stroke="#3b82f6" strokeWidth={2} name="MRR" />
            <Line type="monotone" dataKey="cumulative" stroke="#10b981" strokeWidth={2} name="Cumulative" />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Customers Chart */}
      <div className="rounded-2xl border border-base-200 bg-white p-6 shadow-soft">
        <h3 className="text-lg font-semibold text-base-900 mb-4">Customer Growth</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={monthlyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" label={{ value: 'Month', position: 'insideBottom', offset: -5 }} />
            <YAxis label={{ value: 'Customers', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="customers" fill="#8b5cf6" name="Customers" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Profit Chart */}
      <div className="rounded-2xl border border-base-200 bg-white p-6 shadow-soft md:col-span-2">
        <h3 className="text-lg font-semibold text-base-900 mb-4">Monthly Profit</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={monthlyData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" label={{ value: 'Month', position: 'insideBottom', offset: -5 }} />
            <YAxis label={{ value: 'Profit ($)', angle: -90, position: 'insideLeft' }} />
            <Tooltip formatter={(value) => `$${Number(value).toLocaleString()}`} />
            <Legend />
            <Bar dataKey="profit" fill="#10b981" name="Profit" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
