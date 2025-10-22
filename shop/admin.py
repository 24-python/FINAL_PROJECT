from django.contrib import admin
from .models import Product, Order, OrderItem, Review, SalesReport

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'created_at', 'total_price']
    list_filter = ['status', 'created_at']
    inlines = [OrderItemInline]
    fields = ['user', 'status', 'created_at', 'delivery_address', 'delivery_phone', 'delivery_date', 'total_price']
    readonly_fields = ['created_at', 'total_price']

admin.site.register(Product)
admin.site.register(Review)
admin.site.register(SalesReport)