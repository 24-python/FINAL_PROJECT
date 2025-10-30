# telegram_manager_bot/handlers/orders.py
from aiogram import Router, types
from aiogram.filters import Command
from telegram_manager_bot.utils import get_user_by_telegram_id_sync, is_user_manager, get_order_details_sync
from shop.models import Order
from asgiref.sync import sync_to_async
from telegram_manager_bot.keyboards import get_orders_list_keyboard, get_order_details_keyboard, get_manager_main_keyboard

router = Router()

@router.message(Command(commands=['orders']))
async def cmd_orders(message: types.Message):
    telegram_id = message.from_user.id
    user = await get_user_by_telegram_id_sync(telegram_id)

    if not user or not is_user_manager(user):
        await message.answer("У вас нет прав для просмотра заказов.")
        return

    orders = await sync_to_async(list)(Order.objects.filter(status='new').order_by('-created_at'))

    if not orders:
        await message.answer("Нет заказов для отображения.")
        await message.answer("Меню:", reply_markup=get_manager_main_keyboard())
        return

    keyboard = get_orders_list_keyboard(orders)
    await message.answer("Список заказов:", reply_markup=keyboard)

@router.callback_query(lambda c: c.data.startswith('m_view_order_'))
async def process_view_order_callback(callback_query: types.CallbackQuery):
    order_id_str = callback_query.data.split('_', 2)[-1]
    try:
        order_id = int(order_id_str)
    except ValueError:
        await callback_query.answer("Ошибка обработки запроса.", show_alert=True)
        return

    details = await get_order_details_sync(order_id)
    if not details:
        await callback_query.answer("Заказ не найден.", show_alert=True)
        return

    order_info = (
        f"Детали заказа #{details['id']}:\n"
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

    keyboard = get_order_details_keyboard(details['id'])
    await callback_query.message.edit_text(text=order_info, reply_markup=keyboard)
    await callback_query.answer()

@router.callback_query(lambda c: c.data == 'm_back_to_orders')
async def process_back_to_orders_callback(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    user = await get_user_by_telegram_id_sync(telegram_id)

    if not user or not is_user_manager(user):
        await callback_query.answer("У вас нет прав для просмотра заказов.")
        return

    orders = await sync_to_async(list)(Order.objects.filter(status='new').order_by('-created_at'))

    if not orders:
        await callback_query.message.edit_text("Нет заказов для отображения.")
        await callback_query.message.answer("Меню:", reply_markup=get_manager_main_keyboard())
        return

    keyboard = get_orders_list_keyboard(orders)
    await callback_query.message.edit_text(text="Список заказов:", reply_markup=keyboard)
    await callback_query.answer()

@router.callback_query(lambda c: c.data == 'm_refresh_orders')
async def process_refresh_orders_callback(callback_query: types.CallbackQuery):
    telegram_id = callback_query.from_user.id
    user = await get_user_by_telegram_id_sync(telegram_id)

    if not user or not is_user_manager(user):
        await callback_query.answer("У вас нет прав для просмотра заказов.")
        return

    orders = await sync_to_async(list)(Order.objects.filter(status='new').order_by('-created_at'))

    if not orders:
        await callback_query.message.edit_text("Нет заказов для отображения.")
        await callback_query.message.answer("Меню:", reply_markup=get_manager_main_keyboard())
        return

    keyboard = get_orders_list_keyboard(orders)
    await callback_query.message.edit_text(text="Список заказов (обновлён):", reply_markup=keyboard)
    await callback_query.answer()