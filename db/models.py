"""
Модели базы данных для TaskBridge

Таблицы:
- users: Пользователи Telegram
- messages: Все сообщения из чатов
- tasks: Извлеченные задачи
- categories: Категории задач
- pending_tasks: Задачи, ожидающие подтверждения руководителем
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """Модель пользователя Telegram"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    is_bot = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    messages = relationship("Message", back_populates="user")
    assigned_tasks = relationship("Task", foreign_keys="Task.assigned_to", back_populates="assignee")

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"


class Message(Base):
    """Модель сообщения из чата"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, nullable=False)
    chat_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    text = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False)
    has_task = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    user = relationship("User", back_populates="messages")
    tasks = relationship("Task", back_populates="message")

    def __repr__(self):
        return f"<Message(message_id={self.message_id}, chat_id={self.chat_id})>"


class Category(Base):
    """Модель категории задач"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=True)  # Список ключевых слов для автоматической классификации
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    tasks = relationship("Task", back_populates="category")

    def __repr__(self):
        return f"<Category(name={self.name})>"


class Task(Base):
    """Модель задачи"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # pending, in_progress, completed, cancelled
    priority = Column(String(50), default="normal")  # low, normal, high, urgent
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    message = relationship("Message", back_populates="tasks")
    category = relationship("Category", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_tasks")

    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"


class PendingTask(Base):
    """Модель задачи, ожидающей подтверждения руководителем"""
    __tablename__ = "pending_tasks"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    chat_id = Column(Integer, nullable=False)  # ID группового чата
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Кто написал сообщение

    # Извлеченные AI данные
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    assignee_username = Column(String(255), nullable=True)
    due_date = Column(DateTime, nullable=True)
    priority = Column(String(50), default="normal")

    # Статус подтверждения
    status = Column(String(50), default="pending")  # pending, confirmed, rejected
    telegram_message_id = Column(Integer, nullable=True)  # ID сообщения с кнопками подтверждения

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PendingTask(id={self.id}, title={self.title}, status={self.status})>"


class TaskFile(Base):
    """Модель файла, прикрепленного к задаче (отчёт исполнителя)"""
    __tablename__ = "task_files"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Информация о файле
    file_type = Column(String(50), nullable=False)  # photo, document, video
    file_id = Column(String(500), nullable=False)  # Telegram file_id
    file_name = Column(String(500), nullable=True)  # Имя файла (для документов)
    file_size = Column(Integer, nullable=True)  # Размер в байтах
    mime_type = Column(String(100), nullable=True)  # MIME type

    # Описание от исполнителя
    caption = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TaskFile(id={self.id}, task_id={self.task_id}, type={self.file_type})>"


class Comment(Base):
    """Модель комментария к задаче"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Comment(id={self.id}, task_id={self.task_id})>"
