# telegram_bot/bot/config.py
import os
from pathlib import Path
from dotenv import load_dotenv  # Добавляем импорт

# Загружаем переменные окружения из .env файла
load_dotenv()


class BotConfig:
    """Конфигурация бота без изменения Django логики"""

    # Токен бота из переменных окружения
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

    # Настройки Django интеграции
    DJANGO_BASE_DIR = Path(__file__).resolve().parent.parent.parent
    MEDIA_ROOT = DJANGO_BASE_DIR / 'media'

    # Пути к изображениям продуктов
    PRODUCTS_IMAGE_DIR = MEDIA_ROOT / 'products'

    # Сообщения бота
    MESSAGES = {
        'start': "👋 Привет! Введите ваш email для авторизации:",
        'email_not_found': "❌ Пользователь с таким email не найден",
        'not_admin': "❌ Вы зарегистрированы на сайте, но не являетесь администратором",
        'auth_success': "✅ Авторизация успешна! Вы будете получать уведомления о новых заказах",
        'already_authorized': "✅ Вы уже авторизованы как администратор",
    }

    @classmethod
    def validate(cls):
        """Проверка конфигурации"""
        if not cls.TELEGRAM_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not set in environment variables")
        if not cls.MEDIA_ROOT.exists():
            print(f"⚠️  MEDIA_ROOT not found: {cls.MEDIA_ROOT}")
            # Не блокируем запуск, но предупреждаем