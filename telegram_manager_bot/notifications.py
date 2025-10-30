# telegram_manager_bot/notifications.py
from aiogram import Bot
from aiogram.types import FSInputFile
from django.conf import settings
from django.contrib.auth.models import User
from telegram_manager_bot.utils import get_managers_telegram_ids_sync, get_order_details_sync
from telegram_manager_bot.keyboards import get_order_details_keyboard
import asyncio
from asgiref.sync import sync_to_async
import os

bot = Bot(token=settings.TELEGRAM_MANAGER_BOT_TOKEN)

async def send_new_order_to_managers(order_id):
    """Отправляет уведомление менеджерам о новом заказе."""
    print(f"[DEBUG notifications.py] Начало отправки уведомления о новом заказе #{order_id}")
    try:
        details = await get_order_details_sync(order_id)
        print(f"[DEBUG notifications.py] Получены детали нового заказа: {details}")
    except Exception as e:
        print(f"[ERROR notifications.py] Ошибка получения деталей нового заказа #{order_id}: {e}")
        return # <-- Выходим, если не получили детали

    if not details:
        print(f"[DEBUG notifications.py] Детали нового заказа #{order_id} пусты или не найдены.")
        return

    try:
        manager_ids = await get_managers_telegram_ids_sync()
    except Exception as e:
        print(f"[ERROR notifications.py] Ошибка получения ID менеджеров для нового заказа: {e}")
        return

    if not manager_ids:
        print("Нет зарегистрированных менеджеров для уведомления о новом заказе.")
        return

    # Подготовим основной текст уведомления (caption)
    order_info_caption = (
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
            image_paths = details['image_paths']
            if image_paths:
                # --- ЛОГИКА: Отправить ПЕРВОЕ изображение с caption ---
                first_img_path = image_paths[0]
                if os.path.isfile(first_img_path):
                    try:
                        input_file = FSInputFile(first_img_path)
                        # Отправляем фото с описанием и клавиатурой
                        await bot.send_photo(
                            chat_id=tg_id,
                            photo=input_file,
                            caption=order_info_caption,
                            reply_markup=keyboard # Клавиатура прикрепляется к первому сообщению
                        )
                        print(f"[DEBUG notifications.py] Изображение {first_img_path} с описанием нового заказа успешно отправлено менеджеру {tg_id}")
                        # --- ЛОГИКА: Отправить ОСТАЛЬНЫЕ изображения (если есть) БЕЗ caption ---
                        for img_path in image_paths[1:]:
                            if os.path.isfile(img_path):
                                try:
                                    next_input_file = FSInputFile(img_path)
                                    await bot.send_photo(chat_id=tg_id, photo=next_input_file)
                                    print(f"[DEBUG notifications.py] Дополнительное изображение {img_path} нового заказа успешно отправлено менеджеру {tg_id}")
                                except Exception as e:
                                    print(f"Ошибка отправки дополнительного изображения {img_path} нового заказа менеджеру {tg_id}: {e}")
                            else:
                                print(f"Файл дополнительного изображения нового заказа не найден: {img_path}")
                    except Exception as e:
                        print(f"Ошибка отправки первого изображения с описанием {first_img_path} менеджеру {tg_id}: {e}")
                        # --- Аварийный fallback: если не удалось отправить фото, отправим текст ---
                        await bot.send_message(chat_id=tg_id, text=order_info_caption, reply_markup=keyboard)
                        print(f"[DEBUG notifications.py] Fallback: Текстовое уведомление (из-за ошибки фото) о новом заказе успешно отправлено менеджеру {tg_id}")
                else:
                    print(f"Файл первого изображения нового заказа не найден: {first_img_path}")
                    # --- Аварийный fallback: если файл не найден, отправим текст ---
                    await bot.send_message(chat_id=tg_id, text=order_info_caption, reply_markup=keyboard)
                    print(f"[DEBUG notifications.py] Fallback: Текстовое уведомление (из-за отсутствия фото) о новом заказе успешно отправлено менеджеру {tg_id}")
            else:
                # Если изображений нет, отправим просто текст
                await bot.send_message(chat_id=tg_id, text=order_info_caption, reply_markup=keyboard)
                print(f"[DEBUG notifications.py] Текстовое уведомление (без изображений) о новом заказе успешно отправлено менеджеру {tg_id}")

        except Exception as e:
            print(f"Ошибка отправки уведомления о новом заказе менеджеру {tg_id}: {e}")


# --- НОВАЯ ФУНКЦИЯ: Уведомление об изменении статуса ---
async def send_order_status_update_to_managers(order_id, old_status, new_status, user_id):
    """
    Отправляет уведомление менеджерам об изменении статуса заказа.
    """
    print(f"[DEBUG notifications.py] Начало отправки уведомления об изменении статуса заказа #{order_id}")
    try:
        # Получаем имя пользователя по его ID
        user = await sync_to_async(User.objects.get)(id=user_id)
        username = user.username
        print(f"[DEBUG notifications.py] Пользователь заказа: {username}")
    except User.DoesNotExist:
        username = f"ID:{user_id}"
        print(f"[DEBUG notifications.py] Пользователь с ID {user_id} не найден, используем ID.")
    except Exception as e:
        username = "Неизвестный пользователь"
        print(f"[ERROR notifications.py] Ошибка получения имени пользователя {user_id}: {e}")

    try:
        manager_ids = await get_managers_telegram_ids_sync()
    except Exception as e:
        print(f"[ERROR notifications.py] Ошибка получения ID менеджеров для уведомления о смене статуса: {e}")
        return

    if not manager_ids:
        print("Нет зарегистрированных менеджеров для уведомления о смене статуса.")
        return

    message_text = (
        f"🔄 Статус заказа #{order_id} изменён!\n"
        f"Пользователь: {username}\n"
        f"Старый статус: {old_status}\n"
        f"Новый статус: {new_status}\n"
    )

    for tg_id in manager_ids:
        try:
            # Отправляем текстовое сообщение
            await bot.send_message(chat_id=tg_id, text=message_text)
            print(f"[DEBUG notifications.py] Уведомление об изменении статуса заказа #{order_id} успешно отправлено менеджеру {tg_id}")
        except Exception as e:
            print(f"Ошибка отправки уведомления об изменении статуса заказа #{order_id} менеджеру {tg_id}: {e}")

# --- /НОВАЯ ФУНКЦИЯ: Уведомление об изменении статуса ---


# --- ФУНКЦИЯ ДЛЯ ЗАПУСКА КОУТИН ИЗ СИНХРОННОГО КОДА ---
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
# --- /ФУНКЦИЯ ДЛЯ ЗАПУСКА КОУТИН ИЗ СИНХРОННОГО КОДА ---
