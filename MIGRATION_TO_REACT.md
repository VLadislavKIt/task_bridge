# Миграция на единое React приложение

## Изменения

### Что было раньше:
- ❌ Два разных веб-приложения
- ❌ Старое на ванильном JavaScript (webapp/index.html со скриптами)
- ❌ Новое на React (требовало сборки)
- ❌ Fallback логика между старым и новым
- ❌ Путаница какое приложение используется

### Что стало:
- ✅ **Одно приложение** - только React
- ✅ **Обязательная сборка** - `npm run build` перед запуском
- ✅ **Чистая архитектура** - нет legacy кода
- ✅ **Строгая проверка** - приложение не запустится без сборки
- ✅ **Единая точка входа** - dist/index.html

## Технические детали

### Удалено:
- Старый JavaScript код из index.html
- Fallback логика в app.py
- Множественные варианты интерфейса

### Добавлено:
- Проверка наличия dist/ при старте приложения
- Понятные сообщения об ошибках если сборка не выполнена
- RuntimeError если React не собран

### Структура webapp/:
```
webapp/
├── dist/                    # Production сборка (создается npm run build)
│   ├── assets/
│   │   ├── index.css        # ~11 KB
│   │   └── index.js         # ~195 KB
│   └── index.html           # Главный файл
├── src/                     # Исходники React
│   ├── components/
│   ├── services/
│   ├── utils/
│   ├── styles/
│   ├── App.jsx
│   └── main.jsx
├── index.html              # Шаблон для Vite (не используется напрямую)
├── package.json
├── vite.config.js
└── app.py                  # FastAPI backend
```

## Режимы работы

### Development (разработка)
```bash
cd webapp
npm install
npm run dev
```
- Hot reload при изменениях
- Доступно на http://localhost:5173
- Proxy на FastAPI backend (localhost:8000)
- Используется для разработки интерфейса

### Production (продакшен)
```bash
cd webapp
npm install
npm run build
cd ..
uvicorn webapp.app:app --host 0.0.0.0 --port 8000
```
- Оптимизированная сборка
- Минификация и сжатие
- Все ресурсы в dist/
- FastAPI раздает статику из dist/

### Docker
```bash
docker-compose build --no-cache
docker-compose up -d
```
- Multi-stage build
- Автоматическая сборка React
- Готовый production образ

## Проверка правильности настройки

### 1. Проверить что dist/ существует:
```bash
ls -la webapp/dist/
# Должно быть:
# assets/
# index.html
```

### 2. Запустить FastAPI и проверить логи:
```bash
uvicorn webapp.app:app --reload
```

**Правильные логи:**
```
INFO - Webapp directory: /path/to/webapp
INFO - Dist directory: /path/to/webapp/dist
INFO - Index.html exists: True
INFO - ✓ Mounted assets directory: /path/to/webapp/dist/assets
```

**Неправильные логи (ошибка):**
```
ERROR - React app not built! Please run 'npm run build' in webapp/ directory
RuntimeError: React application not built...
```

### 3. Открыть в браузере:
- Manager: http://localhost:8000/?mode=manager&user_id=1
- Executor: http://localhost:8000/?mode=executor&user_id=1

**Должно быть:**
- ✅ Современный интерфейс с градиентами
- ✅ Плавные анимации
- ✅ Никаких ошибок в консоли

**Не должно быть:**
- ❌ Ошибок 404 на /src/main.jsx
- ❌ Белого экрана
- ❌ Старого дизайна

## Для разработчиков

### Изменение интерфейса:
1. Запустить dev режим: `cd webapp && npm run dev`
2. Редактировать файлы в src/
3. Изменения применяются автоматически
4. После завершения: `npm run build`
5. Закоммитить изменения (но НЕ dist/)

### Изменение API:
1. Редактировать webapp/app.py
2. Перезапустить FastAPI: `uvicorn webapp.app:app --reload`
3. React автоматически использует новое API

### Добавление нового компонента:
1. Создать файл в src/components/
2. Импортировать в нужном месте
3. Проверить в dev режиме
4. Собрать: `npm run build`

## Распространенные проблемы

### "React app not built!" при запуске
**Решение:**
```bash
cd webapp
npm install
npm run build
```

### Изменения в React не применяются
**Причина:** Запущен production режим
**Решение:**
```bash
cd webapp
npm run dev  # Используйте dev режим для разработки
```

### Ошибка 404 на /assets/...
**Причина:** dist/ не создан или пуст
**Решение:**
```bash
cd webapp
rm -rf dist
npm run build
```

### В Docker старое приложение
**Причина:** Образ собран до обновления Dockerfile
**Решение:**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Преимущества единого приложения

1. **Проще поддерживать** - один кодбейс вместо двух
2. **Современный стек** - React, Vite, современный JavaScript
3. **Лучшая производительность** - оптимизация сборки
4. **Единообразие** - один дизайн для всех
5. **Легче развивать** - добавление функций в одном месте
6. **Меньше багов** - нет рассинхрона между версиями

## Обратная совместимость

API endpoints остались без изменений:
- GET /api/tasks
- GET /api/tasks/{id}
- POST /api/tasks/{id}/comments
- POST /api/tasks/{id}/assignees
- DELETE /api/tasks/{id}/assignees/{user_id}
- и т.д.

React приложение использует те же API, что и старое приложение.

## Чеклист для deployment

- [ ] npm install выполнен
- [ ] npm run build выполнен успешно
- [ ] dist/ содержит index.html и assets/
- [ ] FastAPI запускается без ошибок
- [ ] Логи показывают "✓ Mounted assets directory"
- [ ] WebApp открывается в браузере
- [ ] Нет ошибок в консоли браузера
- [ ] Manager режим работает
- [ ] Executor режим работает
- [ ] Добавление/удаление исполнителей работает
- [ ] Комментарии работают
- [ ] Уведомления приходят в Telegram
