"""
Temponest Admin Dashboard - Simple Web UI
"""
from flask import Flask, render_template, jsonify, request
from temponest_sdk import TemponestClient
import os
import yaml
from pathlib import Path
import asyncpg
import asyncio
from datetime import datetime, timedelta
import requests

app = Flask(__name__)

# Configuration
BASE_URL = os.getenv("TEMPONEST_BASE_URL", "http://localhost:9000")
AUTH_TOKEN = os.getenv("TEMPONEST_AUTH_TOKEN")
DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "agentic")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://agentic-prometheus:9090")

def get_client():
    """Get Temponest client"""
    return TemponestClient(base_url=BASE_URL, auth_token=AUTH_TOKEN)


async def get_db_connection():
    """Get database connection"""
    return await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def query_prometheus(query):
    """Query Prometheus"""
    try:
        response = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": query},
            timeout=5
        )
        if response.ok:
            return response.json().get('data', {}).get('result', [])
        return []
    except Exception:
        return []


@app.route("/")
def index():
    """Dashboard home"""
    return render_template("dashboard.html")


@app.route("/agents")
def agents_page():
    """Agents management page"""
    return render_template("agents.html")


@app.route("/schedules")
def schedules_page():
    """Schedules management page"""
    return render_template("schedules.html")


@app.route("/costs")
def costs_page():
    """Costs tracking page"""
    return render_template("costs.html")


@app.route("/visualization")
def visualization_page():
    """Workflow visualization page"""
    return render_template("visualization.html")


# API Endpoints
@app.route("/api/agents", methods=["GET"])
def api_list_agents():
    """List agents"""
    try:
        client = get_client()
        limit = int(request.args.get("limit", 100))
        agents = client.agents.list(limit=limit)
        return jsonify([agent.model_dump() for agent in agents])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/agents", methods=["POST"])
def api_create_agent():
    """Create agent"""
    try:
        client = get_client()
        data = request.json
        agent = client.agents.create(**data)
        return jsonify(agent.model_dump())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/agents/<agent_id>", methods=["GET"])
def api_get_agent(agent_id):
    """Get agent"""
    try:
        client = get_client()
        agent = client.agents.get(agent_id)
        return jsonify(agent.model_dump())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/agents/<agent_id>", methods=["DELETE"])
def api_delete_agent(agent_id):
    """Delete agent"""
    try:
        client = get_client()
        client.agents.delete(agent_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/agents/<agent_id>/execute", methods=["POST"])
def api_execute_agent(agent_id):
    """Execute agent"""
    try:
        client = get_client()
        data = request.json
        result = client.agents.execute(
            agent_id=agent_id,
            user_message=data.get("message"),
            context=data.get("context", {})
        )
        return jsonify(result.model_dump())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/schedules", methods=["GET"])
def api_list_schedules():
    """List schedules"""
    try:
        client = get_client()
        limit = int(request.args.get("limit", 100))
        schedules = client.scheduler.list(limit=limit)
        return jsonify([schedule.model_dump() for schedule in schedules])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/schedules", methods=["POST"])
def api_create_schedule():
    """Create schedule"""
    try:
        client = get_client()
        data = request.json
        schedule = client.scheduler.create(
            agent_id=data["agent_id"],
            cron_expression=data["cron_expression"],
            task_config=data.get("task_config", {})
        )
        return jsonify(schedule.model_dump())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/schedules/<schedule_id>", methods=["DELETE"])
def api_delete_schedule(schedule_id):
    """Delete schedule"""
    try:
        client = get_client()
        client.scheduler.delete(schedule_id)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/costs/summary", methods=["GET"])
def api_cost_summary():
    """Get cost summary"""
    try:
        client = get_client()
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        summary = client.costs.get_summary(
            start_date=start_date,
            end_date=end_date
        )
        return jsonify(summary.model_dump())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/status", methods=["GET"])
def api_status():
    """Get platform status"""
    try:
        import requests

        services = {
            "agent_service": f"{BASE_URL}/health",
            "scheduler_service": f"{BASE_URL.replace(':9000', ':9003')}/health",
        }

        status = {}
        for service, url in services.items():
            try:
                response = requests.get(url, timeout=5)
                status[service] = {
                    "healthy": response.status_code < 400,
                    "status_code": response.status_code
                }
            except Exception:
                status[service] = {"healthy": False, "status_code": 0}

        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Visualization API Endpoints
@app.route("/api/visualization/departments", methods=["GET"])
def api_get_departments():
    """Get department hierarchy and structure"""
    try:
        # Get path to department configs
        config_path = Path(__file__).parent.parent / "config" / "departments"

        departments = []
        department_files = list(config_path.glob("*.yaml"))

        for dept_file in department_files:
            with open(dept_file, 'r') as f:
                dept_config = yaml.safe_load(f)
                if dept_config and 'department' in dept_config:
                    departments.append(dept_config['department'])

        # Build hierarchy
        hierarchy = build_department_hierarchy(departments)

        return jsonify(hierarchy)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/visualization/workflows", methods=["GET"])
def api_get_workflows():
    """Get all workflows across departments"""
    try:
        config_path = Path(__file__).parent.parent / "config" / "departments"

        all_workflows = []
        department_files = list(config_path.glob("*.yaml"))

        for dept_file in department_files:
            with open(dept_file, 'r') as f:
                dept_config = yaml.safe_load(f)
                if dept_config and 'department' in dept_config:
                    dept = dept_config['department']
                    if 'workflows' in dept:
                        for workflow in dept['workflows']:
                            workflow['department_id'] = dept['id']
                            workflow['department_name'] = dept['name']
                            all_workflows.append(workflow)

        return jsonify(all_workflows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/visualization/agents-hierarchy", methods=["GET"])
def api_get_agents_hierarchy():
    """Get agents organized by department"""
    try:
        config_path = Path(__file__).parent.parent / "config" / "departments"

        agents_by_dept = {}
        department_files = list(config_path.glob("*.yaml"))

        for dept_file in department_files:
            with open(dept_file, 'r') as f:
                dept_config = yaml.safe_load(f)
                if dept_config and 'department' in dept_config:
                    dept = dept_config['department']
                    dept_id = dept['id']
                    agents_by_dept[dept_id] = {
                        'department_name': dept['name'],
                        'department_id': dept_id,
                        'parent': dept.get('parent'),
                        'agents': dept.get('agents', [])
                    }

        return jsonify(agents_by_dept)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/visualization/workflow/<workflow_id>", methods=["GET"])
def api_get_workflow_detail(workflow_id):
    """Get detailed workflow with agent connections"""
    try:
        config_path = Path(__file__).parent.parent / "config" / "departments"

        department_files = list(config_path.glob("*.yaml"))

        for dept_file in department_files:
            with open(dept_file, 'r') as f:
                dept_config = yaml.safe_load(f)
                if dept_config and 'department' in dept_config:
                    dept = dept_config['department']
                    if 'workflows' in dept:
                        for workflow in dept['workflows']:
                            if workflow['id'] == workflow_id:
                                workflow['department_id'] = dept['id']
                                workflow['department_name'] = dept['name']
                                return jsonify(workflow)

        return jsonify({"error": "Workflow not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def build_department_hierarchy(departments):
    """Build hierarchical structure from flat department list"""
    # Create a map of departments by ID
    dept_map = {dept['id']: dept for dept in departments}

    # Find root departments (those with no parent)
    roots = []
    for dept in departments:
        dept['children'] = []
        if dept.get('parent') is None:
            roots.append(dept)

    # Build tree structure
    for dept in departments:
        parent_id = dept.get('parent')
        if parent_id and parent_id in dept_map:
            dept_map[parent_id]['children'].append(dept)

    return roots


# Analytics and Monitoring Endpoints
@app.route("/api/analytics/executions/recent", methods=["GET"])
def api_get_recent_executions():
    """Get recent agent executions from cost_tracking"""
    try:
        limit = int(request.args.get("limit", 50))

        async def fetch_executions():
            conn = await get_db_connection()
            try:
                rows = await conn.fetch("""
                    SELECT
                        task_id,
                        agent_name,
                        model_provider,
                        model_name,
                        total_tokens,
                        total_cost_usd,
                        latency_ms,
                        status,
                        created_at,
                        workflow_id,
                        project_id
                    FROM cost_tracking
                    ORDER BY created_at DESC
                    LIMIT $1
                """, limit)
                return [dict(row) for row in rows]
            finally:
                await conn.close()

        executions = asyncio.run(fetch_executions())

        # Convert datetime to ISO format
        for exec in executions:
            if exec.get('created_at'):
                exec['created_at'] = exec['created_at'].isoformat()

        return jsonify(executions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/agents/stats", methods=["GET"])
def api_get_agent_stats():
    """Get agent statistics and load"""
    try:
        async def fetch_stats():
            conn = await get_db_connection()
            try:
                rows = await conn.fetch("""
                    SELECT * FROM v_cost_by_agent
                    ORDER BY total_executions DESC
                """)
                return [dict(row) for row in rows]
            finally:
                await conn.close()

        stats = asyncio.run(fetch_stats())

        # Convert datetime to ISO format
        for stat in stats:
            if stat.get('first_execution'):
                stat['first_execution'] = stat['first_execution'].isoformat()
            if stat.get('last_execution'):
                stat['last_execution'] = stat['last_execution'].isoformat()

        # Add real-time metrics from Prometheus
        for stat in stats:
            agent_name = stat['agent_name']
            # Query running executions
            running_query = f'running_executions{{agent_name="{agent_name}"}}'
            running = query_prometheus(running_query)
            stat['currently_running'] = int(running[0]['value'][1]) if running else 0

        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/executions/timeline", methods=["GET"])
def api_get_execution_timeline():
    """Get execution timeline for last N days"""
    try:
        days = int(request.args.get("days", 7))

        async def fetch_timeline():
            conn = await get_db_connection()
            try:
                rows = await conn.fetch("""
                    SELECT
                        DATE(created_at) as date,
                        agent_name,
                        COUNT(*) as executions,
                        SUM(total_tokens) as total_tokens,
                        SUM(total_cost_usd) as total_cost,
                        AVG(latency_ms) as avg_latency,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failures
                    FROM cost_tracking
                    WHERE created_at >= CURRENT_DATE - INTERVAL '%s days'
                    GROUP BY DATE(created_at), agent_name
                    ORDER BY date DESC, agent_name
                """ % days)
                return [dict(row) for row in rows]
            finally:
                await conn.close()

        timeline = asyncio.run(fetch_timeline())

        # Convert date to ISO format
        for item in timeline:
            if item.get('date'):
                item['date'] = item['date'].isoformat()

        return jsonify(timeline)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/dashboard", methods=["GET"])
def api_get_analytics_dashboard():
    """Get comprehensive analytics dashboard data"""
    try:
        async def fetch_dashboard():
            conn = await get_db_connection()
            try:
                # Get overall stats
                overall = await conn.fetchrow("""
                    SELECT
                        COUNT(*) as total_executions,
                        COUNT(DISTINCT agent_name) as unique_agents,
                        SUM(total_tokens) as total_tokens,
                        SUM(total_cost_usd) as total_cost,
                        AVG(latency_ms) as avg_latency,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as total_failures,
                        COUNT(CASE WHEN created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours' THEN 1 END) as last_24h_executions
                    FROM cost_tracking
                """)

                # Get hourly trend for last 24 hours
                hourly = await conn.fetch("""
                    SELECT
                        DATE_TRUNC('hour', created_at) as hour,
                        COUNT(*) as executions,
                        AVG(latency_ms) as avg_latency
                    FROM cost_tracking
                    WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
                    GROUP BY DATE_TRUNC('hour', created_at)
                    ORDER BY hour DESC
                """)

                # Get top agents by usage
                top_agents = await conn.fetch("""
                    SELECT
                        agent_name,
                        COUNT(*) as executions,
                        SUM(total_cost_usd) as cost
                    FROM cost_tracking
                    WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                    GROUP BY agent_name
                    ORDER BY executions DESC
                    LIMIT 5
                """)

                return {
                    "overall": dict(overall),
                    "hourly_trend": [dict(row) for row in hourly],
                    "top_agents": [dict(row) for row in top_agents]
                }
            finally:
                await conn.close()

        dashboard = asyncio.run(fetch_dashboard())

        # Convert datetime to ISO format
        for item in dashboard['hourly_trend']:
            if item.get('hour'):
                item['hour'] = item['hour'].isoformat()

        # Add Prometheus metrics
        running_total = query_prometheus('sum(running_executions)')
        dashboard['overall']['currently_running'] = int(running_total[0]['value'][1]) if running_total else 0

        return jsonify(dashboard)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analytics/agents/load", methods=["GET"])
def api_get_agent_load():
    """Get real-time agent load from Prometheus"""
    try:
        metrics = {
            'running_executions': query_prometheus('running_executions'),
            'agent_executions_total': query_prometheus('agent_executions_total'),
            'agent_execution_duration_seconds': query_prometheus('rate(agent_execution_duration_seconds_sum[5m])'),
            'agent_execution_errors_total': query_prometheus('agent_execution_errors_total'),
        }

        # Process metrics by agent
        agent_load = {}

        for metric in metrics['running_executions']:
            agent_name = metric['metric'].get('agent_name', 'unknown')
            if agent_name not in agent_load:
                agent_load[agent_name] = {
                    'agent_name': agent_name,
                    'running': 0,
                    'total_executions': 0,
                    'avg_duration': 0,
                    'errors': 0
                }
            agent_load[agent_name]['running'] = int(metric['value'][1])

        for metric in metrics['agent_executions_total']:
            agent_name = metric['metric'].get('agent_name', 'unknown')
            if agent_name not in agent_load:
                agent_load[agent_name] = {
                    'agent_name': agent_name,
                    'running': 0,
                    'total_executions': 0,
                    'avg_duration': 0,
                    'errors': 0
                }
            agent_load[agent_name]['total_executions'] = int(metric['value'][1])

        return jsonify(list(agent_load.values()))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
