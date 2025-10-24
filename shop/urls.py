from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.catalog, name='catalog'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    path('add_to_cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('quick_add_to_cart/<int:pk>/', views.quick_add_to_cart, name='quick_add_to_cart'),
    path('cart/', views.view_cart, name='cart'),
    # --- НОВЫЙ маршрут для имитации оплаты ---
    path('initiate_payment/', views.initiate_payment, name='initiate_payment'),
    # --- /НОВЫЙ маршрут ---
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('repeat_order/<int:order_id>/', views.repeat_order, name='repeat_order'),
]