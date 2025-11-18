"""
Система автоматических напоминаний о задачах
"""

import logging
from datetime import datetime, timedelta
from typing import List
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from sqlalchemy.orm import Session

from config import REMINDER_INTERVALS, REMINDER_TIME_HOUR, REMINDER_CHECK_INTERVAL, TIMEZONE
from db.models import Task, User
from db.database import get_db_session

logger = logging.getLogger(__name__)

# Глобальный планировщик
scheduler = None


async def send_reminder(bot: Bot, task: Task, db: Session, reminder_type: str = "upcoming"):
    """
    Отправляет напоминание о задаче исполнителю

    Args:
        bot: Объект бота
        task: Задача
        db: Сессия БД
        reminder_type: Тип напоминания (upcoming, due_today, overdue)
    """
    try:
        if not task.assignee or task.assignee.telegram_id == -1:
            logger.warning(f"Task {task.id} has no assignee or assignee hasn't started bot")
            return

        # Формируем текст напоминания
        if reminder_type == "upcoming":
            days_left = (task.due_date - datetime.now()).days
            emoji = "📅"
            title = f"Напоминание: До дедлайна {days_left} дн."
        elif reminder_type == "due_today":
            emoji = "⏰"
            title = "Внимание: Дедлайн сегодня!"
        else:  # overdue
            emoji = "⚠️"
            title = "ПРОСРОЧЕНО"

        notification = (
            f"{emoji} <b>{title}</b>\n\n"
            f"<b>Задача:</b> {task.title}\n"
        )

        if task.description and task.description != task.title:
            notification += f"<b>Описание:</b> {task.description}\n"

        if task.due_date:
            notification += f"<b>Срок:</b> {task.due_date.strftime('%d.%m.%Y %H:%M')}\n"

        notification += f"<b>Приоритет:</b> {task.priority}\n"
        notification += f"<b>Статус:</b> {task.status}\n"

        # Отправляем напоминание
        await bot.send_message(
            chat_id=task.assignee.telegram_id,
            text=notification,
            parse_mode="HTML"
        )

        logger.info(f"Reminder sent for task {task.id} to user {task.assignee.telegram_id}")

    except Exception as e:
        logger.error(f"Failed to send reminder for task {task.id}: {e}")


async def check_and_send_reminders(bot: Bot):
    """
    Проверяет все задачи и отправляет напоминания по мере необходимости
    """
    db = get_db_session()

    try:
        logger.info("Checking tasks for reminders...")

        # Получаем текущую дату и время
        tz = pytz.timezone(TIMEZONE)
        now = datetime.now(tz)

        # Получаем все активные задачи с дедлайнами
        tasks = db.query(Task).filter(
            Task.status.in_(["pending", "in_progress"]),
            Task.due_date.isnot(None),
            Task.assigned_to.isnot(None)
        ).all()

        logger.info(f"Found {len(tasks)} active tasks with deadlines")

        for task in tasks:
            try:
                # Преобразуем due_date в aware datetime
                if task.due_date.tzinfo is None:
                    task_due_date = tz.localize(task.due_date)
                else:
                    task_due_date = task.due_date

                # Вычисляем разницу во времени
                time_diff = task_due_date - now

                # Проверяем, нужно ли отправить напоминание
                days_until_due = time_diff.days
                hours_until_due = time_diff.total_seconds() / 3600

                # Проверяем просроченные задачи (отправляем напоминание каждый день)
                if hours_until_due < 0:
                    # Проверяем, сколько дней прошло с момента просрочки
                    days_overdue = abs(days_until_due)
                    logger.info(f"Task {task.id} is overdue by {days_overdue} days, sending reminder")
                    await send_reminder(bot, task, db, "overdue")
                    continue

                # Проверяем задачи на сегодня (если осталось меньше 24 часов)
                if 0 <= hours_until_due <= 24:
                    logger.info(f"Task {task.id} is due today ({hours_until_due:.1f} hours left), sending reminder")
                    await send_reminder(bot, task, db, "due_today")
                    continue

                # Проверяем напоминания за N дней (с диапазоном ±12 часов для точности)
                for interval in REMINDER_INTERVALS:
                    if interval > 0:
                        # Проверяем диапазон: от interval-0.5 до interval+0.5 дней
                        days_diff = time_diff.total_seconds() / (24 * 3600)
                        if abs(days_diff - interval) < 0.5:
                            logger.info(f"Task {task.id} is due in ~{interval} days, sending reminder")
                            await send_reminder(bot, task, db, "upcoming")
                            break

            except Exception as task_error:
                logger.error(f"Error processing task {task.id}: {task_error}", exc_info=True)
                continue

        db.commit()

    except Exception as e:
        logger.error(f"Error in check_and_send_reminders: {e}", exc_info=True)
    finally:
        db.close()


def start_reminder_scheduler(bot: Bot):
    """
    Запускает планировщик напоминаний

    Args:
        bot: Объект бота
    """
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler is already running")
        return

    try:
        # Создаем планировщик
        scheduler = AsyncIOScheduler(timezone=TIMEZONE)

        # Добавляем задачу проверки напоминаний
        scheduler.add_job(
            check_and_send_reminders,
            'interval',
            minutes=REMINDER_CHECK_INTERVAL,
            args=[bot],
            id='check_reminders',
            replace_existing=True
        )

        # Запускаем планировщик
        scheduler.start()

        logger.info(f"Reminder scheduler started with interval {REMINDER_CHECK_INTERVAL} minutes")

    except Exception as e:
        logger.error(f"Failed to start reminder scheduler: {e}", exc_info=True)


def stop_reminder_scheduler():
    """Останавливает планировщик напоминаний"""
    global scheduler

    if scheduler is not None:
        try:
            scheduler.shutdown()
            scheduler = None
            logger.info("Reminder scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
