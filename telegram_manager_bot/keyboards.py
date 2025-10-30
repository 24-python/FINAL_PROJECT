# telegram_manager_bot/keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_order_status_keyboard(order_id):
    """Инлайн-клавиатура для изменения статуса заказа."""
    statuses = [
        ('new', 'Новый'),
        ('confirmed', 'Подтвержден'),
        ('in_progress', 'В работе'),
        ('in_transit', 'В пути'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for status_key, status_label in statuses:
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text=status_label, callback_data=f"m_status_{order_id}_{status_key}")
        ])
    return keyboard

def get_order_details_keyboard(order_id):
    """Инлайн-клавиатура с кнопками статуса и кнопкой 'Назад к списку'."""
    keyboard = get_order_status_keyboard(order_id)
    # Добавляем кнопку "Назад"
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="Назад к списку", callback_data="m_back_to_orders")
    ])
    return keyboard

def get_orders_list_keyboard(orders):
    """Инлайн-клавиатура со списком заказов."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for order in orders:
        # Кнопка с названием заказа (например, ID) и callback_data для его просмотра
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"Заказ #{order.id} - {order.get_status_display()}", # Отображаем ID и статус
                callback_data=f"m_view_order_{order.id}"
            )
        ])
    # Кнопка для обновления списка (опционально)
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="Обновить список", callback_data="m_refresh_orders")
    ])
    return keyboard

# --- Функция для клавиатуры менеджера (ReplyKeyboard) ---
def get_manager_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/start")],
            [KeyboardButton(text="/orders")], # Добавляем кнопку /orders
            [KeyboardButton(text="/report_today")],
            [KeyboardButton(text="/top_products")],
        ],
        resize_keyboard=True
    )
    return keyboard
# --- /Функция ---