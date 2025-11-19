from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


# Промежуточная таблица для связи многие-ко-многим между Task и User (исполнители)
task_assignees = Table(
    'task_assignees',
    Base.metadata,
    Column('task_id', Integer, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('assigned_at', DateTime, default=datetime.utcnow)
)


class User(Base):

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
    assigned_tasks = relationship("Task", secondary=task_assignees, back_populates="assignees")
    created_tasks = relationship("Task", foreign_keys="Task.created_by", back_populates="creator")

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"


class Message(Base):
    
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, nullable=False)
    chat_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    text = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False)
    has_task = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    
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

    
    tasks = relationship("Task", back_populates="category")

    def __repr__(self):
        return f"<Category(name={self.name})>"


class Task(Base):
    """Модель задачи"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Кто создал задачу
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)  # DEPRECATED: используйте assignees
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
    assignees = relationship("User", secondary=task_assignees, back_populates="assigned_tasks")  # Множественные исполнители
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_tasks")
    files = relationship("TaskFile", backref="task", cascade="all, delete-orphan")
    comments = relationship("Comment", backref="task", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"


class PendingTask(Base):
    """Модель задачи, ожидающей подтверждения руководителем"""
    __tablename__ = "pending_tasks"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    chat_id = Column(Integer, nullable=False)  # ID группового чата
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Кто написал сообщение

    # Данные задачи
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    assignee_username = Column(String(255), nullable=True)  # DEPRECATED: один исполнитель
    assignee_usernames = Column(JSON, nullable=True)  # Список username исполнителей ["user1", "user2"]
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

    
    file_type = Column(String(50), nullable=False)  # photo, document, video
    file_id = Column(String(500), nullable=False)  # Telegram file_id
    file_name = Column(String(500), nullable=True)  # Имя файла (для документов)
    file_size = Column(Integer, nullable=True)  # Размер в байтах
    mime_type = Column(String(100), nullable=True)  # MIME type

    
    caption = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TaskFile(id={self.id}, task_id={self.task_id}, type={self.file_type})>"


class Comment(Base):
    """Модель комментария к задаче"""
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Связи
    user = relationship("User", backref="comments")

    def __repr__(self):
        return f"<Comment(id={self.id}, task_id={self.task_id}, user_id={self.user_id})>"
