"""
Prometheus Metrics for Agent Service
Tracks agent execution, costs, performance, and system health
"""
from prometheus_client import Counter, Histogram, Gauge, Info
from typing import Dict, Any
import time


# =============================================================================
# Agent Execution Metrics
# =============================================================================

# Counter for total agent executions
agent_executions_total = Counter(
    'agent_executions_total',
    'Total number of agent executions',
    ['agent_name', 'status', 'tenant_id']
)

# Histogram for agent execution duration
agent_execution_duration_seconds = Histogram(
    'agent_execution_duration_seconds',
    'Agent execution duration in seconds',
    ['agent_name', 'tenant_id'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

# Counter for tokens used
agent_tokens_total = Counter(
    'agent_tokens_total',
    'Total tokens used by agents',
    ['agent_name', 'model', 'token_type', 'tenant_id']  # token_type: input/output
)

# =============================================================================
# Cost Tracking Metrics
# =============================================================================

# Counter for total cost
agent_cost_usd_total = Counter(
    'agent_cost_usd_total',
    'Total cost in USD for agent executions',
    ['agent_name', 'provider', 'model', 'tenant_id', 'project_id']
)

# Gauge for current budget usage
budget_usage_ratio = Gauge(
    'budget_usage_ratio',
    'Current budget usage ratio (0-1)',
    ['tenant_id', 'budget_type']  # budget_type: daily/monthly
)

# Counter for budget alerts
budget_alerts_total = Counter(
    'budget_alerts_total',
    'Total number of budget alerts triggered',
    ['tenant_id', 'alert_type']  # alert_type: warning/exceeded
)

# =============================================================================
# Collaboration Metrics
# =============================================================================

# Counter for collaboration sessions
collaboration_sessions_total = Counter(
    'collaboration_sessions_total',
    'Total number of collaboration sessions',
    ['pattern', 'status', 'tenant_id']
)

# Histogram for collaboration duration
collaboration_duration_seconds = Histogram(
    'collaboration_duration_seconds',
    'Collaboration session duration in seconds',
    ['pattern', 'tenant_id'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0]
)

# Gauge for active collaborations
active_collaborations = Gauge(
    'active_collaborations',
    'Number of currently active collaboration sessions'
)

# =============================================================================
# System Health Metrics
# =============================================================================

# Gauge for service health
service_health = Gauge(
    'service_health',
    'Service health status (1=healthy, 0=unhealthy)',
    ['component']  # component: database, qdrant, langfuse, ollama
)

# Gauge for overall agent service health
agent_service_health = Gauge(
    'agent_service_health',
    'Overall agent service health (1=healthy, 0=unhealthy)'
)

# Info metric for service version
service_info = Info(
    'service',
    'Service information'
)

# Gauge for database connection pool
db_pool_size = Gauge(
    'db_pool_size',
    'Database connection pool size',
    ['pool_type']  # pool_type: size/available/in_use
)

# =============================================================================
# Webhook Metrics
# =============================================================================

# Counter for webhook deliveries
webhook_deliveries_total = Counter(
    'webhook_deliveries_total',
    'Total webhook delivery attempts',
    ['event_type', 'status', 'tenant_id']  # status: success/failed
)

# Histogram for webhook delivery time
webhook_delivery_duration_seconds = Histogram(
    'webhook_delivery_duration_seconds',
    'Webhook delivery duration in seconds',
    ['event_type', 'tenant_id'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# =============================================================================
# Error Tracking
# =============================================================================

# Counter for errors
agent_errors_total = Counter(
    'agent_errors_total',
    'Total number of agent errors',
    ['agent_name', 'error_type', 'tenant_id']
)

# =============================================================================
# RAG Memory Metrics
# =============================================================================

# Counter for RAG queries
rag_queries_total = Counter(
    'rag_queries_total',
    'Total number of RAG memory queries',
    ['agent_name', 'tenant_id']
)

# Histogram for RAG query latency
rag_query_duration_seconds = Histogram(
    'rag_query_duration_seconds',
    'RAG query duration in seconds',
    ['agent_name'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0]
)

# Gauge for vector store size
vector_store_documents = Gauge(
    'vector_store_documents',
    'Number of documents in vector store'
)

# =============================================================================
# Department Metrics
# =============================================================================

# Counter for department tasks
department_tasks_total = Counter(
    'department_tasks_total',
    'Total tasks executed by department',
    ['department_name', 'status', 'tenant_id']
)


# =============================================================================
# Helper Functions
# =============================================================================

class MetricsRecorder:
    """Helper class for recording metrics"""

    @staticmethod
    def record_agent_execution(
        agent_name: str,
        status: str,
        duration_seconds: float,
        tokens_used: Dict[str, int],
        cost_usd: float,
        tenant_id: str,
        project_id: str = None,
        model: str = "unknown",
        provider: str = "ollama"
    ):
        """Record metrics for an agent execution"""
        # Execution count
        agent_executions_total.labels(
            agent_name=agent_name,
            status=status,
            tenant_id=tenant_id
        ).inc()

        # Duration
        agent_execution_duration_seconds.labels(
            agent_name=agent_name,
            tenant_id=tenant_id
        ).observe(duration_seconds)

        # Tokens
        if tokens_used:
            for token_type, count in tokens_used.items():
                agent_tokens_total.labels(
                    agent_name=agent_name,
                    model=model,
                    token_type=token_type,
                    tenant_id=tenant_id
                ).inc(count)

        # Cost
        if cost_usd > 0:
            agent_cost_usd_total.labels(
                agent_name=agent_name,
                provider=provider,
                model=model,
                tenant_id=tenant_id,
                project_id=project_id or "none"
            ).inc(cost_usd)

    @staticmethod
    def record_collaboration(
        pattern: str,
        status: str,
        duration_seconds: float,
        tenant_id: str
    ):
        """Record metrics for a collaboration session"""
        collaboration_sessions_total.labels(
            pattern=pattern,
            status=status,
            tenant_id=tenant_id
        ).inc()

        collaboration_duration_seconds.labels(
            pattern=pattern,
            tenant_id=tenant_id
        ).observe(duration_seconds)

    @staticmethod
    def record_webhook_delivery(
        event_type: str,
        status: str,
        duration_seconds: float,
        tenant_id: str
    ):
        """Record metrics for webhook delivery"""
        webhook_deliveries_total.labels(
            event_type=event_type,
            status=status,
            tenant_id=tenant_id
        ).inc()

        webhook_delivery_duration_seconds.labels(
            event_type=event_type,
            tenant_id=tenant_id
        ).observe(duration_seconds)

    @staticmethod
    def record_error(
        agent_name: str,
        error_type: str,
        tenant_id: str
    ):
        """Record an agent error"""
        agent_errors_total.labels(
            agent_name=agent_name,
            error_type=error_type,
            tenant_id=tenant_id
        ).inc()

    @staticmethod
    def update_service_health(component: str, is_healthy: bool):
        """Update service health gauge"""
        service_health.labels(component=component).set(1 if is_healthy else 0)

    @staticmethod
    def update_budget_usage(tenant_id: str, budget_type: str, usage_ratio: float):
        """Update budget usage gauge"""
        budget_usage_ratio.labels(
            tenant_id=tenant_id,
            budget_type=budget_type
        ).set(usage_ratio)

    @staticmethod
    def record_budget_alert(tenant_id: str, alert_type: str):
        """Record a budget alert"""
        budget_alerts_total.labels(
            tenant_id=tenant_id,
            alert_type=alert_type
        ).inc()
