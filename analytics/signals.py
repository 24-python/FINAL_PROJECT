# analytics/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from shop.models import Order
from .models import SalesReport
# --- ИМПОРТ ДЛЯ УВЕДОМЛЕНИЙ АДМИНИСТРАТОРА О СМЕНЕ СТАТУСА ---
from telegram_manager_bot.notifications import send_order_status_update_to_managers, run_async_notification
# --- /ИМПОРТ ДЛЯ УВЕДОМЛЕНИЙ АДМИНИСТРАТОРА О СМЕНЕ СТАТУСА ---

# --- СИГНАЛ: Обновление отчета и уведомление о НОВОМ заказе ---
@receiver(post_save, sender=Order)
def update_sales_report_and_notify_on_order_save(sender, instance, created, **kwargs):
    """
    Обновляет SalesReport.
    Уведомление о новом заказе теперь отправляется из shop/views.py.
    """
    if created: # Только для новых заказов
        report_date = instance.created_at.date()
        report, created = SalesReport.objects.get_or_create(date=report_date)
        report.orders.add(instance)
        report.update_report()

        # --- УБРАНО: Вызов уведомления о новом заказе ---
        # run_async_notification(send_new_order_to_managers(instance.id)) # <-- Было
        # --- /УБРАНО ---


# --- СИГНАЛ: Уведомление админу о смене статуса ---
@receiver(pre_save, sender=Order)
def notify_admin_on_order_status_change(sender, instance, **kwargs):
    """
    Отправляет уведомление администратору, если статус заказа изменился.
    """
    if instance.pk:  # Только для существующих объектов
        try:
            # Получаем старую версию объекта из БД
            old_instance = Order.objects.get(pk=instance.pk)
            # Проверяем, изменился ли статус
            if old_instance.status != instance.status:
                old_status_display = old_instance.get_status_display()
                new_status_display = instance.get_status_display()
                order_id = instance.id
                user_id = instance.user.id # ID пользователя, сделавшего заказ

                # --- ОТПРАВКА УВЕДОМЛЕНИЯ АДМИНУ ---
                print(f"[DEBUG signals.py] Статус заказа #{order_id} изменён с '{old_status_display}' на '{new_status_display}'. Отправляем уведомление админу.")
                # run_async_notification(send_order_status_update_to_managers(order_id, old_status_display, new_status_display, user_id)) # <-- Было
                run_async_notification(send_order_status_update_to_managers, order_id, old_status_display, new_status_display, user_id) # <-- Стало
                # --- /ОТПРАВКА УВЕДОМЛЕНИЯ АДМИНУ ---
        except Order.DoesNotExist:
            # Объекта не было до этого (хотя pk есть) - маловероятный случай
            pass
# --- /СИГНАЛ: Уведомление админу о смене статуса ---