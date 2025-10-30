# telegram_manager_bot/handlers/orders.py
from aiogram import Router, types
from aiogram.filters import Command
from telegram_manager_bot.keyboards import get_orders_list_keyboard
from telegram_manager_bot.utils import get_all_orders_async, get_order_details_async, update_order_status_async

router = Router()

@router.message(Command("orders"))
async def cmd_orders(message: types.Message):
    """Отправляет список всех заказов."""
    print(f"[DEBUG orders.py] /orders вызван пользователем {message.from_user.id}")
    orders = await get_all_orders_async()
    if orders:
        keyboard = get_orders_list_keyboard(orders)
        await message.answer("Список заказов:", reply_markup=keyboard)
    else:
        await message.answer("Заказов пока нет.")

@router.callback_query(lambda c: c.data.startswith('m_view_order_'))
async def callback_view_order(callback_query: types.CallbackQuery):
    """Показывает детали заказа."""
    order_id = int(callback_query.data.split('_')[-1])
    print(f"[DEBUG orders.py] Просмотр заказа #{order_id} запрошен пользователем {callback_query.from_user.id}")
    details = await get_order_details_async(order_id)
    if details:
        # Формируем текст
        order_info = (
            f"Заказ #{details['id']}\n"
            f"Пользователь: {details['user']}\n"
            f"Статус: {details['status']}\n"
            f"Статус оплаты: {details['payment_status']}\n"
            f"Дата доставки: {details['delivery_date']}\n"
            f"Адрес: {details['delivery_address']}\n"
            f"Телефон: {details['delivery_phone']}\n"
            f"Итого: {details['total_price']} ₽\n"
            f"Комментарий: {details['comment'] or 'Нет'}\n"
            f"Товары:\n" + "\n".join(details['items_list'])
        )
        # Формируем клавиатуру
        from telegram_manager_bot.keyboards import get_order_status_keyboard
        keyboard = get_order_status_keyboard(details['status'].lower()) # Адаптируйте ключ статуса
        await callback_query.message.edit_text(text=order_info, reply_markup=keyboard)
    else:
        await callback_query.answer("Заказ не найден.")
    await callback_query.answer()

@router.callback_query(lambda c: c.data.startswith('m_status_'))
async def callback_change_status(callback_query: types.CallbackQuery):
    """Изменяет статус заказа."""
    data_parts = callback_query.data.split('_')
    if len(data_parts) < 3:
        await callback_query.answer("Неверный формат данных.")
        return

    new_status_key = data_parts[2]
    # Получаем ID заказа из сообщения (если оно содержит ID, иначе нужно передавать в callback_data)
    # Предположим, ID заказа можно извлечь из текста сообщения или хранить в FSM
    # Пока простой способ - предположим, что ID заказа всегда в тексте перед клавиатурой
    message_text = callback_query.message.text
    # Простой парсинг ID из текста "Заказ #123"
    import re
    match = re.search(r'Заказ #(\d+)', message_text)
    if not match:
         # Попробуем из заголовка уведомления "🚨 НОВЫЙ ЗАКАЗ #123"
         match = re.search(r'НОВЫЙ ЗАКАЗ #(\d+)', message_text)
    if not match:
         # Попробуем из "🔄 Статус заказа #123 изменён!"
         match = re.search(r'статус заказа #(\d+)', message_text, re.IGNORECASE)

    if match:
        order_id = int(match.group(1))
        print(f"[DEBUG orders.py] Изменение статуса заказа #{order_id} на {new_status_key} запрошено пользователем {callback_query.from_user.id}")
        old_status, new_status_display = await update_order_status_async(order_id, new_status_key)
        if old_status is not None:
            # Обновляем сообщение с новым статусом
            # Нужно заново получить обновлённые детали
            from telegram_manager_bot.utils import get_order_details_async
            details = await get_order_details_async(order_id)
            if details:
                order_info = (
                    f"Заказ #{details['id']}\n"
                    f"Пользователь: {details['user']}\n"
                    f"Статус: {details['status']}\n" # Уже новый статус
                    f"Статус оплаты: {details['payment_status']}\n"
                    f"Дата доставки: {details['delivery_date']}\n"
                    f"Адрес: {details['delivery_address']}\n"
                    f"Телефон: {details['delivery_phone']}\n"
                    f"Итого: {details['total_price']} ₽\n"
                    f"Комментарий: {details['comment'] or 'Нет'}\n"
                    f"Товары:\n" + "\n".join(details['items_list'])
                )
                from telegram_manager_bot.keyboards import get_order_status_keyboard
                keyboard = get_order_status_keyboard(details['status'].lower())
                await callback_query.message.edit_text(text=order_info, reply_markup=keyboard)
                await callback_query.answer(f"Статус изменён на {new_status_display}")
            else:
                await callback_query.answer("Ошибка обновления информации о заказе.")
        else:
            await callback_query.answer("Заказ не найден.")
    else:
        await callback_query.answer("Не удалось определить ID заказа.")
    await callback_query.answer()

@router.callback_query(lambda c: c.data == 'm_refresh_orders')
async def callback_refresh_orders(callback_query: types.CallbackQuery):
    """Обновляет список заказов."""
    print(f"[DEBUG orders.py] Обновление списка заказов запрошено пользователем {callback_query.from_user.id}")
    orders = await get_all_orders_async()
    if orders:
        keyboard = get_orders_list_keyboard(orders)
        await callback_query.message.edit_reply_markup(reply_markup=keyboard)
    else:
        await callback_query.message.edit_text("Заказов пока нет.")
    await callback_query.answer()