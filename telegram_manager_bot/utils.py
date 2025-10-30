# telegram_manager_bot/utils.py
from django.contrib.auth.models import User
from accounts.models import UserProfile
from asgiref.sync import sync_to_async # Импортируем sync_to_async
from shop.models import Order, OrderItem, Product

# --- Синхронные функции СНАЧАЛА ---
def get_user_by_telegram_id(telegram_id):
    """Находит пользователя Django по manager_telegram_id."""
    try:
        profile = UserProfile.objects.get(manager_telegram_id=telegram_id)
        return profile.user
    except UserProfile.DoesNotExist:
        return None

def get_managers_telegram_ids():
    """Возвращает список telegram_id суперюзеров, у которых заполнен manager_telegram_id."""
    profiles = UserProfile.objects.filter(user__is_superuser=True, manager_telegram_id__isnull=False)
    return [profile.manager_telegram_id for profile in profiles]

def link_manager_telegram_id(telegram_id, django_user):
    """Связывает manager_telegram_id с аккаунтом Django (суперюзера)."""
    if not django_user.is_superuser:
        return False # Только суперюзеры
    profile, created = UserProfile.objects.get_or_create(user=django_user)
    profile.manager_telegram_id = telegram_id
    profile.save()
    return True

def get_user_by_email(email):
    """Находит пользователя Django по email."""
    try:
        user = User.objects.get(email=email)
        return user
    except User.DoesNotExist:
        return None

def get_order_details(order_id):
    """Получает детали заказа для уведомления."""
    try:
        # --- ИСПОЛЬЗУЕМ ORM СИНХРОННО ВНУТРИ ЭТОЙ ФУНКЦИИ ---
        order = Order.objects.get(id=order_id)
        items = OrderItem.objects.filter(order=order).select_related('product')
        products_info = []
        images = []
        for item in items:
            product = item.product
            products_info.append(f"{product.name} x{item.quantity}")
            if product.image: # Предполагаем, что image - это главное фото
                images.append(product.image.path) # Или .url для URL
        order_info = {
            'id': order.id,
            'user': order.user.username,
            'total_price': order.total_price,
            'delivery_date': order.delivery_date,
            'delivery_address': order.delivery_address,
            'delivery_phone': order.delivery_phone,
            'comment': getattr(order, 'comment', ''), # Если поле comment есть
            'items_list': products_info,
            'image_paths': images, # Список путей/URL к изображениям
            'status': order.get_status_display(),
            'payment_status': order.get_payment_status_display(),
        }
        return order_info
    except Order.DoesNotExist:
        return None

def is_user_manager(django_user):
    """Проверяет, является ли пользователь суперюзером (менеджером)."""
    return django_user.is_superuser
# --- /Синхронные функции ---

# --- ОБЕРТКИ sync_to_async ПОСЛЕ ОПРЕДЕЛЕНИЯ ФУНКЦИЙ ---
get_user_by_telegram_id_sync = sync_to_async(get_user_by_telegram_id)
get_managers_telegram_ids_sync = sync_to_async(get_managers_telegram_ids)
link_manager_telegram_id_sync = sync_to_async(link_manager_telegram_id)
get_user_by_email_sync = sync_to_async(get_user_by_email)
get_order_details_sync = sync_to_async(get_order_details) # <-- Убедитесь, что это есть
is_user_manager_sync = sync_to_async(is_user_manager)
# --- /ОБЕРТКИ sync_to_async ---