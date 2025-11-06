'use client'

import { useState, useCallback } from 'react'
import ReactFlow, {
  Background,
  Controls,
  Node,
  Edge,
  MiniMap,
  NodeMouseHandler,
  useNodesState,
  useEdgesState
} from 'reactflow'
import 'reactflow/dist/style.css'
import { X, Activity, Zap, Server } from 'lucide-react'

type NodeData = {
  label: string
  type: 'project' | 'agent' | 'infrastructure' | 'pipeline'
  status?: string
  details?: Record<string, any>
}

type FactoryMapProps = {
  projects: Array<{ id: string; name: string; status: string }>
  agents: Array<{ id: string; name: string; status: string; version: string }>
}

export function FactoryMap({ projects, agents }: FactoryMapProps) {
  const [selectedNode, setSelectedNode] = useState<Node<NodeData> | null>(null)
  const [showPanel, setShowPanel] = useState(false)

  // Build nodes from real data
  const buildNodes = (): Node<NodeData>[] => {
    const nodes: Node<NodeData>[] = []
    let yOffset = 50

    // Add project nodes
    projects.forEach((project, idx) => {
      const statusColors = {
        idle: { bg: '#f1f5f9', border: '#cbd5e1' },
        research: { bg: '#e0f2fe', border: '#38bdf8' },
        build: { bg: '#e0f2fe', border: '#38bdf8' },
        qa: { bg: '#fef3c7', border: '#f59e0b' },
        deploy: { bg: '#fef3c7', border: '#f59e0b' },
        live: { bg: '#d1fae5', border: '#10b981' },
      }
      const colors = statusColors[project.status as keyof typeof statusColors] || statusColors.idle

      nodes.push({
        id: `project-${project.id}`,
        position: { x: 50, y: yOffset },
        data: {
          label: project.name,
          type: 'project',
          status: project.status,
          details: project
        },
        type: 'input',
        style: {
          background: colors.bg,
          border: `2px solid ${colors.border}`,
          borderRadius: '12px',
          padding: '10px 16px',
          cursor: 'pointer'
        },
      })
      yOffset += 120
    })

    // Add agent nodes
    let agentYOffset = 50
    agents.slice(0, 5).forEach((agent, idx) => {
      const statusColors = {
        healthy: { bg: '#d1fae5', border: '#10b981' },
        degraded: { bg: '#fef3c7', border: '#f59e0b' },
        down: { bg: '#ffe4e6', border: '#f43f5e' },
      }
      const colors = statusColors[agent.status as keyof typeof statusColors] || statusColors.down

      nodes.push({
        id: `agent-${agent.id}`,
        position: { x: 400, y: agentYOffset },
        data: {
          label: `${agent.name} Agent`,
          type: 'agent',
          status: agent.status,
          details: agent
        },
        style: {
          background: colors.bg,
          border: `2px solid ${colors.border}`,
          borderRadius: '12px',
          padding: '10px 16px',
          cursor: 'pointer'
        },
      })
      agentYOffset += 100
    })

    // Add infrastructure node
    nodes.push({
      id: 'infra',
      position: { x: 700, y: 200 },
      data: {
        label: 'Infrastructure',
        type: 'infrastructure',
        details: {
          components: ['PostgreSQL', 'Qdrant', 'Temporal', 'Ollama']
        }
      },
      type: 'output',
      style: {
        background: '#fef3c7',
        border: '2px solid #f59e0b',
        borderRadius: '12px',
        padding: '10px 16px',
        cursor: 'pointer'
      },
    })

    return nodes
  }

  // Build edges connecting nodes
  const buildEdges = (): Edge[] => {
    const edges: Edge[] = []
    let edgeId = 0

    // Connect projects to agents
    projects.forEach((project) => {
      agents.slice(0, 3).forEach((agent) => {
        edges.push({
          id: `e${edgeId++}`,
          source: `project-${project.id}`,
          target: `agent-${agent.id}`,
          animated: project.status === 'build' || project.status === 'research',
          style: { stroke: '#94a3b8' }
        })
      })
    })

    // Connect agents to infrastructure
    agents.slice(0, 5).forEach((agent) => {
      edges.push({
        id: `e${edgeId++}`,
        source: `agent-${agent.id}`,
        target: 'infra',
        style: { stroke: '#cbd5e1' }
      })
    })

    return edges
  }

  const [nodes] = useNodesState(buildNodes())
  const [edges] = useEdgesState(buildEdges())

  const onNodeClick: NodeMouseHandler = useCallback((event, node) => {
    setSelectedNode(node as Node<NodeData>)
    setShowPanel(true)
  }, [])

  const closePanel = () => {
    setShowPanel(false)
    setSelectedNode(null)
  }

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'project': return <Zap className="h-4 w-4" />
      case 'agent': return <Activity className="h-4 w-4" />
      case 'infrastructure': return <Server className="h-4 w-4" />
      default: return null
    }
  }

  return (
    <div className="relative h-[600px] rounded-2xl border border-base-200 bg-white shadow-soft overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodeClick={onNodeClick}
        fitView
        className="bg-base-50"
      >
        <Background color="#cbd5e1" gap={16} />
        <Controls />
        <MiniMap
          style={{
            background: '#f8fafc',
            border: '1px solid #e2e8f0'
          }}
          nodeColor={(node) => {
            const data = node.data as NodeData
            if (data.type === 'project') return '#38bdf8'
            if (data.type === 'agent') return '#f59e0b'
            if (data.type === 'infrastructure') return '#10b981'
            return '#94a3b8'
          }}
        />
      </ReactFlow>

      {/* Side Panel */}
      {showPanel && selectedNode && (
        <div className="absolute top-0 right-0 h-full w-80 bg-white border-l border-base-200 shadow-lg z-50 overflow-y-auto">
          <div className="sticky top-0 bg-white border-b border-base-200 p-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getNodeIcon(selectedNode.data.type)}
              <h3 className="font-semibold text-base-900">{selectedNode.data.label}</h3>
            </div>
            <button
              onClick={closePanel}
              className="p-1 hover:bg-base-100 rounded-lg transition-colors"
            >
              <X className="h-5 w-5 text-base-600" />
            </button>
          </div>

          <div className="p-4 space-y-4">
            {/* Type Badge */}
            <div>
              <span className="inline-block px-2 py-1 text-xs font-medium rounded-full bg-base-100 text-base-700">
                {selectedNode.data.type.charAt(0).toUpperCase() + selectedNode.data.type.slice(1)}
              </span>
            </div>

            {/* Status */}
            {selectedNode.data.status && (
              <div>
                <div className="text-xs font-medium text-base-600 mb-1">Status</div>
                <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full ${
                  selectedNode.data.status === 'healthy' || selectedNode.data.status === 'live'
                    ? 'bg-emerald-100 text-emerald-700'
                    : selectedNode.data.status === 'degraded' || selectedNode.data.status === 'qa'
                    ? 'bg-amber-100 text-amber-700'
                    : selectedNode.data.status === 'build' || selectedNode.data.status === 'research'
                    ? 'bg-sky-100 text-sky-700'
                    : 'bg-rose-100 text-rose-700'
                }`}>
                  {selectedNode.data.status.toUpperCase()}
                </span>
              </div>
            )}

            {/* Details */}
            {selectedNode.data.details && (
              <div>
                <div className="text-xs font-medium text-base-600 mb-2">Details</div>
                <div className="space-y-2 text-sm">
                  {Object.entries(selectedNode.data.details).map(([key, value]) => {
                    if (key === 'id') return null
                    if (Array.isArray(value)) {
                      return (
                        <div key={key}>
                          <span className="font-medium text-base-700">{key}:</span>
                          <ul className="ml-4 mt-1 space-y-1">
                            {value.map((item, idx) => (
                              <li key={idx} className="text-base-600">• {item}</li>
                            ))}
                          </ul>
                        </div>
                      )
                    }
                    return (
                      <div key={key}>
                        <span className="font-medium text-base-700">{key}:</span>{' '}
                        <span className="text-base-600">{String(value)}</span>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="pt-4 border-t border-base-200">
              <button className="w-full rounded-xl bg-base-900 px-4 py-2 text-sm font-medium text-white hover:bg-base-800 transition-colors">
                View Details
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
