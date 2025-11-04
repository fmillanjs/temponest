"""
Example 2: Scheduling Agents

This example demonstrates how to:
1. Create an agent
2. Schedule it to run automatically
3. Monitor scheduled executions
4. Pause/resume/trigger schedules
"""

from temponest_sdk import TemponestClient
import time

def main():
    client = TemponestClient(base_url="http://localhost:9000")

    try:
        # Create an agent for scheduled execution
        print("Creating agent...")
        agent = client.agents.create(
            name="DailyReporter",
            description="Generates daily reports",
            model="llama3.2:latest",
            system_prompt="You are a data analyst that generates concise daily reports.",
        )
        print(f"✓ Agent created: {agent.id}")

        # Schedule the agent to run daily at 9 AM
        print("\nCreating schedule...")
        schedule = client.scheduler.create(
            agent_id=agent.id,
            cron_expression="0 9 * * *",  # Every day at 9:00 AM
            task_config={
                "user_message": "Generate today's summary report",
                "context": {
                    "report_type": "daily_summary",
                    "include_metrics": True
                }
            }
        )
        print(f"✓ Schedule created: {schedule.id}")
        print(f"  Cron: {schedule.cron_expression}")
        print(f"  Next run: {schedule.next_run}")
        print(f"  Active: {schedule.is_active}")

        # Manually trigger the schedule (don't wait for cron)
        print("\nTriggering schedule manually...")
        execution = client.scheduler.trigger(schedule.id)
        print(f"✓ Schedule triggered: {execution.id}")

        # Wait a moment for execution
        print("\nWaiting for execution to complete...")
        time.sleep(2)

        # Check execution history
        print("\nChecking execution history...")
        executions = client.scheduler.get_executions(schedule.id, limit=5)
        print(f"✓ Found {len(executions)} executions:")
        for exec in executions:
            print(f"  - {exec.status} at {exec.started_at}")

        # Pause the schedule
        print("\nPausing schedule...")
        schedule = client.scheduler.pause(schedule.id)
        print(f"✓ Schedule paused: {schedule.is_active}")

        # Resume the schedule
        print("\nResuming schedule...")
        schedule = client.scheduler.resume(schedule.id)
        print(f"✓ Schedule resumed: {schedule.is_active}")

        # Update the schedule
        print("\nUpdating schedule to run every hour...")
        schedule = client.scheduler.update(
            schedule_id=schedule.id,
            cron_expression="0 * * * *",  # Every hour
        )
        print(f"✓ Schedule updated: {schedule.cron_expression}")

        # List all schedules for this agent
        print("\nListing schedules for agent...")
        schedules = client.scheduler.list(agent_id=agent.id)
        print(f"✓ Found {len(schedules)} schedules")

        # Clean up
        print("\nCleaning up...")
        client.scheduler.delete(schedule.id)
        client.agents.delete(agent.id)
        print(f"✓ Cleaned up")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        client.close()


if __name__ == "__main__":
    main()
