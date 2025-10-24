from django.db import models
from shop.models import Order
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib import messages

class SalesReport(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название отчёта")
    date = models.DateField(default=timezone.now, verbose_name="Дата")
    users = models.ManyToManyField(User, blank=True, verbose_name="Пользователи, чьи заказы включены")
    orders = models.ManyToManyField(Order, blank=True, verbose_name="Заказы, учтённые в отчёте")
    revenue = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Выручка", default=0)
    expenses = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Расходы", default=0)

    def __str__(self):
        return f"{self.name} - Отчет за {self.date}"

    def save(self, *args, **kwargs):
        # Автоматически вычисляем выручку при сохранении, только если объект уже был сохранён
        if self.pk:
            # ВАЖНО: Это не должно использоваться для основного расчёта, если update_report перезаписывает revenue
            # self.revenue = sum(order.total_price for order in self.orders.all())
            # Лучше рассчитывать revenue только в update_report
            pass
        super().save(*args, **kwargs)

    def update_report(self, request=None):
        """
        Метод для обновления отчёта: пересчитывает выручку
        в зависимости от выбранных пользователей и заказов.
        """
        if not self.pk:
            self.save()

        # Получаем выбранные пользователи и заказы ИЗ ФОРМЫ/БАЗЫ в текущий момент
        # (предполагается, что они уже сохранены до вызова этого метода)
        selected_users = set(self.users.all()) # Используем set для быстрого поиска
        selected_order_instances = set(self.orders.all()) # Множество выбранных заказов

        # Логика 1: Выбран пользователь, не выбраны заказы (то есть, ManyToMany orders пуст)
        if selected_users and not selected_order_instances:
            # Найти все заказы за дату для выбранных пользователей
            orders_for_calculation = Order.objects.filter(
                user__in=selected_users,
                created_at__date=self.date
            )
            # Обновить поле orders, чтобы отразить автоматически добавленные
            # self.orders.set(orders_for_calculation) # Опционально, если хотим хранить их в M2M

        # Логика 2: Не выбран пользователь, выбраны заказы
        elif not selected_users and selected_order_instances:
            # Отфильтровать выбранные заказы по дате
            orders_for_calculation = [
                order for order in selected_order_instances
                if order.created_at.date() == self.date
            ]
            # Опционально: если заказ не за дату, можно вывести алерт
            for order in selected_order_instances:
                if order.created_at.date() != self.date:
                    if request:
                        messages.warning(request, f"Заказ #{order.id} не за дату {self.date}, пропущен.")

        # Логика 3: Выбран пользователь и выбраны заказы
        elif selected_users and selected_order_instances:
            orders_for_calculation = []
            for order in selected_order_instances:
                # Проверяем дату заказа
                if order.created_at.date() != self.date:
                    if request:
                        messages.warning(request, f"Заказ #{order.id} не за дату {self.date}, пропущен.")
                    continue

                # Проверяем, принадлежит ли заказ одному из выбранных пользователей
                if order.user in selected_users:
                    orders_for_calculation.append(order)
                else:
                    # Алерт: заказ принадлежит другому пользователю
                    if request:
                        messages.warning(request, f"Заказ #{order.id} принадлежит пользователю {order.user.username}, который не входит в выбранные. Заказ исключён из отчёта.")
            # Оставляем только те заказы, которые прошли проверку

        # Логика 4: Не выбран ни пользователь, ни заказы -> выручка 0
        else: # (not selected_users and not selected_order_instances)
            orders_for_calculation = []

        # Пересчитать выручку ТОЛЬКО по заказам, которые прошли все проверки
        # Преобразуем в QuerySet для sum, если нужно, или используем список
        # Используем список, так как он уже отфильтрован
        self.revenue = sum(order.total_price for order in orders_for_calculation)
        self.save(update_fields=['revenue'])