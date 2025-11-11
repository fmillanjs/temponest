"""
Multi-tenant isolation integration tests.

Tests tenant isolation across all services:
- Agents service tenant isolation
- Scheduler service tenant isolation
- Data access controls
- Tenant-specific resources
- Cross-tenant access prevention
"""

import pytest
import asyncio


@pytest.mark.asyncio
async def test_agents_tenant_isolation_list(
    authenticated_session,
    second_authenticated_session,
    agents_client,
    test_agent
):
    """
    Test that tenants can only list their own agents.

    Verifies:
    - Tenant A can see their agents
    - Tenant B cannot see Tenant A's agents in their list
    - Each tenant has isolated view
    """
    # Tenant A has test_agent
    tenant_a_list_response = await authenticated_session["client"].get(
        f"{agents_client['base_url']}/agents/",
        headers=authenticated_session["headers"]
    )

    assert tenant_a_list_response.status_code in [200, 404]

    if tenant_a_list_response.status_code == 200:
        tenant_a_agents = tenant_a_list_response.json()

        # Extract agent IDs
        if isinstance(tenant_a_agents, list):
            tenant_a_ids = {a["id"] for a in tenant_a_agents}
        elif "items" in tenant_a_agents:
            tenant_a_ids = {a["id"] for a in tenant_a_agents["items"]}
        else:
            tenant_a_ids = set()

        assert test_agent["id"] in tenant_a_ids, \
            "Tenant A should see their own agent"

    # Tenant B lists their agents
    tenant_b_list_response = await second_authenticated_session["client"].get(
        f"{agents_client['base_url']}/agents/",
        headers=second_authenticated_session["headers"]
    )

    assert tenant_b_list_response.status_code in [200, 404]

    if tenant_b_list_response.status_code == 200:
        tenant_b_agents = tenant_b_list_response.json()

        # Extract agent IDs
        if isinstance(tenant_b_agents, list):
            tenant_b_ids = {a["id"] for a in tenant_b_agents}
        elif "items" in tenant_b_agents:
            tenant_b_ids = {a["id"] for a in tenant_b_agents["items"]}
        else:
            tenant_b_ids = set()

        # Tenant B should NOT see Tenant A's agent
        assert test_agent["id"] not in tenant_b_ids, \
            "Tenant B should NOT see Tenant A's agent in their list"


@pytest.mark.asyncio
async def test_agents_tenant_isolation_get(
    authenticated_session,
    second_authenticated_session,
    agents_client,
    test_agent
):
    """
    Test that tenants cannot directly access other tenants' agents.

    Verifies:
    - Tenant A can GET their own agent
    - Tenant B gets 403/404 when trying to GET Tenant A's agent
    """
    agent_id = test_agent["id"]

    # Tenant A can access their own agent
    tenant_a_response = await authenticated_session["client"].get(
        f"{agents_client['base_url']}/agents/{agent_id}",
        headers=authenticated_session["headers"]
    )

    assert tenant_a_response.status_code == 200, \
        f"Tenant A should access their own agent, got {tenant_a_response.status_code}"

    # Tenant B cannot access Tenant A's agent
    tenant_b_response = await second_authenticated_session["client"].get(
        f"{agents_client['base_url']}/agents/{agent_id}",
        headers=second_authenticated_session["headers"]
    )

    assert tenant_b_response.status_code in [403, 404], \
        f"Tenant B should be denied access to Tenant A's agent, got {tenant_b_response.status_code}"


@pytest.mark.asyncio
async def test_agents_tenant_isolation_update(
    authenticated_session,
    second_authenticated_session,
    agents_client,
    test_agent
):
    """
    Test that tenants cannot update other tenants' agents.

    Verifies:
    - Tenant B gets 403/404 when trying to UPDATE Tenant A's agent
    - Tenant A's agent remains unchanged
    """
    agent_id = test_agent["id"]

    # Tenant B tries to update Tenant A's agent
    tenant_b_update_response = await second_authenticated_session["client"].put(
        f"{agents_client['base_url']}/agents/{agent_id}",
        headers=second_authenticated_session["headers"],
        json={
            "name": "Hijacked Agent Name",
            "description": "This should not work"
        }
    )

    # Should be denied (403/404) or not implemented (404/405)
    assert tenant_b_update_response.status_code in [403, 404, 405], \
        f"Tenant B should not update Tenant A's agent, got {tenant_b_update_response.status_code}"

    # Verify Tenant A's agent is unchanged
    verify_response = await authenticated_session["client"].get(
        f"{agents_client['base_url']}/agents/{agent_id}",
        headers=authenticated_session["headers"]
    )

    assert verify_response.status_code == 200
    agent_data = verify_response.json()
    assert agent_data["name"] != "Hijacked Agent Name", \
        "Agent name should not be changed by Tenant B"


@pytest.mark.asyncio
async def test_agents_tenant_isolation_delete(
    authenticated_session,
    second_authenticated_session,
    agents_client
):
    """
    Test that tenants cannot delete other tenants' agents.

    Verifies:
    - Tenant B gets 403/404 when trying to DELETE Tenant A's agent
    - Tenant A's agent remains intact
    """
    # Tenant A creates an agent
    create_response = await authenticated_session["client"].post(
        f"{agents_client['base_url']}/agents/",
        headers=authenticated_session["headers"],
        json={
            "name": "Tenant A Protected Agent",
            "type": "developer",
            "description": "Should not be deletable by Tenant B",
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022",
            "system_prompt": "Test",
            "tenant_id": authenticated_session["tenant_id"]
        }
    )

    assert create_response.status_code in [200, 201]
    agent_data = create_response.json()
    agent_id = agent_data["id"]

    try:
        # Tenant B tries to delete Tenant A's agent
        tenant_b_delete_response = await second_authenticated_session["client"].delete(
            f"{agents_client['base_url']}/agents/{agent_id}",
            headers=second_authenticated_session["headers"]
        )

        # Should be denied (403/404)
        assert tenant_b_delete_response.status_code in [403, 404], \
            f"Tenant B should not delete Tenant A's agent, got {tenant_b_delete_response.status_code}"

        # Verify Tenant A's agent still exists
        verify_response = await authenticated_session["client"].get(
            f"{agents_client['base_url']}/agents/{agent_id}",
            headers=authenticated_session["headers"]
        )

        assert verify_response.status_code == 200, \
            "Tenant A's agent should still exist after failed delete attempt"

    finally:
        # Cleanup: Tenant A deletes their own agent
        try:
            await authenticated_session["client"].delete(
                f"{agents_client['base_url']}/agents/{agent_id}",
                headers=authenticated_session["headers"]
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_agents_tenant_isolation_execute(
    authenticated_session,
    second_authenticated_session,
    agents_client,
    test_agent
):
    """
    Test that tenants cannot execute other tenants' agents.

    Verifies:
    - Tenant B gets 403/404 when trying to EXECUTE Tenant A's agent
    - Execution costs are not charged to wrong tenant
    """
    agent_id = test_agent["id"]

    # Tenant B tries to execute Tenant A's agent
    tenant_b_execute_response = await second_authenticated_session["client"].post(
        f"{agents_client['base_url']}/agents/{agent_id}/execute",
        headers=second_authenticated_session["headers"],
        json={
            "message": "This should not work",
            "max_tokens": 50
        },
        timeout=60.0
    )

    # Should be denied (403/404) or endpoint not found (404)
    assert tenant_b_execute_response.status_code in [403, 404], \
        f"Tenant B should not execute Tenant A's agent, got {tenant_b_execute_response.status_code}"


@pytest.mark.asyncio
async def test_schedules_tenant_isolation_list(
    authenticated_session,
    second_authenticated_session,
    scheduler_client,
    test_schedule
):
    """
    Test that tenants can only list their own schedules.

    Verifies:
    - Tenant A can see their schedules
    - Tenant B cannot see Tenant A's schedules in their list
    """
    # Tenant A has test_schedule
    tenant_a_list_response = await authenticated_session["client"].get(
        f"{scheduler_client['base_url']}/schedules/",
        headers=authenticated_session["headers"]
    )

    assert tenant_a_list_response.status_code in [200, 404]

    if tenant_a_list_response.status_code == 200:
        tenant_a_schedules = tenant_a_list_response.json()

        # Extract schedule IDs
        if isinstance(tenant_a_schedules, list):
            tenant_a_ids = {s["id"] for s in tenant_a_schedules}
        elif "items" in tenant_a_schedules:
            tenant_a_ids = {s["id"] for s in tenant_a_schedules["items"]}
        else:
            tenant_a_ids = set()

        assert test_schedule["id"] in tenant_a_ids, \
            "Tenant A should see their own schedule"

    # Tenant B lists their schedules
    tenant_b_list_response = await second_authenticated_session["client"].get(
        f"{scheduler_client['base_url']}/schedules/",
        headers=second_authenticated_session["headers"]
    )

    assert tenant_b_list_response.status_code in [200, 404]

    if tenant_b_list_response.status_code == 200:
        tenant_b_schedules = tenant_b_list_response.json()

        # Extract schedule IDs
        if isinstance(tenant_b_schedules, list):
            tenant_b_ids = {s["id"] for s in tenant_b_schedules}
        elif "items" in tenant_b_schedules:
            tenant_b_ids = {s["id"] for s in tenant_b_schedules["items"]}
        else:
            tenant_b_ids = set()

        # Tenant B should NOT see Tenant A's schedule
        assert test_schedule["id"] not in tenant_b_ids, \
            "Tenant B should NOT see Tenant A's schedule in their list"


@pytest.mark.asyncio
async def test_schedules_tenant_isolation_get(
    authenticated_session,
    second_authenticated_session,
    scheduler_client,
    test_schedule
):
    """
    Test that tenants cannot directly access other tenants' schedules.

    Verifies:
    - Tenant A can GET their own schedule
    - Tenant B gets 403/404 when trying to GET Tenant A's schedule
    """
    schedule_id = test_schedule["id"]

    # Tenant A can access their own schedule
    tenant_a_response = await authenticated_session["client"].get(
        f"{scheduler_client['base_url']}/schedules/{schedule_id}",
        headers=authenticated_session["headers"]
    )

    assert tenant_a_response.status_code == 200, \
        f"Tenant A should access their own schedule, got {tenant_a_response.status_code}"

    # Tenant B cannot access Tenant A's schedule
    tenant_b_response = await second_authenticated_session["client"].get(
        f"{scheduler_client['base_url']}/schedules/{schedule_id}",
        headers=second_authenticated_session["headers"]
    )

    assert tenant_b_response.status_code in [403, 404], \
        f"Tenant B should be denied access to Tenant A's schedule, got {tenant_b_response.status_code}"


@pytest.mark.asyncio
async def test_schedules_tenant_isolation_trigger(
    authenticated_session,
    second_authenticated_session,
    scheduler_client,
    test_schedule
):
    """
    Test that tenants cannot trigger other tenants' schedules.

    Verifies:
    - Tenant B gets 403/404 when trying to TRIGGER Tenant A's schedule
    - Execution is not created for Tenant B
    """
    schedule_id = test_schedule["id"]

    # Tenant B tries to trigger Tenant A's schedule
    tenant_b_trigger_response = await second_authenticated_session["client"].post(
        f"{scheduler_client['base_url']}/schedules/{schedule_id}/trigger",
        headers=second_authenticated_session["headers"]
    )

    # Should be denied (403/404) or endpoint not found (404)
    assert tenant_b_trigger_response.status_code in [403, 404], \
        f"Tenant B should not trigger Tenant A's schedule, got {tenant_b_trigger_response.status_code}"


@pytest.mark.asyncio
async def test_schedules_tenant_isolation_delete(
    authenticated_session,
    second_authenticated_session,
    scheduler_client,
    test_agent
):
    """
    Test that tenants cannot delete other tenants' schedules.

    Verifies:
    - Tenant B gets 403/404 when trying to DELETE Tenant A's schedule
    - Tenant A's schedule remains intact
    """
    # Tenant A creates a schedule
    create_response = await authenticated_session["client"].post(
        f"{scheduler_client['base_url']}/schedules/",
        headers=authenticated_session["headers"],
        json={
            "name": "Tenant A Protected Schedule",
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
        # Tenant B tries to delete Tenant A's schedule
        tenant_b_delete_response = await second_authenticated_session["client"].delete(
            f"{scheduler_client['base_url']}/schedules/{schedule_id}",
            headers=second_authenticated_session["headers"]
        )

        # Should be denied (403/404)
        assert tenant_b_delete_response.status_code in [403, 404], \
            f"Tenant B should not delete Tenant A's schedule, got {tenant_b_delete_response.status_code}"

        # Verify Tenant A's schedule still exists
        verify_response = await authenticated_session["client"].get(
            f"{scheduler_client['base_url']}/schedules/{schedule_id}",
            headers=authenticated_session["headers"]
        )

        assert verify_response.status_code == 200, \
            "Tenant A's schedule should still exist after failed delete attempt"

    finally:
        # Cleanup: Tenant A deletes their own schedule
        try:
            await authenticated_session["client"].delete(
                f"{scheduler_client['base_url']}/schedules/{schedule_id}",
                headers=authenticated_session["headers"]
            )
        except Exception:
            pass


@pytest.mark.asyncio
async def test_concurrent_tenant_operations(
    authenticated_session,
    second_authenticated_session,
    agents_client
):
    """
    Test that concurrent operations by different tenants are isolated.

    Verifies:
    - Multiple tenants can create resources concurrently
    - No cross-contamination of data
    - Each tenant sees only their own resources
    """
    # Both tenants create agents concurrently
    tenant_a_task = authenticated_session["client"].post(
        f"{agents_client['base_url']}/agents/",
        headers=authenticated_session["headers"],
        json={
            "name": "Tenant A Concurrent Agent",
            "type": "developer",
            "description": "Tenant A",
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022",
            "system_prompt": "Test A",
            "tenant_id": authenticated_session["tenant_id"]
        }
    )

    tenant_b_task = second_authenticated_session["client"].post(
        f"{agents_client['base_url']}/agents/",
        headers=second_authenticated_session["headers"],
        json={
            "name": "Tenant B Concurrent Agent",
            "type": "qa_tester",
            "description": "Tenant B",
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022",
            "system_prompt": "Test B",
            "tenant_id": second_authenticated_session["tenant_id"]
        }
    )

    tenant_a_response, tenant_b_response = await asyncio.gather(
        tenant_a_task,
        tenant_b_task,
        return_exceptions=True
    )

    # Both should succeed
    assert not isinstance(tenant_a_response, Exception)
    assert not isinstance(tenant_b_response, Exception)
    assert tenant_a_response.status_code in [200, 201]
    assert tenant_b_response.status_code in [200, 201]

    tenant_a_agent = tenant_a_response.json()
    tenant_b_agent = tenant_b_response.json()

    try:
        # Verify tenant isolation
        assert tenant_a_agent["id"] != tenant_b_agent["id"], \
            "Different tenants should get different agent IDs"

        # Tenant A can see their agent but not Tenant B's
        tenant_a_get_own = await authenticated_session["client"].get(
            f"{agents_client['base_url']}/agents/{tenant_a_agent['id']}",
            headers=authenticated_session["headers"]
        )
        assert tenant_a_get_own.status_code == 200

        tenant_a_get_other = await authenticated_session["client"].get(
            f"{agents_client['base_url']}/agents/{tenant_b_agent['id']}",
            headers=authenticated_session["headers"]
        )
        assert tenant_a_get_other.status_code in [403, 404]

        # Tenant B can see their agent but not Tenant A's
        tenant_b_get_own = await second_authenticated_session["client"].get(
            f"{agents_client['base_url']}/agents/{tenant_b_agent['id']}",
            headers=second_authenticated_session["headers"]
        )
        assert tenant_b_get_own.status_code == 200

        tenant_b_get_other = await second_authenticated_session["client"].get(
            f"{agents_client['base_url']}/agents/{tenant_a_agent['id']}",
            headers=second_authenticated_session["headers"]
        )
        assert tenant_b_get_other.status_code in [403, 404]

    finally:
        # Cleanup
        try:
            await authenticated_session["client"].delete(
                f"{agents_client['base_url']}/agents/{tenant_a_agent['id']}",
                headers=authenticated_session["headers"]
            )
        except Exception:
            pass

        try:
            await second_authenticated_session["client"].delete(
                f"{agents_client['base_url']}/agents/{tenant_b_agent['id']}",
                headers=second_authenticated_session["headers"]
            )
        except Exception:
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
