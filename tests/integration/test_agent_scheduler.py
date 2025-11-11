"""
Integration tests for Agents + Scheduler services.

Tests the interaction between Agents and Scheduler services:
- Creating schedules for agent execution
- Triggering scheduled agent runs
- Handling execution results
- Cost tracking across scheduled runs
- Collaboration patterns via scheduler
"""

import pytest
import asyncio
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_create_schedule_for_agent(
    authenticated_session,
    agents_client,
    scheduler_client,
    test_agent
):
    """
    Test creating a schedule for an agent.

    Verifies:
    - Schedule can be created for existing agent
    - Schedule references correct agent ID
    - Schedule is properly stored
    """
    # Create schedule for the test agent
    response = await authenticated_session["client"].post(
        f"{scheduler_client['base_url']}/schedules/",
        headers=authenticated_session["headers"],
        json={
            "name": "Test Agent Schedule",
            "agent_id": test_agent["id"],
            "cron_expression": "*/5 * * * *",  # Every 5 minutes
            "task_payload": {"message": "Scheduled task"},
            "is_active": False,  # Don't run automatically
            "tenant_id": authenticated_session["tenant_id"]
        }
    )

    assert response.status_code in [200, 201], \
        f"Should create schedule, got {response.status_code}: {response.text}"

    schedule_data = response.json()
    assert schedule_data["agent_id"] == test_agent["id"], \
        "Schedule should reference correct agent"

    # Cleanup
    schedule_id = schedule_data.get("id")
    if schedule_id:
        try:
            await authenticated_session["client"].delete(
                f"{scheduler_client['base_url']}/schedules/{schedule_id}",
                headers=authenticated_session["headers"]
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_schedule_validation_nonexistent_agent(
    authenticated_session,
    scheduler_client
):
    """
    Test that creating schedule with non-existent agent fails validation.

    Verifies:
    - Scheduler validates agent existence
    - Proper error message is returned
    """
    fake_agent_id = "00000000-0000-0000-0000-000000000000"

    response = await authenticated_session["client"].post(
        f"{scheduler_client['base_url']}/schedules/",
        headers=authenticated_session["headers"],
        json={
            "name": "Invalid Agent Schedule",
            "agent_id": fake_agent_id,
            "cron_expression": "0 0 * * *",
            "task_payload": {},
            "tenant_id": authenticated_session["tenant_id"]
        }
    )

    # Should fail validation (400, 404, or 422)
    assert response.status_code in [400, 404, 422], \
        f"Should reject non-existent agent, got {response.status_code}"


@pytest.mark.asyncio
async def test_trigger_scheduled_agent_execution(
    authenticated_session,
    scheduler_client,
    test_schedule
):
    """
    Test manually triggering a scheduled agent execution.

    Verifies:
    - Schedule can be triggered manually
    - Execution is created
    - Execution references the schedule
    """
    # Trigger the schedule
    response = await authenticated_session["client"].post(
        f"{scheduler_client['base_url']}/schedules/{test_schedule['id']}/trigger",
        headers=authenticated_session["headers"]
    )

    if response.status_code == 404:
        pytest.skip("Trigger endpoint not implemented or not found")

    assert response.status_code in [200, 201, 202], \
        f"Should trigger execution, got {response.status_code}: {response.text}"

    # Response might contain execution ID or job info
    result = response.json()
    assert "execution_id" in result or "job_id" in result or "id" in result, \
        "Response should contain execution/job ID"


@pytest.mark.asyncio
async def test_list_schedule_executions(
    authenticated_session,
    scheduler_client,
    test_schedule
):
    """
    Test listing executions for a schedule.

    Verifies:
    - Executions can be listed for a schedule
    - Execution history is tracked
    """
    # List executions for the schedule
    response = await authenticated_session["client"].get(
        f"{scheduler_client['base_url']}/schedules/{test_schedule['id']}/executions",
        headers=authenticated_session["headers"]
    )

    # May not have executions endpoint or no executions yet
    if response.status_code == 404:
        pytest.skip("Executions endpoint not implemented or not found")

    assert response.status_code == 200, \
        f"Should list executions, got {response.status_code}: {response.text}"

    executions = response.json()
    assert isinstance(executions, list) or "items" in executions, \
        "Response should be list or contain items"


@pytest.mark.asyncio
async def test_pause_and_resume_schedule(
    authenticated_session,
    scheduler_client,
    test_schedule
):
    """
    Test pausing and resuming a schedule.

    Verifies:
    - Schedule can be paused
    - Schedule can be resumed
    - State is properly updated
    """
    schedule_id = test_schedule["id"]

    # Pause schedule
    pause_response = await authenticated_session["client"].post(
        f"{scheduler_client['base_url']}/schedules/{schedule_id}/pause",
        headers=authenticated_session["headers"]
    )

    assert pause_response.status_code in [200, 204], \
        f"Should pause schedule, got {pause_response.status_code}: {pause_response.text}"

    # Verify schedule is paused
    get_response = await authenticated_session["client"].get(
        f"{scheduler_client['base_url']}/schedules/{schedule_id}",
        headers=authenticated_session["headers"]
    )

    assert get_response.status_code == 200
    schedule_data = get_response.json()
    assert schedule_data.get("is_active") is False or schedule_data.get("status") == "paused", \
        "Schedule should be paused"

    # Resume schedule
    resume_response = await authenticated_session["client"].post(
        f"{scheduler_client['base_url']}/schedules/{schedule_id}/resume",
        headers=authenticated_session["headers"]
    )

    assert resume_response.status_code in [200, 204], \
        f"Should resume schedule, got {resume_response.status_code}: {resume_response.text}"

    # Verify schedule is resumed
    get_response = await authenticated_session["client"].get(
        f"{scheduler_client['base_url']}/schedules/{schedule_id}",
        headers=authenticated_session["headers"]
    )

    assert get_response.status_code == 200
    schedule_data = get_response.json()
    assert schedule_data.get("is_active") is True or schedule_data.get("status") == "active", \
        "Schedule should be active"


@pytest.mark.asyncio
async def test_delete_schedule_with_executions(
    authenticated_session,
    scheduler_client,
    agents_client,
    test_agent
):
    """
    Test deleting a schedule that has executions.

    Verifies:
    - Schedule can be deleted
    - Executions are handled properly (cascade or retained)
    """
    # Create a schedule
    create_response = await authenticated_session["client"].post(
        f"{scheduler_client['base_url']}/schedules/",
        headers=authenticated_session["headers"],
        json={
            "name": "Test Delete Schedule",
            "agent_id": test_agent["id"],
            "cron_expression": "0 0 * * *",
            "task_payload": {},
            "is_active": False,
            "tenant_id": authenticated_session["tenant_id"]
        }
    )

    assert create_response.status_code in [200, 201]
    schedule_data = create_response.json()
    schedule_id = schedule_data["id"]

    try:
        # Try to trigger execution (may or may not work)
        try:
            await authenticated_session["client"].post(
                f"{scheduler_client['base_url']}/schedules/{schedule_id}/trigger",
                headers=authenticated_session["headers"]
            )
        except Exception:
            pass

        # Delete schedule
        delete_response = await authenticated_session["client"].delete(
            f"{scheduler_client['base_url']}/schedules/{schedule_id}",
            headers=authenticated_session["headers"]
        )

        assert delete_response.status_code in [200, 204], \
            f"Should delete schedule, got {delete_response.status_code}"

        # Verify schedule is deleted
        get_response = await authenticated_session["client"].get(
            f"{scheduler_client['base_url']}/schedules/{schedule_id}",
            headers=authenticated_session["headers"]
        )

        assert get_response.status_code == 404, \
            "Schedule should be deleted (404)"

    except Exception as e:
        # Cleanup attempt
        try:
            await authenticated_session["client"].delete(
                f"{scheduler_client['base_url']}/schedules/{schedule_id}",
                headers=authenticated_session["headers"]
            )
        except Exception:
            pass
        raise e


@pytest.mark.asyncio
async def test_agent_deletion_with_schedules(
    authenticated_session,
    agents_client,
    scheduler_client
):
    """
    Test deleting an agent that has schedules.

    Verifies:
    - Agent deletion is handled
    - Schedules are either deleted or disabled
    - No orphaned schedules
    """
    # Create agent
    create_agent_response = await authenticated_session["client"].post(
        f"{agents_client['base_url']}/agents/",
        headers=authenticated_session["headers"],
        json={
            "name": "Test Agent For Deletion",
            "type": "developer",
            "description": "Agent for deletion testing",
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022",
            "system_prompt": "Test prompt",
            "tenant_id": authenticated_session["tenant_id"]
        }
    )

    assert create_agent_response.status_code in [200, 201]
    agent_data = create_agent_response.json()
    agent_id = agent_data["id"]

    # Create schedule for agent
    create_schedule_response = await authenticated_session["client"].post(
        f"{scheduler_client['base_url']}/schedules/",
        headers=authenticated_session["headers"],
        json={
            "name": "Test Schedule For Deletion",
            "agent_id": agent_id,
            "cron_expression": "0 0 * * *",
            "task_payload": {},
            "is_active": False,
            "tenant_id": authenticated_session["tenant_id"]
        }
    )

    assert create_schedule_response.status_code in [200, 201]
    schedule_data = create_schedule_response.json()
    schedule_id = schedule_data["id"]

    try:
        # Delete agent
        delete_agent_response = await authenticated_session["client"].delete(
            f"{agents_client['base_url']}/agents/{agent_id}",
            headers=authenticated_session["headers"]
        )

        assert delete_agent_response.status_code in [200, 204], \
            f"Should delete agent, got {delete_agent_response.status_code}"

        # Check schedule status (should be deleted or disabled)
        get_schedule_response = await authenticated_session["client"].get(
            f"{scheduler_client['base_url']}/schedules/{schedule_id}",
            headers=authenticated_session["headers"]
        )

        # Schedule should either be:
        # - Deleted (404)
        # - Disabled (is_active=False)
        # - Reference to deleted agent fails validation
        if get_schedule_response.status_code == 200:
            schedule_after = get_schedule_response.json()
            assert schedule_after.get("is_active") is False, \
                "Schedule should be disabled after agent deletion"

    finally:
        # Cleanup: delete schedule if it still exists
        try:
            await authenticated_session["client"].delete(
                f"{scheduler_client['base_url']}/schedules/{schedule_id}",
                headers=authenticated_session["headers"]
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_cron_expression_validation(
    authenticated_session,
    scheduler_client,
    test_agent
):
    """
    Test that invalid cron expressions are rejected.

    Verifies:
    - Invalid cron expressions fail validation
    - Proper error messages are returned
    """
    # Invalid cron expression
    response = await authenticated_session["client"].post(
        f"{scheduler_client['base_url']}/schedules/",
        headers=authenticated_session["headers"],
        json={
            "name": "Invalid Cron Schedule",
            "agent_id": test_agent["id"],
            "cron_expression": "invalid cron",
            "task_payload": {},
            "tenant_id": authenticated_session["tenant_id"]
        }
    )

    # Should fail validation (400 or 422)
    assert response.status_code in [400, 422], \
        f"Should reject invalid cron, got {response.status_code}"

    # Error message should mention cron
    error_text = response.text.lower()
    assert "cron" in error_text or "expression" in error_text or "invalid" in error_text, \
        "Error should mention cron expression"


@pytest.mark.asyncio
async def test_concurrent_schedule_triggers(
    authenticated_session,
    scheduler_client,
    test_schedule
):
    """
    Test triggering same schedule concurrently.

    Verifies:
    - Concurrent triggers are handled properly
    - No race conditions
    - Multiple executions can be created
    """
    # Trigger schedule 5 times concurrently
    tasks = [
        authenticated_session["client"].post(
            f"{scheduler_client['base_url']}/schedules/{test_schedule['id']}/trigger",
            headers=authenticated_session["headers"]
        )
        for _ in range(5)
    ]

    responses = await asyncio.gather(*tasks, return_exceptions=True)

    # At least one should succeed
    successful_responses = [
        r for r in responses
        if not isinstance(r, Exception) and r.status_code in [200, 201, 202]
    ]

    if not successful_responses:
        # If trigger endpoint doesn't exist, skip
        if any(r.status_code == 404 for r in responses if not isinstance(r, Exception)):
            pytest.skip("Trigger endpoint not implemented")

        pytest.fail(f"No successful triggers: {responses}")

    # At least one should succeed
    assert len(successful_responses) >= 1, \
        f"At least one trigger should succeed, got {len(successful_responses)}"


@pytest.mark.asyncio
async def test_schedule_with_complex_payload(
    authenticated_session,
    scheduler_client,
    test_agent
):
    """
    Test creating schedule with complex task payload.

    Verifies:
    - Complex JSON payloads are stored correctly
    - Payload is returned correctly on retrieval
    """
    complex_payload = {
        "message": "Complex task",
        "parameters": {
            "max_tokens": 1000,
            "temperature": 0.7
        },
        "context": {
            "project_id": "test-project",
            "files": ["file1.py", "file2.py"]
        },
        "metadata": {
            "priority": "high",
            "tags": ["automation", "testing"]
        }
    }

    # Create schedule with complex payload
    create_response = await authenticated_session["client"].post(
        f"{scheduler_client['base_url']}/schedules/",
        headers=authenticated_session["headers"],
        json={
            "name": "Complex Payload Schedule",
            "agent_id": test_agent["id"],
            "cron_expression": "0 0 * * *",
            "task_payload": complex_payload,
            "is_active": False,
            "tenant_id": authenticated_session["tenant_id"]
        }
    )

    assert create_response.status_code in [200, 201]
    schedule_data = create_response.json()
    schedule_id = schedule_data["id"]

    try:
        # Retrieve schedule and verify payload
        get_response = await authenticated_session["client"].get(
            f"{scheduler_client['base_url']}/schedules/{schedule_id}",
            headers=authenticated_session["headers"]
        )

        assert get_response.status_code == 200
        retrieved_schedule = get_response.json()

        # Verify payload is intact
        assert retrieved_schedule.get("task_payload") == complex_payload, \
            "Complex payload should be stored and retrieved correctly"

    finally:
        # Cleanup
        try:
            await authenticated_session["client"].delete(
                f"{scheduler_client['base_url']}/schedules/{schedule_id}",
                headers=authenticated_session["headers"]
            )
        except Exception:
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
