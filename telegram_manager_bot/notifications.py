# telegram_manager_bot/notifications.py
from aiogram import Bot
from aiogram.types import FSInputFile
from django.conf import settings
from asgiref.sync import sync_to_async
import asyncio
import threading
import logging

logger = logging.getLogger(__name__)

# --- ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР БОТА (только для этой функции) ---
# bot = Bot(token=settings.TELEGRAM_MANAGER_BOT_TOKEN) # <-- Это не подходит для потока
# --- /ГЛОБАЛЬНЫЙ ЭКЗЕМПЛЯР БОТА ---

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ ID МЕНЕДЖЕРОВ (из utils) ---
from telegram_manager_bot.utils import get_user_by_telegram_id_async # или другая логика получения ID

# Предположим, у вас есть способ получить ID админов, например, через модель UserProfile
async def get_manager_chat_ids():
    """Получает список telegram_id администраторов."""
    # Реализуйте логику получения ID из вашей модели, например, через UserProfile
    # Это пример, адаптируйте под вашу модель
    from accounts.models import UserProfile
    profiles = await sync_to_async(list)(UserProfile.objects.filter(user__is_superuser=True))
    chat_ids = [profile.telegram_id for profile in profiles if profile.telegram_id]
    print(f"[DEBUG notifications.py] Найдены ID админов: {chat_ids}")
    return chat_ids
# --- /ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ---

# --- ФУНКЦИЯ ОТПРАВКИ УВЕДОМЛЕНИЯ О НОВОМ ЗАКАЗЕ ---
async def send_new_order_to_managers(order_id, bot_instance):
    """Отправляет уведомление менеджерам о новом заказе."""
    print(f"[DEBUG notifications.py] Начало отправки уведомления о новом заказе #{order_id}")
    logger.info(f"Отправка уведомления о новом заказе #{order_id}")

    # Импортируем тут, чтобы избежать проблем с циклическими импортами при старте Django
    from telegram_manager_bot.utils import get_order_details_async
    from telegram_manager_bot.keyboards import get_order_status_keyboard # Или другая клавиатура

    try:
        details = await get_order_details_async(order_id)
        print(f"[DEBUG notifications.py] Детали заказа #{order_id}: {details}")
    except Exception as e:
        print(f"[ERROR notifications.py] Ошибка получения деталей заказа #{order_id}: {e}")
        logger.error(f"Ошибка получения деталей заказа #{order_id}: {e}")
        return

    if not details or not details.get('image_paths'):
        print(f"[DEBUG notifications.py] Детали заказа #{order_id} пусты или нет изображений.")
        logger.warning(f"Детали заказа #{order_id} пусты или нет изображений.")
        return

    manager_ids = await get_manager_chat_ids()
    if not manager_ids:
        print("Нет зарегистрированных менеджеров для уведомления.")
        logger.info("Нет зарегистрированных менеджеров для уведомления.")
        return

    # Формируем текст
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

    # Формируем клавиатуру
    keyboard = get_order_status_keyboard(details['status'].lower()) # Адаптируйте ключ статуса

    for tg_id in manager_ids:
        try:
            image_paths = details['image_paths']
            if image_paths:
                # Отправляем первое изображение с описанием
                first_img_path = image_paths[0]
                if os.path.isfile(first_img_path):
                    input_file = FSInputFile(first_img_path)
                    await bot_instance.send_photo(
                        chat_id=tg_id,
                        photo=input_file,
                        caption=order_info_caption,
                        reply_markup=keyboard
                    )
                    print(f"[DEBUG notifications.py] Изображение {first_img_path} с описанием отправлено менеджеру {tg_id}")

                    # Отправляем остальные изображения без описания
                    for img_path in image_paths[1:]:
                        if os.path.isfile(img_path):
                            next_input_file = FSInputFile(img_path)
                            await bot_instance.send_photo(chat_id=tg_id, photo=next_input_file)
                            print(f"[DEBUG notifications.py] Изображение {img_path} отправлено менеджеру {tg_id}")
                        else:
                            print(f"[DEBUG notifications.py] Файл изображения не найден: {img_path}")
                else:
                    print(f"[DEBUG notifications.py] Файл первого изображения не найден: {first_img_path}")
                    # Fallback: отправляем текст
                    await bot_instance.send_message(chat_id=tg_id, text=order_info_caption, reply_markup=keyboard)
                    print(f"[DEBUG notifications.py] Fallback: Текстовое уведомление отправлено менеджеру {tg_id}")
            else:
                # Если нет изображений, отправляем текст
                await bot_instance.send_message(chat_id=tg_id, text=order_info_caption, reply_markup=keyboard)
                print(f"[DEBUG notifications.py] Текстовое уведомление (без изображений) отправлено менеджеру {tg_id}")
        except Exception as e:
            print(f"[ERROR notifications.py] Ошибка отправки уведомления менеджеру {tg_id}: {e}")
            logger.error(f"Ошибка отправки уведомления менеджеру {tg_id} (заказ #{order_id}): {e}")

# --- /ФУНКЦИЯ ОТПРАВКИ УВЕДОМЛЕНИЯ О НОВОМ ЗАКАЗЕ ---

# --- ФУНКЦИЯ ОТПРАВКИ УВЕДОМЛЕНИЯ О СМЕНЕ СТАТУСА ---
async def send_order_status_update_to_managers(order_id, old_status, new_status, user_id, bot_instance):
    """Отправляет уведомление менеджерам об изменении статуса заказа."""
    print(f"[DEBUG notifications.py] Начало отправки уведомления об изменении статуса заказа #{order_id}")
    logger.info(f"Отправка уведомления об изменении статуса заказа #{order_id} с '{old_status}' на '{new_status}'")

    # Импортируем тут
    from django.contrib.auth.models import User
    from telegram_manager_bot.utils import get_manager_chat_ids

    try:
        user = await sync_to_async(User.objects.get)(id=user_id)
        username = user.username
        message_text = f"🔄 Статус заказа #{order_id} изменён!\nПользователь: {username}\nСтарый статус: {old_status}\nНовый статус: {new_status}"
    except User.DoesNotExist:
        username = f"ID:{user_id}"
        message_text = f"🔄 Статус заказа #{order_id} изменён!\nПользователь: {username} (имя не найдено)\nСтарый статус: {old_status}\nНовый статус: {new_status}"
    except Exception as e:
        print(f"[ERROR notifications.py] Ошибка получения данных для уведомления о смене статуса заказа {order_id}: {e}")
        logger.error(f"Ошибка получения данных для уведомления о смене статуса заказа {order_id}: {e}")
        return

    manager_ids = await get_manager_chat_ids()
    if not manager_ids:
        print("Нет зарегистрированных менеджеров для уведомления о смене статуса.")
        logger.info("Нет зарегистрированных менеджеров для уведомления о смене статуса.")
        return

    for tg_id in manager_ids:
        try:
            await bot_instance.send_message(chat_id=tg_id, text=message_text)
            print(f"[DEBUG notifications.py] Уведомление об изменении статуса заказа #{order_id} отправлено менеджеру {tg_id}")
            logger.info(f"Уведомление об изменении статуса заказа #{order_id} отправлено менеджеру {tg_id}")
        except Exception as e:
            print(f"[ERROR notifications.py] Ошибка отправки уведомления об изменении статуса заказа #{order_id} менеджеру {tg_id}: {e}")
            logger.error(f"Ошибка отправки уведомления об изменении статуса заказа #{order_id} менеджеру {tg_id}: {e}")

# --- /ФУНКЦИЯ ОТПРАВКИ УВЕДОМЛЕНИЯ О СМЕНЕ СТАТУСА ---

# --- ФУНКЦИЯ ДЛЯ ЗАПУСКА КОУТИН ИЗ СИНХРОННОГО КОДА (DJANGO SIGNALS) ---
def run_async_notification(coro_func, *args):
    """
    Запускает асинхронную корутину из синхронного кода в отдельном потоке.
    Создаёт новый цикл событий и новый экземпляр Bot в потоке.
    """
    print(f"[DEBUG notifications.py] run_async_notification вызвана для {coro_func.__name__ if hasattr(coro_func, '__name__') else 'coroutine'}")
    logger.debug(f"run_async_notification вызвана для корутины: {coro_func.__name__ if hasattr(coro_func, '__name__') else 'unknown'}")

    def run_coroutine():
        from aiogram import Bot # Импортируем Bot внутри потока
        bot_instance = Bot(token=settings.TELEGRAM_MANAGER_BOT_TOKEN)
        print(f"[DEBUG notifications.py] Новый экземпляр Bot создан в потоке {threading.current_thread().name}")
        logger.debug(f"Новый экземпляр Bot создан в потоке {threading.current_thread().name}")

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            print(f"[DEBUG notifications.py] Новый цикл событий создан в потоке {threading.current_thread().name}")
            logger.debug(f"Новый цикл событий создан в потоке {threading.current_thread().name}")

            try:
                coro = coro_func(*args, bot_instance)
                loop.run_until_complete(coro)
                print(f"[DEBUG notifications.py] Корутина {coro_func.__name__ if hasattr(coro_func, '__name__') else 'unknown'} выполнена в потоке {threading.current_thread().name}")
                logger.debug(f"Корутина {coro_func.__name__ if hasattr(coro_func, '__name__') else 'unknown'} выполнена в потоке {threading.current_thread().name}")
            finally:
                loop.close()
                asyncio.set_event_loop(None)
        except Exception as e:
            print(f"[ERROR run_async_notification] Ошибка в потоке: {e}")
            logger.error(f"Ошибка в потоке выполнения корутины: {e}")
        finally:
            # Закрываем сессию бота в потоке
            try:
                temp_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(temp_loop)
                temp_loop.run_until_complete(bot_instance.session.close())
                temp_loop.close()
                asyncio.set_event_loop(None)
                print(f"[DEBUG notifications.py] Сессия Bot закрыта в потоке {threading.current_thread().name}")
                logger.debug(f"Сессия Bot закрыта в потоке {threading.current_thread().name}")
            except Exception as e:
                print(f"[ERROR run_async_notification] Ошибка при закрытии сессии Bot: {e}")
                logger.error(f"Ошибка при закрытии сессии Bot: {e}")

    thread = threading.Thread(target=run_coroutine)
    thread.start()
    # thread.join() # Обычно не ждём завершения потока в сигнале Django

# --- /ФУНКЦИЯ ДЛЯ ЗАПУСКА КОУТИН ИЗ СИНХРОННОГО КОДА ---