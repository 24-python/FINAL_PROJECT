from django.apps import AppConfig

class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analytics'

    # Опционально: подключить сигналы для автоматического создания отчётов
    # def ready(self):
    #     import analytics.signals