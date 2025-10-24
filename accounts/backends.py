# accounts/backends.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class EmailBackend(ModelBackend):
    """
    Кастомный бэкенд аутентификации, позволяющий вход по email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Проверяем, был ли передан username (в нашем случае это будет email)
        if username is None:
            username = kwargs.get('email') # На случай, если передано как 'email'

        if username is None or password is None:
            return None

        try:
            # Ищем пользователя по email
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            # Пользователь с таким email не найден
            # Важно: для безопасности не сообщаем, что email или пароль неверен
            return None
        except User.MultipleObjectsReturned:
            # Если найдено несколько пользователей с одинаковым email (хотя уникальность обычно обеспечивается)
            # Лучше настроить уникальность email на уровне модели
            return None

        # Проверяем пароль
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None