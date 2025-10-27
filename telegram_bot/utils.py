# telegram_bot/utils.py
import secrets
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import UserProfile, PendingTelegramConsent

def generate_token():
    """Генерирует случайный 6-значный токен."""
    return ''.join(secrets.choice('0123456789') for _ in range(6))

def send_auth_token_to_email(email, token):
    """Отправляет токен на указанный email."""
    try:
        send_mail(
            subject='Ваш токен для авторизации в Telegram-боте',
            message=f'Ваш токен авторизации: {token}. Введите его в боте.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False

def get_user_by_email(email):
    """Находит пользователя Django по email."""
    try:
        user = User.objects.get(email=email)
        return user
    except User.DoesNotExist:
        return None

def link_telegram_user_to_django(telegram_id, django_user):
    """Связывает ID Telegram с аккаунтом Django."""
    profile, created = UserProfile.objects.get_or_create(user=django_user)
    if profile.telegram_id is not None and profile.telegram_id != telegram_id:
        # Учет случая, если другой Telegram ID уже привязан к этому email
        # Можно игнорировать или отвязать старый
        pass
    profile.telegram_id = telegram_id
    profile.telegram_email_confirmed = True
    profile.save()

def is_user_admin(django_user):
    """Проверяет, является ли пользователь администратором."""
    return django_user.is_staff or django_user.is_superuser

def get_user_by_telegram_id(telegram_id):
    """Находит пользователя Django по ID Telegram."""
    try:
        profile = UserProfile.objects.get(telegram_id=telegram_id)
        return profile.user
    except UserProfile.DoesNotExist:
        return None

def has_agreed_to_pdn(telegram_id):
    """Проверяет, дал ли пользователь согласие на ПДн (через флаг в профиле)."""
    try:
        profile = UserProfile.objects.get(telegram_id=telegram_id)
        return profile.telegram_agreed_to_pdn
    except UserProfile.DoesNotExist:
        return False

def check_pending_consent(telegram_id):
    """Проверяет, дал ли пользователь согласие через PendingTelegramConsent."""
    try:
        consent = PendingTelegramConsent.objects.get(telegram_id=telegram_id, processed=False)
        return True
    except PendingTelegramConsent.DoesNotExist:
        return False