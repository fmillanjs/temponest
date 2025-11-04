"""
Prometheus Metrics for Scheduler Service
Tracks scheduled task execution, scheduler health, and performance
"""
from prometheus_client import Counter, Histogram, Gauge, Info


# =============================================================================
# Scheduled Task Metrics
# =============================================================================

# Counter for scheduled task executions
scheduled_task_executions_total = Counter(
    'scheduled_task_executions_total',
    'Total number of scheduled task executions',
    ['task_id', 'agent_name', 'status', 'tenant_id']
)

# Histogram for task execution duration
task_execution_duration_seconds = Histogram(
    'task_execution_duration_seconds',
    'Task execution duration in seconds',
    ['agent_name', 'tenant_id'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0]
)

# Gauge for active scheduled tasks
active_scheduled_tasks = Gauge(
    'active_scheduled_tasks',
    'Number of active (not paused) scheduled tasks',
    ['tenant_id']
)

# Gauge for currently running executions
running_executions = Gauge(
    'running_executions',
    'Number of currently running task executions'
)

# Counter for task scheduling operations
task_operations_total = Counter(
    'task_operations_total',
    'Total task operations (create, update, delete)',
    ['operation', 'tenant_id']
)

# =============================================================================
# Scheduler Health Metrics
# =============================================================================

# Gauge for scheduler health
scheduler_health = Gauge(
    'scheduler_health',
    'Scheduler health status (1=running, 0=stopped)'
)

# Gauge for scheduler active jobs
scheduler_active_jobs = Gauge(
    'scheduler_active_jobs',
    'Number of active jobs in scheduler'
)

# Gauge for scheduler next run time
scheduler_next_poll_seconds = Gauge(
    'scheduler_next_poll_seconds',
    'Seconds until next scheduler poll'
)

# =============================================================================
# Task Retry Metrics
# =============================================================================

# Counter for task retries
task_retries_total = Counter(
    'task_retries_total',
    'Total number of task retries',
    ['task_id', 'agent_name', 'tenant_id']
)

# Histogram for retry delays
task_retry_delay_seconds = Histogram(
    'task_retry_delay_seconds',
    'Task retry delay in seconds',
    ['agent_name'],
    buckets=[10, 30, 60, 120, 300, 600]
)

# =============================================================================
# Schedule Type Metrics
# =============================================================================

# Gauge for tasks by schedule type
tasks_by_schedule_type = Gauge(
    'tasks_by_schedule_type',
    'Number of tasks by schedule type',
    ['schedule_type', 'tenant_id']  # schedule_type: cron/interval/once
)

# =============================================================================
# Agent Service Integration Metrics
# =============================================================================

# Counter for agent service calls
agent_service_calls_total = Counter(
    'agent_service_calls_total',
    'Total calls to agent service',
    ['agent_name', 'status', 'tenant_id']  # status: success/timeout/error
)

# Histogram for agent service call duration
agent_service_call_duration_seconds = Histogram(
    'agent_service_call_duration_seconds',
    'Agent service call duration in seconds',
    ['agent_name'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

# Gauge for agent service health
agent_service_health = Gauge(
    'agent_service_health',
    'Agent service health status (1=healthy, 0=unhealthy)'
)

# =============================================================================
# Database Metrics
# =============================================================================

# Gauge for database connection pool
db_pool_size = Gauge(
    'db_pool_size',
    'Database connection pool size',
    ['pool_type']  # pool_type: size/available/in_use
)

# Counter for database operations
db_operations_total = Counter(
    'db_operations_total',
    'Total database operations',
    ['operation', 'table']
)

# Histogram for database query duration
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# =============================================================================
# Error Tracking
# =============================================================================

# Counter for errors
scheduler_errors_total = Counter(
    'scheduler_errors_total',
    'Total scheduler errors',
    ['error_type', 'component']
)

# =============================================================================
# Service Info
# =============================================================================

# Info metric for service version
service_info = Info(
    'service',
    'Service information'
)


# =============================================================================
# Helper Functions
# =============================================================================

class MetricsRecorder:
    """Helper class for recording scheduler metrics"""

    @staticmethod
    def record_task_execution(
        task_id: str,
        agent_name: str,
        status: str,
        duration_seconds: float,
        tenant_id: str,
        retry_count: int = 0
    ):
        """Record metrics for a task execution"""
        scheduled_task_executions_total.labels(
            task_id=task_id,
            agent_name=agent_name,
            status=status,
            tenant_id=tenant_id
        ).inc()

        task_execution_duration_seconds.labels(
            agent_name=agent_name,
            tenant_id=tenant_id
        ).observe(duration_seconds)

        if retry_count > 0:
            task_retries_total.labels(
                task_id=task_id,
                agent_name=agent_name,
                tenant_id=tenant_id
            ).inc(retry_count)

    @staticmethod
    def record_agent_service_call(
        agent_name: str,
        status: str,
        duration_seconds: float,
        tenant_id: str
    ):
        """Record metrics for agent service calls"""
        agent_service_calls_total.labels(
            agent_name=agent_name,
            status=status,
            tenant_id=tenant_id
        ).inc()

        agent_service_call_duration_seconds.labels(
            agent_name=agent_name
        ).observe(duration_seconds)

    @staticmethod
    def record_task_operation(operation: str, tenant_id: str):
        """Record a task operation (create/update/delete)"""
        task_operations_total.labels(
            operation=operation,
            tenant_id=tenant_id
        ).inc()

    @staticmethod
    def update_scheduler_health(is_running: bool):
        """Update scheduler health status"""
        scheduler_health.set(1 if is_running else 0)

    @staticmethod
    def update_active_jobs(count: int):
        """Update active jobs count"""
        scheduler_active_jobs.set(count)

    @staticmethod
    def update_running_executions(count: int):
        """Update running executions count"""
        running_executions.set(count)

    @staticmethod
    def update_agent_service_health(is_healthy: bool):
        """Update agent service health"""
        agent_service_health.set(1 if is_healthy else 0)

    @staticmethod
    def record_error(error_type: str, component: str):
        """Record an error"""
        scheduler_errors_total.labels(
            error_type=error_type,
            component=component
        ).inc()
