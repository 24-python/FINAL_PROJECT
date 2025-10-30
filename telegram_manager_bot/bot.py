# telegram_manager_bot/bot.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# --- ИНТЕГРАЦИЯ С DJANGO ---
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flower_delivery.settings')
django.setup()
# --- /ИНТЕГРАЦИЯ С DJANGO ---

from telegram_manager_bot.handlers.start import router as start_router
from telegram_manager_bot.handlers.order_notifications import router as order_router
from telegram_manager_bot.handlers.status_tracking import router as status_router
from telegram_manager_bot.handlers.analytics import router as analytics_router
# --- НОВЫЙ РОУТЕР ---
from telegram_manager_bot.handlers.orders import router as orders_router
# --- /НОВЫЙ РОУТЕР ---

logging.basicConfig(level=logging.INFO)

async def main():
    bot_token = settings.TELEGRAM_MANAGER_BOT_TOKEN
    if not bot_token:
        raise ValueError("TELEGRAM_MANAGER_BOT_TOKEN не задан в settings.py")
    bot = Bot(token=bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.include_router(start_router)
    dp.include_router(order_router) # Пока без обработчиков, только для регистрации
    dp.include_router(status_router)
    dp.include_router(analytics_router)
    # --- ВКЛЮЧАЕМ НОВЫЙ РОУТЕР ---
    dp.include_router(orders_router)
    # --- /ВКЛЮЧАЕМ НОВЫЙ РОУТЕР ---

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
