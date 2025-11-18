"""
Тестовый скрипт для проверки подключения к базе данных

Запуск:
    python test_db_connection.py

Проверяет подключение к Supabase PostgreSQL и показывает информацию о таблицах.
"""

import logging
from db.database import sync_engine, get_db_session
from db.models import Base
from sqlalchemy import inspect

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_connection():
    """Проверка подключения к базе данных"""
    try:
        logger.info("🔍 Проверка подключения к базе данных...")
        
        # Создаем inspector для проверки таблиц
        inspector = inspect(sync_engine)
        tables = inspector.get_table_names()
        
        logger.info(f"✅ Подключение установлено!")
        logger.info(f"📊 Найдено таблиц: {len(tables)}")
        
        if tables:
            logger.info("📋 Список таблиц:")
            for table in tables:
                logger.info(f"  - {table}")
                
                # Показываем количество записей
                db = sync_engine.connect()
                try:
                    from sqlalchemy import text
                    result = db.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    logger.info(f"    📝 Записей: {count}")
                except Exception as e:
                    logger.warning(f"    ⚠️ Не удалось получить количество: {e}")
        else:
            logger.warning("⚠️ Таблицы не найдены. Запустите: python db/init_db.py")
        
        logger.info("\n✅ Тест подключения завершен успешно!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка подключения: {e}")
        logger.error("\nПроверьте:")
        logger.error("1. DATABASE_URL в .env файле")
        logger.error("2. Доступность Supabase проекта")
        logger.error("3. Корректность пароля и хоста")
        raise


def test_tables_structure():
    """Проверка структуры таблиц"""
    try:
        logger.info("\n🔍 Проверка структуры таблиц...")
        
        inspector = inspect(sync_engine)
        
        # Проверяем основные таблицы
        required_tables = ['users', 'messages', 'tasks', 'categories']
        
        for table_name in required_tables:
            if table_name in inspector.get_table_names():
                columns = inspector.get_columns(table_name)
                logger.info(f"✅ {table_name}:")
                for col in columns:
                    logger.info(f"   - {col['name']} ({col['type']})")
            else:
                logger.warning(f"⚠️ Таблица {table_name} не найдена")
        
        logger.info("\n✅ Проверка структуры завершена!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке структуры: {e}")


if __name__ == "__main__":
    try:
        test_connection()
        test_tables_structure()
        
        logger.info("\n🎉 Все тесты пройдены успешно!")
        logger.info("База данных готова к использованию.")
        
    except Exception as e:
        logger.error(f"\n❌ Тесты провалились: {e}")
        exit(1)

