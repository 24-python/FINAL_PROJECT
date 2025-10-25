from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
# from .models import OrderAnalytics # УДАЛЕНО
from shop.models import Order
from .models import SalesReport # Импортируем SalesReport

@user_passes_test(lambda u: u.is_staff)
def analytics_dashboard(request):
    # Пример: получить все отчёты
    reports = SalesReport.objects.all().order_by('-date')

    # Рассчитать общие показатели
    total_revenue = sum(r.revenue for r in reports)
    total_expenses = sum(r.expenses for r in reports)
    net_profit = total_revenue - total_expenses

    # Пример: получить количество новых заказов (например, со статусом 'new')
    new_orders = Order.objects.filter(status='new').count()

    # Передаём все данные в контекст
    context = {
        'reports': reports,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'new_orders': new_orders,
    }
    return render(request, 'analytics/dashboard.html', context)