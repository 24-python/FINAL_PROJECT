# telegram_manager_bot/keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# --- ОСНОВНОЕ МЕНЮ ---
def get_main_menu_keyboard():
    """Основное меню для администратора."""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📋 Заказы")],
            [KeyboardButton(text="📊 Репорт за сегодня")],
            [KeyboardButton(text="🏆 Топ-продукты")]
        ],
        resize_keyboard=True
    )
    return keyboard
# --- /ОСНОВНОЕ МЕНЮ ---

# --- МЕНЮ СТАТУСА ЗАКАЗА ---
def get_order_status_keyboard(current_status_key):
    """Клавиатура для изменения статуса заказа."""
    # Пример статусов, адаптируй под свои
    status_buttons = [
        "new", "confirmed", "preparing", "shipped", "delivered", "cancelled"
    ]
    buttons = []
    for status_key in status_buttons:
        if status_key != current_status_key:
            buttons.append([InlineKeyboardButton(text=status_key.replace("_", " ").title(), callback_data=f"m_status_{status_key}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
# --- /МЕНЮ СТАТУСА ЗАКАЗА ---

# --- МЕНЮ СПИСКА ЗАКАЗОВ ---
def get_orders_list_keyboard(orders):
    """Клавиатура со списком заказов."""
    buttons = []
    for order in orders:
        buttons.append([InlineKeyboardButton(text=f"Заказ #{order['id']} - {order['status']}", callback_data=f"m_view_order_{order['id']}")])
    # Добавим кнопку обновления списка
    buttons.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="m_refresh_orders")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
# --- /МЕНЮ СПИСКА ЗАКАЗОВ ---