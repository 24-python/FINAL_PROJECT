# telegram_bot/bot.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage # Простое хранилище состояний

# --- ИНТЕГРАЦИЯ С DJANGO ---
import os
import django
from django.conf import settings

# Устанавливаем переменную окружения для Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flower_delivery.settings')
django.setup()
# --- /ИНТЕГРАЦИЯ С DJANGO ---

# Импорты обработчиков (теперь путь правильный, так как бот на уровне проекта)
from telegram_bot.handlers.start import router as start_router
from telegram_bot.handlers.auth import router as auth_router
from telegram_bot.handlers.user_handlers import router as user_router
from telegram_bot.handlers.admin_handlers import router as admin_router

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def main():
    bot_token = settings.TELEGRAM_BOT_TOKEN # Должен быть в settings.py
    bot = Bot(token=bot_token)
    storage = MemoryStorage() # Используйте RedisStorage или др. для продакшена
    dp = Dispatcher(storage=storage)

    # Подключаем роутеры
    dp.include_router(start_router)
    dp.include_router(auth_router)
    dp.include_router(user_router)
    dp.include_router(admin_router)

    # Запуск long polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())