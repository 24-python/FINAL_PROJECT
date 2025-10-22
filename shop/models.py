from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from PIL import Image

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    image = models.ImageField(upload_to='products/', blank=True, verbose_name="Изображение")

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            img = Image.open(self.image.path)
            if img.height > 800 or img.width > 800:
                img.thumbnail((800, 800))
                img.save(self.image.path)

class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('confirmed', 'Подтвержден'),
        ('in_progress', 'В работе'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    products = models.ManyToManyField(Product, through='OrderItem', verbose_name="Товары")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата заказа")
    delivery_address = models.TextField(verbose_name="Адрес доставки")
    delivery_phone = models.CharField(max_length=20, verbose_name="Телефон")
    delivery_date = models.DateTimeField(verbose_name="Дата доставки")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Итоговая цена")

    def __str__(self):
        return f"Заказ #{self.id} от {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Товар")
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], verbose_name="Рейтинг")
    comment = models.TextField(blank=True, verbose_name="Комментарий")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата отзыва")

    def __str__(self):
        return f"Отзыв от {self.user.username} на {self.product.name}"

class SalesReport(models.Model):
    date = models.DateField(default=timezone.now, verbose_name="Дата")
    orders_count = models.PositiveIntegerField(verbose_name="Количество заказов")
    revenue = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Выручка")
    expenses = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Расходы", default=0)

    def __str__(self):
        return f"Отчет за {self.date}"