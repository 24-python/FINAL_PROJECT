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
    # --- НОВЫЕ ПОЛЯ ---
    telegram_id = models.BigIntegerField(null=True, blank=True, unique=True, verbose_name="ID пользователя Telegram")
    telegram_agreed_to_pdn = models.BooleanField(default=False, verbose_name="Согласие на обработку ПДн для Telegram")
    telegram_email_confirmed = models.BooleanField(default=False, verbose_name="Email подтвержден через Telegram")
    # --- /НОВЫЕ ПОЛЯ ---

    def __str__(self):
        return f"Профиль {self.user.username}"

# --- НОВАЯ МОДЕЛЬ ---
class PendingTelegramConsent(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    agreed_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"Pending consent for TG ID {self.telegram_id}"
# --- /НОВАЯ МОДЕЛЬ ---

@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    if created:
        logger.info(f"Создан пользователь: {instance.username}, email: {instance.email}, id: {instance.id}")

# Сигнал для автоматического создания профиля
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    # Если профиль уже существует, он будет обновлен при изменении User (если это нужно)
    # instance.profile.save() # Не вызываем, если не нужно обновлять профиль при каждом изменении User