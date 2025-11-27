# TaskBridge - Установка и запуск на macOS

## Требования

- Python 3.10 или выше
- Node.js 18 или выше
- npm или yarn
- Git

## Установка

### 1. Установка зависимостей macOS

```bash
# Установка Homebrew (если еще не установлен)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Установка Python 3
brew install python@3.10

# Установка Node.js
brew install node
```

### 2. Клонирование репозитория

```bash
git clone https://github.com/VLadislavKIt/task_bridge.git
cd task_bridge
```

### 3. Создание виртуального окружения Python

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Установка зависимостей Python

```bash
pip install -r requirements.txt
```

### 5. Установка зависимостей React

```bash
cd webapp
npm install
npm run build
cd ..
```

### 6. Настройка переменных окружения

Создайте файл `.env` в корневой директории:

```bash
cp .env.example .env
```

Отредактируйте `.env` и добавьте ваши ключи:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
WEB_APP_DOMAIN=https://your-domain.com
```

### 7. Инициализация базы данных

```bash
source venv/bin/activate
python -c "from database.init_db import init_database; init_database()"
```

## Запуск

### Автоматический запуск (рекомендуется)

```bash
chmod +x start_all.sh
./start_all.sh
```

Это запустит:
- Telegram бота (логи в `bot.log`)
- FastAPI веб-приложение на http://localhost:8000 (логи в `webapp.log`)

### Остановка сервисов

```bash
chmod +x stop_all.sh
./stop_all.sh
```

### Ручной запуск

Если вам нужно запустить сервисы по отдельности:

#### Терминал 1 - Telegram Bot
```bash
source venv/bin/activate
python bot/main.py
```

#### Терминал 2 - WebApp
```bash
source venv/bin/activate
uvicorn webapp.app:app --host 0.0.0.0 --port 8000 --reload
```

## Troubleshooting

### Проблема: "Permission denied" при запуске скриптов

Решение:
```bash
chmod +x start_all.sh
chmod +x stop_all.sh
```

### Проблема: "Command not found: python"

Решение: На macOS используйте `python3` вместо `python`:
```bash
python3 -m venv venv
```

### Проблема: Веб-приложение не открывается

1. Проверьте, что React приложение собрано:
```bash
ls webapp/dist/index.html
```

2. Если файла нет, пересоберите:
```bash
cd webapp
npm install
npm run build
cd ..
```

3. Проверьте логи:
```bash
cat webapp.log
cat bot.log
```

### Проблема: "Cannot connect to database"

1. Проверьте, что база данных инициализирована:
```bash
ls data/taskbridge.db
```

2. Если файла нет, инициализируйте:
```bash
source venv/bin/activate
python -c "from database.init_db import init_database; init_database()"
```

### Проблема: Node.js не установлен

```bash
# Установка через Homebrew
brew install node

# Проверка версии
node --version
npm --version
```

## Docker (альтернатива)

Если вы предпочитаете использовать Docker:

```bash
# Сборка и запуск
docker-compose up --build -d

# Остановка
docker-compose down

# Просмотр логов
docker-compose logs -f
```

## Дополнительная информация

- Логи бота: `bot.log`
- Логи веб-приложения: `webapp.log`
- База данных: `data/taskbridge.db`
- PID файлы: `.bot.pid`, `.webapp.pid`

## Поддержка

Если возникли проблемы, создайте issue на GitHub:
https://github.com/VLadislavKIt/task_bridge/issues
