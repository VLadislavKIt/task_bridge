import os
from dotenv import load_dotenv


load_dotenv()



BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

BOT_TOKEN = BOT_TOKEN.strip()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

OPENAI_API_KEY = OPENAI_API_KEY.strip()

USE_WEBHOOK = os.getenv("USE_WEBHOOK", "False").lower() == "true"

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://your-domain.com")

WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")

HOST = os.getenv("HOST", "0.0.0.0")

PORT = int(os.getenv("PORT", "8000"))

WEB_APP_DOMAIN = os.getenv("WEB_APP_DOMAIN", f"http://{HOST}:{PORT}")

MINI_APP_URL = os.getenv("MINI_APP_URL", f"{WEB_APP_DOMAIN}/webapp/index.html")

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.3"))

OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "500"))

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///taskbridge.db")


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


REMINDER_INTERVALS = [3, 1, 0]  


REMINDER_TIME_HOUR = 9  


REMINDER_CHECK_INTERVAL = 60  

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")

MAX_TASK_DESCRIPTION_LENGTH = 2000

TASK_STATUSES = ["pending", "in_progress", "completed", "cancelled"]

TASK_PRIORITIES = ["low", "normal", "high", "urgent"]
