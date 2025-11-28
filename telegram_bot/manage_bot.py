# telegram_bot/manage_bot.py
# !/usr/bin/env python3
import asyncio
import time
from telegram.ext import Application
from bot.config import BotConfig
from bot.handlers import BotHandlers
from bot.django_client import DjangoClient
from bot.utils import OrderChecker


class FlowerDeliveryBot:
    """Основной класс бота для уведомлений о заказах"""

    def __init__(self):
        self.config = BotConfig()
        self.django_client = DjangoClient()
        self.order_checker = OrderChecker()
        self.handlers = BotHandlers()

    async def run_polling(self):
        """Запускает бота в режиме polling"""
        try:
            # Валидируем конфигурацию
            BotConfig.validate()

            # Создаем приложение
            application = Application.builder().token(BotConfig.TELEGRAM_TOKEN).build()

            # Настраиваем обработчики
            self.handlers.setup_handlers(application)

            print("🤖 Бот запущен в режиме polling...")
            print("📍 Проверяем новые заказы каждые 30 секунд")

            # Запускаем polling
            await application.initialize()
            await application.start()
            await application.updater.start_polling()

            # Запускаем проверку заказов в фоне
            asyncio.create_task(self.check_orders_periodically())

            # Бесконечный цикл
            while True:
                await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ Ошибка при запуске бота: {e}")

    async def check_orders_periodically(self):
        """Периодически проверяет новые заказы"""
        while True:
            try:
                await self.check_new_orders()
                await asyncio.sleep(30)  # Проверяем каждые 30 секунд
            except Exception as e:
                print(f"❌ Ошибка при проверке заказов: {e}")
                await asyncio.sleep(60)  # Ждем больше при ошибке

    async def check_new_orders(self):
        """Проверяет и отправляет уведомления о новых заказах"""
        try:
            # Получаем последние заказы (теперь асинхронно)
            orders = await self.django_client.get_new_orders(limit=5)

            if orders:
                print(f"📊 Найдено заказов: {len(orders)}")

            # Фильтруем только новые
            new_orders = self.order_checker.get_new_orders_for_notification(orders)

            if new_orders:
                print(f"🎉 Новые заказы для уведомлений: {len(new_orders)}")

            # Отправляем уведомления
            for order in new_orders:
                print(f"📦 Отправляем уведомление о заказе #{order['id']}")
                await self.handlers.send_order_notification(order)

        except Exception as e:
            print(f"❌ Ошибка при проверке новых заказов: {e}")


async def main():
    """Точка входа"""
    bot = FlowerDeliveryBot()
    await bot.run_polling()


if __name__ == '__main__':
    asyncio.run(main())