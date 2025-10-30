# telegram_manager_bot/handlers/status_tracking.py
from aiogram import Router, types
from aiogram.filters import Command
from telegram_manager_bot.utils import get_orders_by_status_async

router = Router()

# Пример: команда для просмотра заказов по статусу
@router.message(Command("orders_new")) # или /orders_confirmed и т.д.
async def cmd_orders_by_status(message: types.Message):
    """Отправляет список заказов по статусу (например, 'new')."""
    # Извлекаем статус из команды
    command_parts = message.text.split()
    if len(command_parts) < 2:
        await message.answer("Используйте команду в формате /orders_new, /orders_confirmed и т.д.")
        return

    status_key = command_parts[1].lower()
    print(f"[DEBUG status_tracking.py] /orders_{status_key} вызван пользователем {message.from_user.id}")
    orders = await get_orders_by_status_async(status_key)
    if orders:
        report_text = f"Заказы со статусом '{status_key}':\n"
        for order in orders:
            report_text += f"- Заказ #{order['id']}: {order['total_price']} ₽\n"
    else:
        report_text = f"Заказов со статусом '{status_key}' нет."
    await message.answer(report_text)