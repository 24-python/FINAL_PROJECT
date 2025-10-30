# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger('pdn')

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True, verbose_name="Телефон")
    address = models.TextField(blank=True, verbose_name="Адрес")
    # --- ПОЛЯ ДЛЯ ТЕЛЕГРАМ-БОТОВ ---
    # Поля для первого бота (пользовательского)
    telegram_id = models.BigIntegerField(null=True, blank=True, unique=True, verbose_name="ID пользователя Telegram (Пользовательский бот)")
    telegram_agreed_to_pdn = models.BooleanField(default=False, verbose_name="Согласие на обработку ПДн для Telegram (Пользовательский бот)")
    telegram_email_confirmed = models.BooleanField(default=False, verbose_name="Email подтвержден через Telegram (Пользовательский бот)")

    # Поле для второго бота (управленческого)
    manager_telegram_id = models.BigIntegerField(null=True, blank=True, unique=True, verbose_name="ID пользователя Telegram (Управленческий бот)")
    # --- /ПОЛЯ ДЛЯ ТЕЛЕГРАМ-БОТОВ ---

    def __str__(self):
        return f"Профиль {self.user.username}"

class PendingTelegramConsent(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    agreed_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"Pending consent for TG ID {self.telegram_id}"

@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    if created:
        logger.info(f"Создан пользователь: {instance.username}, email: {instance.email}, id: {instance.id}")

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    # instance.profile.save() # Не вызываем, если не нужно обновлять профиль при каждом изменении User