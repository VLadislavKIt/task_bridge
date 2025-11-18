

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from typing import List, Optional

from db.database import get_db
from db.models import Task, User, Category, Message as MessageModel, TaskFile, Comment
from pydantic import BaseModel
import os
from pathlib import Path

app = FastAPI(title="TaskBridge API")


static_dir = Path(__file__).parent / "static"
webapp_dir = Path(__file__).parent



@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Главная страница - редирект на веб-приложение"""
    return FileResponse(webapp_dir / "index.html")


@app.get("/webapp/index.html", response_class=HTMLResponse)
async def read_webapp():
    """Отображение веб-приложения"""
    return FileResponse(webapp_dir / "index.html")


@app.get("/api/tasks", response_model=List[dict])
async def get_tasks(
    status: Optional[str] = None,
    category_id: Optional[int] = None,
    assigned_to: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Получить список задач
    
    Параметры фильтрации:
    - status: Статус задачи (pending, in_progress, completed, cancelled)
    - category_id: ID категории
    - assigned_to: ID исполнителя
    """
    query = db.query(Task)
    
    if status:
        query = query.filter(Task.status == status)
    if category_id:
        query = query.filter(Task.category_id == category_id)
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)
    
    tasks = query.order_by(desc(Task.created_at)).all()
    
    result = []
    for task in tasks:
        assignee = None
        if task.assignee:
            assignee = {
                "id": task.assignee.id,
                "telegram_id": task.assignee.telegram_id,
                "username": task.assignee.username,
                "first_name": task.assignee.first_name
            }
        
        category = None
        if task.category:
            category = {
                "id": task.category.id,
                "name": task.category.name,
                "description": task.category.description,
                "keywords": task.category.keywords
            }
        
        result.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "assignee": assignee,
            "category": category
        })
    
    return result


@app.get("/api/tasks/{task_id}", response_model=dict)
async def get_task(task_id: int, db: Session = Depends(get_db)):
    """Получить задачу по ID"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    assignee = None
    if task.assignee:
        assignee = {
            "id": task.assignee.id,
            "telegram_id": task.assignee.telegram_id,
            "username": task.assignee.username,
            "first_name": task.assignee.first_name
        }
    
    category = None
    if task.category:
        category = {
            "id": task.category.id,
            "name": task.category.name,
            "description": task.category.description,
            "keywords": task.category.keywords
        }
    
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "assignee": assignee,
        "category": category
    }


@app.patch("/api/tasks/{task_id}/status")
async def update_task_status(task_id: int, status: str, db: Session = Depends(get_db)):
    """Обновить статус задачи"""
    task = db.query(Task).filter(Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if status not in ["pending", "in_progress", "completed", "cancelled"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    task.status = status
    db.commit()
    
    return {"id": task.id, "status": task.status}


@app.get("/api/categories", response_model=List[dict])
async def get_categories(db: Session = Depends(get_db)):
    """Получить список категорий"""
    categories = db.query(Category).all()
    
    result = []
    for category in categories:
        task_count = db.query(func.count(Task.id)).filter(Task.category_id == category.id).scalar()
        result.append({
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "keywords": category.keywords,
            "task_count": task_count
        })
    
    return result


@app.get("/api/users", response_model=List[dict])
async def get_users(db: Session = Depends(get_db)):
    """Получить список пользователей"""
    users = db.query(User).filter(User.is_bot == False).all()
    
    result = []
    for user in users:
        task_count = db.query(func.count(Task.id)).filter(Task.assigned_to == user.id).scalar()
        result.append({
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "task_count": task_count
        })
    
    return result


@app.get("/api/stats", response_model=dict)
async def get_stats(db: Session = Depends(get_db)):
    """Получить статистику"""
    total_tasks = db.query(func.count(Task.id)).scalar()
    pending_tasks = db.query(func.count(Task.id)).filter(Task.status == "pending").scalar()
    in_progress_tasks = db.query(func.count(Task.id)).filter(Task.status == "in_progress").scalar()
    completed_tasks = db.query(func.count(Task.id)).filter(Task.status == "completed").scalar()
    total_users = db.query(func.count(User.id)).filter(User.is_bot == False).scalar()

    return {
        "total_tasks": total_tasks,
        "pending_tasks": pending_tasks,
        "in_progress_tasks": in_progress_tasks,
        "completed_tasks": completed_tasks,
        "total_users": total_users
    }


# Файлы задач
@app.get("/api/tasks/{task_id}/files", response_model=List[dict])
async def get_task_files(task_id: int, db: Session = Depends(get_db)):
    """Получить список файлов задачи"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    files = db.query(TaskFile).filter(TaskFile.task_id == task_id).order_by(desc(TaskFile.created_at)).all()

    result = []
    for file in files:
        uploader = db.query(User).filter(User.id == file.uploaded_by_id).first()
        result.append({
            "id": file.id,
            "file_type": file.file_type,
            "file_id": file.file_id,
            "file_name": file.file_name,
            "file_size": file.file_size,
            "mime_type": file.mime_type,
            "caption": file.caption,
            "created_at": file.created_at.isoformat(),
            "uploaded_by": {
                "id": uploader.id,
                "username": uploader.username,
                "first_name": uploader.first_name
            } if uploader else None
        })

    return result


# Комментарии к задачам
class CommentCreate(BaseModel):
    text: str
    user_id: int


@app.get("/api/tasks/{task_id}/comments", response_model=List[dict])
async def get_task_comments(task_id: int, db: Session = Depends(get_db)):
    """Получить список комментариев задачи"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    comments = db.query(Comment).filter(Comment.task_id == task_id).order_by(Comment.created_at).all()

    result = []
    for comment in comments:
        author = db.query(User).filter(User.id == comment.user_id).first()
        result.append({
            "id": comment.id,
            "text": comment.text,
            "created_at": comment.created_at.isoformat(),
            "author": {
                "id": author.id,
                "username": author.username,
                "first_name": author.first_name
            } if author else None
        })

    return result


@app.post("/api/tasks/{task_id}/comments", response_model=dict)
async def create_task_comment(task_id: int, comment_data: CommentCreate, db: Session = Depends(get_db)):
    """Создать комментарий к задаче"""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    user = db.query(User).filter(User.id == comment_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    comment = Comment(
        task_id=task_id,
        user_id=comment_data.user_id,
        text=comment_data.text
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return {
        "id": comment.id,
        "text": comment.text,
        "created_at": comment.created_at.isoformat(),
        "author": {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name
        }
    }
