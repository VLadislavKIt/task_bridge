# Пересборка Docker образа с React приложением

## Проблема
После обновления на React приложение, Docker контейнер не содержит собранные файлы из `webapp/dist/`.

## Решение

Обновлен Dockerfile для использования multi-stage build:
1. **Stage 1** - собирает React приложение с помощью Node.js
2. **Stage 2** - копирует собранные файлы в Python образ

## Как пересобрать и запустить

### Вариант 1: Docker Compose (рекомендуется)

```bash
# Остановить текущий контейнер
docker-compose down

# Пересобрать образ (с очисткой кеша)
docker-compose build --no-cache

# Запустить
docker-compose up -d

# Проверить логи
docker-compose logs -f
```

### Вариант 2: Только Docker

```bash
# Остановить и удалить старый контейнер
docker stop taskbridge
docker rm taskbridge

# Пересобрать образ
docker build --no-cache -t taskbridge:v2 .

# Запустить с переменными окружения
docker run -d \
  --name taskbridge \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -e BOT_TOKEN="your_bot_token" \
  -e OPENAI_API_KEY="your_openai_key" \
  taskbridge:v2
```

### Вариант 3: Быстрая пересборка (использует кеш)

```bash
docker-compose build
docker-compose up -d
```

## Проверка что все работает

После пересборки и запуска:

1. **Проверьте логи при старте:**
```bash
docker-compose logs | grep -i "dist"
```

Должно быть:
```
INFO - Dist directory: /app/webapp/dist
INFO - Index.html exists: True
INFO - Mounted assets directory: /app/webapp/dist/assets
```

НЕ должно быть:
```
WARNING - Dist directory not found at /app/webapp/dist, trying fallback to index.html
```

2. **Проверьте содержимое контейнера:**
```bash
docker exec -it taskbridge ls -la /app/webapp/dist
```

Должны быть:
```
drwxr-xr-x  assets/
-rw-r--r--  index.html
```

3. **Откройте в браузере:**
- Manager: `http://your-domain:8080/?mode=manager&user_id=1`
- Executor: `http://your-domain:8080/?mode=executor&user_id=1`

Не должно быть ошибок 404 на `/src/main.jsx`

## Устранение проблем

### Ошибка: "Dist directory not found"
**Причина:** Образ собран со старым Dockerfile
**Решение:** Пересоберите с `--no-cache`:
```bash
docker-compose build --no-cache
```

### Ошибка: "GET /src/main.jsx HTTP/1.1" 404
**Причина:** Загружается старый index.html вместо собранного
**Решение:**
1. Проверьте что dist существует в контейнере
2. Пересоберите образ
3. Убедитесь что в логах написано "Mounted assets directory"

### Ошибка при сборке: "npm ERR!"
**Причина:** Проблемы с зависимостями или интернетом
**Решение:**
```bash
# Локально проверьте что сборка работает
cd webapp
npm install
npm run build

# Если локально работает, пересоберите Docker
cd ..
docker-compose build --no-cache
```

### Большой размер образа
**Решение:** Multi-stage build уже используется. Размер должен быть ~500-700MB.
Для уменьшения можно:
1. Использовать alpine образы (уже используется для Node)
2. Очистить npm кеш в Dockerfile:
```dockerfile
RUN npm ci && npm cache clean --force
```

## Автоматизация

Добавьте в CI/CD pipeline:

```yaml
# .github/workflows/docker.yml
name: Build and Push Docker

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Build Docker image
        run: docker build -t taskbridge:latest .

      - name: Test React build exists
        run: |
          docker run --rm taskbridge:latest ls -la /app/webapp/dist

      # ... push to registry
```

## Размер образа

С multi-stage build:
- **Frontend builder stage:** ~400MB (не включается в финальный образ)
- **Final image:** ~500-600MB
  - Python 3.10-slim: ~150MB
  - Python зависимости: ~300MB
  - React build: ~200KB (сжато)
  - Код приложения: ~5MB

## Changelog

### v2.0
- ✅ Добавлен multi-stage build для React
- ✅ Автоматическая сборка frontend при build
- ✅ Оптимизирован .dockerignore
- ✅ Fallback на старый index.html если dist нет
