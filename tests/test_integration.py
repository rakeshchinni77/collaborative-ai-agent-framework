import time


def test_integration_result_and_logs(client):
    create = client.post("/api/v1/tasks", json={"prompt": "Integration test"})
    task_id = create.json()["task_id"]

    # Wait for approval state
    for _ in range(10):
        data = client.get(f"/api/v1/tasks/{task_id}").json()
        if data["status"] == "AWAITING_APPROVAL":
            break
        time.sleep(0.5)

    client.post(f"/api/v1/tasks/{task_id}/approve")

    # Wait for completion
    for _ in range(10):
        data = client.get(f"/api/v1/tasks/{task_id}").json()
        if data["status"] == "COMPLETED":
            break
        time.sleep(0.5)

    assert data["result"] is not None
    assert isinstance(data["agent_logs"], list)
    assert len(data["agent_logs"]) >= 3