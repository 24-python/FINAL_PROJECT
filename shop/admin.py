from django.contrib import admin
from .models import Product, Order, OrderItem, Review, SalesReport

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # --- Добавлен payment_status ---
    list_display = ['id', 'user', 'status', 'payment_status', 'created_at', 'total_price']
    list_filter = ['status', 'payment_status', 'created_at']
    # --- /Добавлен payment_status ---
    inlines = [OrderItemInline]
    # --- Добавлено поле payment_status ---
    fields = ['user', 'status', 'payment_status', 'created_at', 'delivery_address', 'delivery_phone', 'delivery_date', 'total_price']
    # --- /Добавлено поле payment_status ---
    readonly_fields = ['created_at', 'total_price']

admin.site.register(Product)
admin.site.register(Review)
admin.site.register(SalesReport)