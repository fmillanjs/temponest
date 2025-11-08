"""
API endpoints for agent collaboration
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from uuid import UUID

from app.collaboration.models import (
    CollaborationRequest,
    CollaborationResponse,
    CollaborationWorkspace,
    AgentRole
)
from app.collaboration.manager import CollaborationManager


router = APIRouter(prefix="/collaboration", tags=["collaboration"])


# Dependency injection
def get_collaboration_manager() -> CollaborationManager:
    """Get collaboration manager from app state"""
    from app.main import collaboration_manager
    return collaboration_manager


def get_current_tenant_id() -> UUID:
    """Get current tenant ID from auth context"""
    # TODO: Extract from JWT token
    return UUID("00000000-0000-0000-0000-000000000000")


def get_current_user_id() -> UUID:
    """Get current user ID from auth context"""
    # TODO: Extract from JWT token
    return UUID("00000000-0000-0000-0000-000000000000")


@router.post("", response_model=CollaborationResponse, status_code=201)
async def start_collaboration(
    request: CollaborationRequest,
    manager: CollaborationManager = Depends(get_collaboration_manager),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Start a new agent collaboration session.

    This endpoint creates a multi-agent collaboration workspace where
    agents work together to accomplish a complex task.
    """
    try:
        response = await manager.start_collaboration(
            request=request,
            tenant_id=tenant_id,
            user_id=user_id
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspaces", response_model=List[CollaborationWorkspace])
async def list_workspaces(
    manager: CollaborationManager = Depends(get_collaboration_manager)
):
    """
    List all active collaboration workspaces.
    """
    return manager.list_workspaces()


@router.get("/workspaces/{workspace_id}", response_model=CollaborationWorkspace)
async def get_workspace(
    workspace_id: UUID,
    manager: CollaborationManager = Depends(get_collaboration_manager)
):
    """
    Get details of a specific collaboration workspace.
    """
    workspace = manager.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    return workspace


@router.get("/patterns")
async def list_collaboration_patterns():
    """
    List available collaboration patterns with descriptions.
    """
    return {
        "patterns": [
            {
                "name": "sequential",
                "description": "Agents execute tasks one after another in sequence",
                "use_cases": [
                    "Development pipeline (code -> test -> deploy)",
                    "Document review process",
                    "Phased project execution"
                ]
            },
            {
                "name": "parallel",
                "description": "Multiple agents work simultaneously on different aspects",
                "use_cases": [
                    "Code review from multiple perspectives",
                    "Parallel feature development",
                    "Multi-faceted analysis"
                ]
            },
            {
                "name": "iterative",
                "description": "Agents work in feedback loops, refining outputs",
                "use_cases": [
                    "Design iteration and refinement",
                    "Code optimization cycles",
                    "Quality improvement loops"
                ]
            },
            {
                "name": "hierarchical",
                "description": "Overseer agent coordinates specialist agents",
                "use_cases": [
                    "Complex project management",
                    "Adaptive task delegation",
                    "Dynamic workflow orchestration"
                ]
            }
        ]
    }


@router.post("/templates/full-stack-feature")
async def create_full_stack_feature_collaboration(
    feature_description: str,
    manager: CollaborationManager = Depends(get_collaboration_manager),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Template: Full-stack feature development collaboration.

    Coordinates Developer -> Designer -> QA -> DevOps in sequence.
    """
    request = CollaborationRequest(
        name="Full-Stack Feature Development",
        description=feature_description,
        pattern="sequential",
        agents=[
            AgentRole.DEVELOPER,
            AgentRole.DESIGNER,
            AgentRole.QA_TESTER,
            AgentRole.DEVOPS
        ],
        workflow_steps=[
            {
                "agent": "developer",
                "task": f"Implement backend and API for: {feature_description}",
                "context": {"phase": "backend"}
            },
            {
                "agent": "designer",
                "task": f"Design UI/UX for: {feature_description}",
                "context": {"phase": "frontend"}
            },
            {
                "agent": "qa_tester",
                "task": f"Create test plan and execute tests for: {feature_description}",
                "context": {"phase": "testing"}
            },
            {
                "agent": "devops",
                "task": f"Deploy and monitor: {feature_description}",
                "context": {"phase": "deployment"}
            }
        ]
    )

    response = await manager.start_collaboration(
        request=request,
        tenant_id=tenant_id,
        user_id=user_id
    )

    return response


@router.post("/templates/security-review")
async def create_security_review_collaboration(
    code_description: str,
    manager: CollaborationManager = Depends(get_collaboration_manager),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Template: Security-focused code review collaboration.

    Coordinates Security Auditor -> Developer (fixes) -> QA (validation).
    """
    request = CollaborationRequest(
        name="Security Review and Remediation",
        description=code_description,
        pattern="iterative",
        agents=[
            AgentRole.SECURITY_AUDITOR,
            AgentRole.DEVELOPER,
            AgentRole.QA_TESTER
        ],
        initial_context={
            "review_type": "security",
            "severity_threshold": "medium"
        }
    )

    response = await manager.start_collaboration(
        request=request,
        tenant_id=tenant_id,
        user_id=user_id
    )

    return response


@router.post("/templates/parallel-analysis")
async def create_parallel_analysis_collaboration(
    project_description: str,
    manager: CollaborationManager = Depends(get_collaboration_manager),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Template: Parallel analysis from multiple perspectives.

    All specialist agents analyze simultaneously:
    - Developer: Code quality and architecture
    - Security: Vulnerabilities and risks
    - Designer: UX and accessibility
    - DevOps: Deployment and scalability
    """
    request = CollaborationRequest(
        name="Multi-Perspective Project Analysis",
        description=project_description,
        pattern="parallel",
        agents=[
            AgentRole.DEVELOPER,
            AgentRole.SECURITY_AUDITOR,
            AgentRole.DESIGNER,
            AgentRole.DEVOPS
        ]
    )

    response = await manager.start_collaboration(
        request=request,
        tenant_id=tenant_id,
        user_id=user_id
    )

    return response
