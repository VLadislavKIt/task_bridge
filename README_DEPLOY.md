# 🚀 Деплой TaskBridge на Railway

## Подготовка

1. Создайте аккаунт на [Railway.app](https://railway.app)
2. Установите Railway CLI (опционально):
   ```bash
   npm install -g @railway/cli
   ```

## Шаг 1: Создание проекта на Railway

1. Войдите на Railway.app
2. Нажмите "New Project"
3. Выберите "Deploy from GitHub repo"
4. Подключите ваш GitHub аккаунт
5. Выберите репозиторий TaskBridge_prototype

## Шаг 2: Настройка переменных окружения

В Railway dashboard, перейдите в "Variables" и добавьте:

```env
BOT_TOKEN=ваш_токен_от_BotFather
OPENAI_API_KEY=ваш_openai_api_key
WEB_APP_DOMAIN=https://ваш-домен.up.railway.app
PORT=8000
HOST=0.0.0.0
```

**Важно:** `WEB_APP_DOMAIN` должен быть HTTPS URL вашего Railway приложения!

## Шаг 3: База данных (опционально)

Railway может автоматически предоставить PostgreSQL:

1. В проекте нажмите "New" → "Database" → "Add PostgreSQL"
2. Railway автоматически установит `DATABASE_URL`
3. Обновите `requirements.txt`, добавив `psycopg2-binary`

Для SQLite (по умолчанию) ничего делать не нужно.

## Шаг 4: Деплой

Railway автоматически задеплоит при push в GitHub:

```bash
git add .
git commit -m "Deploy to Railway"
git push origin main
```

Или через Railway CLI:
```bash
railway up
```

## Шаг 5: Получение URL

После деплоя:

1. Перейдите в "Settings" → "Networking" → "Generate Domain"
2. Railway создаст URL вида `your-app.up.railway.app`
3. Скопируйте этот URL
4. Обновите переменную `WEB_APP_DOMAIN` в Railway:
   ```
   WEB_APP_DOMAIN=https://your-app.up.railway.app
   ```

## Шаг 6: Перезапуск

После обновления `WEB_APP_DOMAIN`:

1. Перейдите в "Deployments"
2. Нажмите "Redeploy" на последнем деплое

## Проверка

1. Откройте Telegram и напишите `/start` вашему боту
2. Нажмите "📱 Открыть мою панель задач"
3. Должно открыться WebApp приложение

## Логи

Просмотр логов:
```bash
railway logs
```

Или в Railway dashboard → "Deployments" → выберите деплой → "View Logs"

## Troubleshooting

### WebApp не открывается
- Убедитесь, что `WEB_APP_DOMAIN` использует HTTPS
- Проверьте, что домен сгенерирован в Railway

### Ошибка "Module not found"
- Проверьте `requirements.txt`
- Пересоберите: "Deployments" → "Redeploy"

### База данных не инициализируется
- Проверьте логи: `railway logs`
- Запустите вручную: добавьте в Procfile:
  ```
  release: python -m db.init_db
  web: python main.py
  ```

## Масштабирование

Railway автоматически выделяет ресурсы. Для увеличения:

1. "Settings" → "Resources"
2. Выберите больше RAM/CPU

## Мониторинг

Railway предоставляет метрики в разделе "Metrics":
- CPU usage
- RAM usage
- Network traffic

## Стоимость

- Free tier: $5 кредитов в месяц
- Hobby plan: $5/месяц
- Pro plan: $20/месяц

Для прототипа достаточно Free tier!
