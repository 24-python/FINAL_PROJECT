# telegram_bot/handlers/user_handlers.py
from aiogram import Router
from aiogram.types import Message
from telegram_bot.utils import get_user_by_telegram_id
from shop.models import Order, OrderItem

router = Router()

@router.message(lambda message: message.text == "Мои заказы")
async def show_user_orders(message: Message):
    telegram_id = message.from_user.id
    user = get_user_by_telegram_id(telegram_id)

    if not user:
        await message.answer("Вы не авторизованы. Пожалуйста, авторизуйтесь по email.")
        return

    orders = Order.objects.filter(user=user).order_by('-created_at')

    if not orders:
        await message.answer("У вас пока нет заказов.")
        return

    for order in orders:
        items = OrderItem.objects.filter(order=order)
        items_str = "\n".join([f"- {item.product.name} x{item.quantity}" for item in items])
        order_info = (
            f"Заказ #{order.id}\n"
            f"Статус: {order.get_status_display()}\n"
            f"Статус оплаты: {order.get_payment_status_display()}\n"
            f"Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"Адрес: {order.delivery_address}\n"
            f"Телефон: {order.delivery_phone}\n"
            f"Итого: {order.total_price} ₽\n"
            f"Товары:\n{items_str}\n"
            "---\n"
        )
        await message.answer(order_info)