"""
Обновленные обработчики с исправлениями всех проблем
"""

import logging
import re
from typing import List, Optional
from datetime import datetime
from aiogram import Bot, Router, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, PhotoSize, Document
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy.orm import Session

from config import TASK_KEYWORDS, MINI_APP_URL, HOST, PORT, WEB_APP_DOMAIN
from db.models import User, Message as MessageModel, Task, Category, PendingTask, TaskFile
from db.database import get_db_session
from bot.ai_extractor import analyze_message
from aiogram.types import WebAppInfo

logger = logging.getLogger(__name__)

router = Router()


def init_default_categories(db: Session):
    """Инициализация стандартных категорий задач"""
    default_categories = [
        {
            "name": "Разработка",
            "description": "Задачи по разработке и программированию",
            "keywords": ["код", "программ", "разработ", "git", "commit", "repo", "repository", "bug", "issue", "pull request", "merge", "deploy", "dev", "development", "backend", "frontend", "api", "endpoint", "database", "sql", "query"]
        },
        {
            "name": "Дизайн",
            "description": "Задачи по дизайну и визуализации",
            "keywords": ["дизайн", "макет", "ui", "ux", "рисун", "эскиз", "mockup", "wireframe", "prototype", "figma", "sketch", "illustration", "graphics", "visual", "interface"]
        },
        {
            "name": "Маркетинг",
            "description": "Маркетинговые задачи и SMM",
            "keywords": ["маркетинг", "реклам", "пост", "smm", "контент", "соцсети", "social", "campaign", "promotion", "advertising", "conversion", "seo", "crm"]
        },
        {
            "name": "Аналитика",
            "description": "Аналитические и отчетные задачи",
            "keywords": ["аналитик", "отчет", "статистик", "metric", "dashboard", "kpi", "analytics", "data", "metric", "report", "analysis"]
        },
        {
            "name": "Встречи",
            "description": "Встречи и переговоры",
            "keywords": ["встреч", "собрание", "звонок", "онлайн", "meeting", "call", "conference", "presentation"]
        },
        {
            "name": "uncategorized",
            "description": "Задачи без определенной категории",
            "keywords": []
        }
    ]

    for cat_data in default_categories:
        category = db.query(Category).filter(Category.name == cat_data["name"]).first()
        if not category:
            category = Category(
                name=cat_data["name"],
                description=cat_data["description"],
                keywords=cat_data["keywords"]
            )
            db.add(category)

    db.commit()


def classify_task(text: str, db: Session) -> Optional[int]:
    """Классификация задачи по категориям на основе keywords из БД"""
    if not text:
        category = db.query(Category).filter(Category.name == "uncategorized").first()
        if not category:
            init_default_categories(db)
            category = db.query(Category).filter(Category.name == "uncategorized").first()
        return category.id

    text_lower = text.lower()
    categories = db.query(Category).filter(Category.keywords.isnot(None)).all()

    for category in categories:
        if category.keywords:
            if any(keyword in text_lower for keyword in category.keywords):
                return category.id

    category = db.query(Category).filter(Category.name == "uncategorized").first()
    if not category:
        init_default_categories(db)
        category = db.query(Category).filter(Category.name == "uncategorized").first()
    return category.id


async def get_or_create_user(bot: Bot, telegram_id: int, username: str = None,
                              first_name: str = None, last_name: str = None,
                              is_bot: bool = False, db: Session = None) -> User:
    """Получает пользователя из БД или создает нового"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_bot=is_bot
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return user


async def get_or_create_user_by_username(db: Session, username: str) -> User:
    """Получает или создает пользователя по username"""
    user = db.query(User).filter(User.username == username).first()

    if not user:
        user = User(
            telegram_id=-1,
            username=username,
            first_name=f"@{username}",
            is_bot=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created temporary user @{username} (ID: {user.id})")

    return user


async def notify_assigned_user(bot: Bot, task_id: int, db: Session):
    """Отправляет уведомление исполнителю о новой задаче"""
    try:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task or not task.assignee:
            logger.warning(f"Task {task_id} has no assignee")
            return

        assignee = task.assignee

        # Проверяем, что у пользователя есть telegram_id
        if assignee.telegram_id == -1 or assignee.telegram_id is None:
            logger.warning(f"User @{assignee.username} hasn't started a chat with the bot")
            return

        # Формируем текст уведомления
        notification = (
            f"🔔 <b>Вам назначена новая задача</b>\n\n"
            f"<b>Задача:</b> {task.title}\n"
        )

        if task.description and task.description != task.title:
            notification += f"<b>Описание:</b> {task.description}\n"

        if task.due_date:
            notification += f"<b>Срок:</b> {task.due_date.strftime('%d.%m.%Y %H:%M')}\n"

        notification += f"<b>Приоритет:</b> {task.priority}\n"
        notification += f"<b>Статус:</b> {task.status}\n"

        # Добавляем кнопки + WebApp для исполнителя
        webapp_url = f"{WEB_APP_DOMAIN}/webapp/index.html?mode=executor&user_id={assignee.id}"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📱 Открыть панель",
                    web_app=WebAppInfo(url=webapp_url)
                )
            ],
            [
                InlineKeyboardButton(
                    text="▶️ Начать выполнение",
                    callback_data=f"task_start:{task.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Выполнено",
                    callback_data=f"task_complete:{task.id}"
                )
            ]
        ])

        # Отправляем уведомление
        await bot.send_message(
            chat_id=assignee.telegram_id,
            text=notification,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        logger.info(f"Notification sent to user @{assignee.username} (ID: {assignee.telegram_id})")

    except TelegramForbiddenError:
        logger.warning(f"User blocked the bot or hasn't started it")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}", exc_info=True)


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    db = get_db_session()

    try:
        user = await get_or_create_user(
            bot=message.bot,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            is_bot=message.from_user.is_bot,
            db=db
        )

        # Обновляем telegram_id, если он был временным
        if user.telegram_id == -1 or user.telegram_id != message.from_user.id:
            user.telegram_id = message.from_user.id
            db.commit()
            logger.info(f"Updated telegram_id for user @{user.username} (ID: {user.id})")

        # WebApp URL для исполнителя
        webapp_url = f"{WEB_APP_DOMAIN}/webapp/index.html?mode=executor&user_id={user.id}"

        welcome_message = (
            "✅ Отлично! Теперь вы будете получать уведомления о задачах.\n\n"
            "🤖 TaskBridge использует AI для автоматического извлечения задач из чатов.\n\n"
            "Добавьте меня в групповой чат, чтобы я начал анализировать сообщения."
        )

        # Кнопка WebApp
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📱 Открыть мою панель задач",
                    web_app=WebAppInfo(url=webapp_url)
                )
            ]
        ])

        await message.answer(welcome_message, reply_markup=keyboard, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error in /start command: {e}", exc_info=True)
        await message.answer("Произошла ошибка. Попробуйте позже.")
    finally:
        db.close()


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "📋 <b>TaskBridge - AI-управление задачами</b>\n\n"
        "<b>Команды:</b>\n"
        "/start - Начать работу и открыть панель задач\n"
        "/help - Показать справку\n\n"
        "<b>Как использовать:</b>\n"
        "1. Добавьте бота в групповой чат\n"
        "2. Пишите сообщения с задачами, например:\n"
        "   • <i>@alex сделай отчет до завтра</i>\n"
        "   • <i>Саша, срочно исправь баг к вечеру</i>\n"
        "3. Бот автоматически извлечет задачу с помощью AI\n"
        "4. Подтвердите задачу или отредактируйте её\n"
        "5. Исполнитель получит уведомление\n\n"
        "🤖 <b>AI автоматически определяет:</b>\n"
        "• Описание задачи\n"
        "• Исполнителя (@username или имя)\n"
        "• Срок выполнения (до вечера, до обеда, конкретные даты)\n"
        "• Приоритет"
    )

    await message.answer(help_text, parse_mode="HTML")




@router.callback_query(F.data.startswith("task_start:"))
async def handle_task_start(callback: CallbackQuery):
    """Обработчик начала выполнения задачи"""
    db = get_db_session()

    try:
        task_id = int(callback.data.split(":")[1])
        task = db.query(Task).filter(Task.id == task_id).first()

        if not task:
            await callback.answer("Задача не найдена", show_alert=True)
            return

        if task.status == "completed":
            await callback.answer("Задача уже выполнена", show_alert=True)
            return

        # Меняем статус на "в процессе"
        task.status = "in_progress"
        db.commit()

        # Обновляем сообщение
        notification = (
            f"▶️ <b>Задача в процессе выполнения</b>\n\n"
            f"<b>Задача:</b> {task.title}\n"
        )

        if task.description and task.description != task.title:
            notification += f"<b>Описание:</b> {task.description}\n"

        if task.due_date:
            notification += f"<b>Срок:</b> {task.due_date.strftime('%d.%m.%Y %H:%M')}\n"

        notification += f"<b>Приоритет:</b> {task.priority}\n"
        notification += f"<b>Статус:</b> в процессе\n"
        notification += f"\n📎 Можете отправить фото/файлы как отчёт"

        # Обновляем кнопки
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Выполнено",
                    callback_data=f"task_complete:{task.id}"
                )
            ]
        ])

        await callback.message.edit_text(notification, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer("Статус изменён на 'в процессе' ✅")

    except Exception as e:
        logger.error(f"Error starting task: {e}", exc_info=True)
        await callback.answer("Произошла ошибка", show_alert=True)
    finally:
        db.close()


@router.callback_query(F.data.startswith("confirm_task:"))
async def handle_confirm_task(callback: CallbackQuery):
    """Обработчик подтверждения задачи"""
    db = get_db_session()

    try:
        pending_task_id = int(callback.data.split(":")[1])
        pending_task = db.query(PendingTask).filter(PendingTask.id == pending_task_id).first()

        if not pending_task:
            await callback.answer("Задача не найдена", show_alert=True)
            return

        if pending_task.status != "pending":
            await callback.answer("Задача уже обработана", show_alert=True)
            return

        # Определяем исполнителя
        assigned_user_id = None
        if pending_task.assignee_username:
            assignee = await get_or_create_user_by_username(db, pending_task.assignee_username)
            assigned_user_id = assignee.id

        # Классифицируем задачу
        category_id = classify_task(pending_task.description or pending_task.title, db)

        # Создаем финальную задачу
        task = Task(
            message_id=pending_task.message_id,
            category_id=category_id,
            assigned_to=assigned_user_id,
            title=pending_task.title,
            description=pending_task.description,
            status="pending",
            priority=pending_task.priority,
            due_date=pending_task.due_date
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        # Обновляем статус ожидающей задачи
        pending_task.status = "confirmed"
        db.commit()

        # Отправляем уведомление исполнителю
        if assigned_user_id:
            await notify_assigned_user(callback.bot, task.id, db)

        # WebApp URL для руководителя (создателя задачи)
        creator = db.query(User).filter(User.id == pending_task.created_by_id).first()
        webapp_url = f"{WEB_APP_DOMAIN}/webapp/index.html?mode=manager&user_id={creator.id}" if creator else f"{WEB_APP_DOMAIN}/webapp/index.html"

        # Кнопка WebApp для руководителя
        manager_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Открыть панель управления",
                    web_app=WebAppInfo(url=webapp_url)
                )
            ]
        ])

        # Обновляем сообщение с подтверждением + WebApp кнопка
        await callback.message.edit_text(
            f"✅ <b>Задача подтверждена и отправлена!</b>\n\n"
            f"<b>Задача:</b> {task.title}\n"
            f"<b>Исполнитель:</b> @{pending_task.assignee_username if pending_task.assignee_username else 'не указан'}\n"
            f"<b>Срок:</b> {task.due_date.strftime('%d.%m.%Y %H:%M') if task.due_date else 'не указан'}\n"
            f"<b>Приоритет:</b> {task.priority}",
            reply_markup=manager_keyboard,
            parse_mode="HTML"
        )

        await callback.answer("Задача создана! ✅")

    except Exception as e:
        logger.error(f"Error confirming task: {e}", exc_info=True)
        await callback.answer("Произошла ошибка", show_alert=True)
    finally:
        db.close()


@router.callback_query(F.data.startswith("reject_task:"))
async def handle_reject_task(callback: CallbackQuery):
    """Обработчик отклонения задачи"""
    db = get_db_session()

    try:
        pending_task_id = int(callback.data.split(":")[1])
        pending_task = db.query(PendingTask).filter(PendingTask.id == pending_task_id).first()

        if not pending_task:
            await callback.answer("Задача не найдена", show_alert=True)
            return

        if pending_task.status != "pending":
            await callback.answer("Задача уже обработана", show_alert=True)
            return

        pending_task.status = "rejected"
        db.commit()

        await callback.message.edit_text(
            f"❌ <b>Задача отклонена</b>\n\n"
            f"Задача: {pending_task.title}",
            parse_mode="HTML"
        )

        await callback.answer("Задача отклонена")

    except Exception as e:
        logger.error(f"Error rejecting task: {e}", exc_info=True)
        await callback.answer("Произошла ошибка", show_alert=True)
    finally:
        db.close()


@router.callback_query(F.data.startswith("task_complete:"))
async def handle_task_complete(callback: CallbackQuery):
    """Обработчик отметки задачи как выполненной"""
    db = get_db_session()

    try:
        task_id = int(callback.data.split(":")[1])
        task = db.query(Task).filter(Task.id == task_id).first()

        if not task:
            await callback.answer("Задача не найдена", show_alert=True)
            return

        if task.status == "completed":
            await callback.answer("Задача уже выполнена", show_alert=True)
            return

        task.status = "completed"
        db.commit()

        await callback.message.edit_text(
            f"✅ <b>Задача выполнена!</b>\n\n"
            f"<b>Задача:</b> {task.title}\n"
            f"<b>Завершена:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            parse_mode="HTML"
        )

        await callback.answer("Отлично! Задача отмечена как выполненная ✅")

    except Exception as e:
        logger.error(f"Error completing task: {e}", exc_info=True)
        await callback.answer("Произошла ошибка", show_alert=True)
    finally:
        db.close()


@router.message(F.chat.type.in_(["group", "supergroup"]))
async def handle_group_message(message: Message):
    """Обработчик сообщений из групповых чатов с AI-извлечением задач"""
    db = get_db_session()

    try:
        # Пропускаем сообщения от ботов
        if message.from_user.is_bot:
            return

        # Получаем или создаем пользователя
        user = await get_or_create_user(
            bot=message.bot,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            is_bot=message.from_user.is_bot,
            db=db
        )

        # Если сообщение без текста (например, только стикер)
        if not message.text:
            logger.info("Message without text, skipping")
            return

        # Сохраняем сообщение
        message_obj = MessageModel(
            message_id=message.message_id,
            chat_id=message.chat.id,
            user_id=user.id,
            text=message.text,
            date=message.date,
            has_task=False
        )

        db.add(message_obj)
        db.commit()
        db.refresh(message_obj)

        # Анализируем сообщение с помощью AI
        logger.info(f"Analyzing message: {message.text[:50]}...")
        ai_result = await analyze_message(message.text, use_ai=True)

        if not ai_result or not ai_result.get("has_task"):
            logger.info("No task found in message")
            return

        # Задача найдена!
        message_obj.has_task = True
        db.commit()

        task_data = ai_result.get("task", {})

        # Создаем ожидающую подтверждения задачу
        pending_task = PendingTask(
            message_id=message_obj.id,
            chat_id=message.chat.id,
            created_by_id=user.id,
            title=task_data.get("title", "Без названия"),
            description=task_data.get("description"),
            assignee_username=task_data.get("assignee_username"),
            due_date=task_data.get("due_date_parsed"),
            priority=task_data.get("priority", "normal"),
            status="pending"
        )

        db.add(pending_task)
        db.commit()
        db.refresh(pending_task)

        # Формируем сообщение для подтверждения
        confirmation_text = (
            f"🤖 <b>AI обнаружил задачу!</b>\n\n"
            f"<b>Задача:</b> {pending_task.title}\n"
        )

        if pending_task.description and pending_task.description != pending_task.title:
            confirmation_text += f"<b>Описание:</b> {pending_task.description}\n"

        if pending_task.assignee_username:
            confirmation_text += f"<b>Исполнитель:</b> @{pending_task.assignee_username}\n"

        if pending_task.due_date:
            confirmation_text += f"<b>Срок:</b> {pending_task.due_date.strftime('%d.%m.%Y %H:%M')}\n"

        confirmation_text += f"<b>Приоритет:</b> {pending_task.priority}\n\n"
        confirmation_text += "Подтвердите создание задачи:"

        # Кнопки подтверждения
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Подтвердить",
                    callback_data=f"confirm_task:{pending_task.id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"reject_task:{pending_task.id}"
                )
            ]
        ])

        # Отправляем сообщение создателю задачи
        sent_message = await message.bot.send_message(
            chat_id=message.from_user.id,
            text=confirmation_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )

        # Сохраняем ID сообщения с подтверждением
        pending_task.telegram_message_id = sent_message.message_id
        db.commit()

        logger.info(f"Task confirmation sent to user {user.telegram_id}")

    except TelegramForbiddenError:
        logger.warning(f"User hasn't started the bot, cannot send confirmation")
        try:
            await message.answer(
                f"👋 {message.from_user.first_name}, пожалуйста, начните чат со мной (/start), "
                f"чтобы подтверждать задачи!"
            )
        except:
            pass
    except Exception as e:
        logger.error(f"Error handling group message: {e}", exc_info=True)
    finally:
        db.close()


@router.message(F.photo | F.document)
async def handle_file_upload(message: Message):
    """Обработчик загрузки файлов (фото, документы) как отчёт по задаче"""
    db = get_db_session()

    try:
        # Получаем пользователя
        user = await get_or_create_user(
            bot=message.bot,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            is_bot=message.from_user.is_bot,
            db=db
        )

        # Ищем активные задачи пользователя (в процессе выполнения)
        active_tasks = db.query(Task).filter(
            Task.assigned_to == user.id,
            Task.status == "in_progress"
        ).all()

        if not active_tasks:
            await message.answer(
                "❌ У вас нет задач в процессе выполнения.\n\n"
                "Сначала начните выполнение задачи, нажав кнопку '▶️ Начать выполнение'."
            )
            return

        # Если несколько активных задач, берем самую свежую
        task = active_tasks[0]
        if len(active_tasks) > 1:
            task = max(active_tasks, key=lambda t: t.updated_at or t.created_at)
            logger.info(f"User has {len(active_tasks)} active tasks, using most recent: {task.id}")

        # Определяем тип файла и извлекаем данные
        file_type = None
        file_id = None
        file_name = None
        file_size = None
        mime_type = None
        caption = message.caption

        if message.photo:
            # Берем самое большое фото
            photo = message.photo[-1]
            file_type = "photo"
            file_id = photo.file_id
            file_size = photo.file_size
            file_name = f"photo_{photo.file_id[:10]}.jpg"
            mime_type = "image/jpeg"

        elif message.document:
            doc = message.document
            file_type = "document"
            file_id = doc.file_id
            file_name = doc.file_name
            file_size = doc.file_size
            mime_type = doc.mime_type

        # Сохраняем файл в БД
        task_file = TaskFile(
            task_id=task.id,
            uploaded_by_id=user.id,
            file_type=file_type,
            file_id=file_id,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            caption=caption
        )

        db.add(task_file)
        db.commit()
        db.refresh(task_file)

        # Формируем подтверждение
        confirmation = (
            f"✅ <b>Файл прикреплён к задаче!</b>\n\n"
            f"<b>Задача:</b> {task.title}\n"
            f"<b>Файл:</b> {file_name}\n"
        )

        if file_size:
            size_mb = file_size / 1024 / 1024
            confirmation += f"<b>Размер:</b> {size_mb:.2f} МБ\n"

        if caption:
            confirmation += f"<b>Описание:</b> {caption}\n"

        confirmation += f"\n📋 Руководитель сможет просмотреть отчёт в веб-панели"

        await message.answer(confirmation, parse_mode="HTML")

        logger.info(f"File saved: task_id={task.id}, file_type={file_type}, file_id={file_id}")

    except Exception as e:
        logger.error(f"Error handling file upload: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при загрузке файла. Попробуйте позже.")
    finally:
        db.close()


@router.message()
async def handle_other_message(message: Message):
    """Обработчик остальных сообщений"""
    if message.chat.type == "private":
        await message.answer(
            "Привет! 👋\n\n"
            "Я работаю в групповых чатах. Добавьте меня в группу, чтобы я начал анализировать задачи.\n\n"
            "Используйте /help для получения справки."
        )
