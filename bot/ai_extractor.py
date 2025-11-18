import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from openai import OpenAI
from dateutil import parser as date_parser
import pytz

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TEMPERATURE, OPENAI_MAX_TOKENS, TIMEZONE

logger = logging.getLogger(__name__)


client = OpenAI(api_key=OPENAI_API_KEY)


def get_current_datetime() -> str:
    
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d %H:%M:%S %Z")


SYSTEM_PROMPT = """Ты — AI-ассистент для извлечения задач из сообщений в Telegram чатах.

Твоя задача — анализировать текст сообщения и определять:
1. Содержит ли сообщение задачу (поручение)?
2. Если да, извлечь детали задачи.

ВАЖНО:
- Текущая дата и время: {current_datetime}
- Относительные даты преобразуй в абсолютные даты в формате "YYYY-MM-DD HH:MM:SS"
- Username ОБЯЗАТЕЛЬНО извлекай если указан через @username или по имени
- Если сообщение начинается с @username - это ВСЕГДА исполнитель задачи
- assignee_username возвращай БЕЗ символа @ (только username)
- Приоритет: "срочно", "важно", "urgent" = high; "когда будет время" = low; остальное = normal

ПРАВИЛА ПАРСИНГА ВРЕМЕНИ:
- "до вечера" / "к вечеру" → сегодня 18:00
- "до обеда" / "к обеду" → сегодня 13:00
- "до утра" / "к утру" → завтра 09:00
- "до конца дня" → сегодня 23:59
- "завтра" → завтра 23:59
- "послезавтра" → через 2 дня 23:59
- "на следующей неделе" → следующий понедельник 23:59
- "в пятницу" → ближайшая пятница 23:59
- "через 3 дня" → текущая дата + 3 дня, 23:59

Ответ СТРОГО в формате JSON:
{{
  "has_task": true/false,
  "task": {{
    "title": "краткое описание задачи (макс 100 символов)",
    "description": "полное описание задачи",
    "assignee_username": "username без @ или null если не указан",
    "due_date": "YYYY-MM-DD HH:MM:SS или null",
    "priority": "low/normal/high/urgent"
  }}
}}

Примеры:

Сообщение: "@alex сделай отчет по продажам до завтра"
Ответ:
{{
  "has_task": true,
  "task": {{
    "title": "Сделать отчет по продажам",
    "description": "Сделать отчет по продажам до завтра",
    "assignee_username": "alex",
    "due_date": "2025-11-16 23:59:59",
    "priority": "normal"
  }}
}}

Сообщение: "@bdcmflex сделай выкладку по товарам и отправь мне фотоотчет"
Ответ:
{{
  "has_task": true,
  "task": {{
    "title": "Сделать выкладку по товарам",
    "description": "Сделать выкладку по товарам и отправить фотоотчет",
    "assignee_username": "bdcmflex",
    "due_date": null,
    "priority": "normal"
  }}
}}

Сообщение: "Саша, срочно исправь баг с авторизацией к вечеру"
Ответ:
{{
  "has_task": true,
  "task": {{
    "title": "Исправить баг с авторизацией",
    "description": "Срочно исправить баг с авторизацией к вечеру",
    "assignee_username": "Саша",
    "due_date": "2025-11-15 18:00:00",
    "priority": "high"
  }}
}}

Сообщение: "Хорошая погода сегодня"
Ответ:
{{
  "has_task": false,
  "task": null
}}

Отвечай ТОЛЬКО JSON, без дополнительных комментариев!
"""


async def analyze_message_with_ai(text: str) -> Optional[Dict[str, Any]]:
  
    if not text or len(text.strip()) == 0:
        return None

    try:
        # Получаем текущую дату и время
        current_dt = get_current_datetime()

        # Формируем промпт с текущей датой
        system_prompt = SYSTEM_PROMPT.format(current_datetime=current_dt)

        # Вызываем OpenAI API
        logger.info(f"Calling OpenAI API to analyze message: {text[:50]}...")

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS,
            response_format={"type": "json_object"}
        )

        
        result_text = response.choices[0].message.content
        logger.info(f"OpenAI response: {result_text}")

        
        result = json.loads(result_text)

        
        if not isinstance(result, dict) or "has_task" not in result:
            logger.error(f"Invalid AI response format: {result}")
            return None

        
        if not result.get("has_task", False):
            return result

        
        task = result.get("task")
        if task and task.get("due_date"):
            try:
                
                due_date_str = task["due_date"]
                task["due_date_parsed"] = date_parser.parse(due_date_str)
            except Exception as date_error:
                logger.warning(f"Failed to parse due_date: {task.get('due_date')}, error: {date_error}")
                task["due_date_parsed"] = None

        return result

    except Exception as e:
        logger.error(f"Error in AI analysis: {e}", exc_info=True)
        return None


def extract_task_simple(text: str) -> bool:
    
    if not text:
        return False

    text_lower = text.lower()

    
    task_keywords = [
        "сделать", "нужно", "необходимо", "надо", "требуется",
        "выполни", "подготовь", "создай", "напиши", "исправь",
        "проверь", "убедись", "организуй", "настрой",
        "до", "к", "срочно", "важно", "deadline",
        "need", "should", "must", "todo", "task",
        "please", "fix", "create", "update", "check"
    ]

    for keyword in task_keywords:
        if keyword in text_lower:
            return True

    
    if '@' in text:
        return True

    return False


async def analyze_message(text: str, use_ai: bool = True) -> Optional[Dict[str, Any]]:
    
    if not text:
        return None

    # Если AI включен, пробуем использовать его
    if use_ai:
        try:
            result = await analyze_message_with_ai(text)
            if result is not None:
                return result
            else:
                
                logger.warning("AI returned None, using simple extraction")
        except Exception as e:
            logger.error(f"AI analysis failed: {e}, using simple extraction")

    
    has_task = extract_task_simple(text)

    if has_task:
        return {
            "has_task": True,
            "task": {
                "title": text[:100],  
                "description": text,
                "assignee_username": None,
                "due_date": None,
                "due_date_parsed": None,
                "priority": "normal"
            }
        }
    else:
        return {
            "has_task": False,
            "task": None
        }
