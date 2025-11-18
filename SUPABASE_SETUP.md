# 🗄️ Настройка Supabase для TaskBridge

Пошаговая инструкция по настройке Supabase PostgreSQL для проекта TaskBridge.

## 📋 Шаг 1: Создание проекта в Supabase

1. Перейдите на [https://supabase.com](https://supabase.com)
2. Нажмите **"Start your project"** или **"Sign In"**
3. Войдите через GitHub (или создайте аккаунт)
4. Нажмите **"New Project"**
5. Заполните форму:
   - **Name**: `taskbridge` (или любое другое имя)
   - **Database Password**: придумайте надежный пароль (сохраните его!)
   - **Region**: выберите ближайший регион
6. Нажмите **"Create new project"**
7. Дождитесь создания проекта (обычно 1-2 минуты)

## 📋 Шаг 2: Получение Connection String

### Вариант A: Через Dashboard (Простой способ)

1. В боковом меню найдите **"Settings"** (⚙️)
2. Выберите **"Database"**
3. Прокрутите до секции **"Connection string"**
4. Выберите **"URI"** в виде
5. Скопируйте строку подключения

Пример строки:
```
postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxxxxxx.supabase.co:5432/postgres
```

### Вариант B: Составление вручную

Если нужно составить вручную:
```
postgresql://postgres:PASSWORD@HOST:5432/postgres
```

Где:
- `PASSWORD` - ваш пароль базы данных
- `HOST` - хост из настроек проекта (например: `db.xxxxx.supabase.co`)

## 📋 Шаг 3: Настройка .env файла

Создайте или обновите файл `.env` в корне проекта:

```env
BOT_TOKEN=ваш_токен_от_BotFather
DATABASE_URL=postgresql://postgres:ваш_пароль@db.xxxxx.supabase.co:5432/postgres
USE_WEBHOOK=False
PORT=8000
MINI_APP_URL=http://localhost:8000/webapp/index.html
```

⚠️ **ВАЖНО**: Замените `ваш_пароль` и `xxxxx` на реальные значения из вашего проекта Supabase!

## 📋 Шаг 4: Установка зависимостей

```bash
pip install -r requirements.txt
```

Теперь установится `asyncpg` для работы с PostgreSQL (современная асинхронная библиотека).

## 📋 Шаг 5: Инициализация базы данных

```bash
python db/init_db.py
```

Вы увидите:
```
Инициализация базы данных...
✓ Таблицы созданы
✓ Категории инициализированы
✅ База данных успешно инициализирована!
```

## 📋 Шаг 6: Проверка подключения

### В Supabase Dashboard:

1. Откройте **"Table Editor"** в боковом меню
2. Вы должны увидеть таблицы:
   - ✅ `users`
   - ✅ `messages`
   - ✅ `tasks`
   - ✅ `categories`

### Через код:

```bash
python main.py
```

Если все работает - бот запустится без ошибок.

## 🔧 Дополнительные настройки

### Настройка SSL (если нужно)

Если возникают проблемы с SSL, добавьте параметр в строку подключения:

```env
DATABASE_URL=postgresql://postgres:password@host:5432/postgres?sslmode=require
```

### Проверка подключения через Python

Создайте файл `test_db.py`:

```python
from db.database import engine
from sqlalchemy import text

# Проверяем подключение
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print("✅ Подключение к базе данных успешно!")
    print(result.scalar())
```

Запустите:
```bash
python test_db.py
```

## 🗑️ Удаление старой SQLite базы

После успешной миграции на Supabase:

1. Удалите файл `taskbridge.db` из корня проекта (если есть)
2. Убедитесь, что в `.gitignore` есть:
   ```
   *.db
   *.sqlite
   ```

## 🚀 Запуск приложения

```bash
# Проверьте, что .env файл настроен правильно
cat .env

# Запустите бота
python main.py
```

## ⚠️ Troubleshooting

### Проблема: "could not translate host name"

**Решение**: Проверьте URL базы данных в `.env`, убедитесь что `@db.xxxxx.supabase.co` корректный.

### Проблема: "password authentication failed"

**Решение**: Проверьте пароль в `.env`. Пароль из Supabase Dashboard -> Settings -> Database.

### Проблема: "module asyncpg not found"

**Решение**: 
```bash
pip install asyncpg
```

### Проблема: "table does not exist"

**Решение**: Запустите инициализацию БД:
```bash
python db/init_db.py
```

## 📊 Мониторинг БД

В Supabase Dashboard вы можете:
- Просматривать таблицы через **"Table Editor"**
- Выполнять SQL запросы через **"SQL Editor"**
- Мониторить производительность

## 🔒 Безопасность

- ⚠️ **НЕ КОММИТЬТЕ** файл `.env` с реальными паролями в Git
- ⚠️ Добавьте `.env` в `.gitignore`
- ✅ Используйте переменные окружения для production

## 📝 Примеры запросов

### SQL Editor в Supabase:

```sql
-- Посмотреть все задачи
SELECT * FROM tasks ORDER BY created_at DESC LIMIT 10;

-- Посмотреть статистику по категориям
SELECT c.name, COUNT(t.id) as task_count
FROM categories c
LEFT JOIN tasks t ON c.id = t.category_id
GROUP BY c.name;

-- Посмотреть все пользователи
SELECT telegram_id, username, first_name FROM users;
```

## ✅ Готово!

Теперь ваш проект использует Supabase PostgreSQL вместо локальной SQLite базы данных.

Все данные будут храниться в облаке и доступны из любого места.
