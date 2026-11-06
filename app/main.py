from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pydantic import BaseModel,Field,field_validator
from app import models
from app.database import get_db
import json
from app.redis_client import cache_get, cache_set, cache_delete
# 创建 FastAPI 应用
app = FastAPI()

# 定义任务数据类型（用于接收 API 请求）
class TaskCreate(BaseModel):
    title: str=Field(min_length=1,max_length=200)
    completed: bool = False
    @field_validator("title")
    @classmethod
    def validate_title(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("任务标题不能为空")

        return value

# 定义首页接口
@app.get("/")
def home():
    return {
        "message": "Docker Task Manager API",
        "status": "running"
    }


# 定义健康检查接口
@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# 获取所有任务（从 PostgreSQL 查询）
@app.get("/tasks")
def get_tasks(db: Session = Depends(get_db)):
    # 1. 安全读取 Redis
    cached_tasks = cache_get("tasks:all")

    if cached_tasks:
        return json.loads(cached_tasks)

    # 2. 缓存不可用或不存在时，查询 PostgreSQL
    tasks = db.query(models.Task).all()

    result = [
        {
            "id": task.id,
            "title": task.title,
            "completed": task.completed
        }
        for task in tasks
    ]

    # 3. 尝试写入缓存，失败也不影响返回
    cache_set("tasks:all", json.dumps(result), 60)

    return result
# 根据 ID 获取指定任务（使用 PostgreSQL）
@app.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(
        models.Task.id == task_id
    ).first()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return task
# 创建新任务（使用postgresql）
@app.post("/tasks")
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    new_task = models.Task(
        title=task.title,
        completed=task.completed
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    cache_delete("tasks:all")
    return new_task
# 修改指定任务（使用 PostgreSQL）
@app.put("/tasks/{task_id}")
def update_task(
    task_id: int,
    updated_task: TaskCreate,
    db: Session = Depends(get_db)
):
    task = db.query(models.Task).filter(
        models.Task.id == task_id
    ).first()

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    task.title = updated_task.title
    task.completed = updated_task.completed

    db.commit()
    db.refresh(task)
    cache_delete("tasks:all")
    return task

# 删除指定任务（使用 PostgreSQL）
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(
        models.Task.id == task_id
    ).first()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    cache_delete("tasks:all")
    return {"message": "Task deleted successfully"}
