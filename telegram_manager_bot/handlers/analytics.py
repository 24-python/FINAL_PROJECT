# telegram_manager_bot/handlers/analytics.py
from aiogram import Router, types
from aiogram.filters import Command
from telegram_manager_bot.utils import get_orders_for_today_async, get_top_products_async

router = Router()

@router.message(Command("report_today"))
async def cmd_report_today(message: types.Message):
    """Отправляет отчёт за сегодня."""
    print(f"[DEBUG analytics.py] /report_today вызван пользователем {message.from_user.id}")
    orders = await get_orders_for_today_async()
    if orders:
        total_revenue = sum(o['total_price'] for o in orders)
        report_text = f"📊 Отчёт за сегодня ({len(orders)} заказов):\n"
        report_text += f"Общая выручка: {total_revenue} ₽\n"
        for order in orders:
            report_text += f"- Заказ #{order['id']}: {order['status']}, {order['total_price']} ₽\n"
    else:
        report_text = "📊 Отчёт за сегодня: заказов нет."
    await message.answer(report_text)

@router.message(Command("top_products"))
async def cmd_top_products(message: types.Message):
    """Отправляет топ-5 продуктов."""
    print(f"[DEBUG analytics.py] /top_products вызван пользователем {message.from_user.id}")
    top_products = await get_top_products_async()
    if top_products:
        report_text = "🏆 Топ-5 продуктов:\n"
        for i, product in enumerate(top_products, 1):
            report_text += f"{i}. {product['name']} - {product['quantity']} шт.\n"
    else:
        report_text = "🏆 Топ-5 продуктов: пока нет данных."
    await message.answer(report_text)