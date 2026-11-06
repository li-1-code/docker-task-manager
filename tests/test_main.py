from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_read_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Docker Task Manager API",
        "status": "running"
    }


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_task_crud():
    task_id = None

    try:
        # 1. 测试创建非法任务：纯空格标题应该被拒绝
        response = client.post(
            "/tasks",
            json={"title": "   "}
        )
        assert response.status_code == 422

        # 2. 创建任务
        response = client.post(
            "/tasks",
            json={"title": "pytest 自动化测试任务"}
        )
        assert response.status_code == 200

        data = response.json()
        task_id = data["id"]

        assert data["title"] == "pytest 自动化测试任务"
        assert data["completed"] is False

        # 3. 查询指定任务
        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "pytest 自动化测试任务"

        # 4. 查询任务列表
        response = client.get("/tasks")
        assert response.status_code == 200
        assert any(task["id"] == task_id for task in response.json())

        # 5. 修改任务
        response = client.put(
            f"/tasks/{task_id}",
            json={
                "title": "pytest 修改后的任务",
                "completed": True
            }
        )
        assert response.status_code == 200
        assert response.json()["title"] == "pytest 修改后的任务"
        assert response.json()["completed"] is True

        # 6. 删除任务
        response = client.delete(f"/tasks/{task_id}")
        assert response.status_code == 200

        # 7. 确认删除后查询返回 404
        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == 404

    finally:
        # 无论测试是否中途失败，都清理本次创建的任务
        if task_id is not None:
            client.delete(f"/tasks/{task_id}")


def test_task_not_found():
    response = client.get("/tasks/2147483647")
    assert response.status_code == 404
