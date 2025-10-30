# telegram_manager_bot/handlers/status_tracking.py
from aiogram import Router, types
from aiogram.filters import Command
from telegram_manager_bot.utils import get_user_by_telegram_id_sync, is_user_manager, get_order_details_sync
from shop.models import Order
from asgiref.sync import sync_to_async
from telegram_manager_bot.keyboards import get_order_status_keyboard

# --- ИМПОРТ ФУНКЦИИ ОТПРАВКИ КЛАВИАТУРЫ ---
from telegram_manager_bot.handlers.start import send_manager_keyboard
# --- /ИМПОРТ ---

router = Router()

@router.callback_query(lambda c: c.data.startswith('m_status_'))
async def process_manager_status_callback(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    # --- ИСПОЛЬЗУЕМ АСИНХРОННУЮ ОБЁРТКУ ---
    user = await get_user_by_telegram_id_sync(telegram_id)
    # --- /ИСПОЛЬЗУЕМ АСИНХРОННУЮ ОБЁРТКУ ---

    if not user or not is_user_manager(user):
        await callback_query.answer("У вас нет прав для изменения статуса.", show_alert=True)
        return

    _, order_id_str, new_status = callback_query.data.split('_', 2)
    try:
        order_id = int(order_id_str)
    except ValueError:
        await callback_query.answer("Ошибка обработки запроса.", show_alert=True)
        return

    try:
        # --- ИСПОЛЬЗУЕМ sync_to_async ---
        order = await sync_to_async(Order.objects.get)(id=order_id)
        # --- /ИСПОЛЬЗУЕМ sync_to_async ---
        old_status = order.get_status_display()
        order.status = new_status
        # --- ИСПОЛЬЗУЕМ sync_to_async ---
        await sync_to_async(order.save)()
        # --- /ИСПОЛЬЗУЕМ sync_to_async ---
        await callback_query.answer(f"Статус заказа #{order_id} изменён с '{old_status}' на '{order.get_status_display()}'.")
        # После изменения статуса, отправляем клавиатуру менеджера
        await send_manager_keyboard(callback_query.message) # Используем функцию для отправки клавиатуры

    except Order.DoesNotExist:
        await callback_query.answer("Заказ не найден.", show_alert=True)
