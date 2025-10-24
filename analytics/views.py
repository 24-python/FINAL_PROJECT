from django.shortcuts import render
# from .models import OrderAnalytics # УДАЛЕНО
from .models import SalesReport # ДОБАВЛЕНО
from django.contrib.auth.decorators import user_passes_test

@user_passes_test(lambda u: u.is_staff)
def analytics_dashboard(request):
    # Пример: получить все отчёты
    reports = SalesReport.objects.all().order_by('-date')
    total_revenue = sum(r.revenue for r in reports)
    total_expenses = sum(r.expenses for r in reports)
    net_profit = total_revenue - total_expenses

    context = {
        'reports': reports,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
    }
    return render(request, 'analytics/dashboard.html', context)