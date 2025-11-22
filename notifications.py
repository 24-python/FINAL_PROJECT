# notifications.py
# pip install python-telegram-bot django

import logging
import os
import django
from telegram import InputFile # Для отправки файлов (изображений)
from telegram.helpers import escape_markdown # Для экранирования специальных символов в сообщениях

# --- 1. Настройка Django ORM ---
# Убедитесь, что этот скрипт импортируется в контексте, где уже настроена среда Django
# или настройте sys.path и os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flower_delivery.settings') и вызовите django.setup()
# В данном случае, мы ожидаем, что setup() будет вызван извне (например, в shop/views.py перед импортом).
# Однако, для автономного тестирования можно добавить:
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flower_delivery.settings')
# django.setup()

# Импорт моделей Django (после setup() в месте импорта)
from shop.models import Order, OrderItem, Product
from accounts.models import UserProfile
from asgiref.sync import sync_to_async

# --- 2. Настройка логирования ---
logging.basicConfig(
    format='%(asctime)s - notifications - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 3. Функция отправки уведомления о заказе админам ---
async def send_order_notification(application, order_id):
    """
    Асинхронная функция для отправки уведомления о новом заказе всем авторизованным админам.
    Вызывается из Django.
    """
    try:
        # Получаем заказ и связанные данные асинхронно
        order = await sync_to_async(
            Order.objects.select_related('user').prefetch_related('orderitem_set__product').first
        )(id=order_id)

        if not order:
            logger.warning(f"Заказ с ID {order_id} не найден для отправки уведомления.")
            return

        # Берем первый OrderItem для получения изображения продукта
        first_item = await sync_to_async(lambda: order.orderitem_set.first())()
        product_image_path = None
        if first_item:
            product_image_path = first_item.product.image.path if first_item.product.image else None

        # Формируем текст сообщения
        user_username = escape_markdown(order.user.username, version=2) # Экранируем специальные символы
        total_price = order.total_price
        delivery_date_str = order.delivery_date.strftime('%d.%m.%Y %H:%M') if order.delivery_date else 'Не указана'
        delivery_address = escape_markdown(order.delivery_address, version=2) if order.delivery_address else 'Не указан'
        delivery_phone = escape_markdown(order.delivery_phone, version=2) if order.delivery_phone else 'Не указан'

        message_text = (
            f"🆕 *Новый Заказ #{order.id}*\n\n"
            f"👤 *Пользователь:* {user_username}\n"
            f"💳 *Стоимость:* {total_price} руб.\n"
            f"📅 *Дата доставки:* {delivery_date_str}\n"
            f"📍 *Адрес доставки:* {delivery_address}\n"
            f"📞 *Телефон:* {delivery_phone}"
        )

        photo = None
        if product_image_path:
            # Проверяем, существует ли файл
            if os.path.exists(product_image_path):
                photo = InputFile(product_image_path)
            else:
                logger.warning(f"Файл изображения {product_image_path} не найден.")
                photo = None # Устанавливаем photo в None, если файл не найден

        # Получаем chat_id админов из профилей
        admin_profiles = await sync_to_async(
            list
        )(UserProfile.objects.filter(user__is_staff=True, telegram_chat_id__isnull=False))

        sent_count = 0
        for profile in admin_profiles:
            try:
                if photo:
                    await application.bot.send_photo(
                        chat_id=profile.telegram_chat_id,
                        photo=photo,
                        caption=message_text,
                        parse_mode='MarkdownV2' # Используем MarkdownV2 для форматирования
                    )
                else:
                    # Если фото нет, отправляем только текст
                    await application.bot.send_message(
                        chat_id=profile.telegram_chat_id,
                        text=message_text,
                        parse_mode='MarkdownV2'
                    )
                sent_count += 1
                logger.info(f"Уведомление о заказе {order_id} отправлено админу {profile.telegram_chat_id} ({profile.user.username})")
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления админу {profile.telegram_chat_id} ({profile.user.username}): {e}")

        logger.info(f"Уведомление о заказе {order_id} отправлено {sent_count} админам.")

    except Exception as e:
        logger.error(f"Критическая ошибка при подготовке/отправке уведомления для заказа {order_id}: {e}")

# --- 4. Функция для вызова из Django (синхронная обертка) ---
def send_order_notification_sync(order_id):
    """
    Синхронная обертка для запуска асинхронной функции отправки уведомления в отдельном потоке.
    Вызывается из Django вьюхи.
    """
    import asyncio
    import threading
    from bot_admin_auth import get_application_instance # Импортируем из файла бота

    application = get_application_instance()
    if not application:
        logger.error("Application instance не найден. Уведомление не отправлено.")
        return

    async def run_notification():
        await send_order_notification(application, order_id)

    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_notification())
        finally:
            loop.close()

    thread = threading.Thread(target=run_in_thread)
    thread.daemon = True  # Поток завершится при завершении основного процесса
    thread.start()
    logger.debug(f"Поток уведомления для заказа {order_id} запущен.")