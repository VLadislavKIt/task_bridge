import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, USE_WEBHOOK, WEBHOOK_PATH, WEBHOOK_URL, HOST, PORT
from bot.handlers import router, init_default_categories
from bot.email_registration import router as email_router
from bot.reminders import start_reminder_scheduler, stop_reminder_scheduler
from db.database import init_db, get_db_session
from webapp.app import app as webapp_app
import uvicorn


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def start_bot_polling():
    """Запуск бота в режиме polling (для разработки)"""

    init_db()
    logger.info("Database initialized")


    db = get_db_session()
    try:
        init_default_categories(db)
        logger.info("Default categories initialized")
    finally:
        db.close()


    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Регистрируем роутеры
    dp.include_router(router)
    dp.include_router(email_router)

    logger.info("Bot started in polling mode")

 
    start_reminder_scheduler(bot)
    logger.info("Reminder scheduler started")

    try:

        await dp.start_polling(bot, handle_as_tasks=False)
    except Exception as e:
        logger.error(f"Error in bot polling: {e}")
    finally:
        stop_reminder_scheduler()
        await bot.session.close()


async def start_bot_webhook():
    init_db()
    logger.info("Database initialized")
    
   
    db = get_db_session()
    try:
        init_default_categories(db)
        logger.info("Default categories initialized")
    finally:
        db.close()
    
    
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Регистрируем роутеры
    dp.include_router(router)
    dp.include_router(email_router)

    try:
       
        await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
        logger.info(f"Webhook set to {WEBHOOK_URL + WEBHOOK_PATH}")
        
        
        loop = asyncio.get_event_loop()
        loop.create_task(uvicorn.Server(uvicorn.Config(webapp_app, host=HOST, port=8080)))
        
      
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Error in bot webhook: {e}")
    finally:
        await bot.session.close()


def start_webapp():
    """Запуск веб-приложения"""
    import os
    
    port = int(os.environ.get("PORT", PORT))
    logger.info(f"Starting web app on {HOST}:{port}")
    uvicorn.run(webapp_app, host=HOST, port=port)


async def main():
    
    if USE_WEBHOOK:
        logger.info("Starting in webhook mode")
        await start_bot_webhook()
    else:
        logger.info("Starting in polling mode")
        
     
        import threading
        webapp_thread = threading.Thread(target=start_webapp, daemon=True)
        webapp_thread.start()
        logger.info("Web app started in background thread")
        
        
        await start_bot_polling()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
