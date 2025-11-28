# telegram_bot/bot/utils.py
from typing import List, Dict
from datetime import datetime


class MessageFormatter:
    """Форматировщик сообщений для заказов"""

    @staticmethod
    def format_order_message(order_data: Dict) -> str:
        """Форматирует сообщение о заказе"""

        products_text = "\n".join([
            f"  • {p['name']} - {p['quantity']} шт. x {p['price']} руб."
            for p in order_data['products']
        ])

        return f"""
🎉 **НОВЫЙ ЗАКАЗ!**

📋 **Детали заказа:**
🆔 #{order_data['id']}
👤 **Клиент:** {order_data['customer_name']}
📞 **Телефон:** {order_data['customer_phone']}
📅 **Дата создания:** {order_data['created_at']}

🚚 **Доставка:**
📍 **Адрес:** {order_data['delivery_address']}
🗓️ **Дата доставки:** {order_data['delivery_date']}

🛍️ **Состав заказа:**
{products_text}

💰 **Итоговая сумма:** {order_data['total_price']}

📊 **Статусы:**
🟡 Статус: {order_data['status']}
💳 Оплата: {order_data['payment_status']}

💬 **Комментарий:** {order_data['comment']}
        """.strip()

    @staticmethod
    def format_products_list(products: List[Dict]) -> str:
        """Форматирует список товаров"""
        if not products:
            return "Товары не найдены"

        return "\n".join([
            f"• {p['name']} - {p['price']} руб. (x{p['quantity']})"
            for p in products
        ])


class OrderChecker:
    """Проверяет новые заказы"""

    def __init__(self):
        self.processed_orders = set()

    def get_new_orders_for_notification(self, orders: List[Dict]) -> List[Dict]:
        """Возвращает только новые заказы для уведомлений"""
        new_orders = []
        for order in orders:
            if order['id'] not in self.processed_orders:
                new_orders.append(order)
                self.processed_orders.add(order['id'])

        return new_orders