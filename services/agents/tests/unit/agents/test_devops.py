"""
Unit tests for DevOps Agent.
"""

import pytest
import yaml
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from app.agents.devops import DevOpsAgent


class TestDevOpsAgent:
    """Test suite for DevOpsAgent"""

    @pytest.fixture
    def mock_rag_memory(self):
        """Create mock RAG memory"""
        mock = AsyncMock()
        mock.retrieve = AsyncMock(return_value=[
            {
                "source": "docs/k8s/deployment.yaml",
                "version": "v1.0",
                "score": 0.95,
                "content": "Example Kubernetes deployment with best practices"
            },
            {
                "source": "docs/terraform/aws.tf",
                "version": "v2.0",
                "score": 0.88,
                "content": "Terraform AWS module examples"
            }
        ])
        return mock

    @pytest.fixture
    def mock_tracer(self):
        """Create mock Langfuse tracer"""
        mock = Mock()
        mock.start_trace = Mock(return_value={"id": "trace-123"})
        mock.end_trace = Mock()
        return mock

    @pytest.fixture
    def devops_agent(self, mock_rag_memory, mock_tracer):
        """Create DevOpsAgent instance with mocked dependencies"""
        with patch('app.agents.devops.Agent'):
            agent = DevOpsAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                code_model="test-model",
                temperature=0.2,
                top_p=0.9,
                max_tokens=3072,
                seed=42
            )
            return agent

    def test_init_default_params(self, mock_rag_memory, mock_tracer):
        """Test DevOpsAgent initialization with default parameters"""
        with patch('app.agents.devops.Agent'):
            agent = DevOpsAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                code_model="test-model"
            )

            assert agent.code_model == "test-model"
            assert agent.temperature == 0.2
            assert agent.top_p == 0.9
            assert agent.max_tokens == 3072
            assert agent.seed == 42

    def test_init_custom_params(self, mock_rag_memory, mock_tracer):
        """Test DevOpsAgent initialization with custom parameters"""
        with patch('app.agents.devops.Agent'):
            agent = DevOpsAgent(
                rag_memory=mock_rag_memory,
                tracer=mock_tracer,
                code_model="custom-model",
                temperature=0.5,
                top_p=0.95,
                max_tokens=4096,
                seed=100
            )

            assert agent.code_model == "custom-model"
            assert agent.temperature == 0.5
            assert agent.top_p == 0.95
            assert agent.max_tokens == 4096
            assert agent.seed == 100

    def test_create_search_infrastructure_patterns_tool(self, devops_agent):
        """Test search infrastructure patterns tool creation"""
        tool = devops_agent._create_search_infrastructure_patterns_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    @pytest.mark.asyncio
    async def test_search_infrastructure_patterns_with_results(self, devops_agent, mock_rag_memory):
        """Test search infrastructure patterns tool returns formatted results"""
        tool = devops_agent._create_search_infrastructure_patterns_tool()

        result = await tool.func("kubernetes deployment")

        # Verify RAG was called with correct query
        mock_rag_memory.retrieve.assert_called_once_with(
            query="infrastructure pattern: kubernetes deployment",
            top_k=5,
            min_score=0.7
        )

        # Verify result format
        assert "[Infrastructure Pattern 1]" in result
        assert "[Infrastructure Pattern 2]" in result
        assert "docs/k8s/deployment.yaml" in result
        assert "v1.0" in result
        assert "0.95" in result

    @pytest.mark.asyncio
    async def test_search_infrastructure_patterns_no_results(self, devops_agent):
        """Test search infrastructure patterns tool when no results found"""
        devops_agent.rag_memory.retrieve = AsyncMock(return_value=[])
        tool = devops_agent._create_search_infrastructure_patterns_tool()

        result = await tool.func("nonexistent pattern")

        assert "No infrastructure patterns found" in result
        assert "industry best practices" in result

    def test_create_validate_k8s_manifest_tool(self, devops_agent):
        """Test validate k8s manifest tool creation"""
        tool = devops_agent._create_validate_k8s_manifest_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    def test_validate_k8s_manifest_valid_deployment(self, devops_agent):
        """Test k8s manifest validation for valid deployment"""
        tool = devops_agent._create_validate_k8s_manifest_tool()

        manifest = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: myapp:v1.0.0
        resources:
          limits:
            cpu: 500m
            memory: 512Mi
          requests:
            cpu: 250m
            memory: 256Mi
        livenessProbe:
          httpGet:
            path: /health
        readinessProbe:
          httpGet:
            path: /ready
"""

        result = tool.func(manifest)

        assert "Quality Score:" in result
        assert "No critical issues" in result or "✓" in result

    def test_validate_k8s_manifest_missing_resources(self, devops_agent):
        """Test k8s manifest validation detects missing resource limits"""
        tool = devops_agent._create_validate_k8s_manifest_tool()

        manifest = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: myapp:v1.0.0
"""

        result = tool.func(manifest)

        assert "Add resource limits and requests" in result

    def test_validate_k8s_manifest_missing_health_probes(self, devops_agent):
        """Test k8s manifest validation detects missing health probes"""
        tool = devops_agent._create_validate_k8s_manifest_tool()

        manifest = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: myapp:v1.0.0
        resources:
          limits:
            cpu: 500m
"""

        result = tool.func(manifest)

        assert "Add livenessProbe" in result
        assert "Add readinessProbe" in result

    def test_validate_k8s_manifest_latest_tag(self, devops_agent):
        """Test k8s manifest validation detects :latest tag"""
        tool = devops_agent._create_validate_k8s_manifest_tool()

        manifest = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: myapp:latest
"""

        result = tool.func(manifest)

        assert "Don't use :latest tag" in result

    def test_validate_k8s_manifest_service_missing_selector(self, devops_agent):
        """Test k8s manifest validation detects missing service selector"""
        tool = devops_agent._create_validate_k8s_manifest_tool()

        manifest = """
apiVersion: v1
kind: Service
metadata:
  name: test-service
spec:
  ports:
  - port: 80
"""

        result = tool.func(manifest)

        assert "Service missing selector" in result

    def test_validate_k8s_manifest_missing_security_context(self, devops_agent):
        """Test k8s manifest validation recommends security context"""
        tool = devops_agent._create_validate_k8s_manifest_tool()

        manifest = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: myapp:v1.0.0
"""

        result = tool.func(manifest)

        assert "Add securityContext" in result

    def test_validate_k8s_manifest_invalid_yaml(self, devops_agent):
        """Test k8s manifest validation with invalid YAML"""
        tool = devops_agent._create_validate_k8s_manifest_tool()

        manifest = "invalid: yaml: syntax: here"

        result = tool.func(manifest)

        assert "Invalid YAML syntax" in result

    def test_validate_k8s_manifest_missing_fields(self, devops_agent):
        """Test k8s manifest validation detects missing required fields"""
        tool = devops_agent._create_validate_k8s_manifest_tool()

        manifest = """
kind: Deployment
metadata:
  name: test-app
"""

        result = tool.func(manifest)

        assert "Missing apiVersion" in result

    def test_create_validate_terraform_tool(self, devops_agent):
        """Test validate terraform tool creation"""
        tool = devops_agent._create_validate_terraform_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    def test_validate_terraform_complete(self, devops_agent):
        """Test terraform validation with complete configuration"""
        tool = devops_agent._create_validate_terraform_tool()

        terraform_code = """
terraform {
  required_version = ">= 1.0"
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "us-east-1"
}

resource "aws_instance" "web" {
  ami           = var.ami_id
  instance_type = "t2.micro"
  tags = {
    Name = "WebServer"
  }
}

output "instance_id" {
  value = aws_instance.web.id
}
"""

        result = tool.func(terraform_code)

        assert "Quality Score:" in result
        assert "No critical issues" in result or "100" in result

    def test_validate_terraform_missing_provider(self, devops_agent):
        """Test terraform validation detects missing provider"""
        tool = devops_agent._create_validate_terraform_tool()

        terraform_code = """
resource "aws_instance" "web" {
  ami = "ami-12345678"
}
"""

        result = tool.func(terraform_code)

        assert "Missing provider configuration" in result

    def test_validate_terraform_recommends_variables(self, devops_agent):
        """Test terraform validation recommends variables"""
        tool = devops_agent._create_validate_terraform_tool()

        terraform_code = """
terraform {}

provider "aws" {
  region = "us-east-1"
}
"""

        result = tool.func(terraform_code)

        assert "Define variables for reusability" in result

    def test_validate_terraform_recommends_outputs(self, devops_agent):
        """Test terraform validation recommends outputs"""
        tool = devops_agent._create_validate_terraform_tool()

        terraform_code = """
terraform {}

provider "aws" {}

variable "test" {
  default = "value"
}
"""

        result = tool.func(terraform_code)

        assert "Add outputs for important resource IDs" in result

    def test_validate_terraform_sensitive_values(self, devops_agent):
        """Test terraform validation detects unsecured sensitive values"""
        tool = devops_agent._create_validate_terraform_tool()

        terraform_code = """
provider "aws" {}

variable "database_password" {
  default = "mysecret"
}
"""

        result = tool.func(terraform_code)

        assert "Sensitive values should be marked as sensitive" in result

    def test_validate_terraform_hardcoded_ip(self, devops_agent):
        """Test terraform validation detects hardcoded IP addresses"""
        tool = devops_agent._create_validate_terraform_tool()

        terraform_code = """
provider "aws" {}

resource "aws_security_group_rule" "allow_ssh" {
  cidr_blocks = ["192.168.1.100/32"]
}
"""

        result = tool.func(terraform_code)

        assert "Hardcoded IP addresses" in result

    def test_validate_terraform_hardcoded_aws_keys(self, devops_agent):
        """Test terraform validation detects hardcoded AWS keys"""
        tool = devops_agent._create_validate_terraform_tool()

        terraform_code = """
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"
}
"""

        result = tool.func(terraform_code)

        assert "Hardcoded AWS access keys" in result

    def test_validate_terraform_recommends_tags(self, devops_agent):
        """Test terraform validation recommends tags"""
        tool = devops_agent._create_validate_terraform_tool()

        terraform_code = """
provider "aws" {}

resource "aws_instance" "web" {
  ami = "ami-12345678"
}
"""

        result = tool.func(terraform_code)

        assert "Add tags/labels to resources" in result

    def test_create_generate_helm_chart_tool(self, devops_agent):
        """Test generate helm chart tool creation"""
        tool = devops_agent._create_generate_helm_chart_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    def test_generate_helm_chart_web_app(self, devops_agent):
        """Test helm chart generation for web-app"""
        tool = devops_agent._create_generate_helm_chart_tool()

        result = tool.func("myapp", "web-app")

        assert "Chart.yaml" in result
        assert "values.yaml" in result
        assert "templates/deployment.yaml" in result
        assert "myapp" in result
        assert "apiVersion: v2" in result

    def test_generate_helm_chart_unknown_type(self, devops_agent):
        """Test helm chart generation with unknown chart type"""
        tool = devops_agent._create_generate_helm_chart_tool()

        result = tool.func("myapp", "unknown-type")

        assert "Unknown chart type" in result

    def test_create_optimize_docker_tool(self, devops_agent):
        """Test optimize dockerfile tool creation"""
        tool = devops_agent._create_optimize_docker_tool()

        assert tool is not None
        assert hasattr(tool, 'func')

    def test_optimize_dockerfile_recommends_multistage(self, devops_agent):
        """Test dockerfile optimization recommends multi-stage build"""
        tool = devops_agent._create_optimize_docker_tool()

        dockerfile = """
FROM node:16
WORKDIR /app
COPY . .
RUN npm install
CMD ["npm", "start"]
"""

        result = tool.func(dockerfile)

        assert "multi-stage build" in result

    def test_optimize_dockerfile_recommends_alpine(self, devops_agent):
        """Test dockerfile optimization recommends alpine base"""
        tool = devops_agent._create_optimize_docker_tool()

        dockerfile = """
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y python3
"""

        result = tool.func(dockerfile)

        assert "alpine or distroless" in result

    def test_optimize_dockerfile_security_non_root_user(self, devops_agent):
        """Test dockerfile optimization detects missing non-root user"""
        tool = devops_agent._create_optimize_docker_tool()

        dockerfile = """
FROM node:16-alpine
WORKDIR /app
COPY . .
"""

        result = tool.func(dockerfile)

        assert "Run container as non-root user" in result

    def test_optimize_dockerfile_security_root_user(self, devops_agent):
        """Test dockerfile optimization detects explicit root user"""
        tool = devops_agent._create_optimize_docker_tool()

        dockerfile = """
FROM node:16-alpine
USER root
"""

        result = tool.func(dockerfile)

        assert "Run container as non-root user" in result

    def test_optimize_dockerfile_apt_get_combining(self, devops_agent):
        """Test dockerfile optimization recommends combining apt-get"""
        tool = devops_agent._create_optimize_docker_tool()

        dockerfile = """
FROM ubuntu:20.04
RUN apt-get update
RUN apt-get install -y python3
"""

        result = tool.func(dockerfile)

        assert "Combine apt-get update && install" in result

    def test_optimize_dockerfile_layer_reduction(self, devops_agent):
        """Test dockerfile optimization recommends reducing layers"""
        tool = devops_agent._create_optimize_docker_tool()

        dockerfile = """
FROM node:16
RUN npm install -g yarn
RUN npm install -g webpack
RUN npm install -g babel
RUN npm install -g eslint
RUN npm install -g prettier
RUN npm install -g jest
"""

        result = tool.func(dockerfile)

        assert "Reduce layers" in result
        assert "RUN commands" in result

    def test_optimize_dockerfile_caching_optimization(self, devops_agent):
        """Test dockerfile optimization recommends better caching"""
        tool = devops_agent._create_optimize_docker_tool()

        dockerfile = """
FROM node:16
COPY . /app
RUN npm install
"""

        result = tool.func(dockerfile)

        assert "Copy dependency files before full COPY for better caching" in result

    def test_optimize_dockerfile_recommends_dockerignore(self, devops_agent):
        """Test dockerfile optimization recommends .dockerignore"""
        tool = devops_agent._create_optimize_docker_tool()

        dockerfile = """
FROM node:16
COPY . .
"""

        result = tool.func(dockerfile)

        assert "Add .dockerignore" in result

    @pytest.mark.asyncio
    async def test_execute_success_kubernetes(self, mock_rag_memory, mock_tracer):
        """Test successful devops agent execution for Kubernetes"""
        with patch('app.agents.devops.Agent'):
            with patch('app.agents.devops.Crew') as mock_crew_class:
                with patch('app.agents.devops.Task'):
                    devops_agent = DevOpsAgent(
                        rag_memory=mock_rag_memory,
                        tracer=mock_tracer,
                        code_model="test-model"
                    )

                    mock_crew = MagicMock()
                    mock_crew.kickoff_async = AsyncMock(return_value='''
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
spec:
  replicas: 3
```

[Infrastructure Pattern 1] k8s/deployment.yaml (v1.0)
[Infrastructure Pattern 2] k8s/service.yaml (v1.1)
''')
                    mock_crew_class.return_value = mock_crew

                    result = await devops_agent.execute(
                        task="Create Kubernetes deployment",
                        context={"app": "myapp"},
                        task_id="task-123"
                    )

                    assert "infrastructure_code" in result
                    assert "validation" in result
                    assert "deployment_instructions" in result
                    assert "citations" in result
                    assert "code_type" in result
                    assert "best_practices" in result
                    assert "execution_time_ms" in result

                    assert result["code_type"] == "kubernetes"
                    assert len(result["citations"]) == 2

                    mock_tracer.start_trace.assert_called_once()
                    mock_tracer.end_trace.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_success_terraform(self, mock_rag_memory, mock_tracer):
        """Test successful devops agent execution for Terraform"""
        with patch('app.agents.devops.Agent'):
            with patch('app.agents.devops.Crew') as mock_crew_class:
                with patch('app.agents.devops.Task'):
                    devops_agent = DevOpsAgent(
                        rag_memory=mock_rag_memory,
                        tracer=mock_tracer,
                        code_model="test-model"
                    )

                    mock_crew = MagicMock()
                    mock_crew.kickoff_async = AsyncMock(return_value='''
```hcl
provider "aws" {
  region = var.region
}

resource "aws_instance" "web" {
  ami = "ami-12345678"
}
```
''')
                    mock_crew_class.return_value = mock_crew

                    result = await devops_agent.execute(
                        task="Create terraform configuration",
                        context={},
                        task_id="task-tf"
                    )

                    assert result["code_type"] == "terraform"

    @pytest.mark.asyncio
    async def test_execute_success_dockerfile(self, mock_rag_memory, mock_tracer):
        """Test successful devops agent execution for Dockerfile"""
        with patch('app.agents.devops.Agent'):
            with patch('app.agents.devops.Crew') as mock_crew_class:
                with patch('app.agents.devops.Task'):
                    devops_agent = DevOpsAgent(
                        rag_memory=mock_rag_memory,
                        tracer=mock_tracer,
                        code_model="test-model"
                    )

                    mock_crew = MagicMock()
                    mock_crew.kickoff_async = AsyncMock(return_value='''
```dockerfile
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
```
''')
                    mock_crew_class.return_value = mock_crew

                    result = await devops_agent.execute(
                        task="Optimize Dockerfile",
                        context={},
                        task_id="task-docker"
                    )

                    assert result["code_type"] == "dockerfile"

    @pytest.mark.asyncio
    async def test_execute_error_handling(self, mock_rag_memory, mock_tracer):
        """Test error handling during execution"""
        with patch('app.agents.devops.Agent'):
            with patch('app.agents.devops.Crew') as mock_crew_class:
                with patch('app.agents.devops.Task'):
                    devops_agent = DevOpsAgent(
                        rag_memory=mock_rag_memory,
                        tracer=mock_tracer,
                        code_model="test-model"
                    )

                    mock_crew = MagicMock()
                    mock_crew.kickoff_async = AsyncMock(side_effect=Exception("Crew failure"))
                    mock_crew_class.return_value = mock_crew

                    with pytest.raises(Exception) as exc_info:
                        await devops_agent.execute(
                            task="Generate infrastructure",
                            context={},
                            task_id="task-error"
                        )

                    assert "Crew failure" in str(exc_info.value)

                    mock_tracer.end_trace.assert_called_once()
                    end_trace_call = mock_tracer.end_trace.call_args
                    assert "error" in end_trace_call[1]["output"]

    def test_extract_citations(self, devops_agent):
        """Test citation extraction from result text"""
        result_text = """
[Infrastructure Pattern 1] k8s/deployment.yaml (v1.0)
[Infrastructure Pattern 2] terraform/aws.tf (v2.1)
[Citation 3] docker/multistage.dockerfile (v3.0)
"""

        citations = devops_agent._extract_citations(result_text)

        assert len(citations) == 3
        assert citations[0]["source"] == "k8s/deployment.yaml"
        assert citations[0]["version"] == "1.0"
        assert citations[1]["source"] == "terraform/aws.tf"
        assert citations[1]["version"] == "2.1"

    def test_extract_citations_limit(self, devops_agent):
        """Test citation extraction limits to 5 citations"""
        result_text = """
[Infrastructure Pattern 1] doc1 (v1.0)
[Infrastructure Pattern 2] doc2 (v1.0)
[Infrastructure Pattern 3] doc3 (v1.0)
[Infrastructure Pattern 4] doc4 (v1.0)
[Infrastructure Pattern 5] doc5 (v1.0)
[Infrastructure Pattern 6] doc6 (v1.0)
[Infrastructure Pattern 7] doc7 (v1.0)
"""

        citations = devops_agent._extract_citations(result_text)

        assert len(citations) == 5

    def test_extract_citations_none_found(self, devops_agent):
        """Test citation extraction when no citations in result"""
        result_text = "Just some text without citations"

        citations = devops_agent._extract_citations(result_text)

        assert len(citations) == 0
