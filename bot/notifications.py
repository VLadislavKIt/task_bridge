"""
Модуль для отправки уведомлений через Telegram бота.
Используется из FastAPI для асинхронных уведомлений.
"""
import logging
from typing import Optional
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.exceptions import TelegramForbiddenError
from sqlalchemy.orm import Session

from db.models import Task, User
from config import WEB_APP_DOMAIN, BOT_TOKEN

logger = logging.getLogger(__name__)

# Глобальный экземпляр бота для уведомлений
_bot_instance: Optional[Bot] = None


def get_notification_bot() -> Bot:
    """Получить экземпляр бота для отправки уведомлений"""
    global _bot_instance
    if _bot_instance is None:
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        _bot_instance = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    return _bot_instance


async def notify_comment_added(task_id: int, comment_author_id: int, comment_text: str, db: Session) -> None:
    """
    Отправляет уведомления о новом комментарии всем участникам задачи
    (создателю и исполнителям), кроме автора комментария.
    """
    try:
        bot = get_notification_bot()

        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            logger.warning(f"Task {task_id} not found")
            return

        comment_author = db.query(User).filter(User.id == comment_author_id).first()
        if not comment_author:
            logger.warning(f"Comment author {comment_author_id} not found")
            return

        # Собираем всех участников задачи (создатель + исполнители)
        participants = set()

        # Добавляем создателя задачи
        if task.creator and task.creator.id != comment_author_id:
            participants.add(task.creator)

        # Добавляем всех исполнителей
        for assignee in task.assignees:
            if assignee.id != comment_author_id:
                participants.add(assignee)

        # Формируем уведомление
        author_name = comment_author.first_name or comment_author.username or "Пользователь"
        notification = (
            f"💬 <b>Новый комментарий к задаче</b>\n\n"
            f"<b>Задача:</b> {task.title}\n"
            f"<b>Автор:</b> {author_name}\n"
            f"<b>Комментарий:</b> {comment_text[:200]}{'...' if len(comment_text) > 200 else ''}\n"
        )

        # Отправляем уведомления всем участникам
        for participant in participants:
            if participant.telegram_id and participant.telegram_id != -1:
                try:
                    webapp_url = f"{WEB_APP_DOMAIN}/webapp/index.html?mode=executor&user_id={participant.id}&task_id={task.id}"
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="📱 Открыть задачу",
                                web_app=WebAppInfo(url=webapp_url)
                            )
                        ]
                    ])

                    await bot.send_message(
                        chat_id=participant.telegram_id,
                        text=notification,
                        reply_markup=keyboard
                    )
                    logger.info(f"Comment notification sent to user @{participant.username} (ID: {participant.telegram_id})")
                except TelegramForbiddenError:
                    logger.warning(f"User @{participant.username} blocked the bot")
                except Exception as e:
                    logger.error(f"Failed to send comment notification to @{participant.username}: {e}")
    except Exception as e:
        logger.error(f"Error in notify_comment_added: {e}", exc_info=True)
