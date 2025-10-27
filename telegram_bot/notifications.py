# telegram_bot/notifications.py
from aiogram import Bot
from django.conf import settings
from accounts.models import UserProfile
from shop.models import Order, OrderItem
import asyncio

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

async def send_new_order_notification(order_id):
    """Отправляет уведомление администраторам о новом заказе."""
    try:
        order = Order.objects.get(id=order_id)
        items = OrderItem.objects.filter(order=order)
        items_str = "\n".join([f"- {item.product.name} x{item.quantity}" for item in items])
        order_info = (
            f"🚨 НОВЫЙ ЗАКАЗ #{order.id}\n"
            f"Пользователь: {order.user.username} (ID: {order.user.id})\n"
            f"Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"Адрес: {order.delivery_address}\n"
            f"Телефон: {order.delivery_phone}\n"
            f"Итого: {order.total_price} ₽\n"
            f"Товары:\n{items_str}\n"
        )

        # Находим всех администраторов с привязанным Telegram ID
        admin_profiles = UserProfile.objects.filter(
            user__is_staff=True, # или user__is_superuser=True
            telegram_id__isnull=False,
            telegram_email_confirmed=True # Убедимся, что аккаунт подтвержден
        )

        for profile in admin_profiles:
            try:
                await bot.send_message(chat_id=profile.telegram_id, text=order_info)
            except Exception as e:
                print(f"Ошибка отправки уведомления админу {profile.telegram_id}: {e}")

    except Order.DoesNotExist:
        print(f"Заказ с ID {order_id} не найден для уведомления.")

async def send_order_status_update_notification(order_id, old_status_display, new_status_display):
    """Отправляет уведомление пользователю об изменении статуса его заказа."""
    try:
        order = Order.objects.get(id=order_id)
        user_profile = getattr(order.user, 'profile', None) # Предполагаем, что related_name='profile'

        if user_profile and user_profile.telegram_id and user_profile.telegram_email_confirmed:
            message = f"Статус вашего заказа #{order.id} изменился с '{old_status_display}' на '{new_status_display}'."
            try:
                await bot.send_message(chat_id=user_profile.telegram_id, text=message)
            except Exception as e:
                print(f"Ошибка отправки уведомления пользователю {user_profile.telegram_id}: {e}")

    except Order.DoesNotExist:
        print(f"Заказ с ID {order_id} не найден для уведомления о статусе.")

# Функция для запуска корутин из синхронного кода (например, из сигналов)
def run_async_notification(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(coro)