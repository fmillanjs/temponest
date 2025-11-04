"""
Temponest CLI - Main Command-Line Interface
"""
import click
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from temponest_sdk import TemponestClient
import os
import sys

console = Console()


def get_client():
    """Get configured Temponest client"""
    base_url = os.getenv("TEMPONEST_BASE_URL", "http://localhost:9000")
    auth_token = os.getenv("TEMPONEST_AUTH_TOKEN")

    return TemponestClient(base_url=base_url, auth_token=auth_token)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    Temponest CLI - Manage your agentic platform

    Set environment variables:
      TEMPONEST_BASE_URL - API base URL (default: http://localhost:9000)
      TEMPONEST_AUTH_TOKEN - Authentication token
    """
    pass


# ============================================================================
# AGENT COMMANDS
# ============================================================================

@cli.group()
def agent():
    """Manage agents"""
    pass


@agent.command("list")
@click.option("--limit", default=20, help="Maximum number of agents to list")
@click.option("--search", help="Search query")
def agent_list(limit, search):
    """List all agents"""
    try:
        client = get_client()
        agents = client.agents.list(limit=limit, search=search)

        if not agents:
            console.print("[yellow]No agents found[/yellow]")
            return

        table = Table(title=f"Agents ({len(agents)} found)")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Model", style="blue")
        table.add_column("Provider", style="magenta")
        table.add_column("Tools", style="yellow")

        for agent in agents:
            table.add_row(
                agent.id[:8],
                agent.name,
                agent.model,
                agent.provider,
                ", ".join(agent.tools) if agent.tools else "-"
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@agent.command("create")
@click.option("--name", required=True, help="Agent name")
@click.option("--model", required=True, help="Model name (e.g., llama3.2:latest)")
@click.option("--description", help="Agent description")
@click.option("--system-prompt", help="System prompt")
@click.option("--provider", default="ollama", help="Model provider")
@click.option("--temperature", default=0.7, type=float, help="Model temperature")
def agent_create(name, model, description, system_prompt, provider, temperature):
    """Create a new agent"""
    try:
        client = get_client()
        agent = client.agents.create(
            name=name,
            model=model,
            description=description,
            system_prompt=system_prompt,
            provider=provider,
            temperature=temperature,
        )

        console.print(f"[green]✓ Agent created successfully![/green]")
        console.print(f"  ID: [cyan]{agent.id}[/cyan]")
        console.print(f"  Name: {agent.name}")
        console.print(f"  Model: {agent.model}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@agent.command("get")
@click.argument("agent_id")
def agent_get(agent_id):
    """Get agent details"""
    try:
        client = get_client()
        agent = client.agents.get(agent_id)

        console.print(f"\n[bold]Agent Details[/bold]")
        console.print(f"  ID: [cyan]{agent.id}[/cyan]")
        console.print(f"  Name: {agent.name}")
        console.print(f"  Description: {agent.description or '-'}")
        console.print(f"  Model: {agent.model}")
        console.print(f"  Provider: {agent.provider}")
        console.print(f"  Temperature: {agent.temperature}")
        console.print(f"  Max Iterations: {agent.max_iterations}")
        console.print(f"  Tools: {', '.join(agent.tools) if agent.tools else '-'}")
        console.print(f"  Created: {agent.created_at}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@agent.command("execute")
@click.argument("agent_id")
@click.argument("message")
@click.option("--stream", is_flag=True, help="Stream the response")
def agent_execute(agent_id, message, stream):
    """Execute an agent"""
    try:
        client = get_client()

        if stream:
            console.print(f"[cyan]Agent Response:[/cyan]\n")
            for chunk in client.agents.execute_stream(agent_id, message):
                console.print(chunk, end='')
            console.print("\n")
        else:
            with console.status("[bold green]Executing agent..."):
                result = client.agents.execute(agent_id, message)

            console.print(f"\n[bold]Execution Result[/bold]")
            console.print(f"  Status: [green]{result.status}[/green]")
            console.print(f"  Response:\n{result.response}")
            console.print(f"\n  Tokens: {result.tokens_used}")
            console.print(f"  Cost: ${result.cost_usd:.6f}")
            console.print(f"  Time: {result.execution_time_seconds:.2f}s")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@agent.command("delete")
@click.argument("agent_id")
@click.confirmation_option(prompt="Are you sure you want to delete this agent?")
def agent_delete(agent_id):
    """Delete an agent"""
    try:
        client = get_client()
        client.agents.delete(agent_id)
        console.print(f"[green]✓ Agent deleted successfully[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


# ============================================================================
# SCHEDULE COMMANDS
# ============================================================================

@cli.group()
def schedule():
    """Manage schedules"""
    pass


@schedule.command("list")
@click.option("--limit", default=20, help="Maximum number of schedules to list")
@click.option("--agent-id", help="Filter by agent ID")
@click.option("--active-only", is_flag=True, help="Show only active schedules")
def schedule_list(limit, agent_id, active_only):
    """List all schedules"""
    try:
        client = get_client()
        schedules = client.scheduler.list(
            limit=limit,
            agent_id=agent_id,
            is_active=True if active_only else None
        )

        if not schedules:
            console.print("[yellow]No schedules found[/yellow]")
            return

        table = Table(title=f"Schedules ({len(schedules)} found)")
        table.add_column("ID", style="cyan")
        table.add_column("Agent ID", style="green")
        table.add_column("Cron", style="blue")
        table.add_column("Active", style="magenta")
        table.add_column("Next Run", style="yellow")
        table.add_column("Run Count", style="white")

        for sched in schedules:
            table.add_row(
                sched.id[:8],
                sched.agent_id[:8],
                sched.cron_expression,
                "✓" if sched.is_active else "✗",
                str(sched.next_run) if sched.next_run else "-",
                str(sched.run_count),
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@schedule.command("create")
@click.option("--agent-id", required=True, help="Agent ID")
@click.option("--cron", required=True, help="Cron expression (e.g., '0 9 * * *')")
@click.option("--message", required=True, help="Message to send to agent")
def schedule_create(agent_id, cron, message):
    """Create a new schedule"""
    try:
        client = get_client()
        schedule = client.scheduler.create(
            agent_id=agent_id,
            cron_expression=cron,
            task_config={"user_message": message}
        )

        console.print(f"[green]✓ Schedule created successfully![/green]")
        console.print(f"  ID: [cyan]{schedule.id}[/cyan]")
        console.print(f"  Cron: {schedule.cron_expression}")
        console.print(f"  Next Run: {schedule.next_run}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@schedule.command("pause")
@click.argument("schedule_id")
def schedule_pause(schedule_id):
    """Pause a schedule"""
    try:
        client = get_client()
        client.scheduler.pause(schedule_id)
        console.print(f"[green]✓ Schedule paused[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@schedule.command("resume")
@click.argument("schedule_id")
def schedule_resume(schedule_id):
    """Resume a schedule"""
    try:
        client = get_client()
        client.scheduler.resume(schedule_id)
        console.print(f"[green]✓ Schedule resumed[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@schedule.command("trigger")
@click.argument("schedule_id")
def schedule_trigger(schedule_id):
    """Manually trigger a schedule"""
    try:
        client = get_client()
        with console.status("[bold green]Triggering schedule..."):
            execution = client.scheduler.trigger(schedule_id)
        console.print(f"[green]✓ Schedule triggered[/green]")
        console.print(f"  Execution ID: [cyan]{execution.id}[/cyan]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@schedule.command("delete")
@click.argument("schedule_id")
@click.confirmation_option(prompt="Are you sure you want to delete this schedule?")
def schedule_delete(schedule_id):
    """Delete a schedule"""
    try:
        client = get_client()
        client.scheduler.delete(schedule_id)
        console.print(f"[green]✓ Schedule deleted[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


# ============================================================================
# COST COMMANDS
# ============================================================================

@cli.group()
def cost():
    """View cost tracking and budgets"""
    pass


@cost.command("summary")
@click.option("--days", default=30, help="Number of days to analyze")
def cost_summary(days):
    """Get cost summary"""
    try:
        from datetime import datetime, timedelta

        client = get_client()
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        with console.status("[bold green]Fetching cost data..."):
            summary = client.costs.get_summary(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat()
            )

        console.print(f"\n[bold]Cost Summary ({days} days)[/bold]")
        console.print(f"  Total: [green]${summary.total_usd:.2f}[/green]")
        console.print(f"  Tokens: {summary.total_tokens}")

        if summary.by_provider:
            console.print(f"\n[bold]By Provider:[/bold]")
            for provider, cost in summary.by_provider.items():
                console.print(f"    {provider}: ${cost:.2f}")

        if summary.by_model:
            console.print(f"\n[bold]By Model:[/bold]")
            for model, cost in summary.by_model.items():
                console.print(f"    {model}: ${cost:.2f}")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cost.command("budget")
def cost_budget():
    """View budget status"""
    try:
        client = get_client()

        with console.status("[bold green]Fetching budget status..."):
            status = client.costs.get_budget_status()

        console.print(f"\n[bold]Budget Status[/bold]")

        if "daily_limit" in status:
            daily_pct = status.get("daily_percentage", 0) * 100
            color = "green" if daily_pct < 80 else ("yellow" if daily_pct < 100 else "red")
            console.print(f"  Daily: [{color}]${status['daily_usage']:.2f} / ${status['daily_limit']:.2f} ({daily_pct:.1f}%)[/{color}]")

        if "monthly_limit" in status:
            monthly_pct = status.get("monthly_percentage", 0) * 100
            color = "green" if monthly_pct < 80 else ("yellow" if monthly_pct < 100 else "red")
            console.print(f"  Monthly: [{color}]${status['monthly_usage']:.2f} / ${status['monthly_limit']:.2f} ({monthly_pct:.1f}%)[/{color}]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cost.command("set-budget")
@click.option("--daily", type=float, help="Daily limit in USD")
@click.option("--monthly", type=float, help="Monthly limit in USD")
@click.option("--threshold", type=float, default=0.8, help="Alert threshold (0-1)")
def cost_set_budget(daily, monthly, threshold):
    """Set budget limits"""
    try:
        client = get_client()
        budget = client.costs.set_budget(
            daily_limit_usd=daily,
            monthly_limit_usd=monthly,
            alert_threshold=threshold
        )

        console.print(f"[green]✓ Budget updated[/green]")
        if budget.daily_limit_usd:
            console.print(f"  Daily: ${budget.daily_limit_usd:.2f}")
        if budget.monthly_limit_usd:
            console.print(f"  Monthly: ${budget.monthly_limit_usd:.2f}")
        console.print(f"  Alert threshold: {budget.alert_threshold * 100:.0f}%")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


# ============================================================================
# STATUS COMMAND
# ============================================================================

@cli.command()
def status():
    """Check platform status"""
    try:
        import requests

        base_url = os.getenv("TEMPONEST_BASE_URL", "http://localhost:9000")

        services = [
            ("Agent Service", f"{base_url}/health"),
            ("Scheduler Service", f"{base_url.replace(':9000', ':9003')}/health"),
            ("Prometheus", f"{base_url.replace(':9000', ':9091')}/-/healthy"),
            ("Grafana", f"{base_url.replace(':9000', ':3003')}/api/health"),
        ]

        table = Table(title="Platform Status")
        table.add_column("Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("URL", style="blue")

        for service_name, url in services:
            try:
                response = requests.get(url, timeout=5)
                status = "✓ Healthy" if response.status_code < 400 else "✗ Unhealthy"
                status_color = "green" if response.status_code < 400 else "red"
            except Exception:
                status = "✗ Unavailable"
                status_color = "red"

            table.add_row(service_name, f"[{status_color}]{status}[/{status_color}]", url)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
