# telegram_manager_bot/utils.py
from django.contrib.auth.models import User
from django.conf import settings
from shop.models import Order, OrderItem, Product
from asgiref.sync import sync_to_async
import os

# --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ---
def is_superuser_by_email(email):
    """Проверяет, является ли пользователь суперпользователем по email."""
    try:
        user = User.objects.get(email=email, is_superuser=True)
        return user is not None
    except User.DoesNotExist:
        return False
# --- /ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ---

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ (СИНХРОННЫЕ) ---
def get_user_by_telegram_id(telegram_id):
    """Получает UserProfile по telegram_id."""
    from accounts.models import UserProfile
    try:
        profile = UserProfile.objects.get(telegram_id=telegram_id)
        return profile.user
    except UserProfile.DoesNotExist:
        return None

def get_order_details(order_id):
    """Получает детали заказа по ID."""
    try:
        order = Order.objects.prefetch_related('orderitem_set__product').get(id=order_id)
        items = order.orderitem_set.all()
        products_info = []
        images = []

        for item in items:
            product = item.product
            products_info.append(f"{product.name} x{item.quantity}")
            if product.image:
                img_path = product.image.path
                print(f"[DEBUG utils.py] Путь к изображению для {product.name}: {img_path}") # Отладочный принт
                print(f"[DEBUG utils.py] Файл существует: {os.path.isfile(img_path)}") # Отладочный принт
                if os.path.isfile(img_path): # Проверяем существование файла
                    images.append(img_path)

        order_info = {
            'id': order.id,
            'user': order.user.username,
            'total_price': order.total_price,
            'delivery_date': order.delivery_date,
            'delivery_address': order.delivery_address,
            'delivery_phone': order.delivery_phone,
            'comment': getattr(order, 'comment', ''), # Если поле comment есть
            'items_list': products_info,
            'image_paths': images,
            'status': order.get_status_display(), # Предполагаем, что у модели Order есть метод get_status_display
            'payment_status': order.get_payment_status_display(), # Аналогично для статуса оплаты
        }
        return order_info
    except Order.DoesNotExist:
        return None

def get_all_orders():
    """Получает все заказы."""
    orders = Order.objects.all().order_by('-created_at')
    return [{'id': o.id, 'status': o.get_status_display(), 'total_price': o.total_price} for o in orders]

def get_orders_by_status(status):
    """Получает заказы по статусу."""
    orders = Order.objects.filter(status=status).order_by('-created_at')
    return [{'id': o.id, 'status': o.get_status_display(), 'total_price': o.total_price} for o in orders]

def get_orders_for_today():
    """Получает заказы за сегодня."""
    from django.utils import timezone
    today = timezone.now().date()
    orders = Order.objects.filter(created_at__date=today).order_by('-created_at')
    return [{'id': o.id, 'status': o.get_status_display(), 'total_price': o.total_price} for o in orders]

def get_top_products(limit=5):
    """Получает топ-5 продаваемых продуктов."""
    from django.db.models import Sum
    top_products = OrderItem.objects.values('product__name').annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:limit]
    return [{'name': item['product__name'], 'quantity': item['total_quantity']} for item in top_products]

def update_order_status(order_id, new_status):
    """Обновляет статус заказа."""
    try:
        order = Order.objects.get(id=order_id)
        old_status = order.status
        order.status = new_status
        order.save()
        return old_status, order.get_status_display()
    except Order.DoesNotExist:
        return None, None
# --- /ФУНКЦИИ ДЛЯ РАБОТЫ С БАЗОЙ (СИНХРОННЫЕ) ---

# --- АСИНХРОННЫЕ ОБЁРТКИ ---
get_user_by_telegram_id_async = sync_to_async(get_user_by_telegram_id)
get_order_details_async = sync_to_async(get_order_details)
get_all_orders_async = sync_to_async(get_all_orders)
get_orders_by_status_async = sync_to_async(get_orders_by_status)
get_orders_for_today_async = sync_to_async(get_orders_for_today)
get_top_products_async = sync_to_async(get_top_products)
update_order_status_async = sync_to_async(update_order_status)
is_superuser_by_email_async = sync_to_async(is_superuser_by_email)
# --- /АСИНХРОННЫЕ ОБЁРТКИ ---