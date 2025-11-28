# telegram_bot/bot/django_client.py
import os
import django
import sys
from typing import Optional, Dict, List
from asgiref.sync import sync_to_async  # Добавляем импорт

# Добавляем путь к Django проекту
DJANGO_PROJECT_PATH = os.path.join(os.path.dirname(__file__), '../../')
sys.path.append(DJANGO_PROJECT_PATH)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flower_delivery.settings')

# Инициализируем Django
try:
    django.setup()
except Exception as e:
    print(f"⚠️  Django setup failed: {e}")
    print("⚠️  Running in standalone mode - some features may be limited")

# Импортируем модели только после инициализации Django
from django.contrib.auth.models import User
from shop.models import Order, Product, OrderItem
from accounts.models import UserProfile


class DjangoClient:
    """Клиент для работы с Django моделями без изменения логики"""

    @staticmethod
    @sync_to_async
    def verify_admin_by_email(email: str) -> Optional[Dict]:
        """
        Проверяет, является ли пользователь с email администратором
        Возвращает данные пользователя или None
        """
        try:
            user = User.objects.filter(email=email).first()
            if not user:
                return None

            # Проверяем права администратора
            is_admin = user.is_staff or user.is_superuser

            return {
                'user_id': user.id,
                'email': user.email,
                'username': user.username,
                'is_admin': is_admin,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        except Exception as e:
            print(f"❌ Error verifying admin: {e}")
            return None

    @staticmethod
    @sync_to_async
    def save_telegram_chat_id(user_id: int, chat_id: int) -> bool:
        """
        Сохраняет chat_id в профиль пользователя
        """
        try:
            profile, created = UserProfile.objects.get_or_create(user_id=user_id)
            profile.telegram_chat_id = chat_id
            profile.telegram_consent_given = True
            profile.save()
            return True
        except Exception as e:
            print(f"❌ Error saving telegram chat_id: {e}")
            return False

    @staticmethod
    @sync_to_async
    def get_admin_chat_ids() -> List[int]:
        """
        Возвращает список chat_id всех администраторов
        """
        try:
            admin_users = User.objects.filter(
                is_staff=True,
                userprofile__telegram_chat_id__isnull=False
            ).select_related('userprofile')

            return [
                user.userprofile.telegram_chat_id
                for user in admin_users
                if user.userprofile.telegram_chat_id
            ]
        except Exception as e:
            print(f"❌ Error getting admin chat_ids: {e}")
            return []

    @staticmethod
    @sync_to_async
    def get_new_orders(limit: int = 10) -> List[Dict]:
        """
        Получает последние заказы для уведомлений
        """
        try:
            orders = Order.objects.select_related('user').prefetch_related(
                'orderitem_set__product'
            ).order_by('-created_at')[:limit]

            result = []
            for order in orders:
                order_data = {
                    'id': order.id,
                    'customer_name': f"{order.user.first_name} {order.user.last_name}".strip() or order.user.username,
                    'customer_phone': getattr(order, 'delivery_phone', 'Не указан'),
                    'delivery_address': order.delivery_address,
                    'delivery_date': order.delivery_date.strftime(
                        '%d.%m.%Y %H:%M') if order.delivery_date else 'Не указана',
                    'total_price': f"{order.total_price} руб.",
                    'status': order.get_status_display(),
                    'payment_status': order.get_payment_status_display(),
                    'comment': getattr(order, 'comment', '') or 'Без комментария',
                    'created_at': order.created_at.strftime('%d.%m.%Y %H:%M'),
                    'products': []
                }

                # Добавляем товары
                for item in order.orderitem_set.all():
                    product_data = {
                        'name': item.product.name,
                        'quantity': item.quantity,
                        'price': item.product.price,
                        'image_path': item.product.image.path if item.product.image else None
                    }
                    order_data['products'].append(product_data)

                result.append(order_data)

            return result
        except Exception as e:
            print(f"❌ Error getting orders: {e}")
            return []