# analytics/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from shop.models import Order
from .models import SalesReport

@receiver(post_save, sender=Order)
def update_sales_report_on_order_save(sender, instance, created, **kwargs):
    """
    Обновляет SalesReport для даты заказа при сохранении Order.
    """
    # Получаем или создаём отчёт для даты заказа
    report_date = instance.created_at.date()
    report, created = SalesReport.objects.get_or_create(date=report_date)

    # Если заказ был только что создан, просто добавим его
    # Если заказ обновляется, get_or_create в ManyToManyField не добавит дубликат
    report.orders.add(instance)

    # Пересчитываем выручку (это вызывает save() модели)
    # report.revenue = sum(order.total_price for order in report.orders.all())
    # report.save()
    # Лучше вызвать update_report, чтобы избежать циклических вызовов (если update_report не вызывает save() Order)
    report.update_report()