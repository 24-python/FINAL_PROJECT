# telegram_bot/keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_user_keyboard():
    """Клавиатура для авторизованного обычного пользователя."""
    kb = [
        [KeyboardButton(text="Мои заказы")],
        [KeyboardButton(text="Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_main_admin_keyboard():
    """Клавиатура для авторизованного администратора."""
    kb = [
        [KeyboardButton(text="Мои заказы")], # Админ тоже может смотреть свои заказы
        [KeyboardButton(text="Новые заказы")],
        [KeyboardButton(text="Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_order_status_keyboard(order_id):
    """Инлайн-клавиатура для изменения статуса заказа (для админа)."""
    # Статусы из модели Order
    statuses = [
        ('new', 'Новый'),
        ('confirmed', 'Подтвержден'),
        ('in_progress', 'В работе'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]
    payment_statuses = [
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачено'),
        ('failed', 'Платёж не прошёл'),
        ('cancelled', 'Платёж отменён'),
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for status_key, status_label in statuses:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=status_label, callback_data=f"status_{order_id}_{status_key}")
        ])
    # Опционально: добавить кнопки для статуса оплаты
    for p_status_key, p_status_label in payment_statuses:
         keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=f"Оплата: {p_status_label}", callback_data=f"pay_status_{order_id}_{p_status_key}")
        ])

    return keyboard

def get_consent_keyboard():
    """Клавиатура для согласия на ПДн."""
    kb = [
        [KeyboardButton(text="✅ Принимаю политику обработки ПДн")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)