# analytics/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from shop.models import Order
from .models import SalesReport
from telegram_manager_bot.notifications import send_new_order_to_managers, run_async_notification

@receiver(post_save, sender=Order)
def update_sales_report_and_notify_on_order_save(sender, instance, created, **kwargs):
    """
    Обновляет SalesReport и отправляет уведомления.
    """
    if created: # Только для новых заказов
        report_date = instance.created_at.date()
        report, created = SalesReport.objects.get_or_create(date=report_date)
        report.orders.add(instance)
        report.update_report()

        # --- НОВОЕ: Уведомление менеджерам ---
        run_async_notification(send_new_order_to_managers(instance.id))
        # --- /НОВОЕ ---