"""
Temponest Admin Dashboard - Simple Web UI
"""
from flask import Flask, render_template, jsonify, request
from temponest_sdk import TemponestClient
import os

app = Flask(__name__)

# Configuration
BASE_URL = os.getenv("TEMPONEST_BASE_URL", "http://localhost:9000")
AUTH_TOKEN = os.getenv("TEMPONEST_AUTH_TOKEN")

def get_client():
    """Get Temponest client"""
    return TemponestClient(base_url=BASE_URL, auth_token=AUTH_TOKEN)


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
