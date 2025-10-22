from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from .models import OrderAnalytics
from shop.models import Order

@user_passes_test(lambda u: u.is_staff)
def analytics_dashboard(request):
    orders = Order.objects.all()
    total_revenue = sum(float(o.total_price) for o in orders)
    new_orders = orders.filter(status='new').count()
    return render(request, 'analytics/dashboard.html', {
        'total_revenue': total_revenue,
        'new_orders': new_orders,
    })