from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from datetime import datetime, UTC
from database import Base


def utcnow_naive():
    return datetime.now(UTC).replace(tzinfo=None)

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String, index=True)
    priority = Column(String, default="medium", nullable=False)
    deadline = Column(Date, nullable=True)
    created_at = Column(DateTime, default=utcnow_naive)
    is_done = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=utcnow_naive, onupdate=utcnow_naive)
    user_id = Column(Integer, ForeignKey("users.id"))

    user = relationship("User", back_populates="tasks")


class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(Integer, primary_key=True, index=True)
    method = Column(String, nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    task_title = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow_naive, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    task = relationship("Task")
