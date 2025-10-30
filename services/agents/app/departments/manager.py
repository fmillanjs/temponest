"""
Department Manager - Dynamic organizational structure management.

Loads department configurations from YAML files and creates agents dynamically.
Supports hierarchical departments (parent/child relationships).
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from llm.unified_client import UnifiedLLMClient
from memory.rag import RAGMemory
from memory.langfuse_tracer import LangfuseTracer


@dataclass
class AgentConfig:
    """Agent configuration from department YAML"""
    id: str
    name: str
    role: str
    provider: str
    model: str
    temperature: float
    responsibilities: List[str]
    tools: List[str]
    department_id: str


@dataclass
class WorkflowConfig:
    """Workflow configuration"""
    id: str
    name: str
    description: str
    trigger: str
    risk_level: str
    steps: List[Dict[str, Any]]
    department_id: str


@dataclass
class Department:
    """Department configuration"""
    id: str
    name: str
    description: str
    parent: Optional[str]
    budget: Dict[str, int]
    agents: List[AgentConfig] = field(default_factory=list)
    sub_departments: List[str] = field(default_factory=list)
    workflows: List[WorkflowConfig] = field(default_factory=list)
    integrations: List[Dict[str, Any]] = field(default_factory=list)

    def get_full_path(self) -> str:
        """Get full hierarchical path (e.g., marketing.video_production)"""
        if self.parent:
            return f"{self.parent}.{self.id}"
        return self.id


class DepartmentManager:
    """
    Manages organizational structure and creates agents dynamically.

    Usage:
        manager = DepartmentManager(config_dir="config/departments")
        await manager.load_all_departments()

        # Get agent by path
        agent = manager.get_agent("marketing.video_production.video_producer")

        # Execute workflow
        result = await manager.execute_workflow("marketing.campaign_launch", {...})
    """

    def __init__(
        self,
        config_dir: str,
        rag_memory: RAGMemory,
        tracer: LangfuseTracer
    ):
        self.config_dir = Path(config_dir)
        self.rag_memory = rag_memory
        self.tracer = tracer

        # Storage
        self.departments: Dict[str, Department] = {}
        self.agents: Dict[str, Any] = {}  # agent_path -> agent instance
        self.workflows: Dict[str, WorkflowConfig] = {}

    async def load_all_departments(self):
        """Load all department configurations from YAML files"""
        print(f"📂 Loading departments from {self.config_dir}")

        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
            print(f"⚠️  No departments directory found. Created {self.config_dir}")
            return

        # Load all YAML files
        yaml_files = list(self.config_dir.glob("*.yaml")) + list(self.config_dir.glob("*.yml"))

        if not yaml_files:
            print(f"⚠️  No department configurations found in {self.config_dir}")
            return

        # First pass: Load department configs
        for yaml_file in yaml_files:
            await self._load_department_file(yaml_file)

        # Second pass: Create agents
        for dept_id, dept in self.departments.items():
            await self._create_department_agents(dept)

        print(f"✅ Loaded {len(self.departments)} departments, {len(self.agents)} agents")

    async def _load_department_file(self, yaml_file: Path):
        """Load a single department YAML file"""
        try:
            with open(yaml_file, 'r') as f:
                config = yaml.safe_load(f)

            dept_config = config.get('department', {})

            # Create department
            department = Department(
                id=dept_config['id'],
                name=dept_config['name'],
                description=dept_config.get('description', ''),
                parent=dept_config.get('parent'),
                budget=dept_config.get('budget', {}),
                sub_departments=dept_config.get('sub_departments', []),
                integrations=dept_config.get('integrations', [])
            )

            # Parse agents
            for agent_config in dept_config.get('agents', []):
                agent = AgentConfig(
                    id=agent_config['id'],
                    name=agent_config['name'],
                    role=agent_config['role'],
                    provider=agent_config.get('provider', 'ollama'),
                    model=agent_config['model'],
                    temperature=agent_config.get('temperature', 0.2),
                    responsibilities=agent_config.get('responsibilities', []),
                    tools=agent_config.get('tools', []),
                    department_id=department.id
                )
                department.agents.append(agent)

            # Parse workflows
            for workflow_config in dept_config.get('workflows', []):
                workflow = WorkflowConfig(
                    id=workflow_config['id'],
                    name=workflow_config['name'],
                    description=workflow_config.get('description', ''),
                    trigger=workflow_config.get('trigger', 'manual'),
                    risk_level=workflow_config.get('risk_level', 'medium'),
                    steps=workflow_config.get('steps', []),
                    department_id=department.id
                )
                department.workflows.append(workflow)

                # Register workflow
                workflow_path = f"{department.get_full_path()}.{workflow.id}"
                self.workflows[workflow_path] = workflow

            # Register department
            self.departments[department.id] = department
            print(f"   📋 Loaded department: {department.name} ({department.id})")

        except Exception as e:
            print(f"❌ Error loading {yaml_file}: {e}")

    async def _create_department_agents(self, department: Department):
        """Create agent instances for a department"""
        for agent_config in department.agents:
            try:
                # Create LLM client
                llm_client = self._create_llm_client(agent_config)

                # Create agent instance (simplified for now)
                agent = DynamicAgent(
                    config=agent_config,
                    llm_client=llm_client,
                    rag_memory=self.rag_memory,
                    tracer=self.tracer
                )

                # Register agent
                agent_path = f"{department.get_full_path()}.{agent_config.id}"
                self.agents[agent_path] = agent

                print(f"      ✅ Created agent: {agent_config.name} ({agent_path})")

            except Exception as e:
                print(f"      ❌ Error creating agent {agent_config.id}: {e}")

    def _create_llm_client(self, agent_config: AgentConfig) -> UnifiedLLMClient:
        """Create LLM client based on agent configuration"""
        # Import settings
        from settings import settings

        if agent_config.provider == "claude":
            return UnifiedLLMClient(
                provider="claude",
                model=agent_config.model,
                temperature=agent_config.temperature,
                claude_auth_url=settings.CLAUDE_AUTH_URL,
                claude_session_token=settings.CLAUDE_SESSION_TOKEN,
                claude_api_url=settings.CLAUDE_API_URL
            )
        elif agent_config.provider == "openai":
            return UnifiedLLMClient(
                provider="openai",
                model=agent_config.model,
                temperature=agent_config.temperature,
                openai_api_key=settings.OPENAI_API_KEY,
                openai_base_url=settings.OPENAI_BASE_URL
            )
        else:  # ollama
            return UnifiedLLMClient(
                provider="ollama",
                model=agent_config.model,
                temperature=agent_config.temperature,
                ollama_base_url=settings.OLLAMA_BASE_URL
            )

    def get_agent(self, agent_path: str) -> Optional[Any]:
        """
        Get agent by full path.

        Examples:
            marketing.marketing_strategist
            marketing.video_production.video_producer
        """
        return self.agents.get(agent_path)

    def get_department(self, department_id: str) -> Optional[Department]:
        """Get department by ID"""
        return self.departments.get(department_id)

    def list_departments(self) -> List[Department]:
        """List all departments"""
        return list(self.departments.values())

    def list_agents(self, department_id: Optional[str] = None) -> List[str]:
        """List all agents, optionally filtered by department"""
        if department_id:
            return [
                path for path in self.agents.keys()
                if path.startswith(f"{department_id}.")
            ]
        return list(self.agents.keys())

    def get_workflow(self, workflow_path: str) -> Optional[WorkflowConfig]:
        """
        Get workflow by full path.

        Examples:
            marketing.campaign_launch
            marketing.video_production.create_marketing_video
        """
        return self.workflows.get(workflow_path)

    async def execute_workflow(
        self,
        workflow_path: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a department workflow"""
        workflow = self.get_workflow(workflow_path)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_path}")

        print(f"🔄 Executing workflow: {workflow.name}")

        results = []
        for step in workflow.steps:
            agent_path = step['agent']
            task = step['task']
            approval_required = step.get('approval_required', False)

            print(f"   → Step: {task} (agent: {agent_path})")

            # Get agent
            agent = self.get_agent(agent_path)
            if not agent:
                raise ValueError(f"Agent not found: {agent_path}")

            # Execute agent task
            result = await agent.execute(task, context)

            # Check if approval required
            if approval_required:
                # TODO: Integrate with approval system
                print(f"      ⚠️  Approval required (not implemented yet)")

            results.append({
                "step": task,
                "agent": agent_path,
                "result": result
            })

        return {
            "workflow": workflow.name,
            "status": "completed",
            "steps_completed": len(results),
            "results": results
        }


class DynamicAgent:
    """Simplified agent that executes tasks using LLM client"""

    def __init__(
        self,
        config: AgentConfig,
        llm_client: UnifiedLLMClient,
        rag_memory: RAGMemory,
        tracer: LangfuseTracer
    ):
        self.config = config
        self.llm = llm_client
        self.rag_memory = rag_memory
        self.tracer = tracer

    async def execute(
        self,
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a task"""
        # Retrieve relevant knowledge
        citations = await self.rag_memory.retrieve(
            query=task,
            top_k=3,
            min_score=0.7
        )

        # Build system prompt with role and responsibilities
        system_prompt = self._build_system_prompt()

        # Build user prompt with task and context
        user_prompt = self._build_user_prompt(task, context, citations)

        # Call LLM
        response = await self.llm.complete(
            prompt=user_prompt,
            system=system_prompt
        )

        return {
            "text": response["text"],
            "citations": citations,
            "agent": self.config.name,
            "department": self.config.department_id
        }

    def _build_system_prompt(self) -> str:
        """Build system prompt from agent config"""
        responsibilities = "\n".join(f"- {r}" for r in self.config.responsibilities)
        return f"""You are {self.config.name}, a {self.config.role}.

Your responsibilities:
{responsibilities}

Provide professional, actionable output that aligns with your role and responsibilities."""

    def _build_user_prompt(
        self,
        task: str,
        context: Dict[str, Any],
        citations: List[Dict[str, Any]]
    ) -> str:
        """Build user prompt with task and RAG context"""
        import json

        context_str = json.dumps(context, indent=2) if context else "No additional context"

        citations_str = ""
        if citations:
            for i, cit in enumerate(citations[:3], 1):
                citations_str += f"\n[Reference {i}] {cit['source']}: {cit['content'][:200]}..."

        return f"""Task: {task}

Context:
{context_str}

Relevant Documentation:
{citations_str if citations_str else "No relevant documentation found."}

Please complete this task according to your role and responsibilities."""
