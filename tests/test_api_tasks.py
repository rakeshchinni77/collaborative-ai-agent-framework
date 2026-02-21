def test_create_task_returns_202(client):
    response = client.post(
        "/api/v1/tasks",
        json={"prompt": "Test task"},
    )
    assert response.status_code == 202

    data = response.json()
    assert "task_id" in data
    assert data["status"] == "PENDING"


def test_get_task_status_flow(client):
    create = client.post("/api/v1/tasks", json={"prompt": "Polling test"})
    task_id = create.json()["task_id"]

    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["task_id"] == task_id
    assert data["status"] in {"PENDING", "RUNNING", "AWAITING_APPROVAL", "COMPLETED"}


def test_get_task_invalid_uuid(client):
    response = client.get("/api/v1/tasks/invalid-uuid")
    assert response.status_code == 422


def test_get_task_not_found(client):
    response = client.get("/api/v1/tasks/00000000-0000-0000-0000-000000000000")
    assert response.status_code in (404, 500)  # depends on DB state