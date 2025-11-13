"""
Department Management API

Endpoints to:
- List departments
- View department structure
- Execute department workflows
- Add/edit department configurations
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import sys
import os

from shared.auth import AuthContext, require_permission, require_any_permission

router = APIRouter(prefix="/departments", tags=["departments"])

# Global department manager (injected from main.py)
_department_manager = None


def set_department_manager(manager):
    """Set global department manager instance"""
    global _department_manager
    _department_manager = manager


class WorkflowExecutionRequest(BaseModel):
    """Request to execute a department workflow"""
    workflow_path: str
    context: Dict[str, Any] = {}


class AgentTaskRequest(BaseModel):
    """Request to execute a task with a specific agent"""
    agent_path: str
    task: str
    context: Dict[str, Any] = {}


@router.get("/")
async def list_departments(
    current_user: AuthContext = Depends(require_permission("departments:read"))
):
    """
    List all departments.

    Requires: departments:read permission
    """
    if not _department_manager:
        raise HTTPException(status_code=503, detail="Department manager not initialized")

    departments = _department_manager.list_departments()

    return {
        "total": len(departments),
        "departments": [
            {
                "id": dept.id,
                "name": dept.name,
                "description": dept.description,
                "parent": dept.parent,
                "full_path": dept.get_full_path(),
                "agents_count": len(dept.agents),
                "workflows_count": len(dept.workflows),
                "sub_departments": dept.sub_departments
            }
            for dept in departments
        ]
    }


@router.get("/{department_id}")
async def get_department(
    department_id: str,
    current_user: AuthContext = Depends(require_permission("departments:read"))
):
    """
    Get department details.

    Requires: departments:read permission
    """
    if not _department_manager:
        raise HTTPException(status_code=503, detail="Department manager not initialized")

    dept = _department_manager.get_department(department_id)
    if not dept:
        raise HTTPException(status_code=404, detail=f"Department not found: {department_id}")

    return {
        "id": dept.id,
        "name": dept.name,
        "description": dept.description,
        "parent": dept.parent,
        "full_path": dept.get_full_path(),
        "budget": dept.budget,
        "agents": [
            {
                "id": agent.id,
                "name": agent.name,
                "role": agent.role,
                "provider": agent.provider,
                "model": agent.model,
                "responsibilities": agent.responsibilities
            }
            for agent in dept.agents
        ],
        "workflows": [
            {
                "id": workflow.id,
                "name": workflow.name,
                "description": workflow.description,
                "risk_level": workflow.risk_level,
                "steps_count": len(workflow.steps)
            }
            for workflow in dept.workflows
        ],
        "sub_departments": dept.sub_departments
    }


@router.get("/{department_id}/agents")
async def list_department_agents(
    department_id: str,
    current_user: AuthContext = Depends(require_permission("departments:read"))
):
    """
    List all agents in a department.

    Requires: departments:read permission
    """
    if not _department_manager:
        raise HTTPException(status_code=503, detail="Department manager not initialized")

    agents = _department_manager.list_agents(department_id)

    return {
        "department": department_id,
        "total": len(agents),
        "agents": agents
    }


@router.get("/workflows/all")
async def list_all_workflows(
    current_user: AuthContext = Depends(require_permission("workflows:read"))
):
    """
    List all workflows across all departments.

    Requires: workflows:read permission
    """
    if not _department_manager:
        raise HTTPException(status_code=503, detail="Department manager not initialized")

    workflows = []
    for dept in _department_manager.list_departments():
        for workflow in dept.workflows:
            workflows.append({
                "path": f"{dept.get_full_path()}.{workflow.id}",
                "name": workflow.name,
                "description": workflow.description,
                "department": dept.name,
                "risk_level": workflow.risk_level,
                "steps_count": len(workflow.steps)
            })

    return {
        "total": len(workflows),
        "workflows": workflows
    }


@router.post("/workflows/execute")
async def execute_workflow(
    request: WorkflowExecutionRequest,
    current_user: AuthContext = Depends(require_permission("workflows:create"))
):
    """
    Execute a department workflow.

    Requires: workflows:create permission
    """
    if not _department_manager:
        raise HTTPException(status_code=503, detail="Department manager not initialized")

    try:
        result = await _department_manager.execute_workflow(
            workflow_path=request.workflow_path,
            context=request.context
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@router.post("/agents/execute")
async def execute_agent_task(
    request: AgentTaskRequest,
    current_user: AuthContext = Depends(require_permission("agents:execute"))
):
    """
    Execute a task with a specific agent.

    Requires: agents:execute permission
    """
    if not _department_manager:
        raise HTTPException(status_code=503, detail="Department manager not initialized")

    agent = _department_manager.get_agent(request.agent_path)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent not found: {request.agent_path}")

    try:
        result = await agent.execute(
            task=request.task,
            context=request.context
        )

        return {
            "agent": request.agent_path,
            "task": request.task,
            "result": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@router.get("/structure")
async def get_org_structure(
    current_user: AuthContext = Depends(require_permission("departments:read"))
):
    """
    Get full organizational structure (hierarchical).

    Requires: departments:read permission
    """
    if not _department_manager:
        raise HTTPException(status_code=503, detail="Department manager not initialized")

    departments = _department_manager.list_departments()

    # Build hierarchical structure
    def build_tree(parent_id: Optional[str] = None):
        return [
            {
                "id": dept.id,
                "name": dept.name,
                "description": dept.description,
                "agents_count": len(dept.agents),
                "workflows_count": len(dept.workflows),
                "children": build_tree(dept.id) if dept.sub_departments else []
            }
            for dept in departments
            if dept.parent == parent_id
        ]

    return {
        "organization": build_tree(None)
    }
