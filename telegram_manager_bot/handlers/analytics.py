# telegram_manager_bot/handlers/analytics.py
from aiogram import Router, types
from aiogram.filters import Command
from telegram_manager_bot.utils import get_user_by_telegram_id_sync, is_user_manager
from shop.models import Order, OrderItem, Product
from django.db.models import Sum, Count
from django.utils import timezone
from asgiref.sync import sync_to_async
from datetime import timedelta

# --- ИМПОРТ ФУНКЦИИ ОТПРАВКИ КЛАВИАТУРЫ ---
from telegram_manager_bot.handlers.start import send_manager_keyboard
# --- /ИМПОРТ ---

router = Router()

@router.message(Command(commands=['report_today']))
async def cmd_report_today(message: types.Message):
    telegram_id = message.from_user.id
    user = await get_user_by_telegram_id_sync(telegram_id)

    if not user or not is_user_manager(user):
        await message.answer("У вас нет прав для просмотра отчётов.")
        return

    now = timezone.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    orders = await sync_to_async(list)(
        Order.objects.filter(
            created_at__gte=start_of_day,
            created_at__lte=end_of_day
        )
    )
    total_revenue = await sync_to_async(
        lambda: Order.objects.filter(
            created_at__gte=start_of_day,
            created_at__lte=end_of_day
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0
    )()
    total_orders = len(orders)

    report_text = f"Отчёт за сегодня ({start_of_day.strftime('%d.%m.%Y')}):\n"
    report_text += f"- Всего заказов: {total_orders}\n"
    report_text += f"- Общая выручка: {total_revenue} ₽\n"
    await message.answer(report_text)
    # После отправки отчёта, отправляем клавиатуру
    await send_manager_keyboard(message)

@router.message(Command(commands=['top_products']))
async def cmd_top_products(message: types.Message):
    telegram_id = message.from_user.id
    user = await get_user_by_telegram_id_sync(telegram_id)

    if not user or not is_user_manager(user):
        await message.answer("У вас нет прав для просмотра отчётов.")
        return

    # Пример: топ-5 товаров за последнюю неделю
    now = timezone.now()
    start_of_week = (now - timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0)

    top_products = await sync_to_async(list)(
        Product.objects.filter(
            orderitem__order__created_at__gte=start_of_week
        ).annotate(
            total_quantity=Sum('orderitem__quantity')
        ).order_by('-total_quantity')[:5]
    )

    if not top_products:
        await message.answer("Нет данных для отчёта о топ-товарах за последнюю неделю.")
        # Отправляем клавиатуру
        await send_manager_keyboard(message)
        return

    report_text = "Топ-5 товаров за последнюю неделю:\n"
    for i, product in enumerate(top_products, 1):
        report_text += f"{i}. {product.name} - {product.total_quantity or 0} шт.\n"

    await message.answer(report_text)
    # После отправки отчёта, отправляем клавиатуру
    await send_manager_keyboard(message)

# Добавьте другие команды аналитики по аналогии