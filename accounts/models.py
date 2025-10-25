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
    telegram_chat_id = models.BigIntegerField(null=True, blank=True, unique=True)  # Уникальность опционально
    telegram_consent_given = models.BooleanField(default=False)

    def __str__(self):
        return f"Профиль {self.user.username}"

@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    if created:
        logger.info(f"Создан пользователь: {instance.username}, email: {instance.email}, id: {instance.id}")