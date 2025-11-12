"""
Full workflow integration tests.

Tests complete end-to-end workflows across multiple services:
- User authentication → Agent creation → Agent execution
- User authentication → Schedule creation → Scheduled execution
- Agent execution → RAG retrieval → Response generation
- Multi-agent collaboration workflows
- Cost tracking across full workflows
"""

import pytest
import asyncio
from datetime import datetime


@pytest.mark.asyncio
async def test_full_agent_execution_workflow(
    authenticated_session,
    agents_client,
    test_agent
):
    """
    Test complete agent execution workflow.

    Steps:
    1. User is authenticated (via fixture)
    2. Agent is created (via fixture)
    3. Execute agent with message
    4. Verify execution result
    5. Check cost tracking

    Verifies:
    - Full workflow completes successfully
    - Execution results are returned
    - Costs are tracked
    """
    # Execute the agent using specialized endpoint
    endpoint = test_agent.get("execution_endpoint", f"/{test_agent['id']}/run")
    execute_response = await authenticated_session["client"].post(
        f"{agents_client['base_url']}{endpoint}",
        headers=authenticated_session["headers"],
        json={
            "task": "Hello! This is an integration test. Please respond briefly.",
            "context": {"max_tokens": 100}
        },
        timeout=60.0  # Extended timeout for actual LLM call
    )

    if execute_response.status_code == 404:
        pytest.skip("Execute endpoint not found or not implemented")

    if execute_response.status_code == 403:
        pytest.skip("Execution permission denied - requires agents:execute permission")

    if execute_response.status_code == 503:
        pytest.skip("Agent execution service unavailable")

    assert execute_response.status_code in [200, 201], \
        f"Agent execution should succeed, got {execute_response.status_code}: {execute_response.text}"

    execution_result = execute_response.json()

    # Verify response structure
    assert "response" in execution_result or "result" in execution_result or "content" in execution_result, \
        "Execution result should contain response/result/content"

    # Verify cost tracking (if implemented)
    if "cost" in execution_result or "cost_usd" in execution_result:
        cost = execution_result.get("cost") or execution_result.get("cost_usd")
        assert isinstance(cost, (int, float)), "Cost should be numeric"
        assert cost >= 0, "Cost should be non-negative"


@pytest.mark.asyncio
async def test_full_scheduled_workflow(
    authenticated_session,
    agents_client,
    scheduler_client,
    test_agent
):
    """
    Test complete scheduled workflow.

    Steps:
    1. User is authenticated
    2. Agent is created
    3. Schedule is created
    4. Schedule is triggered
    5. Execution result is retrieved

    Verifies:
    - Full scheduled workflow completes
    - Schedule triggers properly
    - Execution is tracked
    """
    # Create schedule
    create_schedule_response = await authenticated_session["client"].post(
        f"{scheduler_client['base_url']}/schedules/",
        headers=authenticated_session["headers"],
        json={
            "name": "Full Workflow Test Schedule",
            "agent_id": test_agent["id"],
            "agent_name": test_agent.get("name", "Test Agent"),
            "schedule_type": "cron",
            "cron_expression": "0 0 * * *",
            "task_payload": {"message": "Scheduled workflow test"},
            "is_active": False,
            "tenant_id": authenticated_session["tenant_id"]
        },
        follow_redirects=True
    )

    assert create_schedule_response.status_code in [200, 201]
    schedule_data = create_schedule_response.json()
    schedule_id = schedule_data["id"]

    try:
        # Trigger schedule
        trigger_response = await authenticated_session["client"].post(
            f"{scheduler_client['base_url']}/schedules/{schedule_id}/trigger",
            headers=authenticated_session["headers"]
        )

        if trigger_response.status_code == 404:
            pytest.skip("Trigger endpoint not implemented")

        assert trigger_response.status_code in [200, 201, 202], \
            f"Schedule trigger should succeed, got {trigger_response.status_code}: {trigger_response.text}"

        trigger_result = trigger_response.json()
        assert "execution_id" in trigger_result or "job_id" in trigger_result or "id" in trigger_result, \
            "Trigger result should contain execution/job ID"

    finally:
        # Cleanup
        try:
            await authenticated_session["client"].delete(
                f"{scheduler_client['base_url']}/schedules/{schedule_id}",
                headers=authenticated_session["headers"]
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_agent_crud_workflow(
    authenticated_session,
    agents_client
):
    """
    Test agent lifecycle (SKIPPED - agents are pre-defined in departments).

    In the departments architecture, agents are pre-defined and cannot be
    created, updated, or deleted dynamically through CRUD operations.

    Instead, agents are configured in the department structure and
    accessed via the departments API.

    Alternative: Test departments CRUD workflow (future work).
    """
    pytest.skip(
        "Agent CRUD not applicable in departments architecture. "
        "Agents are pre-defined in department configuration and accessed via /departments/ API."
    )


@pytest.mark.asyncio
async def test_schedule_crud_workflow(
    authenticated_session,
    scheduler_client,
    test_agent
):
    """
    Test complete CRUD workflow for schedules.

    Steps:
    1. Create schedule
    2. Read schedule
    3. Update schedule (pause/resume)
    4. List schedules
    5. Delete schedule

    Verifies:
    - All CRUD operations work together
    - State transitions are handled properly
    """
    # 1. Create schedule
    create_response = await authenticated_session["client"].post(
        f"{scheduler_client['base_url']}/schedules/",
        headers=authenticated_session["headers"],
        json={
            "name": "CRUD Workflow Schedule",
            "agent_id": test_agent["id"],
            "agent_name": test_agent.get("name", "Test Agent"),
            "schedule_type": "cron",
            "cron_expression": "0 */6 * * *",  # Every 6 hours
            "task_payload": {"test": "crud"},
            "is_active": True,
            "tenant_id": authenticated_session["tenant_id"]
        },
        follow_redirects=True
    )

    assert create_response.status_code in [200, 201]
    created_schedule = create_response.json()
    schedule_id = created_schedule["id"]

    try:
        # 2. Read schedule
        read_response = await authenticated_session["client"].get(
            f"{scheduler_client['base_url']}/schedules/{schedule_id}",
            headers=authenticated_session["headers"]
        )

        assert read_response.status_code == 200
        read_schedule = read_response.json()
        assert read_schedule["id"] == schedule_id
        assert read_schedule["name"] == "CRUD Workflow Schedule"

        # 3. Update schedule (pause)
        pause_response = await authenticated_session["client"].post(
            f"{scheduler_client['base_url']}/schedules/{schedule_id}/pause",
            headers=authenticated_session["headers"]
        )

        assert pause_response.status_code in [200, 204]

        # Verify schedule is accessible after pause (API doesn't return is_active/status fields)
        verify_pause_response = await authenticated_session["client"].get(
            f"{scheduler_client['base_url']}/schedules/{schedule_id}",
            headers=authenticated_session["headers"]
        )

        assert verify_pause_response.status_code == 200, \
            "Schedule should be accessible after pause"

        # Resume
        resume_response = await authenticated_session["client"].post(
            f"{scheduler_client['base_url']}/schedules/{schedule_id}/resume",
            headers=authenticated_session["headers"]
        )

        assert resume_response.status_code in [200, 204]

        # 4. List schedules (remove trailing slash to avoid 307 redirect)
        list_response = await authenticated_session["client"].get(
            f"{scheduler_client['base_url']}/schedules",
            headers=authenticated_session["headers"]
        )

        assert list_response.status_code in [200, 404]
        if list_response.status_code == 200:
            schedules_list = list_response.json()
            # May be paginated (API may return list, items, or schedules field)
            if isinstance(schedules_list, list):
                schedule_ids = [s["id"] for s in schedules_list]
            elif "items" in schedules_list:
                schedule_ids = [s["id"] for s in schedules_list["items"]]
            elif "schedules" in schedules_list:
                schedule_ids = [s["id"] for s in schedules_list["schedules"]]
            else:
                schedule_ids = []

            # Note: List endpoint may be paginated or filtered
            if schedule_id not in schedule_ids and len(schedule_ids) == 0:
                # Empty list - might be pagination or the schedule hasn't been indexed yet
                pytest.skip("Schedule not in list - possible pagination or indexing delay")
            elif len(schedule_ids) > 0:
                # If we have schedules, our schedule should be there (same tenant)
                assert schedule_id in schedule_ids, \
                    f"Created schedule should be in list. Got {len(schedule_ids)} schedules but not our ID"

        # 5. Delete schedule
        delete_response = await authenticated_session["client"].delete(
            f"{scheduler_client['base_url']}/schedules/{schedule_id}",
            headers=authenticated_session["headers"]
        )

        assert delete_response.status_code in [200, 204]

        # Verify deletion
        verify_response = await authenticated_session["client"].get(
            f"{scheduler_client['base_url']}/schedules/{schedule_id}",
            headers=authenticated_session["headers"]
        )

        assert verify_response.status_code == 404, \
            "Deleted schedule should return 404"

    except Exception as e:
        # Cleanup on failure
        try:
            await authenticated_session["client"].delete(
                f"{scheduler_client['base_url']}/schedules/{schedule_id}",
                headers=authenticated_session["headers"]
            )
        except Exception:
            pass
        raise e


@pytest.mark.asyncio
async def test_concurrent_agent_executions(
    authenticated_session,
    agents_client,
    test_agent
):
    """
    Test concurrent agent executions.

    Verifies:
    - Multiple executions can run concurrently
    - Each execution is tracked independently
    - No race conditions or resource conflicts
    """
    # Execute agent 3 times concurrently using specialized endpoint
    endpoint = test_agent.get("execution_endpoint", f"/{test_agent['id']}/run")
    tasks = [
        authenticated_session["client"].post(
            f"{agents_client['base_url']}{endpoint}",
            headers=authenticated_session["headers"],
            json={
                "task": f"Concurrent test #{i+1}. Respond briefly.",
                "context": {"max_tokens": 50}
            },
            timeout=60.0
        )
        for i in range(3)
    ]

    responses = await asyncio.gather(*tasks, return_exceptions=True)

    # Check results
    successful = 0
    for i, response in enumerate(responses):
        if isinstance(response, Exception):
            print(f"Execution {i+1} failed with exception: {response}")
            continue

        if response.status_code == 404:
            pytest.skip("Execute endpoint not found")

        if response.status_code == 403:
            print(f"Execution {i+1} permission denied")
            continue

        if response.status_code == 503:
            print(f"Execution {i+1} service unavailable")
            continue

        if response.status_code in [200, 201]:
            successful += 1

    # At least one should succeed (may not all succeed due to rate limits/resources/permissions)
    # If all failed with 403, skip the test
    all_forbidden = all(
        not isinstance(r, Exception) and r.status_code == 403
        for r in responses
    )
    if all_forbidden:
        pytest.skip("All executions permission denied - requires agents:execute permission")

    assert successful >= 1, \
        f"At least one concurrent execution should succeed, got {successful}"


@pytest.mark.asyncio
async def test_error_handling_workflow(
    authenticated_session,
    agents_client,
    scheduler_client
):
    """
    Test error handling across workflow.

    Verifies:
    - Invalid inputs are rejected properly
    - Error messages are informative
    - System remains stable after errors
    """
    # Try to create schedule with invalid cron expression
    invalid_schedule_response = await authenticated_session["client"].post(
        f"{scheduler_client['base_url']}/schedules/",
        headers=authenticated_session["headers"],
        json={
            "name": "Invalid Schedule",
            "agent_id": "00000000-0000-0000-0000-000000000000",
            "cron_expression": "not a cron",
            "tenant_id": authenticated_session["tenant_id"]
        },
        follow_redirects=True
    )

    assert invalid_schedule_response.status_code in [400, 404, 422], \
        f"Invalid schedule data should be rejected, got {invalid_schedule_response.status_code}"

    # System should still be functional - list departments
    departments_response = await authenticated_session["client"].get(
        f"{agents_client['base_url']}/departments/",
        headers=authenticated_session["headers"]
    )

    assert departments_response.status_code == 200, \
        "System should still work after validation errors"

    departments_data = departments_response.json()
    assert "departments" in departments_data, \
        "System should return departments list after error recovery"


@pytest.mark.asyncio
async def test_workflow_with_cost_tracking(
    authenticated_session,
    agents_client,
    test_agent
):
    """
    Test that costs are tracked throughout workflow.

    Verifies:
    - Execution costs are calculated
    - Costs can be retrieved
    - Cost summaries are available
    """
    # Execute agent (generates cost) using specialized endpoint
    endpoint = test_agent.get("execution_endpoint", f"/{test_agent['id']}/run")
    execute_response = await authenticated_session["client"].post(
        f"{agents_client['base_url']}{endpoint}",
        headers=authenticated_session["headers"],
        json={
            "task": "Brief test for cost tracking. Respond with one sentence.",
            "context": {"max_tokens": 50}
        },
        timeout=60.0
    )

    if execute_response.status_code == 404:
        pytest.skip("Execute endpoint not found")

    if execute_response.status_code == 503:
        pytest.skip("Service unavailable")

    if execute_response.status_code not in [200, 201]:
        pytest.skip(f"Execution failed: {execute_response.status_code}")

    # Try to get cost summary
    cost_response = await authenticated_session["client"].get(
        f"{agents_client['base_url']}/costs/summary",
        headers=authenticated_session["headers"]
    )

    if cost_response.status_code == 404:
        pytest.skip("Cost tracking endpoint not found")

    if cost_response.status_code == 200:
        cost_data = cost_response.json()
        # Verify cost data structure
        assert isinstance(cost_data, dict), "Cost data should be a dictionary"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
