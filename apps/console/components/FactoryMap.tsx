'use client'

import ReactFlow, { Background, Controls, Node, Edge } from 'reactflow'
import 'reactflow/dist/style.css'

const initialNodes: Node[] = [
  {
    id: 'p1',
    position: { x: 0, y: 100 },
    data: { label: 'Product A' },
    type: 'input',
    style: { background: '#e0f2fe', border: '2px solid #38bdf8', borderRadius: '12px' },
  },
  {
    id: 'p2',
    position: { x: 0, y: 250 },
    data: { label: 'Product B' },
    type: 'input',
    style: { background: '#d1fae5', border: '2px solid #10b981', borderRadius: '12px' },
  },
  {
    id: 'pipe1',
    position: { x: 220, y: 100 },
    data: { label: 'Research → Build → QA' },
    style: { background: '#f1f5f9', border: '2px solid #cbd5e1', borderRadius: '12px' },
  },
  {
    id: 'pipe2',
    position: { x: 220, y: 250 },
    data: { label: 'Build Pipeline' },
    style: { background: '#f1f5f9', border: '2px solid #cbd5e1', borderRadius: '12px' },
  },
  {
    id: 'agent-dev',
    position: { x: 480, y: 50 },
    data: { label: 'Developer Agent' },
    style: { background: '#fef3c7', border: '2px solid #f59e0b', borderRadius: '12px' },
  },
  {
    id: 'agent-qa',
    position: { x: 480, y: 150 },
    data: { label: 'QA Agent' },
    style: { background: '#fef3c7', border: '2px solid #f59e0b', borderRadius: '12px' },
  },
  {
    id: 'agent-devops',
    position: { x: 480, y: 250 },
    data: { label: 'DevOps Agent' },
    style: { background: '#fef3c7', border: '2px solid #f59e0b', borderRadius: '12px' },
  },
  {
    id: 'infra',
    position: { x: 720, y: 150 },
    data: { label: 'Coolify • Postgres • Qdrant' },
    type: 'output',
    style: { background: '#ffe4e6', border: '2px solid #f43f5e', borderRadius: '12px' },
  },
]

const initialEdges: Edge[] = [
  { id: 'e1-2', source: 'p1', target: 'pipe1', animated: true },
  { id: 'e2-3', source: 'p2', target: 'pipe2', animated: true },
  { id: 'e3-4', source: 'pipe1', target: 'agent-dev' },
  { id: 'e4-5', source: 'pipe1', target: 'agent-qa' },
  { id: 'e5-6', source: 'pipe2', target: 'agent-devops' },
  { id: 'e6-7', source: 'agent-dev', target: 'infra' },
  { id: 'e7-8', source: 'agent-qa', target: 'infra' },
  { id: 'e8-9', source: 'agent-devops', target: 'infra' },
]

export function FactoryMap() {
  return (
    <div className="h-[600px] rounded-2xl border border-base-200 bg-white shadow-soft overflow-hidden">
      <ReactFlow
        nodes={initialNodes}
        edges={initialEdges}
        fitView
        className="bg-base-50"
      >
        <Background color="#cbd5e1" gap={16} />
        <Controls />
      </ReactFlow>
    </div>
  )
}
