from django.urls import path
from . import views # Импорт всё ещё нужен, если у вас есть views

app_name = 'analytics'

urlpatterns = [
    # path('dashboard/', views.analytics_dashboard, name='dashboard'), # Пример, раскомментируйте, если нужно
    # Добавьте другие URL для аналитики, если необходимо
]