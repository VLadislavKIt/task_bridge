# 🏗️ Архитектура TaskBridge

## 📊 Общая схема системы

```
┌─────────────────────────────────────────────────────────────────┐
│                         TELEGRAM                                 │
│  ┌──────────────┐         ┌──────────────┐                      │
│  │  Group Chat  │◄───────►│  Bot Client  │                      │
│  │  (Messages)  │         │   (aiogram)  │                      │
│  └──────────────┘         └──────┬───────┘                      │
│                                   │                               │
└───────────────────────────────────┼───────────────────────────────┘
                                    │
                    ┌───────────────▼────────────────┐
                    │      TASKBRIDGE SERVER         │
                    │         (Railway)              │
                    │                                │
                    │  ┌─────────────────────────┐  │
                    │  │   Bot Handlers Layer     │  │
                    │  │   - Message Analysis     │  │
                    │  │   - Task Confirmation    │  │
                    │  │   - Notifications        │  │
                    │  └──────────┬───────────────┘  │
                    │             │                   │
                    │  ┌──────────▼───────────────┐  │
                    │  │   AI Extraction Layer     │  │
                    │  │   - OpenAI GPT-4o-mini   │  │
                    │  │   - Task Parsing         │  │
                    │  │   - Date/Time Detection  │  │
                    │  └──────────┬───────────────┘  │
                    │             │                   │
                    │  ┌──────────▼───────────────┐  │
                    │  │   Business Logic Layer    │  │
                    │  │   - Task Management      │  │
                    │  │   - User Management      │  │
                    │  │   - Reminder System      │  │
                    │  └──────────┬───────────────┘  │
                    │             │                   │
                    │  ┌──────────▼───────────────┐  │
                    │  │    FastAPI REST API       │  │
                    │  │   - /api/tasks           │  │
                    │  │   - /api/files           │  │
                    │  │   - /api/comments        │  │
                    │  └──────────┬───────────────┘  │
                    │             │                   │
                    │  ┌──────────▼───────────────┐  │
                    │  │   Database Layer (ORM)    │  │
                    │  │   - SQLAlchemy 2.0       │  │
                    │  │   - SQLite / PostgreSQL  │  │
                    │  └──────────────────────────┘  │
                    └────────────┬───────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌──────────────┐      ┌──────────────┐        ┌──────────────┐
│   Telegram   │      │   Telegram   │        │   Telegram   │
│   Mini App   │      │   Mini App   │        │  Background  │
│  (Manager)   │      │  (Executor)  │        │  Scheduler   │
│              │      │              │        │  (APScheduler)│
│ - View tasks │      │ - My tasks   │        │              │
│ - Assign     │      │ - Upload     │        │ - Reminders  │
│ - Monitor    │      │ - Comments   │        │ - Deadlines  │
└──────────────┘      └──────────────┘        └──────────────┘
```

## 🧩 Компоненты системы

### 1. **Telegram Bot (aiogram 3.3.0+)**
**Путь:** `bot/handlers.py`, `main.py`

**Функции:**
- Получение сообщений из групповых чатов
- Обработка команд `/start`, `/help`
- Callback-обработчики для inline-кнопок
- Отправка уведомлений пользователям
- Обработка файлов (фото, документы)

**Режим работы:**
- **Polling mode** (для разработки и простоты деплоя)
- Постоянное соединение с Telegram API
- Обработка событий в реальном времени

---

### 2. **AI Extraction Engine (OpenAI GPT-4o-mini)**
**Путь:** `bot/ai_extractor.py`

**Функции:**
- Анализ текста сообщения на наличие задачи
- Извлечение структурированных данных:
  - Название задачи
  - Описание
  - Исполнитель (`@username`)
  - Дедлайн (естественный язык → datetime)
  - Приоритет (low/normal/high/urgent)

**Особенности:**
- JSON mode для структурированного ответа
- Fallback на keyword matching (если AI недоступен)
- Поддержка русского языка
- Умная обработка времени ("до вечера" → 18:00)

**Пример промпта:**
```
Сообщение: "@alex сделай отчет по продажам до завтра"
Ответ: {
  "has_task": true,
  "task": {
    "title": "Сделать отчет по продажам",
    "assignee_username": "alex",
    "due_date": "2025-11-19 23:59:59",
    "priority": "normal"
  }
}
```

---

### 3. **Database Layer (SQLAlchemy 2.0 + SQLite/PostgreSQL)**
**Путь:** `db/models.py`, `db/database.py`

**Таблицы:**

#### `users`
```python
- id (PK)
- telegram_id (уникальный)
- username
- first_name, last_name
- created_at
```

#### `tasks`
```python
- id (PK)
- title, description
- status (pending/in_progress/completed/cancelled)
- priority (low/normal/high/urgent)
- assigned_to (FK → users)
- due_date
- created_at, updated_at
```

#### `pending_tasks`
```python
- id (PK)
- title, description
- assignee_username
- status (pending/confirmed/rejected)
- created_by_id (FK → users)
- chat_id (Telegram group ID)
```

#### `task_files`
```python
- id (PK)
- task_id (FK → tasks)
- file_type (photo/document/video)
- file_id (Telegram file_id)
- uploaded_by_id (FK → users)
```

#### `comments`
```python
- id (PK)
- task_id (FK → tasks)
- user_id (FK → users)
- text
- created_at
```

---

### 4. **REST API (FastAPI)**
**Путь:** `webapp/app.py`

**Endpoints:**

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/tasks` | Список задач (фильтры: status, category, assigned_to) |
| GET | `/api/tasks/{id}` | Детали задачи |
| PATCH | `/api/tasks/{id}/status` | Обновление статуса |
| GET | `/api/tasks/{id}/files` | Файлы задачи |
| GET | `/api/tasks/{id}/comments` | Комментарии задачи |
| POST | `/api/tasks/{id}/comments` | Добавить комментарий |
| GET | `/api/categories` | Список категорий |
| GET | `/api/users` | Список пользователей |
| GET | `/api/stats` | Общая статистика |

**CORS:** Настроен для Telegram WebApp

---

### 5. **Telegram Mini App (WebApp)**
**Путь:** `webapp/index.html`

**Два режима работы:**

#### **Manager Mode** (`?mode=manager&user_id=X`)
- Просмотр всех задач команды
- Фильтрация по статусу, категории
- Детали задачи с файлами и комментариями
- Статистика по задачам

#### **Executor Mode** (`?mode=executor&user_id=X`)
- Только задачи, назначенные пользователю
- Загрузка отчётных файлов
- Добавление комментариев
- Обновление статуса задачи

**Технологии:**
- Vanilla JavaScript (без фреймворков)
- Telegram WebApp SDK
- Адаптивный дизайн
- Темная тема Telegram

---

### 6. **Reminder System (APScheduler)**
**Путь:** `bot/reminders.py`

**Функции:**
- Проверка задач каждые 60 минут
- Отправка напоминаний:
  - За 3 дня до дедлайна
  - За 1 день до дедлайна
  - В день дедлайна (09:00)
  - При просрочке

**Логика:**
```python
if hours_until_due < 0:
    send_reminder(task, "overdue")
elif 0 <= hours_until_due <= 24:
    send_reminder(task, "due_today")
elif days_until_due in [3, 1]:
    send_reminder(task, "upcoming")
```

---

## 🔄 Поток работы (Workflow)

### 1. **Создание задачи**

```
1. Руководитель пишет в группе: "@alex сделай отчет до вечера"
   ↓
2. Бот анализирует сообщение через OpenAI
   ↓
3. AI извлекает: title, assignee, due_date, priority
   ↓
4. Бот отправляет руководителю подтверждение:
   "🤖 AI обнаружил задачу! [Подтвердить] [Отклонить]"
   ↓
5. Руководитель нажимает "✅ Подтвердить"
   ↓
6. Задача создаётся в БД (status=pending)
   ↓
7. Бот отправляет уведомление исполнителю:
   - Если исполнитель начал чат → личное сообщение
   - Если НЕ начал чат → упоминание в группе
   ↓
8. Руководитель получает кнопку "📊 Открыть панель управления"
```

### 2. **Выполнение задачи**

```
1. Исполнитель получает уведомление с кнопками:
   [📱 Открыть панель] [▶️ Начать] [✅ Выполнено]
   ↓
2. Нажимает "▶️ Начать выполнение"
   ↓
3. Статус меняется: pending → in_progress
   ↓
4. Кнопка обновляется: остаётся только [✅ Выполнено]
   ↓
5. Исполнитель может:
   - Загрузить фото/документы (отчёты)
   - Добавить комментарии
   - Просмотреть детали в WebApp
   ↓
6. Исполнитель нажимает "✅ Выполнено"
   ↓
7. Статус меняется: in_progress → completed
   ↓
8. Руководитель видит обновление в панели управления
```

### 3. **Мониторинг и напоминания**

```
APScheduler работает фоново каждые 60 минут:
   ↓
1. Проверяет все задачи с дедлайнами
   ↓
2. Вычисляет время до дедлайна
   ↓
3. Отправляет напоминания:
   - Просрочено → "⚠️ Задача просрочена!"
   - Сегодня → "🔔 Задача должна быть выполнена сегодня"
   - За 1-3 дня → "📅 Напоминание о задаче"
   ↓
4. Повторяет проверку через 60 минут
```

---

## 🛠️ Технологический стек

| Компонент | Технология | Версия |
|-----------|------------|--------|
| Язык | Python | 3.10+ |
| Telegram Bot | aiogram | 3.3.0+ |
| AI Engine | OpenAI API | GPT-4o-mini |
| Web Framework | FastAPI | Latest |
| ORM | SQLAlchemy | 2.0+ |
| Database | SQLite (dev) / PostgreSQL (prod) | - |
| Task Scheduler | APScheduler | Latest |
| Frontend | Vanilla JS + Telegram WebApp SDK | - |
| Deployment | Railway.app | - |
| VCS | Git + GitHub | - |

---

## 📦 Структура проекта

```
TaskBridge_prototype/
├── bot/
│   ├── __init__.py
│   ├── handlers.py          # Обработчики Telegram событий
│   ├── ai_extractor.py      # AI-движок для извлечения задач
│   └── reminders.py         # Система напоминаний
├── db/
│   ├── __init__.py
│   ├── models.py            # SQLAlchemy модели
│   ├── database.py          # Настройка БД
│   └── init_db.py           # Инициализация схемы
├── webapp/
│   ├── __init__.py
│   ├── app.py               # FastAPI приложение
│   └── index.html           # Telegram Mini App
├── config.py                # Конфигурация (env variables)
├── main.py                  # Точка входа
├── requirements.txt         # Python зависимости
├── Procfile                 # Railway deployment config
├── .env.example             # Шаблон переменных окружения
└── README.md                # Документация проекта
```

---

## 🔐 Безопасность

### Переменные окружения
```env
BOT_TOKEN=xxx                # Telegram Bot Token
OPENAI_API_KEY=xxx           # OpenAI API Key
WEB_APP_DOMAIN=https://...   # HTTPS URL приложения
DATABASE_URL=xxx             # Connection string БД
```

### Защита данных
- ✅ API ключи хранятся в переменных окружения
- ✅ HTTPS для WebApp (требование Telegram)
- ✅ Валидация входных данных через Pydantic
- ✅ SQL Injection защита (ORM)
- ✅ Rate limiting на стороне Telegram

---

## 🚀 Deployment (Railway)

### Процесс деплоя
```bash
1. git push origin main
   ↓
2. Railway автоматически обнаруживает изменения
   ↓
3. Railway устанавливает зависимости (requirements.txt)
   ↓
4. Railway запускает команду из Procfile: "python main.py"
   ↓
5. Приложение стартует:
   - FastAPI сервер на порту $PORT
   - Telegram Bot (polling mode)
   - APScheduler для напоминаний
   ↓
6. Deployment готов! ✅
```

### Мониторинг
- Логи доступны в Railway Dashboard
- Метрики: CPU, RAM, Network
- Автоматический перезапуск при сбоях

---

## 📈 Метрики производительности

| Метрика | Значение |
|---------|----------|
| Время ответа бота | < 1 сек |
| AI обработка сообщения | 2-4 сек |
| API response time | < 100ms |
| Concurrent users | 100+ |
| Database queries | Оптимизированы (eager loading) |

---

## 🎯 Ключевые фичи

1. ✅ **AI-powered task extraction** - автоматическое извлечение задач
2. ✅ **Smart time parsing** - "до вечера" → 18:00
3. ✅ **Dual WebApp modes** - отдельные интерфейсы для менеджеров и исполнителей
4. ✅ **File attachments** - фото и документы как отчёты
5. ✅ **Comment system** - обсуждение задач
6. ✅ **Automatic reminders** - напоминания о дедлайнах
7. ✅ **Group notifications** - fallback для пользователей без чата с ботом
8. ✅ **Category auto-classification** - умная категоризация задач

---

## 🔮 Планы развития (Roadmap)

- [ ] Webhook mode вместо polling (масштабируемость)
- [ ] PostgreSQL для production (вместо SQLite)
- [ ] Редактирование задач через WebApp
- [ ] Приоритизация задач (drag-and-drop)
- [ ] Интеграция с календарями (Google Calendar)
- [ ] Аналитика и отчёты (dashboard)
- [ ] Поддержка нескольких команд (workspaces)
- [ ] Push-уведомления в WebApp
