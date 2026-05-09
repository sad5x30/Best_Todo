from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from datetime import datetime
from database import Base

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable

from .tasks import Task

class User(SQLAlchemyBaseUserTable, Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("Task", back_populates="user", cascade="all, delete")