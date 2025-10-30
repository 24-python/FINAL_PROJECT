# telegram_manager_bot/handlers/status_tracking.py
from aiogram import Router, types
from aiogram.filters import Command
from telegram_manager_bot.utils import get_user_by_telegram_id_sync, is_user_manager
from shop.models import Order
from asgiref.sync import sync_to_async
from telegram_manager_bot.handlers.start import send_manager_keyboard

router = Router()

@router.callback_query(lambda c: c.data.startswith('m_status_'))
async def process_manager_status_callback(callback_query: types.CallbackQuery):
    print(f"[DEBUG status_tracking.py] Callback 'm_status_' получена: {callback_query.data}")
    telegram_id = callback_query.from_user.id
    user = await get_user_by_telegram_id_sync(telegram_id)
    print(f"[DEBUG status_tracking.py] Найден пользователь для изменения статуса: {user}")

    if not user or not is_user_manager(user):
        print(f"[DEBUG status_tracking.py] Пользователь {telegram_id} не является менеджером или не найден для изменения статуса.")
        await callback_query.answer("У вас нет прав для изменения статуса.", show_alert=True)
        return

    # --- ИСПРАВЛЕНИЕ: Корректное извлечение ID и статуса ---
    try:
        parts = callback_query.data.split('_')
        if len(parts) < 4 or parts[0] != 'm' or parts[1] != 'status':
            raise ValueError("Неверный формат callback_data")
        order_id_str = parts[2]
        new_status = '_'.join(parts[3:])
        print(f"[DEBUG status_tracking.py] Извлечён ID заказа: {order_id_str}, новый статус: {new_status}")
        order_id = int(order_id_str)
        print(f"[DEBUG status_tracking.py] ID заказа преобразован в число: {order_id}")
    except (ValueError, IndexError) as e:
        print(f"[DEBUG status_tracking.py] Ошибка преобразования ID заказа или статуса из callback_data '{callback_query.data}': {e}")
        await callback_query.answer("Ошибка обработки запроса.", show_alert=True)
        return
    # --- /ИСПРАВЛЕНИЕ ---

    try:
        print(f"[DEBUG status_tracking.py] Получаем заказ #{order_id} из базы...")
        # --- УЛУЧШЕНИЕ: Используем select_related для избежания дополнительных запросов ---
        order = await sync_to_async(Order.objects.select_related('user').get)(id=order_id)
        # --- /УЛУЧШЕНИЕ ---
        print(f"[DEBUG status_tracking.py] Заказ #{order_id} получен (ID: {order.id}).") # <-- ИЗМЕНЕНО: Без вызова __str__
        old_status = order.get_status_display()
        print(f"[DEBUG status_tracking.py] Старый статус: {old_status}, новый статус: {new_status}")
        order.status = new_status
        print(f"[DEBUG status_tracking.py] Сохраняем заказ #{order_id} с новым статусом...")
        await sync_to_async(order.save)()
        print(f"[DEBUG status_tracking.py] Заказ #{order_id} успешно сохранён.")
        await callback_query.answer(f"Статус заказа #{order_id} изменён с '{old_status}' на '{order.get_status_display()}'.")
        await send_manager_keyboard(callback_query.message)

    except Order.DoesNotExist:
        print(f"[DEBUG status_tracking.py] Заказ #{order_id} не найден в базе.")
        await callback_query.answer("Заказ не найден.", show_alert=True)
