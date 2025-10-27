# telegram_bot/handlers/admin_handlers.py
from aiogram import Router
from aiogram.types import Message, CallbackQuery # Добавлены импорты
from aiogram.filters import Command
from telegram_bot.utils import get_user_by_telegram_id_sync, is_user_admin
from shop.models import Order, OrderItem
from telegram_bot.keyboards import get_order_status_keyboard
# --- ИМПОРТ ДЛЯ АСИНХРОННОСТИ ---
from asgiref.sync import sync_to_async
# --- /ИМПОРТ ДЛЯ АСИНХРОННОСТИ ---

router = Router()

@router.message(lambda message: message.text == "Новые заказы")
async def show_new_orders(message: Message):
    telegram_id = message.from_user.id
    user = await get_user_by_telegram_id_sync(telegram_id) # Вызов асинхронной функции

    if not user or not is_user_admin(user):
        await message.answer("У вас нет прав для просмотра новых заказов.")
        return

    # Показываем заказы со статусом 'new' - синхронная операция, оборачиваем
    orders = await sync_to_async(list)(Order.objects.filter(status='new').order_by('-created_at'))

    if not orders:
        await message.answer("Нет новых заказов.")
        return

    for order in orders:
        # Получаем OrderItem - синхронная операция, оборачиваем
        items = await sync_to_async(list)(OrderItem.objects.filter(order=order))
        items_str = "\n".join([f"- {item.product.name} x{item.quantity}" for item in items])
        order_info = (
            f"Новый Заказ #{order.id}\n"
            f"Пользователь: {order.user.username} (ID: {order.user.id})\n"
            f"Статус: {order.get_status_display()}\n"
            f"Статус оплаты: {order.get_payment_status_display()}\n"
            f"Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"Адрес: {order.delivery_address}\n"
            f"Телефон: {order.delivery_phone}\n"
            f"Итого: {order.total_price} ₽\n"
            f"Товары:\n{items_str}\n"
        )
        # Отправляем информацию и клавиатуру для изменения статуса
        await message.answer(order_info, reply_markup=get_order_status_keyboard(order.id))

# Обработчик callback для изменения статуса
@router.callback_query(lambda c: c.data.startswith('status_'))
async def process_status_callback(callback_query: CallbackQuery):
    telegram_id = callback_query.from_user.id
    user = await get_user_by_telegram_id_sync(telegram_id) # Вызов асинхронной функции

    if not user or not is_user_admin(user):
        await callback_query.answer("У вас нет прав для изменения статуса.", show_alert=True)
        return

    # Извлекаем ID заказа и новый статус из callback_data
    _, order_id_str, new_status = callback_query.data.split('_', 2)
    try:
        order_id = int(order_id_str)
    except ValueError:
        await callback_query.answer("Ошибка обработки запроса.", show_alert=True)
        return

    try:
        # Получаем заказ - синхронная операция, оборачиваем
        order = await sync_to_async(Order.objects.get)(id=order_id)
        old_status = order.get_status_display()
        order.status = new_status
        # Сохраняем заказ - синхронная операция, оборачиваем
        await sync_to_async(order.save)()
        await callback_query.answer(f"Статус заказа #{order_id} изменён с '{old_status}' на '{order.get_status_display()}'.")
        # Обновляем сообщение с заказом
        # Получаем OrderItem - синхронная операция, оборачиваем
        items = await sync_to_async(list)(OrderItem.objects.filter(order=order))
        items_str = "\n".join([f"- {item.product.name} x{item.quantity}" for item in items])
        order_info = (
            f"Заказ #{order.id} - Обновлен\n"
            f"Статус: {order.get_status_display()}\n"
            f"Статус оплаты: {order.get_payment_status_display()}\n"
            f"Адрес: {order.delivery_address}\n"
            f"Телефон: {order.delivery_phone}\n"
            f"Итого: {order.total_price} ₽\n"
            f"Товары:\n{items_str}\n"
        )
        await callback_query.message.edit_text(text=order_info, reply_markup=get_order_status_keyboard(order.id))

    except Order.DoesNotExist:
        await callback_query.answer("Заказ не найден.", show_alert=True)

# Обработчик callback для изменения статуса оплаты (опционально)
@router.callback_query(lambda c: c.data.startswith('pay_status_'))
async def process_payment_status_callback(callback_query: CallbackQuery):
    telegram_id = callback_query.from_user.id
    user = await get_user_by_telegram_id_sync(telegram_id) # Вызов асинхронной функции

    if not user or not is_user_admin(user):
        await callback_query.answer("У вас нет прав для изменения статуса оплаты.", show_alert=True)
        return

    _, order_id_str, new_p_status = callback_query.data.split('_', 2)
    try:
        order_id = int(order_id_str)
    except ValueError:
        await callback_query.answer("Ошибка обработки запроса.", show_alert=True)
        return

    try:
        # Получаем заказ - синхронная операция, оборачиваем
        order = await sync_to_async(Order.objects.get)(id=order_id)
        old_p_status = order.get_payment_status_display()
        order.payment_status = new_p_status
        # Сохраняем заказ - синхронная операция, оборачиваем
        await sync_to_async(order.save)()
        await callback_query.answer(f"Статус оплаты заказа #{order_id} изменён с '{old_p_status}' на '{order.get_payment_status_display()}'.")
        # Обновляем сообщение аналогично статусу
        # Получаем OrderItem - синхронная операция, оборачиваем
        items = await sync_to_async(list)(OrderItem.objects.filter(order=order))
        items_str = "\n".join([f"- {item.product.name} x{item.quantity}" for item in items])
        order_info = (
            f"Заказ #{order.id} - Обновлен\n"
            f"Статус: {order.get_status_display()}\n"
            f"Статус оплаты: {order.get_payment_status_display()}\n"
            f"Адрес: {order.delivery_address}\n"
            f"Телефон: {order.delivery_phone}\n"
            f"Итого: {order.total_price} ₽\n"
            f"Товары:\n{items_str}\n"
        )
        await callback_query.message.edit_text(text=order_info, reply_markup=get_order_status_keyboard(order.id))

    except Order.DoesNotExist:
        await callback_query.answer("Заказ не найден.", show_alert=True)