# telegram_manager_bot/notifications.py
from aiogram import Bot
from django.conf import settings
from telegram_manager_bot.utils import get_managers_telegram_ids_sync, get_order_details_sync
from telegram_manager_bot.keyboards import get_order_status_keyboard, get_order_details_keyboard # Импортируем новую клавиатуру
import asyncio
from asgiref.sync import sync_to_async

bot = Bot(token=settings.TELEGRAM_MANAGER_BOT_TOKEN)

async def send_new_order_to_managers(order_id):
    """Отправляет уведомление менеджерам о новом заказе."""
    details = await get_order_details_sync(order_id)
    if not details:
        print(f"Заказ с ID {order_id} не найден для уведомления.")
        return

    manager_ids = await get_managers_telegram_ids_sync()
    if not manager_ids:
        print("Нет зарегистрированных менеджеров для уведомления.")
        return

    order_info = (
        f"🚨 НОВЫЙ ЗАКАЗ #{details['id']}\n"
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

    # --- ИЗМЕНЕНИЕ: Используем клавиатуру с деталями и статусами ---
    # keyboard = get_order_status_keyboard(details['id'])
    keyboard = get_order_details_keyboard(details['id']) # Теперь сразу кнопки статуса и "назад"
    # --- /ИЗМЕНЕНИЕ ---

    for tg_id in manager_ids:
        try:
            # Отправка изображений (если есть)
            for img_path in details['image_paths']:
                try:
                    with open(img_path, 'rb') as image_file:
                        await bot.send_photo(chat_id=tg_id, photo=image_file)
                except Exception as e:
                    print(f"Ошибка отправки изображения {img_path} менеджеру {tg_id}: {e}")
            # Отправка текста с клавиатурой
            await bot.send_message(chat_id=tg_id, text=order_info, reply_markup=keyboard)
        except Exception as e:
            print(f"Ошибка отправки уведомления менеджеру {tg_id}: {e}")

# Функция для запуска корутин из синхронного кода (сигналов)
def run_async_notification(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(coro)