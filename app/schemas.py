from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

from app.models import TaskStatus


# --- User ---

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None


class UserOut(UserBase):
    id: int

    model_config = {"from_attributes": True}


# --- Project ---

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectOut(ProjectBase):
    id: int
    owner_id: int
    members: List[UserOut] = []

    model_config = {"from_attributes": True}


# --- Task ---

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.todo
    assignee_id: Optional[int] = None


class TaskCreate(TaskBase):
    project_id: int


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    assignee_id: Optional[int] = None


class TaskOut(TaskBase):
    id: int
    project_id: int

    model_config = {"from_attributes": True}


# --- Comment ---

class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    task_id: int


class CommentOut(CommentBase):
    id: int
    task_id: int
    author_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
