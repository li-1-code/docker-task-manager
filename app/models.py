from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base

# 定义任务模型
class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    completed = Column(Boolean, default=False)
