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
    print(f"[DEBUG orders.py] /orders команда получена от {message.from_user.id}")
    telegram_id = message.from_user.id
    user = await get_user_by_telegram_id_sync(telegram_id)
    print(f"[DEBUG orders.py] Найден пользователь: {user}")

    if not user or not is_user_manager(user):
        print(f"[DEBUG orders.py] Пользователь {telegram_id} не является менеджером или не найден.")
        await message.answer("У вас нет прав для просмотра заказов.")
        return

    print(f"[DEBUG orders.py] Получаем список новых заказов...")
    orders = await sync_to_async(list)(Order.objects.filter(status='new').order_by('-created_at'))
    print(f"[DEBUG orders.py] Найдено {len(orders)} заказов.")

    if not orders:
        print(f"[DEBUG orders.py] Нет заказов для отображения.")
        await message.answer("Нет заказов для отображения.")
        await message.answer("Меню:", reply_markup=get_manager_main_keyboard())
        return

    keyboard = get_orders_list_keyboard(orders)
    await message.answer("Список заказов:", reply_markup=keyboard)
    print(f"[DEBUG orders.py] Отправлен список заказов.")

@router.callback_query(lambda c: c.data.startswith('m_view_order_'))
async def process_view_order_callback(callback_query: types.CallbackQuery):
    print(f"[DEBUG orders.py] Callback 'm_view_order_' получена: {callback_query.data}")
    telegram_id = callback_query.from_user.id
    user = await get_user_by_telegram_id_sync(telegram_id)
    print(f"[DEBUG orders.py] Найден пользователь для просмотра заказа: {user}")

    if not user or not is_user_manager(user):
        print(f"[DEBUG orders.py] Пользователь {telegram_id} не является менеджером или не найден для просмотра заказа.")
        await callback_query.answer("У вас нет прав для просмотра заказов.", show_alert=True)
        return

    # --- ИСПРАВЛЕНИЕ: Корректное извлечение ID ---
    # Было: callback_query.data.split('_', 2)[-1] -> 'order_13'
    # Стало:
    try:
        # Разбиваем по '_' и берём последнюю часть ('order_13')
        order_part = callback_query.data.split('_')[-1]
        # Извлекаем ID как целое число из этой части
        order_id = int(order_part)
        print(f"[DEBUG orders.py] ID заказа преобразован в число: {order_id}")
    except (ValueError, IndexError):
        print(f"[DEBUG orders.py] Ошибка преобразования ID заказа из callback_data: {callback_query.data}")
        await callback_query.answer("Ошибка обработки запроса.", show_alert=True)
        return
    # --- /ИСПРАВЛЕНИЕ ---

    print(f"[DEBUG orders.py] Получаем детали заказа #{order_id}...")
    details = await get_order_details_sync(order_id)
    print(f"[DEBUG orders.py] Детали заказа получены: {details is not None}")
    if not details:
        print(f"[DEBUG orders.py] Детали заказа #{order_id} не найдены.")
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
    print(f"[DEBUG orders.py] Отправлены детали заказа #{order_id}.")

@router.callback_query(lambda c: c.data == 'm_back_to_orders')
async def process_back_to_orders_callback(callback_query: types.CallbackQuery):
    print(f"[DEBUG orders.py] Callback 'm_back_to_orders' получена.")
    telegram_id = callback_query.from_user.id
    user = await get_user_by_telegram_id_sync(telegram_id)
    print(f"[DEBUG orders.py] Найден пользователь для возврата к заказам: {user}")

    if not user or not is_user_manager(user):
        print(f"[DEBUG orders.py] Пользователь {telegram_id} не является менеджером или не найден для возврата.")
        await callback_query.answer("У вас нет прав для просмотра заказов.", show_alert=True)
        return

    print(f"[DEBUG orders.py] Получаем список новых заказов для возврата...")
    orders = await sync_to_async(list)(Order.objects.filter(status='new').order_by('-created_at'))
    print(f"[DEBUG orders.py] Найдено {len(orders)} заказов для возврата.")

    if not orders:
        print(f"[DEBUG orders.py] Нет заказов для отображения при возврате.")
        await callback_query.message.edit_text("Нет заказов для отображения.")
        await callback_query.message.answer("Меню:", reply_markup=get_manager_main_keyboard())
        return

    keyboard = get_orders_list_keyboard(orders)
    await callback_query.message.edit_text(text="Список заказов:", reply_markup=keyboard)
    await callback_query.answer()
    print(f"[DEBUG orders.py] Возвращён список заказов.")

@router.callback_query(lambda c: c.data == 'm_refresh_orders')
async def process_refresh_orders_callback(callback_query: types.CallbackQuery):
    print(f"[DEBUG orders.py] Callback 'm_refresh_orders' получена.")
    telegram_id = callback_query.from_user.id
    user = await get_user_by_telegram_id_sync(telegram_id)
    print(f"[DEBUG orders.py] Найден пользователь для обновления списка: {user}")

    if not user or not is_user_manager(user):
        print(f"[DEBUG orders.py] Пользователь {telegram_id} не является менеджером или не найден для обновления.")
        await callback_query.answer("У вас нет прав для просмотра заказов.", show_alert=True)
        return

    print(f"[DEBUG orders.py] Получаем обновлённый список новых заказов...")
    orders = await sync_to_async(list)(Order.objects.filter(status='new').order_by('-created_at'))
    print(f"[DEBUG orders.py] Найдено {len(orders)} заказов для обновления.")

    if not orders:
        print(f"[DEBUG orders.py] Нет заказов для отображения при обновлении.")
        await callback_query.message.edit_text("Нет заказов для отображения.")
        await callback_query.message.answer("Меню:", reply_markup=get_manager_main_keyboard())
        return

    keyboard = get_orders_list_keyboard(orders)
    await callback_query.message.edit_text(text="Список заказов (обновлён):", reply_markup=keyboard)
    await callback_query.answer()
    print(f"[DEBUG orders.py] Отправлен обновлённый список заказов.")