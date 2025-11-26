# Быстрое развертывание обновлений

## Для применения последних изменений

### 1. Скачать изменения с GitHub
```bash
git pull origin main
```

### 2. Пересобрать Docker образ
```bash
# Полная пересборка с нуля
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Проверить логи
docker-compose logs -f
```

### 3. Проверить что все работает

**Логи должны показать:**
```
INFO - Dist directory: /app/webapp/dist
INFO - Index.html exists: True
INFO - ✓ Mounted assets directory: /app/webapp/dist/assets
```

**НЕ должно быть:**
```
WARNING - Dist directory not found
ERROR - React app not built
```

**Открыть в браузере:**
- http://ваш-домен:8080/?mode=manager&user_id=1
- http://ваш-домен:8080/?mode=executor&user_id=1

## Одной командой (Linux/Mac)

```bash
git pull origin main && \
docker-compose down && \
docker-compose build --no-cache && \
docker-compose up -d && \
docker-compose logs -f
```

## Проверка что обновление применилось

```bash
# Проверить что dist/ существует в контейнере
docker-compose exec web ls -la /app/webapp/dist

# Должно быть:
# drwxr-xr-x assets/
# -rw-r--r-- index.html

# Проверить версию кода
docker-compose exec web cat /app/webapp/app.py | grep "React app not built"

# Должно найти строку с проверкой
```

## Если что-то пошло не так

### Проблема: "React app not built" в логах
```bash
# Значит образ не пересобрался
docker-compose build --no-cache --pull
docker-compose up -d
```

### Проблема: Старый интерфейс все еще показывается
```bash
# Очистить все кеши Docker
docker-compose down -v
docker system prune -a
docker-compose build --no-cache
docker-compose up -d
```

### Проблема: Ошибка при сборке образа
```bash
# Проверить что git pull прошел успешно
git status
git log -1

# Проверить что Dockerfile обновлен
cat Dockerfile | head -20
# Должно начинаться с:
# FROM node:18-alpine AS frontend-builder
```

## Быстрая проверка версии

```bash
# Проверить последний коммит
git log -1 --oneline

# Должно быть что-то вроде:
# ae36f36 Обновлен start_all.bat - автоматическая проверка React сборки
```

## После успешного обновления

Проверьте в браузере:
1. ✅ Открывается React приложение (не старое)
2. ✅ Градиентные карточки статистики
3. ✅ Плавные анимации
4. ✅ Модальное окно добавления исполнителей работает
5. ✅ Нет ошибок в консоли браузера (F12)
