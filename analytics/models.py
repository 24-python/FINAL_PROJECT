from django.db import models
from shop.models import Order

class OrderAnalytics(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Аналитика для заказа #{self.order.id}"