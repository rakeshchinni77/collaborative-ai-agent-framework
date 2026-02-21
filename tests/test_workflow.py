import time


def test_full_workflow_lifecycle(client):
    create = client.post("/api/v1/tasks", json={"prompt": "Lifecycle test"})
    task_id = create.json()["task_id"]

    # Wait for worker to move to AWAITING_APPROVAL
    for _ in range(10):
        status = client.get(f"/api/v1/tasks/{task_id}").json()["status"]
        if status == "AWAITING_APPROVAL":
            break
        time.sleep(0.5)

    assert status == "AWAITING_APPROVAL"

    # Approve
    approve = client.post(f"/api/v1/tasks/{task_id}/approve")
    assert approve.status_code == 200

    # Wait for completion
    for _ in range(10):
        status = client.get(f"/api/v1/tasks/{task_id}").json()["status"]
        if status == "COMPLETED":
            break
        time.sleep(0.5)

    assert status == "COMPLETED"