from fastapi import FastAPI

from app.routers import users, projects, tasks, comments

app = FastAPI(title="Project Management API")

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(comments.router, prefix="/comments", tags=["comments"])
