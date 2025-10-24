from django.contrib import admin, messages as admin_messages
from .models import SalesReport

@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'revenue', 'expenses', 'net_profit']
    list_filter = ['date', 'users']
    fields = ['name', 'date', 'users', 'orders', 'revenue', 'expenses']
    readonly_fields = ['revenue', 'net_profit']
    filter_horizontal = ['users', 'orders']
    actions = ['update_selected_reports']

    def net_profit(self, obj):
        return obj.revenue - obj.expenses
    net_profit.short_description = 'Прибыль'

    # --- НОВОЕ: Переопределяем save_model ---
    def save_model(self, request, obj, form, change):
        # Сохраняем объект (включая ManyToMany поля)
        super().save_model(request, obj, form, change)
        # Вызываем update_report после сохранения
        obj.update_report(request=request)
        # Опционально: добавить сообщение
        admin_messages.success(request, f"Отчёт '{obj.name}' обновлён.")

    @admin.action(description="Обновить выбранные отчёты")
    def update_selected_reports(self, request, queryset):
        for report in queryset:
            report.update_report(request=request)
        admin_messages.success(request, f"Обновлено {queryset.count()} отчётов. Проверьте предупреждения для подробной информации.")