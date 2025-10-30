# telegram_manager_bot/bot.py
import asyncio
import logging
import os
import django
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# --- ИНТЕГРАЦИЯ С DJANGO ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flower_delivery.settings')
django.setup()
# --- /ИНТЕГРАЦИЯ С DJANGO ---

from django.conf import settings
from telegram_manager_bot.handlers import start, orders, analytics, status_tracking

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ---
TELEGRAM_MANAGER_BOT_TOKEN = settings.TELEGRAM_MANAGER_BOT_TOKEN
# --- /ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ---

async def main():
    """Основная функция запуска бота."""
    print("[DEBUG bot.py] Инициализация бота...")
    logger.info("Инициализация бота...")

    # --- ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР БОТА И ДИСПЕТЧЕР ---
    bot = Bot(token=TELEGRAM_MANAGER_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    # --- /ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР БОТА И ДИСПЕТЧЕР ---

    # --- РЕГИСТРАЦИЯ РОУТЕРОВ ---
    dp.include_router(start.router)
    dp.include_router(orders.router)
    dp.include_router(analytics.router)
    dp.include_router(status_tracking.router)
    # --- /РЕГИСТРАЦИЯ РОУТЕРОВ ---

    print("[DEBUG bot.py] Роутеры зарегистрированы.")
    logger.info("Роутеры зарегистрированы.")

    # --- ЗАПУСК БОТА ---
    try:
        print("[DEBUG bot.py] Запуск polling...")
        logger.info("Запуск polling...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        print("[DEBUG bot.py] Сессия бота закрыта.")
        logger.info("Сессия бота закрыта.")

if __name__ == '__main__':
    print("[DEBUG bot.py] main запущен.")
    asyncio.run(main())