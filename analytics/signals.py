# analytics/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from shop.models import Order
from .models import SalesReport
# Отложенный импорт для уведомлений менеджеров
# from telegram_bot.notifications import send_new_order_notification, send_order_status_update_notification, run_async_notification # Первый бот
from telegram_manager_bot.notifications import send_new_order_to_managers, run_async_notification # Второй бот

@receiver(post_save, sender=Order)
def update_sales_report_and_notify_on_order_save(sender, instance, created, **kwargs):
    """
    Обновляет SalesReport и отправляет уведомления.
    """
    # Логика обновления отчёта (из старого кода)
    if created: # Только для новых заказов
        report_date = instance.created_at.date()
        report, created = SalesReport.objects.get_or_create(date=report_date)
        report.orders.add(instance)
        report.update_report()

        # --- НОВОЕ: Уведомление менеджерам ---
        run_async_notification(send_new_order_to_managers(instance.id))
        # --- /НОВОЕ ---

    # Пересчитываем выручку (из старого кода)
    # report.revenue = sum(order.total_price for order in report.orders.all())
    # report.save()
    # report.update_report() # Лучше вызвать update_report, чтобы избежать циклических вызовов (если update_report не вызывает save() Order)

# # Сигнал для уведомления пользователя об изменении статуса (для первого бота)
# @receiver(pre_save, sender=Order)
# def notify_status_change(sender, instance, **kwargs):
#     """
#     Отправляет уведомление пользователю, если статус заказа изменился.
#     """
#     if instance.pk: # Только для существующих объектов
#         try:
#             old_instance = Order.objects.get(pk=instance.pk)
#             if old_instance.status != instance.status:
#                 old_status_display = old_instance.get_status_display()
#                 new_status_display = instance.get_status_display()
#                 # --- НОВОЕ: Уведомление пользователю ---
#                 # Отложенный импорт
#                 try:
#                     from telegram_bot.notifications import send_order_status_update_notification, run_async_notification
#                     run_async_notification(send_order_status_update_notification(instance.id, old_status_display, new_status_display))
#                 except ImportError:
#                     # Логгируем ошибку или просто игнорируем, если бот не настроен
#                     print("Модуль telegram_bot не найден. Уведомление о смене статуса не отправлено.")
#                 # --- /НОВОЕ ---
#         except Order.DoesNotExist:
#             # Объекта не было до этого (хотя pk есть) - маловероятный случай
#             pass