"""
Конфигурация TaskBridge
"""

import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла (если существует)
load_dotenv()

# ==================== API КЛЮЧИ ====================

# Telegram Bot Token (от @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

# ==================== БАЗА ДАННЫХ ====================

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///taskbridge.db")

# ==================== TELEGRAM WEBHOOK ====================

# Использовать webhook (False = polling mode для разработки)
USE_WEBHOOK = os.getenv("USE_WEBHOOK", "False").lower() == "true"

# URL для webhook (если USE_WEBHOOK = True)
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-domain.com")

# Путь для webhook
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")

# ==================== ВЕБ-СЕРВЕР ====================

# Хост для веб-приложения
HOST = os.getenv("HOST", "0.0.0.0")

# Порт для веб-приложения
PORT = int(os.getenv("PORT", "8000"))

# Домен для веб-приложения (для Railway используется автоматически)
WEB_APP_DOMAIN = os.getenv("WEB_APP_DOMAIN", f"http://{HOST}:{PORT}")

# URL для Telegram Mini App
MINI_APP_URL = os.getenv("MINI_APP_URL", f"{WEB_APP_DOMAIN}/webapp/index.html")

# ==================== AI НАСТРОЙКИ ====================

# Модель OpenAI для извлечения задач
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Температура для AI (0.0 - детерминированный, 1.0 - креативный)
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))

# Максимальное количество токенов в ответе
OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "500"))

# ==================== ИЗВЛЕЧЕНИЕ ЗАДАЧ ====================

# Ключевые слова для простого определения задач (fallback если AI недоступен)
TASK_KEYWORDS = [
    # Действия
    "сделать", "нужно", "необходимо", "надо", "требуется",
    "выполни", "подготовь", "создай", "напиши", "исправь",
    "проверь", "убедись", "организуй", "настрой",

    # Сроки
    "до", "к", "срочно", "важно", "deadline",

    # Английские
    "need", "should", "must", "todo", "task",
    "please", "fix", "create", "update", "check"
]

# ==================== НАПОМИНАНИЯ ====================

# Интервалы напоминаний (в днях до дедлайна)
REMINDER_INTERVALS = [3, 1, 0]  # За 3 дня, за 1 день, в день дедлайна

# Время отправки напоминаний (часы)
REMINDER_TIME_HOUR = 9  # 09:00 по местному времени

# Интервал проверки напоминаний (минуты)
REMINDER_CHECK_INTERVAL = 60  # Каждые 60 минут

# ==================== ЛОГИРОВАНИЕ ====================

# Уровень логирования (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ==================== РАЗНОЕ ====================

# Таймзона (для корректной работы напоминаний)
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")

# Максимальная длина описания задачи
MAX_TASK_DESCRIPTION_LENGTH = 2000

# Статусы задач
TASK_STATUSES = ["pending", "in_progress", "completed", "cancelled"]

# Приоритеты задач
TASK_PRIORITIES = ["low", "normal", "high", "urgent"]
