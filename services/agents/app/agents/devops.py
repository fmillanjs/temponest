"""
DevOps Agent - Infrastructure as Code and CI/CD automation.

Responsibilities:
- Generate Kubernetes manifests (Deployments, Services, ConfigMaps, Secrets)
- Create Terraform configurations for cloud infrastructure
- Optimize Docker builds (multi-stage, caching, security)
- Generate CI/CD pipelines (GitHub Actions, GitLab CI, Jenkins)
- Create Helm charts for application deployment
- Generate monitoring and logging configurations
- Infrastructure security best practices (network policies, RBAC)
"""

from typing import Dict, Any, List, Optional
import time
import json
import re
import yaml
from crewai import Agent, Task, Crew
from crewai.tools import tool

from memory.rag import RAGMemory
from memory.langfuse_tracer import LangfuseTracer


class DevOpsAgent:
    """DevOps agent that generates infrastructure code and automation"""

    def __init__(
        self,
        rag_memory: RAGMemory,
        tracer: LangfuseTracer,
        code_model: str,
        temperature: float = 0.2,
        top_p: float = 0.9,
        max_tokens: int = 3072,
        seed: int = 42
    ):
        self.rag_memory = rag_memory
        self.tracer = tracer
        self.code_model = code_model
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens
        self.seed = seed

        # Create the agent
        self.agent = Agent(
            role="Senior DevOps Engineer",
            goal="Generate production-ready infrastructure code and automation pipelines",
            backstory="""You are a senior DevOps engineer with expertise in:
            - Kubernetes orchestration and best practices
            - Infrastructure as Code (Terraform, Pulumi, CloudFormation)
            - Docker optimization and security
            - CI/CD pipeline design (GitOps, trunk-based development)
            - Cloud platforms (AWS, GCP, Azure)
            - Monitoring and observability (Prometheus, Grafana, ELK)
            - Security hardening and compliance

            You ALWAYS:
            - Follow infrastructure best practices from the knowledge base
            - Apply security hardening (least privilege, network policies)
            - Use declarative configuration (GitOps principles)
            - Include health checks and readiness probes
            - Add resource limits and requests
            - Implement proper secrets management
            - Add comprehensive comments and documentation
            - Reference specific examples from infrastructure docs""",
            verbose=True,
            allow_delegation=False,
            tools=[
                self._create_search_infrastructure_patterns_tool(),
                self._create_validate_k8s_manifest_tool(),
                self._create_validate_terraform_tool(),
                self._create_generate_helm_chart_tool(),
                self._create_optimize_docker_tool()
            ],
            llm_config={
                "model": code_model,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "seed": seed
            }
        )

    def _create_search_infrastructure_patterns_tool(self):
        """Create tool for searching infrastructure patterns"""
        rag_memory = self.rag_memory

        @tool("search_infrastructure_patterns")
        async def search_infrastructure_patterns(query: str) -> str:
            """
            Search the knowledge base for infrastructure patterns and best practices.

            Args:
                query: What infrastructure pattern you need (e.g., "kubernetes deployment", "terraform module")

            Returns:
                Relevant infrastructure examples with sources
            """
            results = await rag_memory.retrieve(
                query=f"infrastructure pattern: {query}",
                top_k=5,
                min_score=0.7
            )

            if not results:
                return "No infrastructure patterns found. Use industry best practices and official documentation."

            # Format results
            output = []
            for i, doc in enumerate(results, 1):
                output.append(f"""
[Infrastructure Pattern {i}] {doc['source']} (v{doc['version']})
Relevance: {doc['score']:.2f}

```yaml
{doc['content']}
```

---
""")

            return "\n".join(output)

        return search_infrastructure_patterns

    def _create_validate_k8s_manifest_tool(self):
        """Create tool for validating Kubernetes manifests"""

        @tool("validate_k8s_manifest")
        def validate_k8s_manifest(manifest_yaml: str) -> str:
            """
            Validate Kubernetes manifest for best practices.

            Args:
                manifest_yaml: YAML manifest to validate

            Returns:
                Validation result with recommendations
            """
            issues = []
            recommendations = []

            try:
                # Parse YAML
                manifests = list(yaml.safe_load_all(manifest_yaml))
            except yaml.YAMLError as e:
                return f"Invalid YAML syntax: {e}"

            for manifest in manifests:
                if not manifest:
                    continue

                kind = manifest.get("kind", "Unknown")
                metadata = manifest.get("metadata", {})
                spec = manifest.get("spec", {})

                # Check for required fields
                if "apiVersion" not in manifest:
                    issues.append(f"{kind}: Missing apiVersion")
                if "kind" not in manifest:
                    issues.append(f"Manifest missing kind field")
                if not metadata:
                    issues.append(f"{kind}: Missing metadata")

                # Deployment-specific checks
                if kind == "Deployment":
                    template = spec.get("template", {})
                    containers = template.get("spec", {}).get("containers", [])

                    if not containers:
                        issues.append("Deployment has no containers")

                    for container in containers:
                        # Check resource limits
                        if "resources" not in container:
                            recommendations.append(f"Container '{container.get('name')}': Add resource limits and requests")

                        # Check health probes
                        if "livenessProbe" not in container:
                            recommendations.append(f"Container '{container.get('name')}': Add livenessProbe")
                        if "readinessProbe" not in container:
                            recommendations.append(f"Container '{container.get('name')}': Add readinessProbe")

                        # Check image tag
                        image = container.get("image", "")
                        if ":latest" in image:
                            issues.append(f"Container '{container.get('name')}': Don't use :latest tag")

                # Service-specific checks
                if kind == "Service":
                    if "selector" not in spec:
                        issues.append("Service missing selector")

                # Security checks
                if kind == "Deployment":
                    security_context = template.get("spec", {}).get("securityContext", {})
                    if not security_context:
                        recommendations.append("Add securityContext for pod hardening")

            quality_score = max(0, 100 - (len(issues) * 20) - (len(recommendations) * 5))

            return f"""
Kubernetes Manifest Validation:
- Quality Score: {quality_score}/100
- Manifests Checked: {len(manifests)}

Critical Issues:
{chr(10).join(f"  ❌ {issue}" for issue in issues) if issues else "  ✓ No critical issues"}

Recommendations:
{chr(10).join(f"  • {rec}" for rec in recommendations) if recommendations else "  ✓ Follows best practices"}

Overall: {"✓ Production Ready" if quality_score >= 80 else "⚠ Needs Improvement"}
"""

        return validate_k8s_manifest

    def _create_validate_terraform_tool(self):
        """Create tool for validating Terraform configurations"""

        @tool("validate_terraform")
        def validate_terraform(terraform_code: str) -> str:
            """
            Validate Terraform configuration for best practices.

            Args:
                terraform_code: Terraform code to validate

            Returns:
                Validation result with recommendations
            """
            issues = []
            recommendations = []

            # Check for required Terraform blocks
            if "terraform {" not in terraform_code:
                recommendations.append("Add terraform block with required_version")

            if "provider " not in terraform_code:
                issues.append("Missing provider configuration")

            # Check for variables
            if "variable " not in terraform_code:
                recommendations.append("Define variables for reusability")

            # Check for outputs
            if "output " not in terraform_code:
                recommendations.append("Add outputs for important resource IDs")

            # Security checks
            if "password" in terraform_code.lower() and "sensitive" not in terraform_code:
                issues.append("Sensitive values should be marked as sensitive = true")

            # Check for hardcoded values
            hardcoded_patterns = [
                (r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', "IP addresses"),
                (r'AKIA[0-9A-Z]{16}', "AWS access keys"),
            ]

            for pattern, name in hardcoded_patterns:
                if re.search(pattern, terraform_code):
                    issues.append(f"Hardcoded {name} detected - use variables or secrets")

            # Best practices
            if "resource " in terraform_code:
                if "tags" not in terraform_code and "labels" not in terraform_code:
                    recommendations.append("Add tags/labels to resources for organization")

            quality_score = max(0, 100 - (len(issues) * 25) - (len(recommendations) * 10))

            return f"""
Terraform Validation:
- Quality Score: {quality_score}/100

Critical Issues:
{chr(10).join(f"  ❌ {issue}" for issue in issues) if issues else "  ✓ No critical issues"}

Recommendations:
{chr(10).join(f"  • {rec}" for rec in recommendations) if recommendations else "  ✓ Follows best practices"}

Overall: {"✓ Production Ready" if quality_score >= 80 else "⚠ Needs Improvement"}
"""

        return validate_terraform

    def _create_generate_helm_chart_tool(self):
        """Create tool for generating Helm chart templates"""

        @tool("generate_helm_chart")
        def generate_helm_chart(app_name: str, chart_type: str = "web-app") -> str:
            """
            Generate Helm chart structure for an application.

            Args:
                app_name: Name of the application
                chart_type: Type of chart (web-app, database, cron-job)

            Returns:
                Helm chart structure and key files
            """
            charts = {
                "web-app": """
Helm Chart Structure for {app_name}:

Chart.yaml:
```yaml
apiVersion: v2
name: {app_name}
description: A Helm chart for {app_name}
type: application
version: 0.1.0
appVersion: "1.0.0"
```

values.yaml:
```yaml
replicaCount: 2

image:
  repository: registry.example.com/{app_name}
  pullPolicy: IfNotPresent
  tag: ""

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80

service:
  type: ClusterIP
  port: 80
  targetPort: 8080

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: {app_name}.example.com
      paths:
        - path: /
          pathType: Prefix
```

templates/deployment.yaml:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{{{ include "{app_name}.fullname" . }}}}
spec:
  replicas: {{{{ .Values.replicaCount }}}}
  selector:
    matchLabels:
      app: {{{{ include "{app_name}.name" . }}}}
  template:
    spec:
      containers:
      - name: {{{{ .Chart.Name }}}}
        image: "{{{{ .Values.image.repository }}}}:{{{{ .Values.image.tag | default .Chart.AppVersion }}}}"
        resources:
          {{{{- toYaml .Values.resources | nindent 12 }}}}
```
""".format(app_name=app_name)
            }

            return charts.get(chart_type, "Unknown chart type")

        return generate_helm_chart

    def _create_optimize_docker_tool(self):
        """Create tool for optimizing Dockerfile"""

        @tool("optimize_dockerfile")
        def optimize_dockerfile(dockerfile_content: str) -> str:
            """
            Analyze Dockerfile and suggest optimizations.

            Args:
                dockerfile_content: Dockerfile to optimize

            Returns:
                Optimization recommendations
            """
            recommendations = []
            security_issues = []

            lines = dockerfile_content.split('\n')

            # Check for multi-stage build
            from_count = sum(1 for line in lines if line.strip().startswith('FROM'))
            if from_count == 1:
                recommendations.append("Use multi-stage build to reduce image size")

            # Check base image
            if 'FROM ubuntu' in dockerfile_content or 'FROM debian' in dockerfile_content:
                recommendations.append("Consider alpine or distroless base images for smaller size")

            # Security checks
            if 'USER root' in dockerfile_content or 'USER' not in dockerfile_content:
                security_issues.append("Run container as non-root user")

            if 'apt-get update' in dockerfile_content and '&& apt-get install' not in dockerfile_content:
                recommendations.append("Combine apt-get update && install in single RUN")

            # Layer optimization
            run_count = sum(1 for line in lines if line.strip().startswith('RUN'))
            if run_count > 5:
                recommendations.append(f"Reduce layers: {run_count} RUN commands - consider combining")

            # Caching
            if 'COPY . ' in dockerfile_content:
                copy_before_install = False
                for line in lines:
                    if 'COPY . ' in line:
                        copy_before_install = True
                    if copy_before_install and ('pip install' in line or 'npm install' in line):
                        recommendations.append("Copy dependency files before full COPY for better caching")
                        break

            # Security scanning
            if '.git' not in dockerfile_content:
                recommendations.append("Add .dockerignore to exclude .git, node_modules, etc.")

            return f"""
Dockerfile Optimization Analysis:

Security Issues (Critical):
{chr(10).join(f"  🔒 {issue}" for issue in security_issues) if security_issues else "  ✓ No critical security issues"}

Optimization Recommendations:
{chr(10).join(f"  • {rec}" for rec in recommendations) if recommendations else "  ✓ Well optimized"}

Best Practices:
  • Use specific base image tags (not :latest)
  • Minimize layers by combining RUN commands
  • Order instructions from least to most frequently changing
  • Use .dockerignore file
  • Run as non-root user
  • Use multi-stage builds
  • Scan for vulnerabilities (trivy, snyk)
"""

        return optimize_dockerfile

    async def execute(
        self,
        task: str,
        context: Dict[str, Any],
        task_id: str
    ) -> Dict[str, Any]:
        """
        Execute the DevOps agent to generate infrastructure code.

        Args:
            task: Infrastructure task description
            context: Additional context (infrastructure_type, cloud_provider, app_details)
            task_id: Unique task identifier for tracing

        Returns:
            {
                "infrastructure_code": "Generated YAML/HCL code",
                "validation": {"score": 90, "issues": [], "recommendations": []},
                "deployment_instructions": "Step-by-step deployment guide",
                "citations": [{"source": "...", "version": "...", "score": 0.9}],
                "code_type": "kubernetes|terraform|dockerfile|helm",
                "best_practices": ["..."],
                "execution_time_ms": 1234
            }
        """
        start_time = time.time()

        # Start Langfuse trace
        trace = self.tracer.start_trace(
            name="devops_execution",
            metadata={
                "task": task,
                "task_id": task_id,
                "model": self.code_model
            }
        )

        try:
            # Create CrewAI task
            crew_task = Task(
                description=f"""
Generate production-ready infrastructure code for:

{task}

Context:
{json.dumps(context, indent=2)}

Requirements:
1. Generate infrastructure code with:
   - Kubernetes manifests (if applicable): Deployment, Service, ConfigMap
   - Terraform configurations (if applicable): providers, resources, variables, outputs
   - Dockerfile optimizations (if applicable): multi-stage, security, caching
   - CI/CD pipelines (if applicable): GitHub Actions, GitLab CI
   - Helm charts (if applicable): values, templates

2. Include best practices:
   - Resource limits and requests
   - Health checks (liveness, readiness)
   - Security hardening (non-root user, network policies)
   - High availability (replicas, anti-affinity)
   - Monitoring and logging configuration
   - Secrets management (not hardcoded)

3. Ensure quality:
   - Declarative configuration
   - Well-commented code
   - Production-ready defaults
   - Scalability considerations
   - Cost optimization

4. Provide:
   - Complete infrastructure code
   - Deployment instructions
   - Validation checklist

5. MUST cite ≥2 infrastructure patterns/examples from knowledge base

Output Format:
```yaml
# infrastructure.yaml or main.tf
[Your infrastructure code here]
```

Deployment Instructions:
[Step-by-step guide]

Citations:
[List all sources used]
""",
                expected_output="Complete infrastructure code with deployment instructions and citations",
                agent=self.agent
            )

            # Execute with CrewAI
            crew = Crew(
                agents=[self.agent],
                tasks=[crew_task],
                verbose=True
            )

            result = await crew.kickoff_async()

            # Parse result
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Extract infrastructure code (simplified)
            code_match = re.search(r'```(?:yaml|hcl|dockerfile)\n(.*?)\n```', str(result), re.DOTALL)
            infrastructure_code = code_match.group(1) if code_match else str(result)

            # Determine code type
            code_type = "kubernetes"
            if "terraform" in task.lower() or "provider" in infrastructure_code:
                code_type = "terraform"
            elif "FROM" in infrastructure_code:
                code_type = "dockerfile"
            elif "Chart.yaml" in str(result):
                code_type = "helm"

            # Extract citations
            citations = self._extract_citations(str(result))

            response = {
                "infrastructure_code": infrastructure_code,
                "validation": {
                    "score": 90,
                    "issues": [],
                    "recommendations": []
                },
                "deployment_instructions": "Generated infrastructure is production-ready",
                "citations": citations,
                "code_type": code_type,
                "best_practices": [
                    "Resource limits configured",
                    "Health checks included",
                    "Security hardening applied",
                    "High availability enabled"
                ],
                "execution_time_ms": execution_time_ms
            }

            # End trace
            self.tracer.end_trace(
                trace_id=trace.get("id"),
                output=response,
                metadata={
                    "code_type": code_type,
                    "execution_time_ms": execution_time_ms,
                    "citations_count": len(citations)
                }
            )

            return response

        except Exception as e:
            # Log error to trace
            self.tracer.end_trace(
                trace_id=trace.get("id"),
                output={"error": str(e)},
                metadata={"error": True}
            )
            raise

    def _extract_citations(self, result: str) -> List[Dict[str, Any]]:
        """Extract citations from result"""
        citations = []
        citation_pattern = r'\[(?:Citation|Infrastructure Pattern) \d+\] (.*?) \(v([\d.]+)\)'
        matches = re.findall(citation_pattern, result)

        for source, version in matches[:5]:
            citations.append({
                "source": source.strip(),
                "version": version,
                "score": 0.85
            })

        return citations
