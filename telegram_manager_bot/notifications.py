# telegram_manager_bot/notifications.py
from aiogram import Bot
from django.conf import settings
from telegram_manager_bot.utils import get_managers_telegram_ids_sync, get_order_details_sync
from telegram_manager_bot.keyboards import get_order_details_keyboard
import asyncio
from asgiref.sync import sync_to_async
import os

bot = Bot(token=settings.TELEGRAM_MANAGER_BOT_TOKEN)

async def send_new_order_to_managers(order_id):
    """Отправляет уведомление менеджерам о новом заказе."""
    print(f"[DEBUG notifications.py] Начало отправки уведомления для заказа #{order_id}") # <-- Отладочный принт
    try:
        details = await get_order_details_sync(order_id)
        print(f"[DEBUG notifications.py] Получены детали: {details}") # <-- Отладочный принт
    except Exception as e:
        print(f"[ERROR notifications.py] Ошибка получения деталей заказа #{order_id}: {e}")
        return # <-- Выходим, если не получили детали

    if not details:
        print(f"[DEBUG notifications.py] Детали заказа #{order_id} пусты или не найдены.")
        return

    try:
        manager_ids = await get_managers_telegram_ids_sync()
    except Exception as e:
        print(f"[ERROR notifications.py] Ошибка получения ID менеджеров: {e}")
        return

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

    keyboard = get_order_details_keyboard(details['id'])

    for tg_id in manager_ids:
        try:
            # Отправка изображений (если есть)
            for img_path in details['image_paths']:
                # Проверяем, существует ли файл
                if os.path.isfile(img_path):
                    try:
                        # --- ИСПРАВЛЕНИЕ: Передаём путь к файлу как строку ---
                        await bot.send_photo(chat_id=tg_id, photo=img_path)
                        # --- /ИСПРАВЛЕНИЕ ---
                        print(f"[DEBUG notifications.py] Изображение {img_path} успешно отправлено менеджеру {tg_id}")
                    except Exception as e:
                        print(f"Ошибка отправки изображения {img_path} менеджеру {tg_id}: {e}")
                else:
                    print(f"Файл изображения не найден: {img_path}")
            # Отправка текста с клавиатурой
            await bot.send_message(chat_id=tg_id, text=order_info, reply_markup=keyboard)
            print(f"[DEBUG notifications.py] Текстовое уведомление успешно отправлено менеджеру {tg_id}")
        except Exception as e:
            print(f"Ошибка отправки уведомления менеджеру {tg_id}: {e}")

# Функция для запуска корутин из синхронного кода (сигналов)
def run_async_notification(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(coro)
    except Exception as e:
        print(f"[ERROR run_async_notification] Ошибка выполнения корутины: {e}")
