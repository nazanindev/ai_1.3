from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app import models, schemas

router = APIRouter(
    prefix="/projects/{project_id}/tasks",
    tags=["tasks"],
)

# Valid forward-only transitions (skipping is forbidden)
_FORWARD_ORDER = [
    models.TaskStatus.todo,
    models.TaskStatus.in_progress,
    models.TaskStatus.done,
]


def _check_membership(project_id: int, user_id: int, db: Session) -> None:
    member = (
        db.query(models.ProjectMember)
        .filter(
            models.ProjectMember.project_id == project_id,
            models.ProjectMember.user_id == user_id,
        )
        .first()
    )
    if member is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a project member")


def _get_task_or_404(task_id: int, project_id: int, db: Session) -> models.Task:
    task = (
        db.query(models.Task)
        .filter(models.Task.id == task_id, models.Task.project_id == project_id)
        .first()
    )
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


def _validate_status_transition(current: models.TaskStatus, new: models.TaskStatus) -> None:
    current_idx = _FORWARD_ORDER.index(current)
    new_idx = _FORWARD_ORDER.index(new)
    # Back transitions and same-status are always fine; only forward skips are forbidden
    if new_idx > current_idx + 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status transition: {current.value} -> {new.value}",
        )


@router.post("/", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    project_id: int,
    payload: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _check_membership(project_id, current_user.id, db)
    if payload.assignee_id is not None:
        _check_membership(project_id, payload.assignee_id, db)
    task = models.Task(
        **payload.model_dump(),
        project_id=project_id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/", response_model=list[schemas.TaskResponse])
def list_tasks(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _check_membership(project_id, current_user.id, db)
    return db.query(models.Task).filter(models.Task.project_id == project_id).all()


@router.get("/{task_id}", response_model=schemas.TaskResponse)
def get_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _check_membership(project_id, current_user.id, db)
    return _get_task_or_404(task_id, project_id, db)


@router.patch("/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    project_id: int,
    task_id: int,
    payload: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _check_membership(project_id, current_user.id, db)
    task = _get_task_or_404(task_id, project_id, db)
    if payload.assignee_id is not None:
        _check_membership(project_id, payload.assignee_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _check_membership(project_id, current_user.id, db)
    task = _get_task_or_404(task_id, project_id, db)
    db.delete(task)
    db.commit()


@router.patch("/{task_id}/status", response_model=schemas.TaskResponse)
def update_task_status(
    project_id: int,
    task_id: int,
    payload: schemas.TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _check_membership(project_id, current_user.id, db)
    task = _get_task_or_404(task_id, project_id, db)
    _validate_status_transition(task.status, payload.status)
    task.status = payload.status
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}/assign", response_model=schemas.TaskResponse)
def assign_task(
    project_id: int,
    task_id: int,
    payload: schemas.TaskAssign,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _check_membership(project_id, current_user.id, db)
    task = _get_task_or_404(task_id, project_id, db)
    _check_membership(project_id, payload.assignee_id, db)
    task.assignee_id = payload.assignee_id
    db.commit()
    db.refresh(task)
    return task
from fastapi import APIRouter

router = APIRouter()
