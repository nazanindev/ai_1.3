from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import Comment, Task, Project, ProjectMembership, User
from app.schemas import CommentCreate, CommentUpdate, CommentResponse

router = APIRouter(prefix="/tasks/{task_id}/comments", tags=["comments"])


def _get_task_or_404(task_id: int, db: Session) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


def _get_comment_or_404(comment_id: int, task_id: int, db: Session) -> Comment:
    comment = (
        db.query(Comment)
        .filter(Comment.id == comment_id, Comment.task_id == task_id)
        .first()
    )
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return comment


def _require_project_member(project_id: int, user_id: int, db: Session) -> None:
    membership = (
        db.query(ProjectMembership)
        .filter(
            ProjectMembership.project_id == project_id,
            ProjectMembership.user_id == user_id,
        )
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this project",
        )


@router.post("/", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
def create_comment(
    task_id: int,
    body: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = _get_task_or_404(task_id, db)
    _require_project_member(task.project_id, current_user.id, db)
    comment = Comment(content=body.content, task_id=task_id, author_id=current_user.id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.get("/", response_model=list[CommentResponse])
def list_comments(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_task_or_404(task_id, db)
    return db.query(Comment).filter(Comment.task_id == task_id).all()


@router.get("/{comment_id}", response_model=CommentResponse)
def get_comment(
    task_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_task_or_404(task_id, db)
    return _get_comment_or_404(comment_id, task_id, db)


@router.patch("/{comment_id}", response_model=CommentResponse)
def update_comment(
    task_id: int,
    comment_id: int,
    body: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_task_or_404(task_id, db)
    comment = _get_comment_or_404(comment_id, task_id, db)
    if comment.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the author can edit this comment",
        )
    if body.content is not None:
        comment.content = body.content
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    task_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = _get_task_or_404(task_id, db)
    comment = _get_comment_or_404(comment_id, task_id, db)
    project = db.query(Project).filter(Project.id == task.project_id).first()
    is_author = comment.author_id == current_user.id
    is_project_owner = project is not None and project.owner_id == current_user.id
    if not (is_author or is_project_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the author or project owner can delete this comment",
        )
    db.delete(comment)
    db.commit()
